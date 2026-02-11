# Installation Guide

This project is a Python-based virtual version of the AFWI board game.

## Requirements
- **Python 3.10+** recommended
- **Git** (optional, but recommended)

## Installation Process

### Download the project
Clone with Git:
```bash
git clone https://github.com/tybrun/senior-design.git
cd senior-design
```

Or download ZIP from GitHub and unzip it.

### Create a virtual environment
Virtual environments keep your dependencies isolated and avoid version conflicts.

#### Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the game
Try:
```bash
python main.py
```

If that doesn’t work, check your repo for a file that launches the UI.

## If installation fails
Go to: [Troubleshooting](troubleshooting.md)
