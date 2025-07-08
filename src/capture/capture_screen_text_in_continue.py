from PIL import ImageGrab
import win32gui
import ctypes
import time
import os
import sys
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

# Variable to track the last saved OCR text to avoid duplicates
last_saved_text = None

time_to_run = 10
print(f"Starting screenshot capture for {time_to_run} seconds...")
print(f"📊 OCR results will be saved to the database (duplicates will be skipped)")
start_time = time.time()
screenshot_count = 0

while screenshot_count < time_to_run:  # Take exactly time_to_run screenshots
    loop_start = time.time()
    
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
        print(f"Screenshot {screenshot_count} saved: {filename}")
        
        # Perform OCR on the screenshot
        try:
            print(f"Performing OCR on {filename}...")
            extracted_text = ocr(filename)
            
            # Clean and prepare the text
            cleaned_text = extracted_text.strip() if extracted_text.strip() else "(No text detected)"
            
            # Check if this text is different from the last saved text
            if last_saved_text is None or cleaned_text != last_saved_text:
                # Get Unix timestamp
                unix_timestamp = int(time.time())
                
                # Store in database
                store_event(
                    timestamp=unix_timestamp,
                    source_type="ocr",
                    content=cleaned_text,
                    vectorized=False,
                    media_path=filename
                )
                
                # Update the last saved text
                last_saved_text = cleaned_text
                
                print(f"✅ OCR completed and saved to database for screenshot {screenshot_count}")
            else:
                print(f"🔄 OCR text identical to previous screenshot - skipped database save for screenshot {screenshot_count}")
            
        except Exception as ocr_error:
            print(f"❌ OCR error for screenshot {screenshot_count}: {ocr_error}")
            
            # For errors, we always save them
            # because errors are important to track
            unix_timestamp = int(time.time())
            error_message = f"OCR Error: {str(ocr_error)}"
            
            store_event(
                timestamp=unix_timestamp,
                source_type="ocr",
                content=error_message,
                vectorized=False,
                media_path=filename
            )
            
            # Don't update last_saved_text for errors
        
    except Exception as e:
        print(f"Error taking screenshot {screenshot_count + 1}: {e}")
        print("Taking full screen screenshot instead...")
        try:
            screenshot = ImageGrab.grab()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'images_screened/screenshot_{timestamp}_{screenshot_count:03d}.png'
            screenshot.save(filename)
            screenshot_count += 1
            print(f"Screenshot {screenshot_count} saved: {filename}")
            
            # Perform OCR on the fallback screenshot
            try:
                print(f"Performing OCR on {filename}...")
                extracted_text = ocr(filename)
                
                # Clean and prepare the text
                cleaned_text = extracted_text.strip() if extracted_text.strip() else "(No text detected)"
                
                # Check if this text is different from the last saved text
                if last_saved_text is None or cleaned_text != last_saved_text:
                    # Get Unix timestamp
                    unix_timestamp = int(time.time())
                    
                    # Store in database
                    store_event(
                        timestamp=unix_timestamp,
                        source_type="ocr",
                        content=cleaned_text,
                        vectorized=False,
                        media_path=filename
                    )
                    
                    # Update the last saved text
                    last_saved_text = cleaned_text
                    
                    print(f"✅ OCR completed and saved to database for screenshot {screenshot_count}")
                else:
                    print(f"🔄 OCR text identical to previous screenshot - skipped database save for screenshot {screenshot_count}")
                
            except Exception as ocr_error:
                print(f"❌ OCR error for screenshot {screenshot_count}: {ocr_error}")
                
                # For errors, we always save them
                unix_timestamp = int(time.time())
                error_message = f"OCR Error: {str(ocr_error)}"
                
                store_event(
                    timestamp=unix_timestamp,
                    source_type="ocr",
                    content=error_message,
                    vectorized=False,
                    media_path=filename
                )
                
                # Don't update last_saved_text for errors
            
        except Exception as e2:
            print(f"Failed to take screenshot: {e2}")
    
    # Calculate how long to sleep to maintain 1 second intervals
    elapsed = time.time() - loop_start
    sleep_time = max(0, 1.0 - elapsed)
    if sleep_time > 0:
        time.sleep(sleep_time)

print(f"🎉 Capture complete! Processed {screenshot_count} screenshots.")
print(f"📊 OCR results saved to database (snap.db) - duplicates were automatically skipped")
print(f"📁 Screenshots saved in 'images_screened' folder")
