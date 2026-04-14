"""
Shared pytest fixtures for TransferDB tests.

Tests connect directly to MySQL (no Flask app context needed).
Set DB credentials via environment variables if they differ from defaults:
  DB_USER, DB_PASSWORD, DB_NAME
"""
import os
import sys

import pymysql
import pymysql.cursors
import pytest

# Make the project root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

DB_CONFIG = {
    'host': 'localhost',
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'DB'),
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit': False,
    'charset': 'utf8mb4',
}


@pytest.fixture(scope='function')
def db():
    """
    Provides a raw pymysql connection for each test.
    The connection is closed after the test regardless of outcome.
    """
    conn = pymysql.connect(**DB_CONFIG)
    yield conn
    conn.close()
