import psycopg2
import datetime
import os
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from contextlib import contextmanager


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


@contextmanager
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def create_db_tables():
    with get_db_connection() as conn:
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


def get_all_urls():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT urls.id, urls.name, last_check.created_at AS last_check,
                   last_check.status_code
                FROM urls
                LEFT JOIN (
                    SELECT DISTINCT ON (url_id) url_id, created_at, status_code
                    FROM url_checks
                    ORDER BY url_id, created_at DESC
                    ) AS last_check ON urls.id = last_check.url_id
                ORDER BY urls.id DESC
                """)
            urls = cur.fetchall()
        return urls


def insert_url(url):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO urls (name, created_at) VALUES (%s, %s)
                RETURNING id
                """, (url, datetime.datetime.now()))
            url_id = cur.fetchone()[0]
            conn.commit()
            return url_id


def get_url_by_id(url_id):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
            url = cur.fetchone()
    return url


def get_url_checks(url_id):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""SELECT * FROM url_checks WHERE url_id = %s
                        ORDER BY created_at DESC""", (url_id,))
            checks = cur.fetchall()
        return checks


def insert_url_check(url_id, status_code, h1, title, description):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO url_checks (url_id, status_code, h1,
                                        title, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (url_id, status_code, h1, title,
                      description, datetime.datetime.now()))
            conn.commit()


def url_exists(url):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM urls WHERE name = %s", (url,))
            existing_url = cur.fetchone()
        return existing_url
