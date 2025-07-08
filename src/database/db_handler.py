# src/database/db_handler.py
import sqlite3
import os
from datetime import datetime

DB_PATH = 'snap.db'

def db_exists():
    """Vérifie l'existence de la base de données."""
    return os.path.exists(DB_PATH)

def init_db():
    """Crée la table des événements si elle n'existe pas."""
    if not db_exists():
        print(f"Création de la base de données : {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp    INTEGER NOT NULL,
            source_type  TEXT NOT NULL,
            content      TEXT,
            vectorized   BOOLEAN DEFAULT FALSE,
            media_path   TEXT
        )
    ''')
    # Créer un index sur timestamp pour optimiser les requêtes
    c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)')
    conn.commit()
    conn.close()

def store_event(timestamp: int, source_type: str, content: str | None = None, vectorized: bool = False, media_path: str | None = None):
    """Stocke un événement dans la base de données."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        '''INSERT INTO events (timestamp, source_type, content, vectorized, media_path)
           VALUES (?, ?, ?, ?, ?)''',
        (timestamp, source_type, content, vectorized, media_path)
    )
    conn.commit()
    conn.close()
    print(f"💾 Événement stocké dans la base de données pour le timestamp {timestamp} (type: {source_type})")

def get_event_by_id(event_id: int):
    """Récupère un événement par son ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM events WHERE id = ?', (event_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'timestamp': result[1],
            'source_type': result[2],
            'content': result[3],
            'vectorized': result[4],
            'media_path': result[5]
        }
    return None

def get_all_events():
    """Récupère tous les événements de la base de données."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM events ORDER BY timestamp DESC')
    results = c.fetchall()
    conn.close()
    
    events = []
    for result in results:
        events.append({
            'id': result[0],
            'timestamp': result[1],
            'source_type': result[2],
            'content': result[3],
            'vectorized': result[4],
            'media_path': result[5]
        })
    return events
