**SnapChronicles

Hackathon Qualcomm

**Universal Edge OCR & Audio Transcription Toolkit**

SnapChronicles is a lightweight Python toolkit for extracting clean, structured text from screenshots and audio on your local device. It is optimized for real-world scenarios—scientific articles, web pages, news, social platforms, and more—while keeping your data private (no cloud required unless you enable Groq summarization).

---

## Features

* **Universal OCR (Optical Character Recognition)**

  * Adapted for a wide range of content types: scientific publishers (arXiv, ScienceDirect, Springer), Wikipedia, news, e-commerce (Amazon, Apple), social/chat (Discord, YouTube), blogs (Medium, Substack), technical docs (GitHub), and more.
  * Pattern-specific mode detection applies the best cropping and noise reduction for each content type, maximizing OCR accuracy.
  * Batch processing supported.
  * Outputs human-readable text, ready to copy/paste or archive.

* **Speech-to-Text Transcription**

  * High-quality audio transcription from files or speakers using open-source ASR (Automatic Speech Recognition).
  * Edge-first: All transcription runs locally.
  * Simple CLI usage.

* **Structured Archival & Search**

  * All extracted text and audio events are stored in a local SQLite database.
  * Simple CLI interface to view and search events.
  * Ready for semantic search with vectorization modules (see `vector_handler.py`).

* **Optional LLM Summarization (Groq/Llama 3)**

  * Plug-and-play integration for summarizing large text via Groq’s blazing-fast Llama API (if API key is provided).
  * Summarization is **optional**; core features work fully offline.

---

## 📦 Installation

```bash
git clone https://github.com/awfaaq/SnapChronicles.git
cd SnapChronicles
python -m venv .venv
. .venv/Scripts/activate  # (Windows) or source .venv/bin/activate (Linux/Mac)
pip install -r requirements.txt
```

* **Tesseract** is required for OCR (install from [https://github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract)).
* For Groq API features, set your API key as an environment variable:
  `export GROQ_API_KEY="your_api_key"` (Linux/Mac) or `set GROQ_API_KEY=your_api_key` (Windows).

---

## Usage

**OCR from Screenshot**

```bash
python capture_screen_text_in_continue.py path/to/screenshot.png
```

* Mode is auto-detected (arXiv, ScienceDirect, YouTube, Discord, Wikipedia, etc.).

* Clean text is output to terminal and stored in the database.

* Transcribes and stores the audio as a text event.

**Optional: LLM Summarization via Groq**

---

## Limitations

* **Text OCR only:** Does not extract tables, images, or mathematical formulas as LaTeX.
* **Layout-dependent:** Extreme or very noisy layouts may require custom tuning.
* **Speech-to-text:** Best quality with clear audio; no language identification or diarization yet.
* **Groq API is optional:** Summarization works only if a valid Groq API key is provided.

---

## Tech Stack

* **Python 3.10+**
* **Tesseract OCR**
* **Open-source ASR (Whisper or similar)**
* **Groq API / Llama 3 (optional for summarization)**
* **SQLite for local archiving**

---

## Privacy & Edge-First

* All OCR and transcription features run fully on your device by default.
* No data leaves your computer unless you explicitly enable Groq summarization.

---

## Credits

Developed by [Daniel Ashraful](https://github.com/awfaaq), [Mohammad-Habib Javaid](https://github.com/mhjd), [Harith Proietti](https://github.com/HarithProietti)

---

**SnapChronicles empowers you to capture, extract, and organize information from the digital world—simply, locally, and securely.**

---



