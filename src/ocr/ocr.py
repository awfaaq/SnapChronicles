import cv2
import numpy as np
import pytesseract
import os
import re
from glob import glob

# Change ce chemin selon ton install
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def ocr_discord(image_path, debug=False):
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    # Discord : colonne centrale large (20% à 81%)
    left, right = int(0.20 * w), int(0.81 * w)
    img_core = img[:, left:right]
    gray = cv2.cvtColor(img_core, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    th = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 31, 10)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15,3))
    morph = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel)
    cnts, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    core_w = right - left
    rects = []
    for c in cnts:
        x, y, ww, hh = cv2.boundingRect(c)
        if ww > 0.40*core_w or (ww > 0.32*core_w and hh > 30):
            rects.append((x, y, ww, hh))
    rects = sorted(rects, key=lambda r: (r[1], r[0]))
    lines = []
    for x, y, ww, hh in rects:
        crop = gray[y:y+hh, x:x+ww]
        crop = cv2.equalizeHist(crop)
        text = pytesseract.image_to_string(crop, lang="fra+eng", config='--oem 3 --psm 6')
        for L in text.splitlines():
            L2 = L.strip()
            if len(L2) > 2:
                lines.append(L2)
        lines.append("")
    # Nettoie le texte OCR Discord (enlève bruit, lignes isolées)
    cleaned = []
    for l in lines:
        if len(l.strip()) > 0 and not re.match(r'^[@#+\-•\s]*$', l):
            cleaned.append(l.strip())
    return "\n".join(cleaned).strip()

def ocr_wikipedia(image_path, debug=False):
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    left, right = int(0.28 * w), int(0.75 * w)
    top, bottom = int(0.12 * h), int(0.92 * h)
    img_core = img[top:bottom, left:right]
    gray = cv2.cvtColor(img_core, cv2.COLOR_BGR2GRAY)
    eq = cv2.equalizeHist(gray)
    th = cv2.adaptiveThreshold(eq, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 31, 10)
    text = pytesseract.image_to_string(th, lang="eng+fra", config="--oem 3 --psm 4")
    # Nettoyage :
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 12]
    lines = [l for l in lines if not re.match(r'^(Tools|History|Talk|View|Languages|Search|Contents|Article|Help|Read|Navigation|Appearance|Donate|Login|Account|Wikipedia)', l)]
    return "\n".join(lines)

def ocr_youtube(image_path, debug=False):
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    left, right = int(0.22 * w), int(0.72 * w)
    top, bottom = int(0.11 * h), int(0.91 * h)
    img_core = img[top:bottom, left:right]
    gray = cv2.cvtColor(img_core, cv2.COLOR_BGR2GRAY)
    eq = cv2.equalizeHist(gray)
    th = cv2.adaptiveThreshold(eq, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 31, 10)
    text = pytesseract.image_to_string(th, lang="eng+fra", config="--oem 3 --psm 4")
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 8]
    # Omet certains menus
    lines = [l for l in lines if not re.search(r'(Shorts|Subscribe|Account|Gaming|Music|Sign In|Sort by|Mixes|Share|Replay|Add to|Menu|Download|Help|Settings|Feedback|Home)', l, re.I)]
    return "\n".join(lines)

def ocr_sciencedirect(image_path, debug=False):
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    left, right = int(0.19 * w), int(0.80 * w)
    top, bottom = int(0.12 * h), int(0.90 * h)
    img_core = img[top:bottom, left:right]
    gray = cv2.cvtColor(img_core, cv2.COLOR_BGR2GRAY)
    eq = cv2.equalizeHist(gray)
    th = cv2.adaptiveThreshold(eq, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 31, 10)
    text = pytesseract.image_to_string(th, lang="eng+fra", config="--oem 3 --psm 4")
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 12]
    lines = [l for l in lines if not re.search(r'(Download|Help|Rights|Recommended|Feedback|Account|Mendeley|Share|Cite|Journal|Copyright|PDF|View details|More articles|Search|ScienceDirect)', l, re.I)]
    return "\n".join(lines)

def ocr_pdf_article(image_path, debug=False):
    # Par défaut : colonne centrale large, style "web article/PDF"
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    left, right = int(0.18 * w), int(0.83 * w)
    img_core = img[:, left:right]
    gray = cv2.cvtColor(img_core, cv2.COLOR_BGR2GRAY)
    eq = cv2.equalizeHist(gray)
    th = cv2.adaptiveThreshold(eq, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 31, 10)
    text = pytesseract.image_to_string(th, lang="eng+fra", config="--oem 3 --psm 4")
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 10]
    return "\n".join(lines)

def detect_mode(image_path):
    name = os.path.basename(image_path).lower()
    if "discord" in name or name == "image.png":
        return "discord"
    elif "wikipedia" in name:
        return "wikipedia"
    elif "youtube" in name:
        return "youtube"
    elif "sciencedirect" in name:
        return "sciencedirect"
    elif name.endswith(".pdf") or "article" in name:
        return "pdf_article"
    else:
        # Heuristique : par défaut = "web/article"
        return "web"

def ocr_web(image_path, debug=False):
    # Découpe centrale neutre, fallback universel (mode web)
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    left, right = int(0.21 * w), int(0.78 * w)
    img_core = img[:, left:right]
    gray = cv2.cvtColor(img_core, cv2.COLOR_BGR2GRAY)
    eq = cv2.equalizeHist(gray)
    th = cv2.adaptiveThreshold(eq, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 31, 10)
    text = pytesseract.image_to_string(th, lang="eng+fra", config="--oem 3 --psm 4")
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 8]
    return "\n".join(lines)

def ocr(img_path):  
    mode = detect_mode(img_path)
    if mode == "discord":
        result = ocr_discord(img_path)
    elif mode == "wikipedia":
        result = ocr_wikipedia(img_path)
    elif mode == "youtube":
        result = ocr_youtube(img_path)
    elif mode == "sciencedirect":
        result = ocr_sciencedirect(img_path)
    elif mode == "pdf_article":
        result = ocr_pdf_article(img_path)
    else:
        result = ocr_web(img_path)
    return result
