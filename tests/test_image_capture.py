from PIL import ImageGrab
import win32gui
import ctypes
import time
import os
from datetime import datetime

# Handle DPI scaling issues
ctypes.windll.user32.SetProcessDPIAware()

# Create images_screened folder if it doesn't exist
os.makedirs('images_screened', exist_ok=True)

time_to_run = 20
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
        except Exception as e2:
            print(f"Failed to take screenshot: {e2}")
    
    # Calculate how long to sleep to maintain 1 second intervals
    elapsed = time.time() - loop_start
    sleep_time = max(0, 1.0 - elapsed)
    if sleep_time > 0:
        time.sleep(sleep_time)

print(f"Capture complete! Saved {screenshot_count} screenshots in 'images_screened' folder.")
