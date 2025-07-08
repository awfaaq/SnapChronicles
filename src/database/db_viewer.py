# src/database/db_viewer.py
from datetime import datetime
from db_handler import get_all_events, db_exists

def truncate_content(content, max_length=100):
    """Truncate content to a maximum length."""
    if not content:
        return "(Empty)"
    if len(content) <= max_length:
        return content
    return content[:max_length] + "..."

def format_timestamp(unix_timestamp):
    """Convert a Unix timestamp into a human-readable format."""
    try:
        return datetime.fromtimestamp(unix_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return f"Invalid timestamp: {unix_timestamp}"

def format_vectorized(vectorized):
    """Format the vectorized status with emojis."""
    return "✅ Yes" if vectorized else "❌ No"

def print_database_content():
    """Nicely print all the content of the database."""
    
    print("🗄️  SnapChronicles Database Viewer")
    print("=" * 80)
    
    # Check if the database exists
    if not db_exists():
        print("❌ Database not found! Please run the application first to create it.")
        return
    
    # Retrieve all events
    print("📊 Loading all events from database...")
    events = get_all_events()
    
    if not events:
        print("📭 Database is empty - no events found.")
        return
    
    print(f"📈 Found {len(events)} events in database\n")
    
    # Print each event
    for i, event in enumerate(events, 1):
        print(f"┌─ Event #{event['id']} ({'#' + str(i)}/{len(events)}) ─" + "─" * 50)
        print(f"│ 🕐 Timestamp:  {format_timestamp(event['timestamp'])} (Unix: {event['timestamp']})")
        print(f"│ 📂 Type:       {event['source_type'].upper()}")
        print(f"│ 🔄 Vectorized: {format_vectorized(event['vectorized'])}")
        
        # Truncated content
        truncated_content = truncate_content(event['content'], 100)
        print(f"│ 📝 Content:    {truncated_content}")
        
        # Media path
        if event['media_path']:
            print(f"│ 📁 Media:      {event['media_path']}")
        else:
            print(f"│ 📁 Media:      (No media file)")
        
        print("└" + "─" * 75)
        
        # Add a blank line between events except for the last one
        if i < len(events):
            print()
    
    # Final statistics
    print("\n" + "=" * 80)
    print("📊 Database Statistics:")
    
    # Count by source type
    source_counts = {}
    vectorized_count = 0
    
    for event in events:
        source_type = event['source_type']
        source_counts[source_type] = source_counts.get(source_type, 0) + 1
        if event['vectorized']:
            vectorized_count += 1
    
    print(f"   📈 Total events: {len(events)}")
    print(f"   🔄 Vectorized: {vectorized_count} ({vectorized_count/len(events)*100:.1f}%)")
    print(f"   📊 By source type:")
    
    for source_type, count in sorted(source_counts.items()):
        percentage = count / len(events) * 100
        print(f"      • {source_type.upper()}: {count} events ({percentage:.1f}%)")
    
    # Time range
    if events:
        oldest = min(event['timestamp'] for event in events)
        newest = max(event['timestamp'] for event in events)
        print(f"   📅 Time range: {format_timestamp(oldest)} → {format_timestamp(newest)}")

def print_recent_events(limit=5):
    """Print the most recent events."""
    
    print(f"🕐 Last {limit} Recent Events")
    print("=" * 50)
    
    if not db_exists():
        print("❌ Database not found!")
        return
    
    events = get_all_events()
    recent_events = events[:limit]  # Already sorted by timestamp DESC
    
    if not recent_events:
        print("📭 No events found.")
        return
    
    for event in recent_events:
        print(f"🆔 ID {event['id']} | {event['source_type'].upper()} | {format_timestamp(event['timestamp'])}")
        print(f"   📝 {truncate_content(event['content'], 80)}")
        if event['media_path']:
            print(f"   📁 {event['media_path']}")
        print("   " + "-" * 60)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--recent":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        print_recent_events(limit)
    else:
        print_database_content()
