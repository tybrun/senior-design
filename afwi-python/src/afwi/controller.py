import random
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from .dice import d4, d4_advantage
from .models import (
    GameState,
    IntelState,
    Side,
    TokenCategory,
    TokenInstance,
    TokenType,
    Weapon,
)
from .loaders import load_token_manifest, load_token_stats
from .state import Phase


@dataclass
class Posture:
    name: str
    enabler_limit: int
    squadron_limit: int


# Placeholder postures for now. We'll replace with real posture stats later.
POSTURES = [
    Posture("Standard", enabler_limit=4, squadron_limit=2),
    Posture("ACE", enabler_limit=3, squadron_limit=2),
    Posture("Surge", enabler_limit=5, squadron_limit=3),
]


class MasMode(Enum):
    NONE = auto()
    MENU = auto()
    MOVE = auto()
    ACQUIRE = auto()
    SHOOT = auto()


class GameController:
    """Owns the game state AND the current 'input mode' for the prototype UI."""

    def __init__(self, seed: int = 1) -> None:
        self.rng = random.Random(seed)
        self.phase = Phase.SETUP
        self.gs = GameState()

        # Prototype decks (strings for now)
        self.us_enabler_deck = [f"US_Enabler_{i}" for i in range(1, 31)]
        self.prc_enabler_deck = [f"PRC_Enabler_{i}" for i in range(1, 31)]
        self.us_squadron_deck = [f"US_Squadron_{i}" for i in range(1, 16)]
        self.prc_squadron_deck = [f"PRC_Squadron_{i}" for i in range(1, 16)]

        # MAS input state
        self.mas_mode: MasMode = MasMode.NONE
        self.selected_own_idx: int = 0
        self.selected_enemy_idx: int = 0
        self.pending_band: Optional[int] = None

    # ----------------- helpers -----------------
    def log(self, msg: str) -> None:
        self.gs.log.append(msg)

    def _other(self, side: Side) -> Side:
        return Side.PRC if side == Side.US else Side.US

    def _own_tokens_on_board(self, side: Side) -> list[str]:
        ids = [tid for tid, t in self.gs.tokens.items() if t.side == side and t.band is not None]
        ids.sort()
        return ids

    def _enemy_tokens_on_board(self, side: Side) -> list[str]:
        ids = [tid for tid, t in self.gs.tokens.items() if t.side != side and t.band is not None]
        ids.sort()
        return ids

    def _get_type(self, token_id: str) -> TokenType:
        inst = self.gs.tokens[token_id]
        return self.gs.token_types[inst.type_id]

    def _begin_turn(self, side: Side) -> None:
        """Apply 'beginning of turn' housekeeping.

        Rules: tokens with Winchester must return to base at the beginning of the player's next turn.
        In prototype: we move them to base (band=None) and clear winchester.
        """
        for tid, inst in self.gs.tokens.items():
            if inst.side != side:
                continue
            if inst.winchester and inst.band is not None:
                inst.band = None
                inst.at_base = True
                inst.winchester = False
                self.log(f"{side.value}: {tid} returns to base (Winchester).")

    # ----------------- data loading -----------------
    def load_tokens(self, manifest_path: str, stats_path: str) -> None:
        """Loads token images (manifest) + token stats (json) into TokenTypes.

        If a token id appears in the manifest but not in token_stats.json, we load safe defaults.
        """
        manifest = load_token_manifest(manifest_path)
        stats = load_token_stats(stats_path)
        stats_map = (stats.get("tokens") or {})

        def parse_category(raw: str) -> TokenCategory:
            try:
                return TokenCategory[raw]
            except Exception:
                return TokenCategory.OTHER

        def parse_weapon(obj) -> Optional[Weapon]:
            if not obj:
                return None
            return Weapon(range=int(obj.get("range", 0)), hit=int(obj.get("hit", 5)))

        count = 0
        for t in manifest.get("tokens", []):
            token_id = t["id"]
            side = Side.US if t["side"] == "US" else Side.PRC

            s = stats_map.get(token_id, {})
            name = s.get("name") or t.get("name") or token_id

            tt = TokenType(
                id=token_id,
                name=name,
                side=side,
                category=parse_category(s.get("category", "OTHER")),
                move=int(s.get("move", 1)),
                sensor=int(s.get("sensor", 1)),
                acquisition_bonus=int(s.get("acquisition_bonus", 0)),
                missile=parse_weapon(s.get("missile")),
                bomb=parse_weapon(s.get("bomb")),
                uas_infinite_ammo=bool(s.get("uas_infinite_ammo", False)),
                can_deploy_any_band=bool(s.get("can_deploy_any_band", False)),
                image_path=t.get("image_path"),
            )

            self.gs.token_types[tt.id] = tt
            count += 1

        self.log(f"Loaded {count} token types (manifest + stats).")

    # ----------------- phase flow -----------------
    def new_game(self) -> None:
        self.gs = GameState()
        self.phase = Phase.ATO_START
        self.mas_mode = MasMode.NONE
        self.log("New game started. Cyber rates set to 1; Intel NORMAL.")
        self.log(f"ATO {self.gs.ato_number} begins: select postures. (Keys: 1/2/3)")

    def _draw_cards(self, side: Side, posture: Posture) -> None:
        p = self.gs.player(side)
        if side == Side.US:
            e_deck, s_deck = self.us_enabler_deck, self.us_squadron_deck
        else:
            e_deck, s_deck = self.prc_enabler_deck, self.prc_squadron_deck

        while len(p.enablers_in_hand) < posture.enabler_limit and e_deck:
            p.enablers_in_hand.append(e_deck.pop(0))
        while len(p.squadrons_in_hand) < posture.squadron_limit and s_deck:
            p.squadrons_in_hand.append(s_deck.pop(0))

        self.log(
            f"{side.value} draws: {len(p.enablers_in_hand)} enablers, {len(p.squadrons_in_hand)} squadrons."
        )

    def choose_posture(self, posture_index_1based: int) -> None:
        if self.phase != Phase.ATO_START:
            self.log("Not in ATO_START phase.")
            return

        idx = posture_index_1based - 1
        if idx < 0 or idx >= len(POSTURES):
            self.log("Invalid posture selection.")
            return

        side = self.gs.current_side
        posture = POSTURES[idx]
        p = self.gs.player(side)
        p.posture = posture.name
        self.log(f"{side.value} chooses posture: {posture.name}")

        self._draw_cards(side, posture)

        # Switch to other side posture selection
        self.gs.current_side = self._other(side)
        if self.gs.us.posture and self.gs.prc.posture:
            self.phase = Phase.INITIATIVE
            self.log("Both postures selected. Proceed to Initiative. (Key: I)")
        else:
            self.log(f"{self.gs.current_side.value}: choose posture next. (Keys: 1/2/3)")

    def resolve_initiative(self) -> None:
        if self.phase != Phase.INITIATIVE:
            self.log("Not in INITIATIVE phase.")
            return

        while True:
            us_roll = d4(self.rng)
            prc_roll = d4(self.rng)
            self.log(f"Initiative roll: US={us_roll}, PRC={prc_roll}")
            if us_roll != prc_roll:
                break
            self.log("Tie — rerolling initiative...")

        winner = Side.US if us_roll > prc_roll else Side.PRC
        loser = self._other(winner)

        self.gs.player(winner).intel = IntelState.ADVANTAGE
        self.gs.player(loser).intel = IntelState.NORMAL
        self.gs.current_side = winner
        self.phase = Phase.INTEL_ROLL
        self.log(f"{winner.value} wins initiative, takes first, and gains Intel Advantage.")
        self.log("Proceed to Intel Roll. (Key: R)")

    def intel_roll(self) -> None:
        if self.phase != Phase.INTEL_ROLL:
            self.log("Not in INTEL_ROLL phase.")
            return

        for side in (Side.US, Side.PRC):
            player = self.gs.player(side)
            if player.intel == IntelState.ADVANTAGE:
                rr = d4_advantage(self.rng)
                self.log(f"Intel ({side.value}, ADV): rolls={rr.rolls} chosen={rr.chosen}")
            else:
                r = d4(self.rng)
                self.log(f"Intel ({side.value}): {r}")

        self.phase = Phase.TURNS
        self._begin_turn(self.gs.current_side)
        self.log(
            "Turn phase begins. Keys: E=Enabler, S=Activate Squadron, M=MAS, P=Pass."
        )

    # ----------------- squadron activation (deploy tokens) -----------------
    def _next_instance_id(self, side: Side) -> str:
        existing = [tid for tid, inst in self.gs.tokens.items() if inst.side == side]
        n = len(existing) + 1
        return f"{side.value}_T{n:03d}"

    def _pick_token_type_for_deploy(self, side: Side, category: TokenCategory) -> Optional[TokenType]:
        candidates = [t for t in self.gs.token_types.values() if t.side == side and t.category == category]
        candidates.sort(key=lambda x: x.id)
        if candidates:
            return candidates[0]
        return None

    def _deploy_token(self, tt: TokenType, band: int) -> str:
        inst_id = self._next_instance_id(tt.side)
        self.gs.tokens[inst_id] = TokenInstance(
            instance_id=inst_id,
            type_id=tt.id,
            side=tt.side,
            band=band,
            at_base=False,
            face_up=False,
            winchester=False,
        )
        self.log(f"{tt.side.value} deploys token {inst_id} (face-down) to Band {band}.")
        return inst_id

    def activate_squadron(self) -> None:
        """Prototype squadron activation.

        Rules say: flip squadron face up and place all associated tokens face down into bands.
        We don't have the real squadron contents wired yet, so in prototype we deploy:
          - one 5G fighter (if available) else any OTHER
          - one UAS (if available)

        Deployment rules (prototype):
          - default band is 1
          - UAS may deploy to any band; we default to 3
        """
        if self.phase != Phase.TURNS:
            self.log("Not in TURNS phase.")
            return

        side = self.gs.current_side
        p = self.gs.player(side)
        if not p.squadrons_in_hand:
            self.log(f"{side.value} has no squadrons to activate.")
            return

        sq = p.squadrons_in_hand.pop(0)
        p.passed = False
        self.log(f"{side.value} activates squadron: {sq}")

        fighter = self._pick_token_type_for_deploy(side, TokenCategory.FIGHTER_5G)
        if fighter is None:
            fighter = self._pick_token_type_for_deploy(side, TokenCategory.OTHER)
        uas = self._pick_token_type_for_deploy(side, TokenCategory.UAS)

        if fighter:
            self._deploy_token(fighter, band=1)
        if uas:
            default_band = 3 if uas.can_deploy_any_band else 1
            self._deploy_token(uas, band=default_band)

        self._end_action_and_pass_turn()

    # ----------------- turn actions -----------------
    def play_enabler(self) -> None:
        if self.phase != Phase.TURNS:
            self.log("Not in TURNS phase.")
            return

        side = self.gs.current_side
        p = self.gs.player(side)
        if not p.enablers_in_hand:
            self.log(f"{side.value} has no enablers to play.")
            return

        card = p.enablers_in_hand.pop(0)
        p.passed = False
        self.log(f"{side.value} plays enabler: {card} (effects not implemented yet).")
        self._end_action_and_pass_turn()

    def pass_turn(self) -> None:
        if self.phase != Phase.TURNS:
            self.log("Not in TURNS phase.")
            return

        side = self.gs.current_side
        self.gs.player(side).passed = True
        self.log(f"{side.value} passes.")

        if self.gs.us.passed and self.gs.prc.passed:
            self.end_ato()
            return

        self._switch_turn()

    def _end_action_and_pass_turn(self) -> None:
        # action took place, so clear pass flag
        self.gs.player(self.gs.current_side).passed = False
        self._switch_turn()

    def _switch_turn(self) -> None:
        self.gs.current_side = self._other(self.gs.current_side)
        self._begin_turn(self.gs.current_side)
        self.mas_mode = MasMode.NONE
        self.pending_band = None
        self.selected_own_idx = 0
        self.selected_enemy_idx = 0
        self.log(f"It is now {self.gs.current_side.value}'s turn.")

    # ----------------- MAS: mode + selection -----------------
    def mas_enter_menu(self) -> None:
        if self.phase != Phase.TURNS:
            self.log("Not in TURNS phase.")
            return
        self.mas_mode = MasMode.MENU
        self.log("MAS Menu: 1=Move, 2=Acquire, 3=Shoot, ESC=Exit MAS")

    def mas_exit(self) -> None:
        if self.mas_mode != MasMode.NONE:
            self.mas_mode = MasMode.NONE
            self.pending_band = None
            self.log("Exited MAS.")

    def mas_choose(self, n: int) -> None:
        if self.mas_mode != MasMode.MENU:
            return
        if n == 1:
            self.mas_mode = MasMode.MOVE
            self.pending_band = None
            self.log("MOVE: Use [ ] to select own token, A/D to change destination band, ENTER to confirm.")
        elif n == 2:
            self.mas_mode = MasMode.ACQUIRE
            self.log("ACQUIRE: Use [ ] to select sensor, , . to select target, ENTER to roll acquire.")
        elif n == 3:
            self.mas_mode = MasMode.SHOOT
            self.log("SHOOT: Use [ ] to select shooter, , . to select target, ENTER to roll attack.")

    def select_prev_own(self) -> None:
        ids = self._own_tokens_on_board(self.gs.current_side)
        if not ids:
            return
        self.selected_own_idx = (self.selected_own_idx - 1) % len(ids)

    def select_next_own(self) -> None:
        ids = self._own_tokens_on_board(self.gs.current_side)
        if not ids:
            return
        self.selected_own_idx = (self.selected_own_idx + 1) % len(ids)

    def select_prev_enemy(self) -> None:
        ids = self._enemy_tokens_on_board(self.gs.current_side)
        if not ids:
            return
        self.selected_enemy_idx = (self.selected_enemy_idx - 1) % len(ids)

    def select_next_enemy(self) -> None:
        ids = self._enemy_tokens_on_board(self.gs.current_side)
        if not ids:
            return
        self.selected_enemy_idx = (self.selected_enemy_idx + 1) % len(ids)

    def get_selected_ids(self) -> tuple[Optional[str], Optional[str]]:
        own_ids = self._own_tokens_on_board(self.gs.current_side)
        enemy_ids = self._enemy_tokens_on_board(self.gs.current_side)
        own = own_ids[self.selected_own_idx] if own_ids else None
        enemy = enemy_ids[self.selected_enemy_idx] if enemy_ids else None
        return own, enemy

    # ----------------- MAS: Move -----------------
    def move_adjust_destination(self, delta: int) -> None:
        if self.mas_mode != MasMode.MOVE:
            return
        own, _ = self.get_selected_ids()
        if not own:
            self.log("MOVE: You have no tokens on the board.")
            return
        inst = self.gs.tokens[own]
        if inst.band is None:
            self.log("MOVE: Selected token is not on the board.")
            return
        dest = inst.band if self.pending_band is None else self.pending_band
        dest = max(1, min(5, dest + delta))
        self.pending_band = dest

    def move_confirm(self) -> None:
        if self.mas_mode != MasMode.MOVE:
            return
        own, _ = self.get_selected_ids()
        if not own:
            self.log("MOVE: You have no tokens on the board.")
            return

        inst = self.gs.tokens[own]
        tt = self._get_type(own)
        if inst.band is None:
            self.log("MOVE: Selected token is not on the board.")
            return

        dest = self.pending_band if self.pending_band is not None else inst.band
        dist = abs(dest - inst.band)
        if dist > tt.move:
            self.log(f"MOVE failed: {own} move={tt.move}, requested distance={dist}.")
            return

        inst.band = dest
        self.log(f"MOVE: {own} -> Band {dest}.")
        self._end_action_and_pass_turn()

    # ----------------- MAS: Acquire -----------------
    def acquire_attempt(self) -> None:
        if self.mas_mode != MasMode.ACQUIRE:
            return
        own, enemy = self.get_selected_ids()
        if not own or not enemy:
            self.log("ACQUIRE: Need at least one own token and one enemy token on board.")
            return

        sensor_inst = self.gs.tokens[own]
        target_inst = self.gs.tokens[enemy]
        sensor_tt = self._get_type(own)
        target_tt = self._get_type(enemy)

        if sensor_inst.band is None or target_inst.band is None:
            self.log("ACQUIRE: Tokens must be on the board.")
            return

        band_dist = abs(sensor_inst.band - target_inst.band)
        if band_dist > sensor_tt.sensor:
            self.log(
                f"ACQUIRE failed: target out of sensor range (dist={band_dist}, sensor={sensor_tt.sensor})."
            )
            return

        roll = d4(self.rng)
        total = roll + sensor_tt.acquisition_bonus
        needed = target_tt.acquisition_target()

        if total >= needed:
            target_inst.face_up = True
            self.log(
                f"ACQUIRE success: rolled {roll} + bonus {sensor_tt.acquisition_bonus} = {total} >= {needed}. {enemy} is revealed."
            )
        else:
            self.log(
                f"ACQUIRE fail: rolled {roll} + bonus {sensor_tt.acquisition_bonus} = {total} < {needed}."
            )

        self._end_action_and_pass_turn()

    # ----------------- MAS: Shoot -----------------
    def shoot_attempt(self) -> None:
        if self.mas_mode != MasMode.SHOOT:
            return
        own, enemy = self.get_selected_ids()
        if not own or not enemy:
            self.log("SHOOT: Need at least one own token and one enemy token on board.")
            return

        shooter_inst = self.gs.tokens[own]
        target_inst = self.gs.tokens[enemy]
        shooter_tt = self._get_type(own)
        target_tt = self._get_type(enemy)

        if shooter_inst.band is None or target_inst.band is None:
            self.log("SHOOT: Tokens must be on the board.")
            return

        # Rules: a token must be acquired before it can be shot.
        if not target_inst.face_up:
            self.log("SHOOT blocked: target is not acquired / not face-up yet.")
            return

        # Decide which weapon we are using.
        # Prototype: use missile vs non-IAMD, bomb vs IAMD.
        weapon = None
        weapon_name = ""
        if target_tt.category == TokenCategory.IAMD:
            weapon = shooter_tt.bomb
            weapon_name = "BOMB"
        else:
            weapon = shooter_tt.missile
            weapon_name = "MISSILE"

        if weapon is None:
            self.log(f"SHOOT failed: shooter has no {weapon_name} weapon.")
            return

        band_dist = abs(shooter_inst.band - target_inst.band)
        if band_dist > weapon.range:
            self.log(
                f"SHOOT failed: target out of range (dist={band_dist}, {weapon_name}_range={weapon.range})."
            )
            return

        roll = d4(self.rng)
        if roll >= weapon.hit:
            # destroy target
            del self.gs.tokens[enemy]
            self.log(f"SHOOT hit! {own} rolled {roll} (needed {weapon.hit}). {enemy} destroyed.")
        else:
            self.log(f"SHOOT miss: {own} rolled {roll} (needed {weapon.hit}).")

        # Winchester rule: after shooting, shooter gets Winchester unless roll==4 (first-shot kill).
        if not shooter_tt.uas_infinite_ammo:
            if roll == 4:
                self.log("First-shot kill (roll=4): no Winchester marker.")
            else:
                shooter_inst.winchester = True
                self.log(f"{own} gains Winchester marker.")

        self._end_action_and_pass_turn()

    # ----------------- ATO end / cleanup -----------------
    def end_ato(self) -> None:
        self.phase = Phase.ATO_END
        self.log("Both players passed. ATO ends. Cleaning up board (prototype clears deployed tokens).")

        # Prototype cleanup: remove all tokens on the board.
        self.gs.tokens.clear()

        self.gs.us.passed = False
        self.gs.prc.passed = False
        self.gs.us.posture = None
        self.gs.prc.posture = None

        self.gs.ato_number += 1
        self.phase = Phase.ATO_START
        self.gs.current_side = Side.US
        self.log(f"ATO {self.gs.ato_number} begins: select postures. (Keys: 1/2/3)")
