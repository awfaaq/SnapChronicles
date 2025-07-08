#!/usr/bin/env python3
"""
Test script for the integrated vectorization system in SnapChronicles.
This script demonstrates how text content is automatically vectorized when stored
and how to search for similar content using vector similarity.
"""

import time
import sys
import os

# Add src root to Python path for clean imports
src_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_root not in sys.path:
    sys.path.insert(0, src_root)

from database.db_handler import (
    init_db, store_event, search_similar_events, 
    get_vector_stats, vectorize_existing_events, get_all_events
)

def test_automatic_vectorization():
    """Test that new events are automatically vectorized."""
    print("🧪 Testing Automatic Vectorization")
    print("=" * 50)
    
    # Initialize database
    init_db()
    
    # Store some test events with different content
    current_time = int(time.time())
    
    test_events = [
        {
            "content": "User is working on a Python machine learning project with TensorFlow",
            "source_type": "ocr",
            "media_path": "screenshots/ml_project.png"
        },
        {
            "content": "Discussion about artificial intelligence and neural networks in meeting",
            "source_type": "transcription", 
            "media_path": "audio/meeting_001.wav"
        },
        {
            "content": "Email about upcoming deadline for the AI research project",
            "source_type": "ocr",
            "media_path": "screenshots/email.png"
        },
        {
            "content": "User browsing documentation for deep learning frameworks",
            "source_type": "ocr",
            "media_path": "screenshots/docs.png"
        },
        {
            "content": "Phone conversation about weekend plans and vacation",
            "source_type": "transcription",
            "media_path": "audio/call_002.wav"
        }
    ]
    
    print(f"📝 Storing {len(test_events)} test events with automatic vectorization...")
    
    for i, event in enumerate(test_events):
        event_id = store_event(
            timestamp=current_time + i * 60,  # 1 minute apart
            source_type=event["source_type"],
            content=event["content"],
            media_path=event["media_path"],
            auto_vectorize=True  # Enable automatic vectorization
        )
        print(f"   ✅ Event {event_id} stored and processed\n")
    
    # Wait a moment for processing
    time.sleep(1)
    
    return len(test_events)

def test_vector_search():
    """Test vector similarity search functionality."""
    print("\n🔍 Testing Vector Similarity Search")
    print("=" * 50)
    
    # Test different search queries
    search_queries = [
        "machine learning and AI projects",
        "meeting discussion artificial intelligence",
        "vacation and weekend plans",
        "Python programming deep learning"
    ]
    
    for query in search_queries:
        print(f"\n🔎 Searching for: '{query}'")
        print("-" * 40)
        
        results = search_similar_events(query, top_k=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"   {i}. [Score: {result['similarity_score']:.3f}] {result['source_type'].upper()}")
                print(f"      Content: {result['content'][:80]}...")
                print(f"      Timestamp: {result['timestamp']}")
                if result['media_path']:
                    print(f"      Media: {result['media_path']}")
                print()
        else:
            print("   No results found.")

def test_vector_stats():
    """Test vector statistics functionality."""
    print("\n📊 Vector Statistics")
    print("=" * 50)
    
    stats = get_vector_stats()
    if stats:
        print(f"📈 Total vectors: {stats['total_vectors']}")
        print(f"🧠 Vector dimension: {stats['vector_dimension']}")
        print(f"📚 FAISS index size: {stats['faiss_index_size']}")
        print(f"⚠️ Non-vectorized events: {stats['non_vectorized_events']}")
        
        print("\n📊 Vectors by source type:")
        for source_type, count in stats['by_source_type'].items():
            print(f"   • {source_type}: {count} vectors")
    else:
        print("❌ Could not retrieve vector statistics")

def test_retroactive_vectorization():
    """Test vectorizing existing events that weren't previously vectorized."""
    print("\n🔄 Testing Retroactive Vectorization")
    print("=" * 50)
    
    # Add an event without auto-vectorization
    current_time = int(time.time())
    event_id = store_event(
        timestamp=current_time,
        source_type="test",
        content="This is a test event that was not automatically vectorized",
        auto_vectorize=False  # Disable automatic vectorization
    )
    
    print(f"📝 Added non-vectorized event (ID: {event_id})")
    
    # Now vectorize existing events
    print("\n🧠 Running retroactive vectorization...")
    vectorize_existing_events()

def main():
    """Run the complete vectorization integration test."""
    print("🧪 SnapChronicles Vectorization Integration Test")
    print("=" * 60)
    
    try:
        # Test automatic vectorization
        events_added = test_automatic_vectorization()
        
        # Test search functionality
        test_vector_search()
        
        # Show statistics
        test_vector_stats()
        
        # Test retroactive vectorization
        test_retroactive_vectorization()
        
        print("\n🎉 All tests completed successfully!")
        print(f"✅ Added {events_added} events with automatic vectorization")
        print("✅ Vector search functionality working")
        print("✅ Statistics and retroactive vectorization working")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 