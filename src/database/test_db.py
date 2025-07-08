# src/database/test_db.py
import time
from datetime import datetime
from db_handler import init_db, store_event, get_event_by_id, get_all_events, db_exists

def test_database():
    """Database test with sample data."""

    print("🔧 SnapChronicles Database Test")
    print("=" * 50)

    # Check if the database already exists
    if db_exists():
        print("✅ Existing database detected")
    else:
        print("🆕 Creating a new database")

    # Initialize the database
    init_db()

    # Create example timestamps (Unix timestamps)
    current_time = int(time.time())

    # Insert sample data
    print("\n📝 Inserting sample data...")

    # OCR event
    store_event(
        timestamp=current_time,
        source_type="ocr",
        content="Hello World! This is OCR text from a screenshot.",
        vectorized=False,
        media_path="screenshots/screenshot_001.png"
    )

    # Transcription event
    store_event(
        timestamp=current_time + 10,
        source_type="transcription",
        content="User said: How are you doing today?",
        vectorized=True,
        media_path="audio/recording_001.wav"
    )

    # Summary event
    store_event(
        timestamp=current_time + 20,
        source_type="summary",
        content="Brief conversation about daily activities and wellbeing.",
        vectorized=True,
        media_path=None
    )

    # Another OCR event
    store_event(
        timestamp=current_time + 30,
        source_type="ocr",
        content="Login screen detected: Username field visible",
        vectorized=False,
        media_path="screenshots/login_screen.png"
    )

    print("\n🔍 Testing data retrieval...")

    # Retrieve an event by ID
    print("\n📋 Retrieving event with ID=2:")
    event = get_event_by_id(2)
    if event:
        print(f"  ID: {event['id']}")
        print(f"  Timestamp: {event['timestamp']} ({datetime.fromtimestamp(event['timestamp'])})")
        print(f"  Type: {event['source_type']}")
        print(f"  Content: {event['content']}")
        print(f"  Vectorized: {event['vectorized']}")
        print(f"  Media file: {event['media_path']}")
    else:
        print("  ❌ Event not found")

    # Retrieve all events
    print("\n📚 All events in the database:")
    all_events = get_all_events()

    for event in all_events:
        print(f"  [{event['id']}] {event['source_type'].upper()}: {event['content'][:50]}{'...' if len(event['content']) > 50 else ''}")
        print(f"      📅 {datetime.fromtimestamp(event['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"      🔄 Vectorized: {'✅' if event['vectorized'] else '❌'}")
        if event['media_path']:
            print(f"      📁 Media: {event['media_path']}")
        print()

    print(f"📊 Total: {len(all_events)} events in the database")

if __name__ == "__main__":
    test_database()
