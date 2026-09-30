import os
import sqlite3
from pathlib import Path

import pandas as pd


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "finsight.db"

CSV_PATH = DATA_DIR / "transactions.csv"


# ============================================================
# Database configuration
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")


def using_postgresql():
    """Return True when DATABASE_URL is configured."""
    return bool(DATABASE_URL)


# ============================================================
# Database connection
# ============================================================

def get_connection():
    """
    Connect to PostgreSQL when DATABASE_URL is available.
    Otherwise, use local SQLite.
    """

    if using_postgresql():
        import psycopg2

        database_url = DATABASE_URL

        # Some PostgreSQL providers may return postgres://
        # while psycopg2 expects postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://",
                "postgresql://",
                1
            )

        return psycopg2.connect(database_url)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    return sqlite3.connect(DB_PATH)


# ============================================================
# Initialize database
# ============================================================

def initialize_database():
    """Create the transactions table if it does not exist."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if using_postgresql():
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    type TEXT NOT NULL,
                    amount DOUBLE PRECISION NOT NULL,
                    payment_method TEXT NOT NULL
                )
                """
            )
        else:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    payment_method TEXT NOT NULL
                )
                """
            )

        connection.commit()

    finally:
        connection.close()


# ============================================================
# Import CSV only when database is empty
# ============================================================

def import_csv_if_database_empty(csv_path=CSV_PATH):
    """
    Import the CSV into the database only when the transactions
    table is empty.
    """

    initialize_database()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM transactions")
        count = cursor.fetchone()[0]

    finally:
        connection.close()

    if count > 0:
        return

    if not Path(csv_path).exists():
        return

    df = pd.read_csv(csv_path)

    replace_transactions(df)


# ============================================================
# Replace all transactions
# ============================================================

def replace_transactions(df):
    """
    Replace all existing transactions with the supplied DataFrame.
    """

    initialize_database()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Remove existing transactions
        cursor.execute("DELETE FROM transactions")

        if using_postgresql():
            insert_query = """
                INSERT INTO transactions
                (date, description, category, type, amount, payment_method)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
        else:
            insert_query = """
                INSERT INTO transactions
                (date, description, category, type, amount, payment_method)
                VALUES (?, ?, ?, ?, ?, ?)
            """

        records = []

        for _, row in df.iterrows():
            date_value = pd.to_datetime(row["date"]).strftime("%Y-%m-%d")

            records.append(
                (
                    date_value,
                    str(row["description"]),
                    str(row["category"]),
                    str(row["type"]),
                    float(row["amount"]),
                    str(row["payment_method"]),
                )
            )

        if using_postgresql():
            cursor.executemany(insert_query, records)
        else:
            cursor.executemany(insert_query, records)

        connection.commit()

    finally:
        connection.close()


# ============================================================
# Get transactions
# ============================================================

def get_transactions():
    """
    Return all transactions as a list of dictionaries.
    """

    connection = get_connection()

    try:
        if using_postgresql():
            query = """
                SELECT
                    id,
                    date,
                    description,
                    category,
                    type,
                    amount,
                    payment_method
                FROM transactions
                ORDER BY date DESC, id DESC
            """

            df = pd.read_sql_query(query, connection)

        else:
            query = """
                SELECT
                    id,
                    date,
                    description,
                    category,
                    type,
                    amount,
                    payment_method
                FROM transactions
                ORDER BY date DESC, id DESC
            """

            df = pd.read_sql_query(query, connection)

    finally:
        connection.close()

    return df.to_dict(orient="records")