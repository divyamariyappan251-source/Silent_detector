from flask import Flask, jsonify
import threading
import time

import sounddevice as sd
import numpy as np

from backend.silence_detector import SilenceDetector
from backend.notifier import Notifier
from backend.database import init_db, log_event

app = Flask(__name__)
init_db()

monitoring = threading.Event()

SAMPLE_RATE = 44100
DURATION = 1  # seconds

def record_audio(duration=DURATION, rate=SAMPLE_RATE):
    frames = int(duration * rate)
    audio = sd.rec(frames, samplerate=rate, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()

def monitor_loop():
    detector = SilenceDetector(sample_rate=SAMPLE_RATE)
    notifier = Notifier()

    while monitoring.is_set():
        audio_data = record_audio()

        if detector.check_silence(audio_data):
            notifier.send("Silence detected in class")
            log_event("Silence detected")

        if not notifier.check_network():
            notifier.send("Network connection issue")
            log_event("Network issue")

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
    import sqlite3
    conn = sqlite3.connect("monitor.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT event, timestamp FROM logs ORDER BY id DESC LIMIT 10"
    )
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

if __name__ == "__main__":
    app.run(port=5000)
