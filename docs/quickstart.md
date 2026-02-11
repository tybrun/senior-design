# Quick Start

This is the fastest path to getting the game running.

## Get the project
- **Option A:** clone the repo with Git
- **Option B:** download the ZIP from GitHub and unzip it

## Create a Python virtual environment

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

## Install dependencies
From the project root (folder containing `requirements.txt`):

```bash
pip install -r requirements.txt
```

## Run the game
Repo’s entry point may change during development. Try one of these options:

```bash
python main.py
```

or, if you have a `src/` package:

```bash
python -m src.main
```

## Learn the basics
- Start with: [User Guide](user-guide.md)
- If you get stuck: [Troubleshooting](troubleshooting.md)
