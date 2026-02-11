import random
from dataclasses import dataclass
from .models import GameState, Side, IntelState
from .dice import d4, d4_advantage

@dataclass
class RulesEngine:
    rng: random.Random

    def new_game(self) -> GameState:
        gs = GameState()
        gs.log.append("New game started. Cyber rate set to 1 for both sides.")
        return gs

    def resolve_initiative(self, gs: GameState, us_discard_bonus: int = 0, prc_discard_bonus: int = 0) -> None:
        """
        Matches rules: players may discard enablers for +1 each, then roll 1d4; ties reroll.
        Winner chooses who goes first and gets Intel Advantage + cyber attempt (we'll add cyber later).
        """
        while True:
            us_roll = d4(self.rng) + us_discard_bonus
            prc_roll = d4(self.rng) + prc_discard_bonus
            gs.log.append(f"Initiative: US rolled {us_roll} (bonus {us_discard_bonus}), PRC rolled {prc_roll} (bonus {prc_discard_bonus}).")
            if us_roll != prc_roll:
                break
            gs.log.append("Initiative tie — rerolling.")

        winner = Side.US if us_roll > prc_roll else Side.PRC
        loser = Side.PRC if winner == Side.US else Side.US

        gs.player(winner).intel = IntelState.ADVANTAGE
        gs.player(loser).intel = IntelState.NORMAL

        # Winner chooses who goes first; for now, default: winner goes first.
        gs.current_side = winner
        gs.log.append(f"{winner.value} wins initiative, takes first turn, and gains Intel Advantage.")
        # Rules reference: initiative winner chooses who goes first + gets intel advantage. :contentReference[oaicite:8]{index=8}

    def intel_roll(self, gs: GameState) -> None:
        """
        Both roll 1d4; advantage side rolls at advantage.
        In the real game this reveals # of enabler cards seen. We'll log it for now.
        """
        for side in (Side.US, Side.PRC):
            player = gs.player(side)
            if player.intel == IntelState.ADVANTAGE:
                rr = d4_advantage(self.rng)
                gs.log.append(f"Intel roll ({side.value}, ADV): rolls={rr.rolls} chosen={rr.chosen}")
            else:
                r = d4(self.rng)
                gs.log.append(f"Intel roll ({side.value}): {r}")
