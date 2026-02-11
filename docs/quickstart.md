# Quick Start

This is the fastest path to getting the game running.

## 1) Get the project
- **Option A (recommended):** clone the repo with Git
- **Option B:** download the ZIP from GitHub and unzip it

## 2) Create a Python virtual environment (recommended)

### Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### macOS / Linux (Terminal)
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3) Install dependencies
From the project root (the folder that contains `requirements.txt`):

```bash
pip install -r requirements.txt
```

## 4) Run the game
This repo’s entry point may change during development. Try one of these common options:

```bash
python main.py
```

or, if you have a `src/` package:

```bash
python -m src.main
```

If neither works, look for the file that creates the Pygame window (often named `main.py`, `app.py`, `run.py`, or `ui_pygame.py`).

## 5) Learn the basics
- Start with: [User Guide](user-guide.md)
- If you get stuck: [Troubleshooting](troubleshooting.md)
