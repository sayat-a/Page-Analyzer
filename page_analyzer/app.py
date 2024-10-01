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
from page_analyzer import db
from page_analyzer.parser import parse_url


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
        if not validate_url(url) or len(url) > 255:
            flash("Некорректный URL", 'danger')
            return render_template('index.html', url=url), 422
        normalized_url = normalize_url(url)
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
        result = parse_url(url)
        db.insert_url_check(
            id,
            result['status_code'],
            result['h1'],
            result['title'],
            result['description']
            )
        flash("Страница успешно проверена", 'success')
        return redirect(f'/urls/{id}')
    except requests.exceptions.RequestException:
        flash("Произошла ошибка при проверке", "danger")
        return redirect(url_for("show_url", id=id))
