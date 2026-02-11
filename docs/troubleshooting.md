# Troubleshooting

## Startup problems

### “No module named X”
Cause: dependencies not installed in the environment you’re running.

Fix:
1. Activate your venv
2. Install requirements:
```bash
pip install -r requirements.txt
```

### The window opens but is blank / freezes
Fix checklist:
- Run from terminal and read any printed errors
- Confirm your asset paths are correct (images/data exist)
- Confirm you didn’t accidentally point to missing files

### Assets don’t load (missing images)
Fix checklist:
- Verify the asset folder exists in your repo
- Check filename capitalization (macOS/Linux can be case-sensitive)
- Ensure your code uses relative paths based on project root

## Gameplay problems

### “I can’t select a token / click does nothing”
- Ensure it’s your turn
- Ensure the token is eligible for the action
- Try zoom/pan reset (if supported)

### “Acquire” or “Shoot” feels inconsistent
If your build includes dice rolls:
- verify the roll result appears in a log
- confirm the target is in range
- confirm the target is eligible (acquired/known, not already removed)

## Reporting bugs
When reporting a bug, include:
1. What you expected
2. What happened
3. Steps to reproduce
4. OS + Python version
5. Screenshot or terminal text
