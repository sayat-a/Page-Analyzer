import os
from flask import Flask, render_template


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    render_template('/index.html')
