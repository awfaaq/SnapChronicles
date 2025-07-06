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

# Handle DPI scaling issues
ctypes.windll.user32.SetProcessDPIAware()

# Create images_screened folder if it doesn't exist
os.makedirs('images_screened', exist_ok=True)

# Initialize the log file
log_file = 'log_image.md'
with open(log_file, 'w', encoding='utf-8') as f:
    f.write(f"# Screenshot OCR Log\n\n")
    f.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

time_to_run = 10
print(f"Starting screenshot capture for {time_to_run} seconds...")
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
            
            # Append to log file
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"## Screenshot {screenshot_count}: {filename}\n")
                f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("**Extracted Text:**\n")
                f.write("```\n")
                f.write(extracted_text.strip() if extracted_text.strip() else "(No text detected)")
                f.write("\n```\n\n")
                f.write("---\n\n")
            
            print(f"OCR completed for screenshot {screenshot_count}")
            
        except Exception as ocr_error:
            print(f"OCR error for screenshot {screenshot_count}: {ocr_error}")
            # Log the error
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"## Screenshot {screenshot_count}: {filename}\n")
                f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**OCR Error:** {ocr_error}\n\n")
                f.write("---\n\n")
        
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
                
                # Append to log file
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"## Screenshot {screenshot_count}: {filename}\n")
                    f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("**Extracted Text:**\n")
                    f.write("```\n")
                    f.write(extracted_text.strip() if extracted_text.strip() else "(No text detected)")
                    f.write("\n```\n\n")
                    f.write("---\n\n")
                
                print(f"OCR completed for screenshot {screenshot_count}")
                
            except Exception as ocr_error:
                print(f"OCR error for screenshot {screenshot_count}: {ocr_error}")
                # Log the error
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"## Screenshot {screenshot_count}: {filename}\n")
                    f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"**OCR Error:** {ocr_error}\n\n")
                    f.write("---\n\n")
            
        except Exception as e2:
            print(f"Failed to take screenshot: {e2}")
    
    # Calculate how long to sleep to maintain 1 second intervals
    elapsed = time.time() - loop_start
    sleep_time = max(0, 1.0 - elapsed)
    if sleep_time > 0:
        time.sleep(sleep_time)

print(f"Capture complete! Saved {screenshot_count} screenshots in 'images_screened' folder.")
print(f"OCR results saved to '{log_file}'")

# Add completion timestamp to log
with open(log_file, 'a', encoding='utf-8') as f:
    f.write(f"**Completed at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"**Total screenshots processed:** {screenshot_count}\n")
