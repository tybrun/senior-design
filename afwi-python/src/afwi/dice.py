import random
from dataclasses import dataclass

@dataclass(frozen=True)
class RollResult:
    rolls: tuple[int, ...]
    chosen: int

def d4(rng: random.Random) -> int:
    return rng.randint(1, 4)

def d4_advantage(rng: random.Random) -> RollResult:
    a, b = d4(rng), d4(rng)
    return RollResult(rolls=(a, b), chosen=max(a, b))

def d4_disadvantage(rng: random.Random) -> RollResult:
    a, b = d4(rng), d4(rng)
    return RollResult(rolls=(a, b), chosen=min(a, b))
