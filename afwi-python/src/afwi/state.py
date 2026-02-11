from enum import Enum, auto

class Phase(Enum):
    SETUP = auto()
    ATO_START = auto()
    INITIATIVE = auto()
    INTEL_ROLL = auto()
    TURNS = auto()
    ATO_END = auto()
    ENDGAME = auto()
