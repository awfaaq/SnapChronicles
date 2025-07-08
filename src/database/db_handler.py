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
    """Check if the database exists."""
    return os.path.exists(DB_PATH)

def init_db():
    """Create the events table if it doesn't exist."""
    if not db_exists():
        print(f"Creating database: {DB_PATH}")
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
    # Create an index on timestamp to optimize queries
    c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)')
    conn.commit()
    conn.close()

def store_event(timestamp: int, source_type: str, content: str | None = None, vectorized: bool = False, media_path: str | None = None, auto_vectorize: bool = True):
    """Store an event in the database and automatically vectorize it if possible."""
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
        raise RuntimeError("Failed to retrieve event ID after insertion")
    
    print(f"💾 Event stored in database for timestamp {timestamp} (type: {source_type}, ID: {event_id})")
    
    # Automatically vectorize text content if available and requested
    if auto_vectorize and content and content.strip() and not vectorized:
        vector_handler = get_vector_handler()
        if vector_handler:
            try:
                vector_id = vector_handler.vectorize_and_store(event_id, content)
                if vector_id:
                    print(f"🧠 Content automatically vectorized (vector_id: {vector_id})")
                else:
                    print(f"⚠️ Vectorization failed for event {event_id}")
            except Exception as e:
                print(f"❌ Error during vectorization for event {event_id}: {e}")
        else:
            print(f"⚠️ Vector handler not available - vectorization skipped for event {event_id}")
    
    return event_id

def get_event_by_id(event_id: int):
    """Retrieve an event by its ID."""
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
    """Retrieve all events from the database."""
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
    """Search for similar events.

    Steps:
    1. First launch a search on the original question.
    2. Call a local LLM (via *llama-cpp*) to generate other queries.
       The model is prompted to output **only** queries, one per line.
    3. Each query is vectorized then searched in the FAISS index.
    4. We aggregate results keeping the best similarity for each *event*.

    This improves recall compared to the simple initial question.
    """

    vector_handler = get_vector_handler()
    if not vector_handler:
        print("⚠️ Vector handler not available - vector search impossible")
        return []

    # 1) Set of queries: user question + LLM queries (if available)
    queries: list[str] = [query_text]

    try:
        from llm.query_expander import expand_query
        extra_phrases = expand_query(query_text)
        if extra_phrases:
            print(f"🧠 LLM generated {len(extra_phrases)} additional queries for search")
            queries.extend(extra_phrases)
    except Exception as llm_err:
        print(f"⚠️ Query expansion via LLM impossible: {llm_err}")

    # 2) Launch search for each query and aggregate
    aggregated: dict[int, dict] = {}

    for q in queries:
        try:
            partial_results = vector_handler.search_similar(q, top_k)
            for res in partial_results:
                eid = res['event_id']
                # Keep the best similarity (smallest distance) per event
                if eid not in aggregated or res['similarity_score'] < aggregated[eid]['similarity_score']:
                    aggregated[eid] = res
        except Exception as e:
            print(f"⚠️ Search error for query '{q}': {e}")

    # 3) Transform to list sorted by increasing similarity
    results = sorted(aggregated.values(), key=lambda r: r['similarity_score'])

    if results:
        print(f"🔍 Found {len(results)} results (after aggregation) for: '{query_text}'")
    else:
        print(f"❌ No results found for: '{query_text}'")

    return results[:top_k]

def get_vector_stats():
    """Retrieve statistics on stored vectors."""
    vector_handler = get_vector_handler()
    if not vector_handler:
        print("⚠️ Vector handler not available")
        return None
    
    try:
        stats = vector_handler.get_vector_stats()
        return stats
    except Exception as e:
        print(f"❌ Error retrieving statistics: {e}")
        return None

def vectorize_existing_events(force_revectorize: bool = False):
    """Vectorize existing events that haven't been vectorized yet."""
    vector_handler = get_vector_handler()
    if not vector_handler:
        print("⚠️ Vector handler not available")
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
    
    print(f"🧠 Vectorizing {len(events_to_vectorize)} events...")
    
    vectorized_count = 0
    for event_id, content in events_to_vectorize:
        try:
            vector_id = vector_handler.vectorize_and_store(event_id, content)
            if vector_id:
                vectorized_count += 1
                print(f"✅ Event {event_id} vectorized (vector_id: {vector_id})")
            else:
                print(f"⚠️ Vectorization failed for event {event_id}")
        except Exception as e:
            print(f"❌ Error for event {event_id}: {e}")
    
    print(f"🎉 Vectorization completed: {vectorized_count}/{len(events_to_vectorize)} events processed")
