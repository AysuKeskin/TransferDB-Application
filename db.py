import os

import pymysql
import pymysql.cursors
from flask import g

DB_CONFIG = {
    'host': 'localhost',
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'DB'),
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit': False,
    'charset': 'utf8mb4',
}


def get_db():
    """Return per-request DB connection stored in Flask g."""
    if 'db' not in g:
        g.db = pymysql.connect(**DB_CONFIG)
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def execute_query(query, params=None):
    """Execute a write query (INSERT/UPDATE/DELETE). Auto-commits."""
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(query, params)
    conn.commit()


def execute_read(query, params=None):
    """Execute a SELECT query. Returns list of dicts."""
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_read_one(query, params=None):
    """Execute a SELECT query. Returns one dict or None."""
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()
