# SnapChronicles Architecture

## Root (`/`)
Role: project entrypoint for capture, OCR/ASR processing, semantic search, and documentation.

Files:
- `AGENTS.md`: local operating rules for reliability, observability, and architecture documentation updates.
- `Makefile`: central command runner for setup, execution, tests, lint/format, and cleanup tasks.
- `README.md`: product overview, setup, and user-facing usage notes.
- `requirements.txt`: pinned Python dependencies (OCR, audio capture, Whisper, FAISS, sentence-transformers, etc.).
- `search.py`: root wrapper that loads `src/` in `sys.path` and starts the interactive semantic search CLI (`src/database/search_cli.py`).
- `video_snapchronicles.mp4`: demo asset.
- `LICENSE`: license placeholder (currently empty).
- `ARCHITECTURE.md`: this architecture reference file.

Directories:
- `docs/`: project documentation placeholders.
- `scripts/`: automation/bootstrap placeholders.
- `src/`: application source code (capture, OCR, ASR, database, search).
- `tests/`: standalone/manual test scripts.
- `.venv/`, `venv/`: local Python virtual environments.

## `docs/`
Role: documentation folder intended for setup, benchmarking, and architecture notes.

Files:
- `docs/setup.md`: setup documentation placeholder (currently empty).
- `docs/bench.md`: benchmark documentation placeholder (currently empty).
- `docs/architecture.md`: old architecture placeholder (currently empty). Root `ARCHITECTURE.md` is the active architecture document.

## `scripts/`
Role: operational scripts folder.

Files:
- `scripts/bootstrap.ps1`: bootstrap placeholder script (currently empty).

## `src/`
Role: core application logic for continuous capture, extraction, storage, and retrieval.

### `src/run_dual_capture.py`
Role: orchestrator that launches screen capture and speaker capture as two child processes, handles graceful shutdown, and enforces cleanup.

Relations:
- Starts `src/capture/capture_screen_text_in_continue.py`.
- Starts `src/capture/capture_speaker_text_in_continue.py`.

### `src/capture/`
Role: continuous ingestion pipelines from screen and system audio.

Files:
- `src/capture/capture_screen_text_in_continue.py`: captures active-window screenshots on a fixed interval, runs OCR, deduplicates repeated OCR text, stores OCR events in SQLite.
- `src/capture/capture_speaker_text_in_continue.py`: records desktop loopback audio in segments, transcribes each segment with Whisper, logs transcriptions, stores events in SQLite.

Relations:
- Uses `src/ocr/ocr.py` for OCR extraction.
- Uses `src/asr/asr.py` for transcription.
- Uses `src/database/db_handler.py` for persistence.

### `src/ocr/`
Role: OCR extraction and preprocessing strategies.

Files:
- `src/ocr/ocr.py`: mode-based OCR pipeline (Discord/Wikipedia/YouTube/ScienceDirect/PDF/Web heuristics) using OpenCV + Tesseract.
- `src/ocr/test_opencv.py`: quick OCR experiment script over `image.png`.

### `src/asr/`
Role: speech-to-text abstraction layer.

Files:
- `src/asr/asr.py`: `WhisperASR` class for model loading, transcription, language choice helper, text extraction utilities, and timing logs.

### `src/database/`
Role: persistence and retrieval layer (events + vectors + semantic search CLI).

Files:
- `src/database/db_handler.py`: SQLite event schema/init, event storage, auto-vectorization trigger, semantic search aggregation, vector stats, retroactive vectorization.
- `src/database/vector_handler.py`: sentence-transformer embedding generation, vectors table management, FAISS index lifecycle, similarity search and stats.
- `src/database/search_cli.py`: interactive semantic search CLI, optional query expansion provider selection, result/stat formatting.
- `src/database/db_viewer.py`: utility to print stored events and summary stats from SQLite.
- `src/database/test_db.py`: manual test script for DB CRUD flow.
- `src/database/test_vectorisation.py`: standalone vectorization/search benchmark script.
- `src/database/test_vectorization_integration.py`: end-to-end integration test for auto-vectorization and semantic search.

Relations:
- `db_handler.py` lazily imports `vector_handler.py` to keep vector stack optional until needed.
- `search_cli.py` uses `db_handler.py` for search/stat APIs.
- Root `search.py` calls `search_cli.py` entrypoint.

### `src/cli/`
Role: reserved CLI package location.

Files:
- `src/cli/snapcli.py`: placeholder (currently empty).

## `tests/`
Role: extra standalone/manual testing scripts outside `src/`.

Files:
- `tests/test_capture_audio.py`: continuous audio capture test without transcription pipeline (focus on stable segmented recording).
- `tests/test_image_capture.py`: active-window screenshot capture test.
- `tests/test_capture.py`: placeholder (currently empty).
- `tests/test_ocr.py`: placeholder (currently empty).

## Runtime Artifacts (generated, not versioned by default)
Role: data produced during local runs.

Examples:
- `snap.db`: SQLite events database.
- `vectors.faiss`: FAISS index persisted by vector search module.
- `images_screened/`: captured screenshots.
- `recording_session_YYYYMMDD_HHMMSS/`: saved audio segments.
- `log_audio.md`: audio transcription session logs.
