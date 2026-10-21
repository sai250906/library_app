import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'library.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows dict-like access (replaces dictionary=True)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn