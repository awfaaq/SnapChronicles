import cv2
import pytesseract
import numpy as np

def ocr():
    # Load image
    img = cv2.imread("image.png")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Remove noise and smooth
    gray = cv2.medianBlur(gray, 3)

    # Adaptive Thresholding for better contrast
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 10
    )

    # Optional: invert if needed (e.g. dark background)
    white_ratio = cv2.countNonZero(thresh) / (thresh.shape[0] * thresh.shape[1])
    if white_ratio < 0.5:
        thresh = cv2.bitwise_not(thresh)

    # OCR with Tesseract
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(thresh, config=config)

    # Basic cleaning
    lines = text.splitlines()
    cleaned = [l.strip() for l in lines if len(l.strip()) > 3]
    return "\n".join(cleaned)
print(ocr()) 
