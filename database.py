import sqlite3

DB_NAME = "monitor.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def log_event(event):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO logs (event) VALUES (?)", (event,))

    conn.commit()
    conn.close()

# Run once to create database
if __name__ == "__main__":
    init_db()
    log_event("Silence detected")
    log_event("Network unstable")
    print("Event saved successfully!")