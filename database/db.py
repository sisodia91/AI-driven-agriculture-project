import sqlite3

DB_NAME = "farm_data.db"


def connect_db():
    return sqlite3.connect(DB_NAME)


def create_table():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS farm_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        temperature REAL,
        humidity REAL,
        soil_moisture REAL,
        health_score REAL,
        prediction TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def insert_data(temp, humidity, soil, health, prediction):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO farm_logs (temperature, humidity, soil_moisture, health_score, prediction)
    VALUES (?, ?, ?, ?, ?)
    """, (temp, humidity, soil, health, prediction))

    conn.commit()
    conn.close()