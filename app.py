from flask import Flask, jsonify
import threading
import time
import sqlite3

import sounddevice as sd
import numpy as np

app = Flask(__name__)

# =====================
# Database
# =====================
def init_db():
    conn = sqlite3.connect("monitor.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def log_event(event):
    conn = sqlite3.connect("monitor.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (event) VALUES (?)", (event,))
    conn.commit()
    conn.close()

init_db()

# =====================
# Audio settings
# =====================
SAMPLE_RATE = 44100
DURATION = 1  # seconds
monitoring = threading.Event()

# =====================
# Audio functions
# =====================
def record_audio():
    frames = int(DURATION * SAMPLE_RATE)
    audio = sd.rec(frames, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()

def is_silence(audio, threshold=0.01):
    volume = np.mean(np.abs(audio))
    return volume < threshold

# =====================
# Background loop
# =====================
def monitor_loop():
    while monitoring.is_set():
        audio = record_audio()

        if is_silence(audio):
            log_event("Silence detected")
            print("Silence detected")

        time.sleep(1)

@app.route("/start", methods=["POST"])
def start_monitoring():
    if not monitoring.is_set():
        monitoring.set()
        threading.Thread(target=monitor_loop, daemon=True).start()
    return jsonify({"status": "Monitoring started"})

@app.route("/stop", methods=["POST"])
def stop_monitoring():
    monitoring.clear()
    return jsonify({"status": "Monitoring stopped"})

@app.route("/logs")
def get_logs():
    conn = sqlite3.connect("monitor.db")
    cursor = conn.cursor()
    cursor.execute("SELECT event, timestamp FROM logs ORDER BY id DESC LIMIT 10")
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

# =====================
# Run app
# =====================
if __name__ == "__main__":
    app.run(port=5000)