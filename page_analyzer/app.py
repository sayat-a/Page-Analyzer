import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    )
import validators
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlparse
from . import db


load_dotenv()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


db.create_db_tables()


@app.route('/')
def index():
    url = request.args.get('url', '')
    return render_template('index.html', url=url)


@app.route('/urls', methods=['GET', 'POST'])
def show_urls():
    if request.method == 'POST':
        url = request.form['url']
        if not validators.url(url) or len(url) > 255:
            flash("Некорректный URL", 'danger')
            return render_template('index.html', url=url), 422
        parsed_url = urlparse(url)
        normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        existing_url = db.url_exists(normalized_url)
        if existing_url:
            flash("Страница уже существует", 'warning')
            return redirect(url_for('show_url', id=existing_url[0]))
        url_id = db.insert_url(normalized_url)
        flash("Страница успешно добавлена", 'success')
        return redirect(url_for('show_url', id=url_id))
    urls = db.get_all_urls()
    return render_template('urls.html', urls=urls)


@app.route('/urls/<int:id>', methods=['GET'])
def show_url(id):
    url = db.get_url_by_id(id)
    checks = db.get_url_checks(id)
    return render_template('url.html', url=url, checks=checks)


@app.route('/urls/<int:id>/checks', methods=['POST'])
def check_url(id):
    url = db.get_url_by_id(id)['name']
    try:
        response = requests.get(url)
        status_code = response.status_code
        soup = BeautifulSoup(response.text, 'html.parser')
        h1 = soup.h1.string if soup.h1 else ''
        title = soup.title.string if soup.title else ''
        description = soup.find('meta', attrs={'name': 'description'})
        description = description['content'] if description else ''
        db.insert_url_check(id, status_code, h1, title, description)
        flash("Страница успешно проверена", 'success')
        return redirect(f'/urls/{id}')
    except requests.RequestException:
        flash("Произошла ошибка при проверке", 'danger')
        return redirect(f'/urls/{id}')
