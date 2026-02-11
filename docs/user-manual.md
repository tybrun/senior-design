# User Manual (Reference)

Use this manual for quick lookup and definitions.

## Glossary (short)
- **ATO cycle:** The larger “round” of play made up of alternating turns.
- **Turn:** One player action opportunity.
- **MAS:** Move / Acquire / Shoot.
- **Enabler:** A card that provides multi-domain effects (intel/cyber/logistics/etc.).
- **Squadron:** A card that represents a set of assets that can deploy tokens.

For more help go to
 - [Rules](game-resources/AFWIRulesV10_01.8.24.pdf)
 - [Glossary](game-resources/AFWI_Glossary.pdf)
 - [Move Flow Chart](/game-resources/Move_Flow_Chart.pptx)
 - [Base Strike Flowchart](/game-resources/AFWI_Base_Strike_Flowchart.pptx)
 - [Token Depiction Chart](/game-resources/AFWI_Token_Depiction_Chart.pptx)

## Game objects

### Tokens
Tokens represent units on the board (air, maritime, IAMD, etc.). Common properties:
- movement
- attack range / strength
- defense / survivability
- acquisition / sensor power

> Document your exact token stats source here (JSON/CSV/XLSX) when finalized.

### Cards
#### Squadron cards
- generate / enable deployment of tokens
- can be destroyed or disabled depending on rules

#### Enabler cards
- usually played once, sometimes persistent for an ATO
- can affect initiative, intel, cyber, movement, targeting, etc.

#### Mission cards
- define scoring conditions

#### Posture cards
- define limits and special conditions for an ATO

## Dice and resolution (template)
Document your in-game dice rules:
- what die is used (d4/d6/etc.)
- how advantage/disadvantage works
- what “success” means (threshold vs opposed roll)
- how damage is applied

## Saving and loading (if supported)
- Where save files are stored
- What is saved (board state, hands, tracks)
- Known limitations

## File locations (fill in for your repo)
- Token images: `assets/tokens/`
- Card images: `assets/cards/`
- Data files (stats): `data/`
- Saves/logs: `saves/` or `logs/`

Update these paths to match your actual project structure.
