"""
Continuous Desktop Audio Recorder
Enregistrement continu avec segments de 15 secondes - SANS GAPS
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

class ContinuousRecorder:
    def __init__(self, segment_duration=15):
        self.segment_duration = segment_duration
        self.recording = False
        self.audio_queue = queue.Queue()
        self.save_thread = None
        self.p = None
        self.stream = None
        
        # Créer le dossier de destination avec timestamp
        self.session_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_folder = f"recording_session_{self.session_timestamp}"
        os.makedirs(self.output_folder, exist_ok=True)
        print(f"📁 Dossier de sauvegarde: {self.output_folder}")
        
    def setup_audio(self):
        """Configure le périphérique audio"""
        print("🎵 Configuration audio...")
        
        self.p = pyaudio.PyAudio()
        
        # Utiliser le périphérique loopback par défaut
        try:
            default_device = self.p.get_default_wasapi_loopback()
            device_index = default_device['index']
            print(f"📱 Périphérique: {default_device['name']}")
        except:
            print("❌ Aucun périphérique loopback trouvé")
            return False
        
        # Paramètres d'enregistrement
        device_info = self.p.get_device_info_by_index(device_index)
        self.sample_rate = int(device_info['defaultSampleRate'])
        self.channels = min(device_info['maxInputChannels'], 2)
        self.chunk_size = 256
        
        print(f"🎚️  Paramètres: {self.sample_rate}Hz, {self.channels} canaux")
        
        # Ouvrir le stream UNE SEULE FOIS
        try:
            self.stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            print("✅ Stream audio ouvert")
            return True
        except Exception as e:
            print(f"❌ Erreur ouverture stream: {e}")
            return False
    
    def save_segment(self, audio_data, segment_number):
        """Sauvegarde un segment audio (exécuté dans un thread séparé)"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"segment_{segment_number:03d}_{timestamp}.wav"
        filepath = os.path.join(self.output_folder, filename)
        
        try:
            # Convertir en int16 pour le fichier WAV
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())
            
            duration = len(audio_data) / (self.sample_rate * self.channels)
            file_size = os.path.getsize(filepath) / (1024 * 1024)
            print(f"💾 Segment {segment_number} sauvé: {filepath} ({duration:.1f}s, {file_size:.1f}MB)")
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde segment {segment_number}: {e}")
    
    def save_worker(self):
        """Worker thread pour sauvegarder les segments sans interrompre l'enregistrement"""
        while self.recording or not self.audio_queue.empty():
            try:
                # Attendre un segment à sauvegarder (timeout pour vérifier l'arrêt)
                segment_data = self.audio_queue.get(timeout=1.0)
                audio_data, segment_number = segment_data
                
                # Sauvegarder dans un thread séparé pour ne pas bloquer
                save_thread = threading.Thread(
                    target=self.save_segment, 
                    args=(audio_data, segment_number)
                )
                save_thread.start()
                
            except queue.Empty:
                continue
    
    def start_recording(self):
        """Démarre l'enregistrement continu"""
        if not self.setup_audio():
            return
        
        self.recording = True
        
        # Démarrer le thread de sauvegarde
        self.save_thread = threading.Thread(target=self.save_worker)
        self.save_thread.start()
        
        print(f"🔴 ENREGISTREMENT CONTINU DÉMARRÉ")
        print(f"📊 Segments de {self.segment_duration} secondes")
        print(f"📁 Sauvegarde dans: {self.output_folder}")
        print("⏹️  Appuyez sur Ctrl+C pour arrêter")
        print("=" * 50)
        
        # Calculer le nombre d'échantillons par segment (incluant tous les canaux)
        samples_per_segment = self.sample_rate * self.segment_duration * self.channels
        
        segment_number = 1
        current_segment = []
        samples_in_current_segment = 0
        
        try:
            while self.recording:
                # Lire les données audio EN CONTINU
                try:
                    if not self.stream:
                        break
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    audio_chunk = np.frombuffer(data, dtype=np.float32)
                    
                    # Ajouter au segment actuel
                    current_segment.append(audio_chunk)
                    samples_in_current_segment += len(audio_chunk)
                    
                    # Si le segment est complet
                    if samples_in_current_segment >= samples_per_segment:
                        # Concatener tout le segment
                        full_segment = np.concatenate(current_segment)
                        
                        # Prendre exactement le nombre d'échantillons requis
                        segment_data = full_segment[:samples_per_segment]
                        
                        # Envoyer au thread de sauvegarde SANS ATTENDRE
                        self.audio_queue.put((segment_data, segment_number))
                        
                        print(f"📦 Segment {segment_number} prêt ({self.segment_duration}s)")
                        
                        # Préparer le segment suivant avec les données restantes
                        remaining_data = full_segment[samples_per_segment:]
                        current_segment = [remaining_data] if len(remaining_data) > 0 else []
                        samples_in_current_segment = len(remaining_data)
                        segment_number += 1
                    
                except Exception as e:
                    print(f"⚠️  Erreur lecture: {e}")
                    time.sleep(0.001)
                    continue
        
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé...")
        
        finally:
            self.stop_recording()
            
            # Sauvegarder le dernier segment partiel s'il existe
            if current_segment and samples_in_current_segment > 0:
                final_segment = np.concatenate(current_segment)
                self.audio_queue.put((final_segment, segment_number))
                print(f"📦 Segment final {segment_number} ({len(final_segment)/(self.sample_rate * self.channels):.1f}s)")
    
    def stop_recording(self):
        """Arrête l'enregistrement proprement"""
        self.recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            print("🔴 Stream fermé")
        
        if self.p:
            self.p.terminate()
            print("🔴 PyAudio terminé")
        
        # Attendre que toutes les sauvegardes se terminent
        if self.save_thread:
            self.save_thread.join()
            print("💾 Toutes les sauvegardes terminées")
            
        # Afficher le résumé
        try:
            segment_files = [f for f in os.listdir(self.output_folder) if f.endswith('.wav')]
            print(f"📊 Résumé: {len(segment_files)} segments sauvés dans {self.output_folder}")
        except:
            print(f"📊 Session terminée - Dossier: {self.output_folder}")

def main():
    """Fonction principale"""
    
    # Vérifier PyAudioWPatch
    try:
        import pyaudiowpatch
    except ImportError:
        print("❌ PyAudioWPatch non installé")
        print("💡 Installez avec: pip install PyAudioWPatch")
        return
    
    # Créer et démarrer l'enregistreur
    recorder = ContinuousRecorder(segment_duration=15)
    
    def signal_handler(signum, frame):
        print("\n🛑 Signal d'arrêt reçu...")
        recorder.stop_recording()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        recorder.start_recording()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        recorder.stop_recording()
    
    print("✅ Enregistrement terminé")

if __name__ == "__main__":
    main() 