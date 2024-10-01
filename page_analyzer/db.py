import datetime
import os
from psycopg2.extras import DictCursor


class UrlRepository:
    def __init__(self, conn):
        self.conn = conn

    def create_db_tables(self):
        with self.conn.cursor() as cur:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            sql_file_path = os.path.join(base_dir, '../database.sql')
            with open(sql_file_path) as file:
                sql = file.read()
                try:
                    cur.execute(sql)
                    self.conn.commit()
                except Exception as e:
                    self.conn.rollback()
                    print(f"Ошибка при создании таблицы: {e}")

    def get_all_urls(self):
        with self.conn.cursor() as cur:
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

    def insert_url(self, url):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO urls (name, created_at) VALUES (%s, %s)
                RETURNING id
                """, (url, datetime.datetime.now()))
            url_id = cur.fetchone()[0]
            self.conn.commit()
        return url_id

    def get_url_by_id(self, url_id):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
            url = cur.fetchone()
        return url

    def get_url_checks(self, url_id):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""SELECT * FROM url_checks WHERE url_id = %s
                        ORDER BY created_at DESC""", (url_id,))
            checks = cur.fetchall()
        return checks

    def insert_url_check(self, url_id, status_code, h1, title, description):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO url_checks (url_id, status_code, h1,
                                        title, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (url_id, status_code, h1, title,
                      description, datetime.datetime.now()))
            self.conn.commit()

    def url_exists(self, url):
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM urls WHERE name = %s", (url,))
            existing_url = cur.fetchone()
        return existing_url
