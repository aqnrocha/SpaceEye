import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import OperationalError
from contextlib import contextmanager


load_dotenv()

class Database:

    def __init__(self):
        self.connection = {
            "host": os.getenv("host"),
            "database": os.getenv("database"),
            "user": os.getenv("user"),
            "password": os.getenv("password"),
            "port": os.getenv("port"),
        }

    @contextmanager
    def conn(self):
        conn = psycopg2.connect(**self.connection)
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()