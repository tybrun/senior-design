from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class Side(Enum):
    US = "US"
    PRC = "PRC"


class IntelState(Enum):
    NORMAL = auto()
    ADVANTAGE = auto()


class TokenCategory(Enum):
    """Used for acquisition target values from the rules."""

    FIGHTER_5G = auto()   # acquisition target 4
    UAS = auto()          # acquisition target 3
    OTHER = auto()        # acquisition target 2
    IAMD = auto()         # treated as OTHER for acquire, but special shooting rules later


@dataclass
class Weapon:
    range: int
    hit: int  # d4 must be >= hit


@dataclass
class TokenType:
    """Data-driven token definition."""

    id: str
    name: str
    side: Side
    category: TokenCategory

    move: int
    sensor: int
    acquisition_bonus: int = 0

    missile: Optional[Weapon] = None
    bomb: Optional[Weapon] = None

    uas_infinite_ammo: bool = False
    can_deploy_any_band: bool = False

    image_path: Optional[str] = None

    def acquisition_target(self) -> int:
        # Acquisition table from rules: 5G=4, UAS=3, all others=2
        if self.category == TokenCategory.FIGHTER_5G:
            return 4
        if self.category == TokenCategory.UAS:
            return 3
        # IAMD and OTHER share target 2
        return 2


@dataclass
class TokenInstance:
    instance_id: str
    type_id: str
    side: Side

    # location
    band: Optional[int] = None  # 1..5 when on the board; None means at base / offboard
    at_base: bool = True

    # fog-of-war
    face_up: bool = False  # acquired => face_up True (both can see)

    # ammo
    winchester: bool = False


@dataclass
class PlayerState:
    side: Side
    intel: IntelState = IntelState.NORMAL
    cyber_rate: int = 1
    vp: int = 0

    passed: bool = False
    posture: Optional[str] = None

    enablers_in_hand: list[str] = field(default_factory=list)
    squadrons_in_hand: list[str] = field(default_factory=list)


@dataclass
class GameState:
    ato_number: int = 1
    current_side: Side = Side.US

    us: PlayerState = field(default_factory=lambda: PlayerState(Side.US))
    prc: PlayerState = field(default_factory=lambda: PlayerState(Side.PRC))

    token_types: dict[str, TokenType] = field(default_factory=dict)
    tokens: dict[str, TokenInstance] = field(default_factory=dict)

    log: list[str] = field(default_factory=list)

    def player(self, side: Side) -> PlayerState:
        return self.us if side == Side.US else self.prc
