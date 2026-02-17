# FarmIntel - MySQL connection using PyMySQL (no system MySQL libs needed)
import pymysql.cursors
from flask import g
from config import Config

def get_db():
    """Get current request DB connection (DictCursor)."""
    if 'db' not in g:
        g.db = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            cursorclass=pymysql.cursors.DictCursor,
        )
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    app.teardown_appcontext(close_db)

class MySQL:
    """Wrapper so existing code using mysql.connection.cursor() still works."""
    @property
    def connection(self):
        return get_db()

mysql = MySQL()
