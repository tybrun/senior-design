# Appendix
## References and Citations
1. Air Force Wargaming Institute (AFWI). AFWI Rules v1.0 (January 8, 2024). Physical game rules document.
2. Air Force Wargaming Institute (AFWI). AFWI Player Guide v1.0. Official player reference manual.
3. AFWI Glossary of Terms. Air Force Wargaming Institute, 2024.
4. Pygame Community. Pygame Documentation v2.x. https://www.pygame.org/docs/
5. Python Software Foundation. Python 3.11 Standard Library. https://docs.python.org/3/
6. Python Dataclasses — PEP 557. https://peps.python.org/pep-0557/

## Repository
1. main.py — Game logic, Pygame rendering, state machine, event handling
2. game_data.py — Dataclass definitions for all tokens, squadrons, enablers, missions, postures, and campaigns
3. /assets/ — All token, card, and board image assets
4. README.md — Setup instructions, dependencies, and run guide

## Issues and Future Work
1. Online Multiplayer Mode: Local PvP is implemented. Network play over LAN/Internet is a planned future feature
2. AI Opponent: A CPU opponent using real strategy is a planned enhancement for solo training use
3. Enabler Cards: All card images are implemented, a small portion of card effects are stubbed and await full logic
