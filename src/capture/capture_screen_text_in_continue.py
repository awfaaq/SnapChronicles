from PIL import ImageGrab
import win32gui
import ctypes
import time
import os
import sys
import signal
import threading
import queue
from datetime import datetime

# Add src root to Python path for clean imports
src_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_root not in sys.path:
    sys.path.insert(0, src_root)

# Now we can import as if we're at src root
from ocr.ocr import ocr
from database.db_handler import init_db, store_event

# Handle DPI scaling issues
ctypes.windll.user32.SetProcessDPIAware()

# Create images_screened folder if it doesn't exist
os.makedirs('images_screened', exist_ok=True)

# Initialize the database
print("🔧 Initializing database...")
init_db()

# Global variables for continuous capture
capturing = False
last_saved_text = None
screenshot_queue = queue.Queue()
ocr_thread = None
screenshot_count = 0
CAPTURE_INTERVAL = 4.0  # seconds

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global capturing
    print("\n🛑 Stop signal received...")
    print("🔄 Finishing OCR processing of remaining screenshots...")
    capturing = False

def ocr_worker():
    """Worker thread for processing OCR on captured screenshots"""
    global last_saved_text
    
    while capturing or not screenshot_queue.empty():
        try:
            # Get screenshot data from queue
            screenshot_data = screenshot_queue.get(timeout=1.0)
            filename, screenshot_num = screenshot_data
            
            # Process OCR
            process_screenshot_ocr(filename, screenshot_num)
            
            # Mark task as done
            screenshot_queue.task_done()
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ OCR worker error: {e}")

def process_screenshot_ocr(filename, screenshot_num):
    """Process OCR for a single screenshot"""
    global last_saved_text
    
    try:
        print(f"🔍 Performing OCR on {filename}...")
        extracted_text = ocr(filename)
        
        # Clean and prepare the text
        cleaned_text = extracted_text.strip() if extracted_text.strip() else "(No text detected)"
        
        # Check if this text is different from the last saved text
        if last_saved_text is None or cleaned_text != last_saved_text:
            # Get Unix timestamp
            unix_timestamp = int(time.time())
            
            # Store in database (will be automatically vectorized)
            store_event(
                timestamp=unix_timestamp,
                source_type="ocr",
                content=cleaned_text,
                media_path=filename
            )
            
            # Update the last saved text
            last_saved_text = cleaned_text
            
            print(f"✅ OCR completed and saved to database for screenshot {screenshot_num}")
        else:
            # Duplicate detected – delete the screenshot to avoid clutter
            try:
                os.remove(filename)
                print(f"🗑️ Deleted duplicate screenshot {filename}")
            except Exception as del_err:
                print(f"⚠️ Could not delete duplicate screenshot {filename}: {del_err}")
            print(f"🔄 OCR text identical to previous screenshot - skipped database save for screenshot {screenshot_num}")
        
    except Exception as ocr_error:
        print(f"❌ OCR error for screenshot {screenshot_num}: {ocr_error}")
        
        # For errors, we always save them
        # because errors are important to track
        unix_timestamp = int(time.time())
        error_message = f"OCR Error: {str(ocr_error)}"
        
        store_event(
            timestamp=unix_timestamp,
            source_type="ocr",
            content=error_message,
            media_path=filename
        )
        
        # Don't update last_saved_text for errors

def take_screenshot():
    """Take a single screenshot and queue it for OCR processing"""
    global screenshot_count
    
    try:
        # Get the active window handle
        hwnd = win32gui.GetForegroundWindow()
        
        # Check if window handle is valid
        if hwnd and hwnd != 0:
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            # Take screenshot of active window
            screenshot = ImageGrab.grab((left, top, right, bottom))
        else:
            # Take full screen screenshot if no valid window
            screenshot = ImageGrab.grab()
        
        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'images_screened/screenshot_{timestamp}_{screenshot_count:03d}.png'
        screenshot.save(filename)
        
        screenshot_count += 1
        print(f"📸 Screenshot {screenshot_count} saved: {filename}")
        
        # Queue for OCR processing
        screenshot_queue.put((filename, screenshot_count))
        
        return True
        
    except Exception as e:
        print(f"❌ Error taking screenshot {screenshot_count + 1}: {e}")
        print("🔄 Trying full screen screenshot instead...")
        
        try:
            screenshot = ImageGrab.grab()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'images_screened/screenshot_{timestamp}_{screenshot_count:03d}.png'
            screenshot.save(filename)
            screenshot_count += 1
            print(f"📸 Screenshot {screenshot_count} saved: {filename} (fallback)")
            
            # Queue for OCR processing
            screenshot_queue.put((filename, screenshot_count))
            
            return True
            
        except Exception as e2:
            print(f"❌ Failed to take screenshot: {e2}")
            return False

def start_continuous_capture():
    """Start continuous screenshot capture with OCR processing"""
    global capturing, ocr_thread
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🔴 CONTINUOUS SCREENSHOT CAPTURE STARTED")
    print(f"📊 Capture interval: {CAPTURE_INTERVAL} seconds")
    print(f"📁 Output folder: images_screened/")
    print(f"🗄️ Database: OCR results saved to snap.db")
    print("⏹️  Press Ctrl+C to stop")
    print("=" * 60)
    
    capturing = True
    
    # Start OCR worker thread
    ocr_thread = threading.Thread(target=ocr_worker, daemon=True)
    ocr_thread.start()
    
    try:
        while capturing:
            loop_start = time.time()
            
            # Take screenshot and queue for processing
            if take_screenshot():
                # Calculate how long to sleep to maintain the capture interval
                elapsed = time.time() - loop_start
                sleep_time = max(0, CAPTURE_INTERVAL - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            else:
                # If screenshot failed, wait a bit before trying again
                time.sleep(1.0)
    
    except KeyboardInterrupt:
        print("\n🛑 Stop requested...")
    
    finally:
        # Stop capturing
        capturing = False
        
        # Wait for OCR processing to complete
        print("🔄 Waiting for OCR processing to complete...")
        if ocr_thread and ocr_thread.is_alive():
            ocr_thread.join(timeout=30.0)  # Wait up to 30 seconds
        
        # Wait for queue to be processed
        try:
            screenshot_queue.join()  # Wait for all queued items to be processed
            print("✅ All OCR processing completed")
        except:
            print("⚠️ OCR processing timeout - some items may not be processed")
        
        # Show final summary
        print(f"\n🎉 Capture session completed!")
        print(f"📸 Total screenshots captured: {screenshot_count}")
        print(f"📊 OCR results saved to database (snap.db)")
        print(f"📁 Screenshots saved in 'images_screened' folder")

# Run the continuous capture
if __name__ == "__main__":
    start_continuous_capture()
