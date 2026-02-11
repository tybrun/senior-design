# Gameplay Walkthrough

This walkthrough is written for players who want a step-by-step view of a typical game.

> Your implementation may simplify steps while you build the prototype. That’s okay—update this page as features land.

## 1) Campaign setup
1. Choose a campaign/scenario (how many ATO cycles, which map/setup)
2. Each player chooses a mission (often secret until end)
3. Initialize any tracks (e.g., Intel/Cyber), if your build supports them

## 2) Start an ATO cycle
### Choose posture
Posture may affect:
- how many squadron cards you can use
- how many enabler cards you can draw/play
- other special conditions

### Draw cards
Draw squadron and enabler cards up to the posture limits.

### Place squadrons
Place selected squadrons at airbases (usually face down).

## 3) Initiative + Intelligence (if supported)
Many AFWI flows include:
- a bid for initiative (possibly discarding cards for bonuses)
- an intel roll (sometimes with advantage/disadvantage)
These steps determine who acts first and what information is revealed.

## 4) Turns (repeat until both pass)
On your turn, choose one:
- Play an enabler
- Activate a squadron (deploy tokens)
- MAS (Move/Acquire/Shoot)
- Pass

### MAS in more detail
#### Move
Reposition a token according to its movement rules.

#### Acquire
Attempt to reveal an enemy token (fog-of-war). Some units are better at acquiring than others.

#### Shoot
Attack a target in range. Apply results (markers, damage, or destruction).

## 5) End of ATO cycle
When both players pass, the ATO cycle ends.
Depending on your build, you may:
- clear certain temporary effects
- advance to the next ATO
- update the UI/log with a summary

## 6) End of campaign
At campaign end:
- reveal mission cards (if secret)
- compute VP
- declare winner

## Suggested screenshots to add
- ATO start screen (posture + draw)
- Squadron placement
- An “Acquire” result
- A “Shoot” resolution
- End-of-ATO summary
