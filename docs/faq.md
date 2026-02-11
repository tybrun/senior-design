# FAQ

## Installing / Running

**Q: The game won’t start. What should I check first?**  
A: Make sure:
- you’re in the project root folder
- your virtual environment is activated
- dependencies are installed: `pip install -r requirements.txt`

**Q: I get `ModuleNotFoundError` (pygame, pandas, etc.).**  
A: Activate your venv and reinstall dependencies:
```bash
pip install -r requirements.txt
```

**Q: I get permission errors on Windows PowerShell activation.**  
A: You may need to allow script execution for your user:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Gameplay

**Q: Why are tokens face down?**  
A: Fog-of-war: the enemy doesn’t know what a token is until it’s acquired/revealed.

**Q: What’s the difference between an ATO cycle and a turn?**  
A: ATO cycle is the larger round; turns are the back-and-forth actions inside it.

**Q: The UI won’t let me shoot a target. Why?**  
A: Common reasons:
- target is not acquired/revealed yet
- target is out of range
- shooter already acted / has no weapons (winchester) / is disabled

## Project

**Q: Where do I report bugs?**  
A: Open a GitHub Issue with:
- steps to reproduce
- expected vs actual behavior
- screenshots or terminal output
