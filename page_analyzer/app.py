import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
import requests
from dotenv import load_dotenv
from page_analyzer.validator import validate_url, normalize_url
from page_analyzer.parser import parse_url
from page_analyzer.db import UrlRepository


load_dotenv()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')


repo = UrlRepository(DATABASE_URL)


@app.route('/')
def index():
    url = request.args.get('url', '')
    return render_template('index.html', url=url)


@app.route('/urls', methods=['GET', 'POST'])
def show_urls():
    if request.method == 'POST':
        return post_show_urls()
    return get_show_urls()


def get_show_urls():
    urls = repo.get_all_urls()
    return render_template('urls.html', urls=urls)


def post_show_urls():
    url = request.form['url']
    if not validate_url(url):
        flash("Некорректный URL", 'danger')
        return render_template('index.html', url=url), 422
    normalized_url = normalize_url(url)
    existing_url = repo.url_exists(normalized_url)
    if existing_url:
        flash("Страница уже существует", 'warning')
        return redirect(url_for('show_url', id=existing_url[0]))
    url_id = repo.insert_url(normalized_url)
    flash("Страница успешно добавлена", 'success')
    return redirect(url_for('show_url', id=url_id))


@app.route('/urls/<int:id>', methods=['GET'])
def show_url(id):
    url = repo.get_url_by_id(id)
    checks = repo.get_url_checks(id)
    return render_template('url.html', url=url, checks=checks)


@app.route('/urls/<int:id>/checks', methods=['POST'])
def check_url(id):
    url = repo.get_url_by_id(id)['name']
    try:
        response = parse_url(url)
        check_params = {
            'url_id': id,
            'status_code': response['status_code'],
            'h1': response['h1'],
            'title': response['title'],
            'description': response['description'],
        }
        repo.insert_url_check(check_params)
        flash("Страница успешно проверена", 'success')
        return redirect(f'/urls/{id}')
    except requests.exceptions.RequestException:
        flash("Произошла ошибка при проверке", "danger")
        return redirect(url_for("show_url", id=id))
