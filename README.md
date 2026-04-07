# Air Force Wargame: Indo-Pacific — Digital Edition

## Quick Start
```bash
pip install pygame
python main.py
```

## Structure
```
V_AFWI/
├── main.py, game_data.py, board.jpg
└── assets/
    ├── tokens/{us,prc}/    # Token images
    └── cards/{us,prc}/     # Card images
```

## Design
- Board.jpg renders directly — tokens overlay at correct band positions
- Cards (enabler/mission/posture) in side panel only
- Click to toggle card selection up to posture limits
- Handoff screens between turns for hotseat privacy
- Hover tokens for stat tooltips
