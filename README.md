# RDM - Rohan's Download Manager

A full-featured, IDM-like download manager with multi-threaded segmented downloads, browser integration, scheduling, and a modern professional UI. Built with PySide6 and powered by [aria2](https://aria2.github.io/) as the download engine.

## Features

- **Multi-threaded segmented downloads** – Up to 16 connections per download
- **Pause / Resume / Restart** – Full support with persistent state across restarts
- **Download queue** – Configurable max concurrent downloads, priority ordering
- **Speed limiter** – Global and per-download bandwidth limits
- **Categories** – Auto-categorize by file type (Documents, Videos, Music, etc.)
- **Download history** – SQLite-backed, searchable
- **Scheduler** – Schedule downloads for specific times
- **Clipboard monitoring** – Add downloads from copied URLs
- **Browser integration** – Chrome/Edge extension sends downloads to RDM
- **Batch downloads** – Multiple URLs, URL patterns, import from file
- **Themes** – Light and dark mode
- **System tray** – Minimize to tray, notifications

## Requirements

- **Python 3.11+**
- **aria2** – RDM uses [aria2](https://aria2.github.io/) as the download engine. You must have `aria2c` on your PATH, or place the `aria2c` binary in `~/.rdm/aria2/` (see [rdm/core/aria2_manager.py](rdm/core/aria2_manager.py)). The app does not bundle aria2; install it separately (e.g. [Windows](https://github.com/aria2/aria2/releases), macOS: `brew install aria2`).

## Releases

Pre-built installers are produced by GitHub Actions:

- **Windows**: download `RDM.exe` from the [Actions](https://github.com/wingsaberrohan/RDM/actions) run artifacts (e.g. **RDM-Windows-0.1.0**), or from a [Release](https://github.com/wingsaberrohan/RDM/releases) if you tag a version.
- **macOS**: download the `.dmg` from the same artifacts or releases (e.g. **RDM-macOS-0.1.0**).

To create a release: update `rdm/__init__.py` version, push, then create a Release in the repo; the workflow will attach the Windows and macOS builds to that release.

## Installation

1. Clone or download this repository.
2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Ensure `aria2c` is on your PATH, or let RDM use its built-in handling (see docs).

## Usage

Run the application:

```bash
python main.py
```

- **Add download**: Toolbar → Add, or paste a URL and use clipboard prompt.
- **Pause/Resume**: Right-click a download or use toolbar actions.
- **Categories**: Use the left sidebar to filter by category.
- **Settings**: Toolbar → Settings for connection count, speed limits, themes.

## Project structure

- `main.py` – Entry point
- `rdm/` – Main package
  - `app.py` – Application setup, single-instance lock
  - `core/` – aria2 manager, download manager, RPC client, clipboard, scheduler, etc.
  - `db/` – SQLite database and models
  - `ui/` – Main window, download table, dialogs, themes
  - `utils/` – File and URL helpers
  - `resources/` – Icons and stylesheets
- `browser_extension/` – Chrome/Edge extension for browser integration

## License

MIT
