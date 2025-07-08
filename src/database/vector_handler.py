import sqlite3
import numpy as np
import faiss
import pickle
import os
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Optional, Dict, Any
import time

DB_PATH = 'snap.db'
VECTOR_INDEX_PATH = 'vectors.faiss'
MODEL_NAME = 'all-MiniLM-L6-v2'

class VectorHandler:
    def __init__(self):
        """Initialize the vector handler with model and index."""
        self.model: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.Index] = None
        self.dimension: Optional[int] = None
        self._load_model()
        self._init_vector_table()
        self._load_or_create_index()
    
    def _load_model(self):
        """Load the sentence transformer model."""
        print("🧠 Loading sentence transformer model...")
        start_time = time.time()
        self.model = SentenceTransformer(MODEL_NAME)
        load_time = (time.time() - start_time) * 1000
        print(f"✅ Model loaded in {load_time:.2f} ms")
    
    def _init_vector_table(self):
        """Create the vectors table if it doesn't exist."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                vector BLOB NOT NULL,
                vector_dimension INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE
            )
        ''')
        # Create index on event_id for fast lookups
        c.execute('CREATE INDEX IF NOT EXISTS idx_vectors_event_id ON vectors(event_id)')
        conn.commit()
        conn.close()
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create a new one."""
        if self.model is None:
            raise RuntimeError("Model must be loaded before creating index")
            
        # First, determine dimension by encoding a sample text
        sample_vector = self.model.encode(["sample text"], convert_to_tensor=False)
        self.dimension = sample_vector.shape[1]
        
        if os.path.exists(VECTOR_INDEX_PATH):
            print(f"📚 Loading existing FAISS index from {VECTOR_INDEX_PATH}")
            self.index = faiss.read_index(VECTOR_INDEX_PATH)
        else:
            print(f"🆕 Creating new FAISS index with dimension {self.dimension}")
            self.index = faiss.IndexFlatL2(self.dimension)
            self._rebuild_index_from_db()
    
    def _rebuild_index_from_db(self):
        """Rebuild FAISS index from vectors stored in database."""
        if self.index is None:
            raise RuntimeError("Index must be initialized before rebuilding")
            
        print("🔄 Rebuilding FAISS index from database...")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT event_id, vector FROM vectors ORDER BY id')
        results = c.fetchall()
        conn.close()
        
        if results:
            vectors = []
            for event_id, vector_blob in results:
                vector = pickle.loads(vector_blob)
                vectors.append(vector)
            
            vectors_array = np.array(vectors, dtype=np.float32)
            self.index.add(vectors_array)
            print(f"✅ Rebuilt index with {len(vectors)} vectors")
        else:
            print("📭 No existing vectors found in database")
    
    def vectorize_text(self, text: str) -> Optional[np.ndarray]:
        """Convert text to vector representation."""
        if not text or not text.strip():
            return None
        
        if self.model is None:
            raise RuntimeError("Model must be loaded before vectorizing text")
        
        start_time = time.time()
        vector = self.model.encode([text.strip()], convert_to_tensor=False)[0]
        vectorize_time = (time.time() - start_time) * 1000
        print(f"🧠 Vectorized text in {vectorize_time:.2f} ms")
        return vector.astype(np.float32)
    
    def store_vector(self, event_id: int, vector: np.ndarray) -> Optional[int]:
        """Store vector in database and add to FAISS index."""
        if self.index is None:
            raise RuntimeError("Index must be initialized before storing vectors")
            
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Serialize vector
        vector_blob = pickle.dumps(vector)
        
        # Store in database
        c.execute('''
            INSERT INTO vectors (event_id, vector, vector_dimension)
            VALUES (?, ?, ?)
        ''', (event_id, vector_blob, len(vector)))
        
        vector_id = c.lastrowid
        conn.commit()
        conn.close()
        
        # Add to FAISS index
        self.index.add(np.array([vector], dtype=np.float32))
        
        # Save updated index
        self._save_index()
        
        print(f"💾 Vector stored for event {event_id} (vector_id: {vector_id})")
        return vector_id
    
    def vectorize_and_store(self, event_id: int, text: str) -> Optional[int]:
        """Vectorize text and store both in database and FAISS index."""
        if not text or not text.strip():
            print(f"⚠️ Empty text provided for event {event_id}, skipping vectorization")
            return None
        
        # Vectorize the text
        vector = self.vectorize_text(text)
        if vector is None:
            return None
        
        # Store the vector
        vector_id = self.store_vector(event_id, vector)
        
        # Update event to mark as vectorized
        self._mark_event_vectorized(event_id)
        
        return vector_id
    
    def _mark_event_vectorized(self, event_id: int):
        """Mark an event as vectorized in the events table."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE events SET vectorized = TRUE WHERE id = ?', (event_id,))
        conn.commit()
        conn.close()
    
    def _save_index(self):
        """Save the FAISS index to disk."""
        faiss.write_index(self.index, VECTOR_INDEX_PATH)
    
    def search_similar(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar text content using vector similarity."""
        if not query_text or not query_text.strip():
            return []
        
        if self.index is None:
            raise RuntimeError("Index must be initialized before searching")
        
        # Vectorize query
        start_time = time.time()
        query_vector = self.vectorize_text(query_text)
        if query_vector is None:
            return []
        
        # Search in FAISS index
        query_array = np.array([query_vector], dtype=np.float32)
        distances, indices = self.index.search(query_array, min(top_k, self.index.ntotal))
        
        search_time = (time.time() - start_time) * 1000
        print(f"🔍 Search completed in {search_time:.2f} ms")
        
        # Get corresponding events from database
        results = []
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get all vectors with event info
        c.execute('''
            SELECT v.event_id, e.timestamp, e.source_type, e.content, e.media_path, v.id as vector_id
            FROM vectors v
            JOIN events e ON v.event_id = e.id
            ORDER BY v.id
        ''')
        vector_events = c.fetchall()
        conn.close()
        
        # Match indices to events
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(vector_events):
                event_data = vector_events[idx]
                results.append({
                    'event_id': event_data[0],
                    'timestamp': event_data[1],
                    'source_type': event_data[2],
                    'content': event_data[3],
                    'media_path': event_data[4],
                    'vector_id': event_data[5],
                    'similarity_score': float(distance),
                    'rank': i + 1
                })
        
        return results
    
    def get_vector_stats(self) -> Dict[str, Any]:
        """Get statistics about stored vectors."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Count total vectors
        c.execute('SELECT COUNT(*) FROM vectors')
        total_vectors = c.fetchone()[0]
        
        # Count vectorized events by source type
        c.execute('''
            SELECT e.source_type, COUNT(v.id) as vector_count
            FROM events e
            LEFT JOIN vectors v ON e.id = v.event_id
            WHERE v.id IS NOT NULL
            GROUP BY e.source_type
        ''')
        by_source = dict(c.fetchall())
        
        # Count non-vectorized events
        c.execute('SELECT COUNT(*) FROM events WHERE vectorized = FALSE')
        non_vectorized = c.fetchone()[0]
        
        conn.close()
        
        return {
            'total_vectors': total_vectors,
            'by_source_type': by_source,
            'non_vectorized_events': non_vectorized,
            'faiss_index_size': self.index.ntotal if self.index else 0,
            'vector_dimension': self.dimension
        }

# Singleton instance
_vector_handler = None

def get_vector_handler() -> VectorHandler:
    """Get or create the global vector handler instance."""
    global _vector_handler
    if _vector_handler is None:
        _vector_handler = VectorHandler()
    return _vector_handler 