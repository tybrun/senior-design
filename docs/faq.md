# FAQ

## Installing / Running

**Q: Game won’t start. What should I check first?**  
A: Make sure:
- You’re in the project root folder
- Your virtual environment is activated
- Dependencies are installed: `pip install -r requirements.txt`

**Q: I get `ModuleNotFoundError` (pygame, pandas, etc.).**  
A: Activate your venv and reinstall dependencies:
```bash
pip install -r requirements.txt
```

## Gameplay

**Q: Why are tokens face down?**  
A: Fog-of-war: The enemy doesn’t know what a token is until it’s acquired/revealed.

**Q: What’s the difference between an ATO cycle and a turn?**  
A: ATO cycle is the larger round; turns are the back-and-forth actions inside it.

**Q: The UI won’t let me shoot a target. Why?**  
A: Common reasons:
- Target is not acquired/revealed yet
- Target is out of range
- Shooter already acted / has no weapons (winchester) / is disabled
