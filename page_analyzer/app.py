import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    flash,
    get_flashed_messages
    )
import psycopg2
import validators
import datetime
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


def create_table_urls():
    with conn.cursor() as cur:
        with open('../database.sql') as file:
            sql = file.read()
            try:
                cur.execute(sql)
                conn.commit()
            except Exception as e:
                conn.rollback()  # Откат транзакции при ошибке
                print(f"Ошибка при создании таблицы: {e}")

# Инициализируем базу данных при запуске приложения
create_table_urls()

@app.route('/')
def index():
    return render_template('/index.html')


@app.route('/urls', methods=['GET', 'POST'])
def show_urls():
    if request.method == 'POST':
        url = request.form['url']
        if not validators.url(url) or len(url) > 255:
            return "Invalid URL", 400
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s)", (url, datetime.datetime.now()))
                conn.commit()
            # После добавления URL перенаправляем на маршрут /urls
            return redirect('/urls')
        except Exception as e:
            conn.rollback()  # Откат транзакции при ошибке
            return f"Ошибка базы данных: {e}", 500
    
    # Обработка GET-запроса для отображения списка URL
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM urls ORDER BY id DESC")
            urls = cur.fetchall()
            return render_template('urls.html', urls=urls)
    except Exception as e:
        conn.rollback()  # Откат транзакции при ошибке
        return f"Ошибка базы данных: {e}", 500
