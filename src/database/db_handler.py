# src/database/db_handler.py
import sqlite3
import os
from datetime import datetime

DB_PATH = 'snap.db'

def init_db():
    """Crée la table des événements si elle n'existe pas."""
    if not os.path.exists(DB_PATH):
        print(f"Création de la base de données : {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ts        TEXT NOT NULL,
            ocr_text  TEXT,
            asr_text  TEXT,
            summary   TEXT,
            embedding BLOB,
            screenshot_path TEXT,
            audio_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

def store_event(ts: datetime, ocr_text: str, asr_text: str, summary: str, embedding: bytes, screenshot_path: str, audio_path: str):
    """Stocke un événement complet dans la base de données."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        '''INSERT INTO events (ts, ocr_text, asr_text, summary, embedding, screenshot_path, audio_path)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (ts.isoformat(), ocr_text, asr_text, summary, embedding, screenshot_path, audio_path)
    )
    conn.commit()
    conn.close()
    print(f"💾 Événement stocké dans la base de données pour le timestamp {ts.isoformat()}")
