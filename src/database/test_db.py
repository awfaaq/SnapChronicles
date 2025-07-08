# src/database/test_db.py
import time
from datetime import datetime
from db_handler import init_db, store_event, get_event_by_id, get_all_events, db_exists

def test_database():
    """Test de la base de données avec des données d'exemple."""
    
    print("🔧 Test de la base de données SnapChronicles")
    print("=" * 50)
    
    # Vérifier si la base existe déjà
    if db_exists():
        print("✅ Base de données existante détectée")
    else:
        print("🆕 Création d'une nouvelle base de données")
    
    # Initialiser la base de données
    init_db()
    
    # Créer des timestamps d'exemple (Unix timestamps)
    current_time = int(time.time())
    
    # Insérer des données d'exemple
    print("\n📝 Insertion de données d'exemple...")
    
    # Événement OCR
    store_event(
        timestamp=current_time,
        source_type="ocr",
        content="Hello World! This is OCR text from a screenshot.",
        vectorized=False,
        media_path="screenshots/screenshot_001.png"
    )
    
    # Événement de transcription
    store_event(
        timestamp=current_time + 10,
        source_type="transcription",
        content="User said: How are you doing today?",
        vectorized=True,
        media_path="audio/recording_001.wav"
    )
    
    # Événement de résumé
    store_event(
        timestamp=current_time + 20,
        source_type="summary",
        content="Brief conversation about daily activities and wellbeing.",
        vectorized=True,
        media_path=None
    )
    
    # Autre événement OCR
    store_event(
        timestamp=current_time + 30,
        source_type="ocr",
        content="Login screen detected: Username field visible",
        vectorized=False,
        media_path="screenshots/login_screen.png"
    )
    
    print("\n🔍 Test de récupération des données...")
    
    # Récupérer un événement par ID
    print("\n📋 Récupération de l'événement avec ID=2:")
    event = get_event_by_id(2)
    if event:
        print(f"  ID: {event['id']}")
        print(f"  Timestamp: {event['timestamp']} ({datetime.fromtimestamp(event['timestamp'])})")
        print(f"  Type: {event['source_type']}")
        print(f"  Contenu: {event['content']}")
        print(f"  Vectorisé: {event['vectorized']}")
        print(f"  Fichier média: {event['media_path']}")
    else:
        print("  ❌ Événement non trouvé")
    
    # Récupérer tous les événements
    print("\n📚 Tous les événements dans la base:")
    all_events = get_all_events()
    
    for event in all_events:
        print(f"  [{event['id']}] {event['source_type'].upper()}: {event['content'][:50]}{'...' if len(event['content']) > 50 else ''}")
        print(f"      📅 {datetime.fromtimestamp(event['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"      🔄 Vectorisé: {'✅' if event['vectorized'] else '❌'}")
        if event['media_path']:
            print(f"      📁 Média: {event['media_path']}")
        print()
    
    print(f"📊 Total: {len(all_events)} événements dans la base de données")

if __name__ == "__main__":
    test_database() 