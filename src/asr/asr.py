import whisper
import time

def detect_between_two_languages(audio_path, lang1="en", lang2="fr", model_size="base"):
    """
    Detect language between two specific options for faster processing
    """
    start_time = time.time()
    
    model = whisper.load_model(model_size)
    
    # Load and prepare audio
    audio = whisper.load_audio(audio_path)
    audio = whisper.pad_or_trim(audio)
    mel = whisper.log_mel_spectrogram(audio).to(model.device)
    
    # Get language probabilities
    _, probs = model.detect_language(mel)
    
    # Filter to only your two target languages
    target_probs = {lang: probs.get(lang, 0.0) for lang in [lang1, lang2]}
    detected_language = max(target_probs, key=target_probs.get)
    
    print(f"Language probabilities: {target_probs}")
    print(f"Selected language: {detected_language}")
    
    # Transcribe with the detected language
    result = model.transcribe(audio_path, language=detected_language)
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"⏱️ Transcription completed in {duration:.2f} seconds")
    
    return result, detected_language


def transcribe_audio(audio_path, lang="en"):
    """
    Transcribe audio file with timing
    """
    start_time = time.time()
    print(f"🎙️ Starting transcription of: {audio_path}")
    print(f"📝 Language: {lang}")
    
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language=lang)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"⏱️ Transcription completed in {duration:.2f} seconds")
    
    return result

def extract_text_from_result(result):
    """
    Extract clean text from whisper transcription result
    """
    if isinstance(result, dict) and 'text' in result:
        return result['text'].strip()
    return str(result)

def get_segmented_text(result):
    """
    Extract text segments with timestamps from whisper result
    """
    if isinstance(result, dict) and 'segments' in result:
        segments = []
        for segment in result['segments']:
            segments.append({
                'start': segment.get('start', 0),
                'end': segment.get('end', 0),
                'text': segment.get('text', '').strip()
            })
        return segments
    return []

def format_duration(seconds):
    """
    Format duration in a human-readable way
    """
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.2f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.2f}s"

def transcribe_with_detailed_timing(audio_path, lang="en"):
    """
    Transcribe audio with detailed timing breakdown
    """
    total_start = time.time()
    
    print(f"🎙️ Starting transcription of: {audio_path}")
    print(f"📝 Language: {lang}")
    print("=" * 50)
    
    # Model loading
    model_start = time.time()
    print("⏳ Loading Whisper model...")
    model = whisper.load_model("base")
    model_end = time.time()
    print(f"✅ Model loaded in {format_duration(model_end - model_start)}")
    
    # Audio processing
    audio_start = time.time()
    print("⏳ Processing audio...")
    result = model.transcribe(audio_path, language=lang)
    audio_end = time.time()
    print(f"✅ Audio processed in {format_duration(audio_end - audio_start)}")
    
    total_end = time.time()
    total_duration = total_end - total_start
    
    print("=" * 50)
    print(f"🏁 Total transcription time: {format_duration(total_duration)}")
    print("=" * 50)
    
    return result

# Usage example
# result, detected_lang = detect_between_two_languages(
#     "C:\\Users\\Habib\\gite\\SnapChronicles\\src\\asr\\audio.mp3", 
#     lang1="en", 
#     lang2="fr"
# )

print("🚀 Starting detailed transcription with timing...")
result = transcribe_with_detailed_timing(
    "C:\\Users\\Habib\\gite\\SnapChronicles\\src\\asr\\audio.mp3", 
    lang="fr"
)

# Extract clean text
clean_text = extract_text_from_result(result)
print("\n📄 Clean transcription:")
print(clean_text)

# Optionally, get segmented text with timestamps
print("\n🔍 Segmented text:")
segments = get_segmented_text(result)
for segment in segments:
    print(f"[{segment['start']:.2f}s - {segment['end']:.2f}s]: {segment['text']}")