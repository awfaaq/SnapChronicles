"""
Continuous Desktop Audio Recorder with Real-time Transcription
Captures speaker audio in 15-second chunks and transcribes them using Whisper ASR
"""

import pyaudiowpatch as pyaudio
import wave
import numpy as np
import datetime
import time
import signal
import threading
import queue
import os
import sys
from pathlib import Path

# Add the parent directory to the path to import ASR and database
sys.path.append(str(Path(__file__).parent.parent))
from asr.asr import WhisperASR
from database.db_handler import init_db, store_event

class ContinuousRecorderWithTranscription:
    def __init__(self, segment_duration=15, language="fr", model_size="base"):
        self.segment_duration = segment_duration
        self.language = language
        self.recording = False
        self.audio_queue = queue.Queue()
        self.transcription_queue = queue.Queue()
        self.save_thread = None
        self.transcription_thread = None
        self.p = None
        self.stream = None
        
        # Initialize ASR
        print(f"🤖 Initializing ASR with model: {model_size}")
        self.asr = WhisperASR(model_size)
        
        # Initialize database
        print("🔧 Initializing database...")
        init_db()
        
        # Create the session folder with timestamp
        self.session_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_folder = f"recording_session_{self.session_timestamp}"
        os.makedirs(self.output_folder, exist_ok=True)
        print(f"📁 Session folder: {self.output_folder}")
        
        # Initialize log file
        self.log_file = "log_audio.md"
        self.init_log_file()
        
    def init_log_file(self):
        """Initialize the log file with header"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## Audio Recording Session - {self.session_timestamp}\n")
            f.write(f"**Started:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Language:** {self.language}\n")
            f.write(f"**Segment Duration:** {self.segment_duration}s\n")
            f.write("**Database:** Transcriptions will be saved to database\n")
            f.write("\n---\n\n")
        
    def setup_audio(self):
        """Configure audio device"""
        print("🎵 Setting up audio...")
        
        self.p = pyaudio.PyAudio()
        
        # Use default loopback device
        try:
            default_device = self.p.get_default_wasapi_loopback()
            device_index = default_device['index']
            print(f"📱 Device: {default_device['name']}")
        except:
            print("❌ No loopback device found")
            return False
        
        # Recording parameters
        device_info = self.p.get_device_info_by_index(device_index)
        self.sample_rate = int(device_info['defaultSampleRate'])
        self.channels = min(device_info['maxInputChannels'], 2)
        self.chunk_size = 256
        
        print(f"🎚️  Settings: {self.sample_rate}Hz, {self.channels} channels")
        
        # Open stream
        try:
            self.stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            print("✅ Audio stream opened")
            return True
        except Exception as e:
            print(f"❌ Stream error: {e}")
            return False
    
    def save_segment(self, audio_data, segment_number):
        """Save audio segment to WAV file"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"segment_{segment_number:03d}_{timestamp}.wav"
        filepath = os.path.join(self.output_folder, filename)
        
        try:
            # Convert to int16 for WAV file
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())
            
            duration = len(audio_data) / (self.sample_rate * self.channels)
            file_size = os.path.getsize(filepath) / (1024 * 1024)
            print(f"💾 Segment {segment_number} saved: {filename} ({duration:.1f}s, {file_size:.1f}MB)")
            
            # Queue for transcription
            self.transcription_queue.put((filepath, segment_number, timestamp))
            
        except Exception as e:
            print(f"❌ Save error for segment {segment_number}: {e}")
    
    def transcribe_segment(self, filepath, segment_number, timestamp):
        """Transcribe an audio segment"""
        try:
            print(f"🎙️ Transcribing segment {segment_number}...")
            
            # Transcribe using ASR
            result = self.asr.transcribe_audio(filepath, self.language)
            text = self.asr.extract_text_from_result(result)
            
            # Log to markdown file
            self.log_transcription(filepath, segment_number, timestamp, text)
            
            # Save to database
            self.save_transcription_to_db(filepath, text)
            
            print(f"✅ Segment {segment_number} transcribed and saved to database")
            
        except Exception as e:
            print(f"❌ Transcription error for segment {segment_number}: {e}")
            # Log error to file
            self.log_transcription(filepath, segment_number, timestamp, f"[ERROR: {str(e)}]")
            
            # Save error to database as well
            self.save_transcription_to_db(filepath, f"Transcription Error: {str(e)}")
    
    def save_transcription_to_db(self, filepath, text):
        """Save transcription to database"""
        try:
            # Get Unix timestamp
            unix_timestamp = int(time.time())
            
            # Clean the text
            cleaned_text = text.strip() if text.strip() else "(No speech detected)"
            
            # Store in database (will be automatically vectorized)
            store_event(
                timestamp=unix_timestamp,
                source_type="transcription",
                content=cleaned_text,
                media_path=filepath
            )
            
        except Exception as e:
            print(f"❌ Database save error: {e}")
    
    def log_transcription(self, filepath, segment_number, timestamp, text):
        """Log transcription to markdown file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"### Segment {segment_number:03d} - {timestamp}\n")
                f.write(f"**File:** `{filepath}`\n")
                f.write(f"**Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Text:**\n")
                f.write(f"{text}\n\n")
                f.write("---\n\n")
        except Exception as e:
            print(f"❌ Log error: {e}")
    
    def save_worker(self):
        """Worker thread for saving segments"""
        while self.recording or not self.audio_queue.empty():
            try:
                # Get segment to save
                segment_data = self.audio_queue.get(timeout=1.0)
                audio_data, segment_number = segment_data
                
                # Save in separate thread
                save_thread = threading.Thread(
                    target=self.save_segment, 
                    args=(audio_data, segment_number)
                )
                save_thread.start()
                
            except queue.Empty:
                continue
    
    def transcription_worker(self):
        """Worker thread for transcribing segments"""
        while self.recording or not self.transcription_queue.empty():
            try:
                # Get segment to transcribe
                transcription_data = self.transcription_queue.get(timeout=1.0)
                filepath, segment_number, timestamp = transcription_data
                
                # Transcribe in separate thread
                transcription_thread = threading.Thread(
                    target=self.transcribe_segment,
                    args=(filepath, segment_number, timestamp)
                )
                transcription_thread.start()
                
            except queue.Empty:
                continue
    
    def start_recording(self):
        """Start continuous recording with transcription"""
        if not self.setup_audio():
            return
        
        self.recording = True
        
        # Start worker threads
        self.save_thread = threading.Thread(target=self.save_worker)
        self.transcription_thread = threading.Thread(target=self.transcription_worker)
        
        self.save_thread.start()
        self.transcription_thread.start()
        
        print(f"🔴 CONTINUOUS RECORDING WITH TRANSCRIPTION STARTED")
        print(f"📊 Segments: {self.segment_duration}s each")
        print(f"🌐 Language: {self.language}")
        print(f"📁 Output folder: {self.output_folder}")
        print(f"📝 Log file: {self.log_file}")
        print(f"🗄️ Database: Transcriptions saved to snap.db")
        print("⏹️  Press Ctrl+C to stop")
        print("=" * 60)
        
        # Calculate samples per segment
        samples_per_segment = self.sample_rate * self.segment_duration * self.channels
        
        segment_number = 1
        current_segment = []
        samples_in_current_segment = 0
        
        try:
            while self.recording:
                try:
                    if not self.stream:
                        break
                    
                    # Read audio data continuously
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    audio_chunk = np.frombuffer(data, dtype=np.float32)
                    
                    # Add to current segment
                    current_segment.append(audio_chunk)
                    samples_in_current_segment += len(audio_chunk)
                    
                    # Check if segment is complete
                    if samples_in_current_segment >= samples_per_segment:
                        # Concatenate segment
                        full_segment = np.concatenate(current_segment)
                        
                        # Take exact number of samples
                        segment_data = full_segment[:samples_per_segment]
                        
                        # Queue for saving (non-blocking)
                        self.audio_queue.put((segment_data, segment_number))
                        
                        print(f"📦 Segment {segment_number} ready for processing")
                        
                        # Prepare next segment with remaining data
                        remaining_data = full_segment[samples_per_segment:]
                        current_segment = [remaining_data] if len(remaining_data) > 0 else []
                        samples_in_current_segment = len(remaining_data)
                        segment_number += 1
                
                except Exception as e:
                    print(f"⚠️  Read error: {e}")
                    time.sleep(0.001)
                    continue
        
        except KeyboardInterrupt:
            print("\n🛑 Stop requested...")
        
        finally:
            self.stop_recording()
            
            # Save final partial segment if exists
            if current_segment and samples_in_current_segment > 0:
                final_segment = np.concatenate(current_segment)
                self.audio_queue.put((final_segment, segment_number))
                print(f"📦 Final segment {segment_number} ({len(final_segment)/(self.sample_rate * self.channels):.1f}s)")
    
    def stop_recording(self):
        """Stop recording cleanly"""
        self.recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            print("🔴 Stream closed")
        
        if self.p:
            self.p.terminate()
            print("🔴 PyAudio terminated")
        
        # Wait for threads to finish
        if self.save_thread:
            self.save_thread.join()
            print("💾 All saves completed")
        
        if self.transcription_thread:
            self.transcription_thread.join()
            print("🎙️ All transcriptions completed")
        
        # Update log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n**Session ended:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Output folder:** `{self.output_folder}`\n\n")
        
        # Show summary
        try:
            segment_files = [f for f in os.listdir(self.output_folder) if f.endswith('.wav')]
            print(f"📊 Summary: {len(segment_files)} segments recorded and transcribed")
            print(f"📁 Files saved in: {self.output_folder}")
            print(f"📝 Transcriptions logged in: {self.log_file}")
            print(f"🗄️ Database: All transcriptions saved to snap.db")
        except:
            print(f"📊 Session completed - Check {self.output_folder}, {self.log_file}, and snap.db")


def main():
    """Main function"""
    
    # Check dependencies
    try:
        import pyaudiowpatch
        import whisper
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install with: pip install PyAudioWPatch openai-whisper")
        return
    
    # Default parameters
    segment_duration = 30 # seconds
    language = "en"  # English
    model_size = "base"  # Whisper model
    
    # Create recorder
    recorder = ContinuousRecorderWithTranscription(
        segment_duration=segment_duration,
        language=language,
        model_size=model_size
    )
    
    # Signal handler
    def signal_handler(signum, frame):
        print("\n🛑 Stop signal received...")
        recorder.stop_recording()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        recorder.start_recording()
    except Exception as e:
        print(f"❌ Error: {e}")
        recorder.stop_recording()
    
    print("✅ Recording and transcription completed")


if __name__ == "__main__":
    main()

