import whisper
import time

class WhisperASR:
    """
    Whisper ASR class that loads the model once and provides transcription methods
    """
    
    def __init__(self, model_size="base"):
        """
        Initialize the WhisperASR with a specific model size
        """
        print(f"🔄 Loading Whisper model ({model_size})...")
        start_time = time.time()
        self.model = whisper.load_model(model_size)
        self.model_size = model_size
        end_time = time.time()
        print(f"✅ Model loaded in {self.format_duration(end_time - start_time)}")
    
    def detect_between_two_languages(self, audio_path, lang1="en", lang2="fr"):
        """
        Detect language between two specific options for faster processing
        """
        start_time = time.time()
        
        # Load and prepare audio
        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
        
        # Get language probabilities
        _, probs = self.model.detect_language(mel)
        
        # Filter to only your two target languages
        # Handle probabilities as dictionary
        if isinstance(probs, dict):
            target_probs = {lang: probs.get(lang, 0.0) for lang in [lang1, lang2]}
        else:
            # Fallback if probs is not a dict
            target_probs = {lang1: 0.5, lang2: 0.5}
        
        detected_language = max(target_probs, key=lambda k: target_probs[k])
        
        print(f"Language probabilities: {target_probs}")
        print(f"Selected language: {detected_language}")
        
        # Transcribe with the detected language
        result = self.model.transcribe(audio_path, language=detected_language)
        
        end_time = time.time()
        duration = end_time - start_time
        print(f"⏱️ Transcription completed in {duration:.2f} seconds")
        
        return result, detected_language

    def transcribe_audio(self, audio_path, lang="fr"):
        """
        Transcribe audio file with timing
        """
        start_time = time.time()
        print(f"🎙️ Starting transcription of: {audio_path}")
        print(f"📝 Language: {lang}")
        
        result = self.model.transcribe(audio_path, language=lang)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Transcription completed in {duration:.2f} seconds")
        
        return result

    def transcribe_with_detailed_timing(self, audio_path, lang="fr"):
        """
        Transcribe audio with detailed timing breakdown
        """
        total_start = time.time()
        
        print(f"🎙️ Starting transcription of: {audio_path}")
        print(f"📝 Language: {lang}")
        print("=" * 50)
        
        # Audio processing (model is already loaded)
        audio_start = time.time()
        print("⏳ Processing audio...")
        result = self.model.transcribe(audio_path, language=lang)
        audio_end = time.time()
        print(f"✅ Audio processed in {self.format_duration(audio_end - audio_start)}")
        
        total_end = time.time()
        total_duration = total_end - total_start
        
        print("=" * 50)
        print(f"🏁 Total transcription time: {self.format_duration(total_duration)}")
        print("=" * 50)
        
        return result

    def extract_text_from_audio(self, audio_path, lang="fr"):
        """
        Extract clean text from audio file
        """
        result = self.transcribe_audio(audio_path, lang)
        return self.extract_text_from_result(result)

    @staticmethod
    def extract_text_from_result(result):
        """
        Extract clean text from whisper transcription result
        """
        if isinstance(result, dict) and 'text' in result:
            return result['text'].strip()
        return str(result)

    @staticmethod
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

    @staticmethod
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


# Backward compatibility functions (deprecated, use WhisperASR class instead)
def detect_between_two_languages(audio_path, lang1="en", lang2="fr", model_size="base"):
    """
    Detect language between two specific options for faster processing
    [DEPRECATED] Use WhisperASR class instead
    """
    asr = WhisperASR(model_size)
    return asr.detect_between_two_languages(audio_path, lang1, lang2)

def transcribe_audio(audio_path, lang="fr"):
    """
    Transcribe audio file with timing
    [DEPRECATED] Use WhisperASR class instead
    """
    asr = WhisperASR()
    return asr.transcribe_audio(audio_path, lang)

def extract_text_from_result(result):
    """
    Extract clean text from whisper transcription result
    [DEPRECATED] Use WhisperASR.extract_text_from_result instead
    """
    return WhisperASR.extract_text_from_result(result)

def extract_text_from_audio(audio_path, lang="fr"):
    """
    [DEPRECATED] Use WhisperASR class instead
    """
    asr = WhisperASR()
    return asr.extract_text_from_audio(audio_path, lang)

def get_segmented_text(result):
    """
    Extract text segments with timestamps from whisper result
    [DEPRECATED] Use WhisperASR.get_segmented_text instead
    """
    return WhisperASR.get_segmented_text(result)

def format_duration(seconds):
    """
    Format duration in a human-readable way
    [DEPRECATED] Use WhisperASR.format_duration instead
    """
    return WhisperASR.format_duration(seconds)

def transcribe_with_detailed_timing(audio_path, lang="fr"):
    """
    Transcribe audio with detailed timing breakdown
    [DEPRECATED] Use WhisperASR class instead
    """
    asr = WhisperASR()
    return asr.transcribe_with_detailed_timing(audio_path, lang)

# Usage example
if __name__ == "__main__":
    # Create ASR instance (model loads once)
    asr = WhisperASR("base")
    asr.extract_text_from_audio("C:\\Users\\Habib\\gite\\SnapChronicles\\src\\asr\\audio.mp3", "fr")
    # Example usage
    # result, detected_lang = asr.detect_between_two_languages(
    #     "C:\\Users\\Habib\\gite\\SnapChronicles\\src\\asr\\audio.mp3", 
    #     lang1="en", 
    #     lang2="fr"
    # )

    # print("🚀 Starting detailed transcription with timing...")
    # result = asr.transcribe_with_detailed_timing(
    #     "C:\\Users\\Habib\\gite\\SnapChronicles\\src\\asr\\audio.mp3", 
    #     lang="fr"
    # )
    # 
    # # Extract clean text
    # clean_text = asr.extract_text_from_result(result)
    # print("\n📄 Clean transcription:")
    # print(clean_text)
    # 
    # # Optionally, get segmented text with timestamps
    # print("\n🔍 Segmented text:")
    # segments = asr.get_segmented_text(result)
    # for segment in segments:
    #     print(f"[{segment['start']:.2f}s - {segment['end']:.2f}s]: {segment['text']}")