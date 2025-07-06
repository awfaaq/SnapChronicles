# src/main.py
import time
import threading
import queue
import os
from datetime import datetime, timedelta
from PIL import ImageGrab
import pyaudiowpatch as pyaudio
import wave
import numpy as np

# Importe les modules de ton projet
from ocr.ocr import extract_text_from_image
from asr.asr import WhisperASR
from summarize.summarize import generate_summary
from embed.embed import embed_text
from database import db_handler

# --- Configuration ---
CAPTURE_INTERVAL_SEC = 1.0  # Capture d'écran toutes les secondes
AUDIO_SEGMENT_DURATION_SEC = 15 # Segments audio de 15 secondes
PROCESSING_MODE = 'local' # 'local' ou 'groq'
SESSION_DIR = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
SCREENSHOT_DIR = os.path.join(SESSION_DIR, "screenshots")
AUDIO_DIR = os.path.join(SESSION_DIR, "audio")

class SnapChronicleAgent:
    def __init__(self):
        self.stop_event = threading.Event()
        self.file_queue = queue.Queue() # Queue pour les chemins de fichiers (audio & screenshots)

        # Initialisation des composants
        print("--- Initialisation de SnapChronicle Agent ---")
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        os.makedirs(AUDIO_DIR, exist_ok=True)
        print(f"📁 Dossiers de session créés dans : {SESSION_DIR}")

        self.asr_module = WhisperASR(model_size="tiny") # 'tiny' pour la perf, ou 'base'
        db_handler.init_db()
        print("------------------------------------------")

    def _screen_capture_worker(self):
        """Thread qui prend des captures d'écran à intervalle régulier."""
        print("📸 Worker de capture d'écran démarré.")
        while not self.stop_event.is_set():
            loop_start_time = time.time()
            
            try:
                now = datetime.now()
                filename = f"screenshot_{now.strftime('%Y%m%d_%H%M%S_%f')}.png"
                filepath = os.path.join(SCREENSHOT_DIR, filename)
                ImageGrab.grab().save(filepath)
                self.file_queue.put(('screenshot', filepath, now))
            except Exception as e:
                print(f"[ERROR Capture Ecran] {e}")

            # Attendre pour respecter l'intervalle de 1s
            elapsed = time.time() - loop_start_time
            sleep_time = max(0, CAPTURE_INTERVAL_SEC - elapsed)
            time.sleep(sleep_time)
        print("📸 Worker de capture d'écran arrêté.")

    def _audio_capture_worker(self):
        """Thread qui enregistre des segments audio en continu."""
        print("🎵 Worker de capture audio démarré.")
        p = pyaudio.PyAudio()
        try:
            device = p.get_default_wasapi_loopback()
            rate = int(device['defaultSampleRate'])
            channels = min(device['maxInputChannels'], 2)
            chunk_size = 1024

            stream = p.open(format=pyaudio.paFloat32, channels=channels, rate=rate, input=True,
                            input_device_index=device['index'], frames_per_buffer=chunk_size)
        except Exception as e:
            print(f"[ERROR Capture Audio] Initialisation impossible : {e}")
            return
        
        while not self.stop_event.is_set():
            now = datetime.now()
            filename = f"audio_{now.strftime('%Y%m%d_%H%M%S')}.wav"
            filepath = os.path.join(AUDIO_DIR, filename)
            frames = []
            
            # Enregistrer pour la durée du segment
            for _ in range(0, int(rate / chunk_size * AUDIO_SEGMENT_DURATION_SEC)):
                if self.stop_event.is_set(): break
                try:
                    data = stream.read(chunk_size)
                    frames.append(data)
                except IOError: # Peut arriver si le device change
                    pass

            if not frames: continue

            # Sauvegarder le fichier WAV
            wf = wave.open(filepath, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(pyaudio.paFloat32))
            wf.setframerate(rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            self.file_queue.put(('audio', filepath, now))
            
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("🎵 Worker de capture audio arrêté.")
        
    def _processing_worker(self):
        """Thread qui traite les fichiers en attente."""
        print("⚙️ Worker de traitement démarré.")
        
        pending_screenshots = []

        while not self.stop_event.is_set() or not self.file_queue.empty():
            try:
                file_type, file_path, timestamp = self.file_queue.get(timeout=1.0)

                if file_type == 'screenshot':
                    pending_screenshots.append((file_path, timestamp))
                
                elif file_type == 'audio':
                    # Un segment audio a été enregistré, traitons-le avec les screenshots correspondants
                    print(f"\n--- Traitement du segment audio : {os.path.basename(file_path)} ---")
                    
                    # 1. Filtrer les screenshots pris durant la période de l'audio
                    audio_end_time = timestamp + timedelta(seconds=AUDIO_SEGMENT_DURATION_SEC)
                    relevant_screenshots = [s for s in pending_screenshots if timestamp <= s[1] < audio_end_time]
                    
                    # Garder les autres screenshots pour le prochain cycle
                    pending_screenshots = [s for s in pending_screenshots if s[1] >= audio_end_time]
                    
                    # 2. ASR sur l'audio
                    asr_text = self.asr_module.transcribe_audio(file_path, language='fr')
                    
                    # 3. OCR sur les screenshots pertinents
                    ocr_texts = [extract_text_from_image(s_path) for s_path, _ in relevant_screenshots]
                    full_ocr_text = "\n".join(filter(None, ocr_texts))
                    
                    # 4. Résumé
                    summary = generate_summary(full_ocr_text, asr_text, mode=PROCESSING_MODE)
                    
                    # 5. Embedding
                    combined_text = f"Summary: {summary}\nOCR: {full_ocr_text}\nASR: {asr_text}"
                    embedding_vector = embed_text(combined_text)
                    
                    # 6. Stockage
                    # On prend le chemin du dernier screenshot comme référence
                    last_screenshot_path = relevant_screenshots[-1][0] if relevant_screenshots else ""
                    db_handler.store_event(
                        ts=timestamp,
                        ocr_text=full_ocr_text,
                        asr_text=asr_text,
                        summary=summary,
                        embedding=embedding_vector.tobytes(),
                        screenshot_path=last_screenshot_path,
                        audio_path=file_path
                    )
                    
            except queue.Empty:
                continue # Pas de fichier, on continue la boucle
            except Exception as e:
                print(f"[ERROR Processing] {e}")

        print("⚙️ Worker de traitement arrêté.")

    def start(self):
        """Démarre tous les workers de l'agent."""
        self.threads = [
            threading.Thread(target=self._screen_capture_worker, daemon=True),
            threading.Thread(target=self._audio_capture_worker, daemon=True),
            threading.Thread(target=self._processing_worker, daemon=True)
        ]
        for t in self.threads:
            t.start()
        print("✅ Agent SnapChronicle démarré. Appuyez sur Ctrl+C pour arrêter.")

    def stop(self):
        """Arrête proprement tous les workers."""
        print("\n🛑 Arrêt de l'agent en cours...")
        self.stop_event.set()
        for t in self.threads:
            t.join(timeout=5.0) # Attendre que les threads se terminent
        print("✅ Agent arrêté proprement.")

if __name__ == "__main__":
    agent = SnapChronicleAgent()
    try:
        agent.start()
        # Garder le thread principal en vie pour attendre le Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()
