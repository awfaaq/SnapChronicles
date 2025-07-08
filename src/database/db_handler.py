# src/database/db_handler.py
import sqlite3
import os
from datetime import datetime
from typing import Optional

DB_PATH = 'snap.db'

# Import vector handler (will be lazily loaded)
_vector_handler = None

def get_vector_handler():
    """Get the vector handler instance, loading it only when needed."""
    global _vector_handler
    if _vector_handler is None:
        try:
            from .vector_handler import get_vector_handler as get_vh
            _vector_handler = get_vh()
        except ImportError as e:
            print(f"⚠️ Vector handler not available: {e}")
            _vector_handler = False  # Mark as unavailable
    return _vector_handler if _vector_handler is not False else None

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

def store_event(timestamp: int, source_type: str, content: str | None = None, vectorized: bool = False, media_path: str | None = None, auto_vectorize: bool = True):
    """Stocke un événement dans la base de données et le vectorise automatiquement si possible."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        '''INSERT INTO events (timestamp, source_type, content, vectorized, media_path)
           VALUES (?, ?, ?, ?, ?)''',
        (timestamp, source_type, content, vectorized, media_path)
    )
    event_id = c.lastrowid
    conn.commit()
    conn.close()
    
    if event_id is None:
        raise RuntimeError("Échec de récupération de l'ID de l'événement après insertion")
    
    print(f"💾 Événement stocké dans la base de données pour le timestamp {timestamp} (type: {source_type}, ID: {event_id})")
    
    # Automatically vectorize text content if available and requested
    if auto_vectorize and content and content.strip() and not vectorized:
        vector_handler = get_vector_handler()
        if vector_handler:
            try:
                vector_id = vector_handler.vectorize_and_store(event_id, content)
                if vector_id:
                    print(f"🧠 Contenu vectorisé automatiquement (vector_id: {vector_id})")
                else:
                    print(f"⚠️ Échec de la vectorisation pour l'événement {event_id}")
            except Exception as e:
                print(f"❌ Erreur lors de la vectorisation pour l'événement {event_id}: {e}")
        else:
            print(f"⚠️ Vector handler non disponible - vectorisation ignorée pour l'événement {event_id}")
    
    return event_id

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

def search_similar_events(query_text: str, top_k: int = 5):
    """Recherche des événements similaires.

    Étapes :
    1. On lance d'abord une recherche sur la question originale.
    2. On appelle un LLM local (via *llama-cpp*) pour générer d'autres requêtes.
       Le modèle est invité à sortir **uniquement** des requêtes, une par ligne.
    3. Chaque requête est vectorisée puis recherchée dans l'index FAISS.
    4. On agrège les résultats en gardant la meilleure similarité pour chaque *event*.

    Cela améliore le rappel par rapport à la simple question initiale.
    """

    vector_handler = get_vector_handler()
    if not vector_handler:
        print("⚠️ Vector handler non disponible - recherche vectorielle impossible")
        return []

    # 1) Ensemble de requêtes : question de l'utilisateur + requêtes LLM (si dispo)
    queries: list[str] = [query_text]

    try:
        from llm.query_expander import expand_query
        extra_phrases = expand_query(query_text)
        if extra_phrases:
            print(f"🧠 LLM a généré {len(extra_phrases)} requêtes supplémentaires pour la recherche")
            queries.extend(extra_phrases)
    except Exception as llm_err:
        print(f"⚠️ Expansion de requête via LLM impossible : {llm_err}")

    # 2) Lancer la recherche pour chaque requête et agréger
    aggregated: dict[int, dict] = {}

    for q in queries:
        try:
            partial_results = vector_handler.search_similar(q, top_k)
            for res in partial_results:
                eid = res['event_id']
                # Garder la meilleure similarité (plus petite distance) par événement
                if eid not in aggregated or res['similarity_score'] < aggregated[eid]['similarity_score']:
                    aggregated[eid] = res
        except Exception as e:
            print(f"⚠️ Erreur de recherche pour la requête '{q}': {e}")

    # 3) Transformer en liste triée par similarité croissante
    results = sorted(aggregated.values(), key=lambda r: r['similarity_score'])

    if results:
        print(f"🔍 Trouvé {len(results)} résultats (après agrégation) pour: '{query_text}'")
    else:
        print(f"❌ Aucun résultat trouvé pour: '{query_text}'")

    return results[:top_k]

def get_vector_stats():
    """Récupère les statistiques sur les vecteurs stockés."""
    vector_handler = get_vector_handler()
    if not vector_handler:
        print("⚠️ Vector handler non disponible")
        return None
    
    try:
        stats = vector_handler.get_vector_stats()
        return stats
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des statistiques: {e}")
        return None

def vectorize_existing_events(force_revectorize: bool = False):
    """Vectorise les événements existants qui ne l'ont pas encore été."""
    vector_handler = get_vector_handler()
    if not vector_handler:
        print("⚠️ Vector handler non disponible")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get events that need vectorization
    if force_revectorize:
        c.execute('SELECT id, content FROM events WHERE content IS NOT NULL AND content != ""')
    else:
        c.execute('SELECT id, content FROM events WHERE content IS NOT NULL AND content != "" AND vectorized = FALSE')
    
    events_to_vectorize = c.fetchall()
    conn.close()
    
    print(f"🧠 Vectorisation de {len(events_to_vectorize)} événements...")
    
    vectorized_count = 0
    for event_id, content in events_to_vectorize:
        try:
            vector_id = vector_handler.vectorize_and_store(event_id, content)
            if vector_id:
                vectorized_count += 1
                print(f"✅ Événement {event_id} vectorisé (vector_id: {vector_id})")
            else:
                print(f"⚠️ Échec de la vectorisation pour l'événement {event_id}")
        except Exception as e:
            print(f"❌ Erreur pour l'événement {event_id}: {e}")
    
    print(f"🎉 Vectorisation terminée: {vectorized_count}/{len(events_to_vectorize)} événements traités")
