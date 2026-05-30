# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Kataster-Sorter is an offline tool that reorders the pages of German *Liegenschaftskataster* (real-estate cadastre) PDF exports and merges in the matching cover sheets ("Deckblätter"). Users upload a Kataster export plus one or two cover-sheet PDFs; the app classifies each file automatically, regroups pages, and produces a single combined PDF for download.

The domain is German and **the codebase (comments, docstrings, UI strings, variable names) is written in German**. Match that convention when editing — keep terms like `ffn` (Fortführungsfallnummer), `gb` (Grundbuchblatt), `lfd_nr` (laufende Nummer), `akz` (Antragskennzeichen), `Sonderfall`, and `Deckblatt`.

## Architecture

There is **one processing engine and two interchangeable frontends**, all sharing `pdf_processor.py`:

- `pdf_processor.py` — the entire domain logic. `KatasterSorter.process_files(list[(filename, bytes)]) -> dict` is the single entry point both frontends call. It returns a result dict (counts, detected AKZ, AKZ corrections, `combined_pdf` bytes, and a `debug_log`). The class also exposes a module-level `detect_file_type(pdf_bytes)` used for auto-classification.
- `app.py` — Streamlit web UI. Reads uploaded files into bytes, calls `process_files`, renders stats/debug, offers the combined PDF as a download.
- `desktop_app.py` — standalone CustomTkinter desktop UI. Uses a `filedialog` to pick files and runs `process_files` on a background `threading.Thread` (the engine is otherwise identical). This is the file packaged into the Windows `.exe`.

When changing behavior, edit `pdf_processor.py` so both frontends benefit. The frontends should stay thin — they only marshal file bytes in and render the result dict out.

### Processing pipeline (inside `process_files`)

1. **Auto-classify** each input file via `detect_file_type` (scans the first 5 pages): `kataster` (contains "Fortführungsfallnummer"), `cover_standard` ("Grundbuchblatt (lfd. Nr.)"), or `cover_sonder` ("mehrere Grundbuchblätter"). Exactly one Kataster file is required or it raises `ValueError`.
2. **Extract** per-page info from the Kataster export with `pdfplumber` text extraction, driven by the regex patterns defined at the top of the module (`FFN_PATTERN`, `GB_PATTERN`, `LFD_NR_PATTERN`, `GB_COVER_PATTERN`, `AKZ_PATTERN`, etc.).
3. **Group** pages into `Package`s by Fortführungsfallnummer (pages without their own FFN inherit the current one).
4. **Analyze**: a package spanning more than one Grundbuchblatt becomes a `Sonderfall`; otherwise it is a Standard package keyed by its single GB.
5. **Sort & combine** (`_create_combined_pdf`): Standard packages are grouped by GB number, ordered by GB then by lfd. Nr. (FFN as fallback); **one** standard cover sheet is emitted per GB group, followed by all its pages. Sonderfall packages each get a Sonderfall cover. PDF pages are copied with `pypdf` (`PdfReader`/`PdfWriter`).
6. **AKZ correction** (`_apply_akz_correction`): if a cover sheet's Antragskennzeichen differs from the one detected in the Kataster export, a white `reportlab` overlay is drawn over the cover at a fixed position and merged onto the page; each correction is logged in `akz_mismatches`.

The `debug_log` / `akz_mismatches` lists are the primary debugging surface — both UIs surface them in a collapsible "Debug-Info" panel.

## Running

```bash
pip install -r requirements.txt          # streamlit, pdfplumber, pypdf, reportlab
streamlit run app.py                      # web UI at http://localhost:8501
python desktop_app.py                     # desktop UI
```

The dev container auto-runs `streamlit run app.py` on attach and forwards port 8501.

There is **no test suite, linter, or CI** configured. Verification is manual: feed sample PDFs through the UI and inspect the combined output and debug log.

## Windows packaging

`build_windows.bat` (Windows only) creates a venv, installs `requirements.txt` + `pyinstaller`, and bundles `desktop_app.py` into `dist\Kataster-Sorter.exe` (`--onefile --windowed`, bundling `pdf_processor.py` and collecting `customtkinter`). `installer.iss` then wraps that exe into an Inno Setup installer. See `BUILD_WINDOWS.md`.

## Gotchas

- **`requirements.txt` covers the web app only.** The desktop app additionally needs `customtkinter`, and packaging needs `pyinstaller` (the build script installs both explicitly). Add `customtkinter` to requirements if you intend to run the desktop UI from a plain install.
- `desktop_app.py` expects an `icon.ico` next to it (and resolves it via `sys._MEIPASS` when frozen by PyInstaller); the file is not committed.
- The `README.md` references `Kataster-Sorter.bat` / `Kataster-Sorter.sh` launchers that do not exist in the repo — the real entry points are the commands above.
- Text extraction relies on the PDFs being text-based, not scanned images; the regexes are tuned to the exact German cadastre export wording.
