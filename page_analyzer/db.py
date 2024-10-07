import datetime
import psycopg2
from psycopg2.extras import DictCursor


class DatabaseConnectionManager:
    def __init__(self, database_url):
        self.database_url = database_url

    def __enter__(self):
        self.conn = psycopg2.connect(self.database_url)
        self.cur = self.conn.cursor(cursor_factory=DictCursor)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.cur.close()
        self.conn.close()


class UrlRepository:
    def __init__(self, database_url):
        self.database_url = database_url

    def get_all_urls(self):
        with DatabaseConnectionManager(self.database_url) as conn:
            conn.cur.execute("""
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
            urls = conn.cur.fetchall()
        return urls

    def insert_url(self, url):
        with DatabaseConnectionManager(self.database_url) as conn:
            conn.cur.execute("""
                INSERT INTO urls (name, created_at) VALUES (%s, %s)
                RETURNING id
            """, (url, datetime.datetime.now()))
            url_id = conn.cur.fetchone()[0]
        return url_id

    def get_url_by_id(self, url_id):
        with DatabaseConnectionManager(self.database_url) as conn:
            conn.cur.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
            url = conn.cur.fetchone()
        return url

    def get_url_checks(self, url_id):
        with DatabaseConnectionManager(self.database_url) as conn:
            conn.cur.execute("""
                SELECT * FROM url_checks WHERE url_id = %s
                ORDER BY created_at DESC
            """, (url_id,))
            checks = conn.cur.fetchall()
        return checks

    def insert_url_check(self, check_params):
        with DatabaseConnectionManager(self.database_url) as conn:
            conn.cur.execute("""
                INSERT INTO url_checks (url_id, status_code, h1,
                                        title, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                check_params['url_id'],
                check_params['status_code'],
                check_params['h1'],
                check_params['title'],
                check_params['description'],
                datetime.datetime.now()))

    def url_exists(self, url):
        with DatabaseConnectionManager(self.database_url) as conn:
            conn.cur.execute("SELECT id FROM urls WHERE name = %s", (url,))
            existing_url = conn.cur.fetchone()
        return existing_url
