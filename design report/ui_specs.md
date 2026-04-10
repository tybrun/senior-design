# User Interface Specification

## Philosophy
The design mirrors the physical game board, cards, and tokens as closely as possible, while adding a digital side panel to control user actions.
No command line input is required, players interact only through mouse clicks.

## Main Menu
On start, the player is allowed to select which mode they want to continue with.
Players have the option of a tutorial mode or Player v Player

## PvP Screen Layout
The window is composed of the following regions
| Region        | Description                                                           |
| Game Board    | Central panel showing range bands, bases, and squadron card sprites   |
| Action Panel  | Buttons for available actions MAS, Enabler cards, end turn            |
| Turn Display  | Output text below the action panel describing previous player's moves |
| Score Board   | Running tally of victory points, updated each turn                    |

### Interactions
All interactions are click-based. Hovering on a token displays its capabilities, and clicking an action in the action panel initiates that move.
Invalid actions are greyed out or alerted upon click.
