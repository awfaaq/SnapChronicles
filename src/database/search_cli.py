#!/usr/bin/env python3
"""
SnapChronicles Database Search CLI

Interactive command-line tool for searching through captured content using 
natural language queries and vector similarity search.

Usage:
    python search_cli.py

Commands:
    - Enter any natural language query to search
    - Type 'q' to quit
    - Use Ctrl+C to exit
"""

import sys
import os
import signal
from datetime import datetime

# Add src root to Python path for clean imports
src_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_root not in sys.path:
    sys.path.insert(0, src_root)

# Core DB helpers
from database.db_handler import (
    search_similar_events,
    get_vector_stats,
    db_exists,
)

# Query expansion with local LLM (Ollama)
try:
    from llm.query_expander import expand_query
except Exception as _qe_err:  # LLM not available – fallback silently
    expand_query = None  # type: ignore


def format_timestamp(timestamp):
    """Convert Unix timestamp to readable format."""
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return f"Invalid timestamp: {timestamp}"


def truncate_content(content, max_length=100):
    """Truncate content to specified length."""
    if not content:
        return "(No content)"
    
    if len(content) <= max_length:
        return content
    
    return content[:max_length] + "..."


def display_results(results, query):
    """Display search results in a formatted way."""
    if not results:
        print("❌ No results found for your query.")
        print("💡 Try using different keywords or check if your database has vectorized content.")
        return
    
    print(f"\n🔍 Search Results for: '{query}'")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        # Format the output
        event_id = result['event_id']
        media_path = result.get('media_path', 'No path')
        source_type = result['source_type'].upper()
        content = truncate_content(result.get('content', ''), 100)
        similarity_score = result['similarity_score']
        timestamp = format_timestamp(result['timestamp'])
        
        print(f"{i}. ID: {event_id} | Type: {source_type} | Score: {similarity_score:.3f}")
        print(f"   📁 Path: {media_path}")
        print(f"   🕐 Time: {timestamp}")
        print(f"   📝 Content: {content}")
        print()


def display_stats():
    """Display database statistics."""
    print("📊 Database Statistics")
    print("-" * 40)
    
    stats = get_vector_stats()
    if stats:
        print(f"Total vectors: {stats['total_vectors']}")
        print(f"Vector dimension: {stats['vector_dimension']}")
        print(f"Non-vectorized events: {stats['non_vectorized_events']}")
        
        if stats['by_source_type']:
            print("\nVectors by source type:")
            for source_type, count in stats['by_source_type'].items():
                print(f"  • {source_type}: {count}")
        print()
    else:
        print("❌ Could not retrieve statistics")


def setup_signal_handler():
    """Setup signal handler for graceful exit on Ctrl+C."""
    def signal_handler(sig, frame):
        print("\n\n👋 Thanks for using SnapChronicles Search!")
        print("Goodbye! 🚀")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)


def show_help():
    """Display help information."""
    print("""
🆘 Help - SnapChronicles Search CLI

Commands:
  • Enter any question or keywords to search your captured content
  • Type 'q' to quit
  • Type 'help' to show this help
  • Type 'stats' to show database statistics
  • Use Ctrl+C to exit anytime

Search Examples:
  • "machine learning projects"
  • "email about deadlines"
  • "meeting discussion artificial intelligence"
  • "weekend plans vacation"
  • "Python programming code"

Tips:
  • Use natural language - the system understands context
  • Try different phrasings if you don't find what you're looking for
  • The search looks through OCR text from screenshots and audio transcriptions
    """)


def main():
    """Main CLI loop."""
    # Setup signal handler for Ctrl+C
    setup_signal_handler()
    
    # Check if database exists
    if not db_exists():
        print("❌ Database not found!")
        print("Please run some capture sessions first to populate the database.")
        return 1
    
    # Welcome message
    print("🔍 SnapChronicles Database Search CLI")
    print("=" * 60)
    print("Search through your captured screenshots and audio transcriptions")
    print("using natural language queries powered by AI.")
    print()
    print("💡 Type 'help' for commands, 'stats' for database info, or 'q' to quit")
    print()
    
    # Show initial stats
    display_stats()
    
    try:
        while True:
            # Get user input
            try:
                query = input("🔎 Enter your search query: ").strip()
            except EOFError:
                # Handle Ctrl+D
                print("\n\n👋 Thanks for using SnapChronicles Search!")
                break
            
            # Check for quit command
            if query.lower() in ['q', 'quit', 'exit']:
                print("👋 Thanks for using SnapChronicles Search!")
                break
            
            # Check for help command
            if query.lower() in ['help', 'h', '?']:
                show_help()
                continue
            
            # Check for stats command
            if query.lower() in ['stats', 'statistics', 'info']:
                display_stats()
                continue
            
            # Skip empty queries
            if not query:
                print("⚠️ Please enter a search query or 'q' to quit")
                continue
            
            # Perform LLM-based expansion (optional)
            expanded_phrases = []
            if expand_query is not None:
                try:
                    expanded_phrases = expand_query(query, max_tokens=128)
                except Exception as e:
                    print(f"⚠️  Query expansion failed – continuing without it: {e}")

            # Log what we're about to search
            print(f"\n🧠 Searching for: '{query}'")
            if expanded_phrases:
                print("   🔎 Additional generated requests:")
                for p in expanded_phrases:
                    print(f"     • {p}")
            
            # Run search (db handler now internally reuses expansion, but we pass original)
            results = search_similar_events(query, top_k=6)
            display_results(results, query)
            
            print("-" * 80)
    
    except KeyboardInterrupt:
        # This shouldn't happen due to signal handler, but just in case
        print("\n\n👋 Thanks for using SnapChronicles Search!")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 