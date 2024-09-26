import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    get_flashed_messages
    )
import psycopg2
import validators
import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


def create_db_tables():
    with conn.cursor() as cur:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file_path = os.path.join(base_dir, '../database.sql')
        with open(sql_file_path) as file:
            sql = file.read()
            try:
                cur.execute(sql)
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"Ошибка при создании таблицы: {e}")


create_db_tables()

@app.route('/')
def index():
    url = request.args.get('url', '')
    return render_template('index.html', url=url)


@app.route('/urls', methods=['GET', 'POST'])
def show_urls():
    if request.method == 'POST':
        url = request.form['url']
        
        # Проверка валидности URL
        if not validators.url(url) or len(url) > 255:
            flash("Некорректный URL", 'danger')  # Сообщение об ошибке
            return redirect(url_for('index', url=url))  # Возврат на главную страницу

        try:
            with conn.cursor() as cur:
                # Проверяем, существует ли уже URL
                cur.execute("SELECT id FROM urls WHERE name = %s", (url,))
                existing_url = cur.fetchone()
                
                if existing_url:
                    flash("Страница уже существует", 'warning')  # Сообщение о существующем URL
                    return redirect(url_for('show_url', id=existing_url[0]))  # Переадресация на существующий URL
                
                # Если URL не существует, добавляем его
                cur.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id", (url, datetime.datetime.now()))
                url_id = cur.fetchone()[0]
                conn.commit()

                flash("Страница успешно добавлена", 'success')  # Сообщение об успехе
                return redirect(url_for('show_url', id=url_id))
        except Exception as e:
            conn.rollback()
            return f"Ошибка базы данных: {e}", 500
    
    # Логика для GET-запроса
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT urls.id, urls.name, last_check.created_at AS last_check, last_check.status_code
                FROM urls
                LEFT JOIN (
                    SELECT DISTINCT ON (url_id) url_id, created_at, status_code
                    FROM url_checks
                    ORDER BY url_id, created_at DESC
                ) AS last_check ON urls.id = last_check.url_id
                ORDER BY urls.id DESC
            """)
            urls = cur.fetchall()
            return render_template('urls.html', urls=urls)
    except Exception as e:
        conn.rollback()
        return f"Ошибка базы данных: {e}", 500


@app.route('/urls/<int:id>', methods=['GET'])
def show_url(id):
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
            url = cur.fetchone()
            cur.execute("SELECT * FROM url_checks WHERE url_id = %s ORDER BY created_at DESC", (id,))
            checks = cur.fetchall()
        return render_template('url.html', url=url, checks=checks)
    except Exception as e:
        return f"Ошибка базы данных: {e}", 500


@app.route('/urls/<int:id>/checks', methods=['POST'])
def check_url(id):
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM urls WHERE id = %s", (id,))
            url = cur.fetchone()[0]
        response = requests.get(url)
        status_code = response.status_code
        soup = BeautifulSoup(response.text, 'html.parser')
        h1 = soup.h1.string if soup.h1 else ''
        title = soup.title.string if soup.title else ''
        description = soup.find('meta', attrs={'name': 'description'})
        description = description['content'] if description else ''
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO url_checks (url_id, status_code, h1, title, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (id, status_code, h1, title, description, datetime.datetime.now()))
            conn.commit()
        flash("Проверка успешно завершена", 'success')
        return redirect(f'/urls/{id}')
    except Exception as e:
        conn.rollback()
        return f"Ошибка при проверке сайта: {e}", 500