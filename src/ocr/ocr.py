import pytesseract
from PIL import Image

# Install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki
# Configure tesseract path (if not in PATH)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def ocr(image_path):
    # Open an image file
    image = Image.open(image_path)

    # Extract text from the image
    text = pytesseract.image_to_string(image)

    return text

# print(ocr("src/ocr/image2.png"))
