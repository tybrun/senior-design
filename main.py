#!/usr/bin/env python3
"""
Air Force Wargame: Indo-Pacific — Digital Edition
Board-based rendering: board.jpg is displayed directly, tokens overlaid at correct positions.
Cards (enabler/mission/posture) shown in side panel only. Squadron cards in airbase area.
"""
import pygame, sys, os, random, math, re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from game_data import (
    Side, TokenCat, EnablerUse, Phase, T, BOARD_BANDS, ALL_LOCATIONS, BAND_POS,
    band_dist, SquadronDef, EnablerDef, MissionDef, PostureDef, CampaignDef,
    US_SQN, PRC_SQN, US_ENB, PRC_ENB, MISSIONS, US_POS, PRC_POS, CAMPAIGNS,
    CYBER_ACCESS, TokenDef,
)

# ══════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════
WIDTH, HEIGHT = 1280, 800
FPS = 30
ROOT = os.path.dirname(os.path.abspath(__file__))

# Colors
WHITE=(255,255,255); BLACK=(0,0,0); GRAY=(160,160,160); DKGRAY=(80,80,80)
LTGRAY=(210,210,210); RED=(200,50,50); BLUE=(50,80,180); GREEN=(50,170,80)
YELLOW=(240,210,50); CYAN=(60,200,220); NAVY=(20,40,100); ORANGE=(220,150,40)
US_CLR=(40,70,160); PRC_CLR=(180,30,30)
PANEL=(30,35,50); PANEL2=(45,52,72); GOLD=(255,215,0)

# Board display — the board.jpg is 896x1344, we scale to fit
BOARD_ORIG_W, BOARD_ORIG_H = 896, 1344
BOARD_DISP_H = 785
BOARD_SCALE = BOARD_DISP_H / BOARD_ORIG_H
BOARD_DISP_W = int(BOARD_ORIG_W * BOARD_SCALE)
BOARD_X, BOARD_Y = 5, 8

# Side panel starts after the board
SIDE_X = BOARD_X + BOARD_DISP_W + 10
SIDE_W = WIDTH - SIDE_X - 5

# ──────────────────────────────────────────────────────────────────
# BOARD REGION MAPPING (proportional coordinates on the board image)
# These define where each game zone is on the actual board.jpg
# Format: (x_frac, y_frac, w_frac, h_frac) as fractions of board size
# ──────────────────────────────────────────────────────────────────
_REGIONS = {
    # PRC zones (top of board, labels are upside-down)
    "prc_airbase":  (0.05, 0.09, 0.6, 0.1),
    "prc_standoff": (0.76, 0.09, 0.2, 0.1),
    # 5 Range bands (ocean area). PRC band 1 at top, US band 1 at bottom.
    "band5": (0.1, 0.23, 0.8, 0.08),   # top band (PRC side)
    "band4": (0.1, 0.35, 0.8, 0.08),
    "band3": (0.1, 0.46, 0.8, 0.08),
    "band2": (0.1, 0.58, 0.8, 0.08),
    "band1": (0.1, 0.695, 0.8, 0.08),   # bottom band (US side)
    # US zones (bottom of board)
    "us_standoff":    (0.08, 0.81, 0.15, 0.1),
    "us_airbase":     (0.225, 0.81, 0.6, 0.1),
    "us_contingency": (0.76, 0.81, 0.2, 0.1),
}

def _board_rect(region_key):
    """Convert a proportional region to a pixel Rect on the displayed board."""
    xf, yf, wf, hf = _REGIONS[region_key]
    return pygame.Rect(
        BOARD_X + int(xf * BOARD_DISP_W),
        BOARD_Y + int(yf * BOARD_DISP_H),
        int(wf * BOARD_DISP_W),
        int(hf * BOARD_DISP_H),
    )

# ══════════════════════════════════════════════════════════════════
#  ASSET LOADER — tries many path variants to find files
# ══════════════════════════════════════════════════════════════════
_img_cache = {}
_path_cache = {}

def _resolve_path(filename, side, asset_type="tokens"):
    """Find the actual path for an asset file. Tries many naming variants."""
    cache_key = (filename, side.value if side else "", asset_type)
    if cache_key in _path_cache:
        return _path_cache[cache_key]

    side_dir = side.value.lower() if side else ""

    # Generate name variants: f16c_back.png -> f-16c_back.png, etc.
    base, ext = os.path.splitext(filename)
    variants = [filename]
    dashed = re.sub(r'^([a-zA-Z]+)(\d)', r'\1-\2', base) + ext
    if dashed != filename:
        variants.append(dashed)
    # Try replacing all underscores with dashes and vice versa
    variants.append(base.replace("_", "-") + ext)
    variants.append(base.replace("-", "_") + ext)
    # backf-35a -> backf-35a, f-35a -> f-35a
    dashed2 = re.sub(r'([a-z])(\d)', r'\1-\2', base, count=1) + ext
    if dashed2 not in variants:
        variants.append(dashed2)

    # Search directories in order of priority
    search_dirs = []
    if side_dir:
        search_dirs.append(os.path.join(ROOT, "assets", asset_type, side_dir))
    search_dirs.append(os.path.join(ROOT, "assets", asset_type))
    search_dirs.append(os.path.join(ROOT, "assets"))
    search_dirs.append(ROOT)

    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for v in variants:
            p = os.path.join(d, v)
            if os.path.isfile(p):
                _path_cache[cache_key] = p
                return p
        # Last resort: scan the directory for a fuzzy match
        try:
            files_in_dir = os.listdir(d)
            base_clean = base.replace("-","").replace("_","").lower()
            for f in files_in_dir:
                f_clean = os.path.splitext(f)[0].replace("-","").replace("_","").lower()
                if f_clean == base_clean and f.lower().endswith(ext.lower()):
                    p = os.path.join(d, f)
                    _path_cache[cache_key] = p
                    return p
        except OSError:
            pass

    # Absolute fallback
    fallback = os.path.join(ROOT, "assets", asset_type, side_dir, filename) if side_dir else os.path.join(ROOT, filename)
    _path_cache[cache_key] = fallback
    return fallback

def load_img(path_or_name, size=None, side=None, asset_type="tokens"):
    """Load an image with caching. If side is provided, resolves through asset dirs."""
    if side is not None:
        path = _resolve_path(path_or_name, side, asset_type)
    elif os.path.isabs(path_or_name):
        path = path_or_name
    else:
        path = os.path.join(ROOT, path_or_name)

    k = (path, size)
    if k not in _img_cache:
        try:
            img = pygame.image.load(path).convert_alpha()
        except Exception:
            img = pygame.Surface(size or (64,64), pygame.SRCALPHA)
            img.fill((180,80,180,200))
            f = pygame.font.SysFont("arial",10)
            name = os.path.basename(path)
            img.blit(f.render(name[:15],True,WHITE),(2,2))
        if size:
            img = pygame.transform.smoothscale(img, size)
        _img_cache[k] = img
    return _img_cache[k]

# ══════════════════════════════════════════════════════════════════
#  LIVE GAME OBJECTS
# ══════════════════════════════════════════════════════════════════
_next_id = 0
def _nid():
    global _next_id; _next_id += 1; return _next_id

@dataclass
class LiveToken:
    tid: int; tdef: TokenDef; side: Side; band: str
    face_up: bool = False; winchester: bool = False
    destroyed: bool = False; sqn_cid: str = ""
    salvo_used: int = 0
    _rect: pygame.Rect = field(default_factory=lambda: pygame.Rect(0,0,0,0), repr=False)

@dataclass
class LiveSquadron:
    sdef: SquadronDef; location: str
    activated: bool = False; damage: int = 0; destroyed: bool = False

# ══════════════════════════════════════════════════════════════════
#  GAME STATE
# ══════════════════════════════════════════════════════════════════
class GS:
    def __init__(self):
        self.phase = Phase.MAIN_MENU
        self.campaign: Optional[CampaignDef] = None
        self.ato_num = 0; self.max_ato = 1  # current ATO and total ATOs for this campaign
        self.us_mission: Optional[MissionDef] = None
        self.prc_mission: Optional[MissionDef] = None
        self.us_posture: Optional[PostureDef] = None
        self.prc_posture: Optional[PostureDef] = None
        # Card hands: squadrons and enablers each player holds this ATO
        self.us_sqn_hand: List[SquadronDef] = []
        self.prc_sqn_hand: List[SquadronDef] = []
        self.us_enb_hand: List[EnablerDef] = []
        self.prc_enb_hand: List[EnablerDef] = []
        # Played enablers: single-turn effects vs. enduring (persist all ATO)
        self.us_enb_played: List[EnablerDef] = []
        self.prc_enb_played: List[EnablerDef] = []
        self.us_enb_enduring: List[EnablerDef] = []
        self.prc_enb_enduring: List[EnablerDef] = []
        self.tokens: List[LiveToken] = []  # all tokens currently on the board
        self.us_sqns: List[LiveSquadron] = []
        self.prc_sqns: List[LiveSquadron] = []
        self.us_cyber = 1; self.prc_cyber = 1  # cyber track position (1–4)
        self.us_intel_adv = False; self.prc_intel_adv = False  # initiative bonus flag
        self.initiative_winner: Optional[Side] = None
        self.active_side: Side = Side.US
        # Per-turn action flags reset each turn
        self.turn_moved = False; self.turn_acquired = False
        self.turn_shot = False; self.turn_activated = False
        self.turn_played_enb = False
        self.turn_did_action = False  # True after activate OR any MAS action
        self.us_vp = 0; self.prc_vp = 0
        self.consecutive_passes = 0  # 4 consecutive passes ends the ATO
        self.us_destroyed: List[LiveToken] = []   # enemy tokens destroyed BY US
        self.prc_destroyed: List[LiveToken] = []
        self.msgs: List[Tuple[str,Tuple]] = []  # game log entries (text, color)
        self.sel_tok: Optional[LiveToken] = None  # token selected for current action
        self.sub: str = ""  # active sub-action: "move", "acquire", or "shoot"
        self.side_sel: Side = Side.US
        self.show_screen: str = ""
        self.handoff = False; self.handoff_side: Optional[Side] = None; self.handoff_msg = ""
        self.hover_tok: Optional[LiveToken] = None
        self.scroll = 0
        self.tutorial_step = 0; self.is_tutorial = False
        self._place_idx = None

    def log(self, text, color=WHITE):
        self.msgs.append((text, color))
        if len(self.msgs) > 200: self.msgs.pop(0)  # keep log from growing unbounded

    def reset_turn(self):
        self.turn_moved=False; self.turn_acquired=False; self.turn_shot=False
        self.turn_activated=False; self.turn_played_enb=False; self.turn_did_action=False
        self.sel_tok=None; self.sub=""

    def toks_at(self, band, side=None):
        return [t for t in self.tokens if t.band==band and not t.destroyed
                and (side is None or t.side==side)]

# ══════════════════════════════════════════════════════════════════
#  DRAWING HELPERS
# ══════════════════════════════════════════════════════════════════
def txt(s, text, pos, color=WHITE, size=20, bold=False, center=False):
    f = pygame.font.SysFont("arial", size, bold=bold)
    r = f.render(str(text), True, color)
    p = (pos[0]-r.get_width()//2, pos[1]-r.get_height()//2) if center else pos  # center adjusts origin to middle
    s.blit(r, p)
    return r.get_rect(topleft=p)

def draw_panel(s, rect, color=PANEL, border=DKGRAY, rad=6):
    pygame.draw.rect(s, color, rect, border_radius=rad)
    pygame.draw.rect(s, border, rect, 1, border_radius=rad)

# ══════════════════════════════════════════════════════════════════
#  BUTTON
# ══════════════════════════════════════════════════════════════════
class Btn:
    def __init__(self, rect, label, color=BLUE, tag=None, enabled=True, fsize=18):
        self.rect = pygame.Rect(rect)
        self.label = label; self.color = color; self.tag = tag
        self.enabled = enabled; self.hovered = False; self.fsize = fsize
    def draw(self, s):
        # Brighten color on hover; gray out if disabled
        c = tuple(min(x+35,255) for x in self.color) if self.hovered and self.enabled else self.color
        if not self.enabled: c = GRAY
        pygame.draw.rect(s, c, self.rect, border_radius=6)
        pygame.draw.rect(s, WHITE, self.rect, 2, border_radius=6)  # white border outline
        txt(s, self.label, (self.rect.centerx, self.rect.centery),
            WHITE if self.enabled else DKGRAY, self.fsize, True, True)
    def update(self, ev):
        if ev.type == pygame.MOUSEMOTION: self.hovered = self.rect.collidepoint(ev.pos)
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos) and self.enabled: return True  # clicked
        return False

# ══════════════════════════════════════════════════════════════════
#  GAME LOGIC
# ══════════════════════════════════════════════════════════════════
def roll_d4(adv=False, disadv=False, bonus=0):
    r1, r2 = random.randint(1,4), random.randint(1,4)
    if adv: return max(r1,r2)+bonus     # advantage: keep the higher roll
    if disadv: return min(r1,r2)+bonus  # disadvantage: keep the lower roll
    return r1+bonus

def gen_tokens(gs, sqn, side):
    td = T.get(sqn.sdef.tok_key)  # look up token definition by key
    if not td: return
    count = sqn.sdef.tok_count
    is_cont = sqn.location == "us_contingency"
    if is_cont:
        # ACE posture or an enduring enabler skips the contingency roll
        auto = (gs.us_posture and gs.us_posture.name=="ACE") or \
               any(e.effect=="contingency_auto" for e in gs.us_enb_enduring)
        if not auto:
            r = roll_d4()
            count = min(count, r)  # roll caps how many tokens actually deploy
            gs.log(f"  Contingency roll: {r} → {count} tokens", CYAN)
    dep = sqn.sdef.deploy
    # Map deploy type to the correct board location for each side
    if dep == "band1":   band = "band1" if side==Side.US else "band5"
    elif dep == "standoff": band = "us_standoff" if side==Side.US else "prc_standoff"
    elif dep == "airbase":  band = "us_airbase" if side==Side.US else "prc_airbase"
    else: band = "band1" if side==Side.US else "band5"
    for _ in range(count):
        gs.tokens.append(LiveToken(tid=_nid(), tdef=td, side=side, band=band, sqn_cid=sqn.sdef.cid))
    gs.log(f"  Deployed {count}x {td.name} → {band}", GREEN if side==Side.US else RED)

def try_move(gs, tok, dest):
    # Validate: one move per turn, must own the token, can't be out of ammo
    if gs.turn_moved: gs.log("Already moved.", ORANGE); return False
    if tok.side != gs.active_side: gs.log("Not your token!", RED); return False
    if tok.winchester: gs.log("Winchester — must RTB.", ORANGE); return False
    if tok.tdef.move == 0: gs.log(f"{tok.tdef.name} cannot move.", ORANGE); return False
    d = band_dist(tok.band, dest)
    mx = tok.tdef.move
    # Certain enabler cards grant +1 extra move this turn
    if any(e.effect=="extra_move" for e in (gs.us_enb_played if tok.side==Side.US else gs.prc_enb_played)):
        mx += 1
    if d > mx: gs.log(f"Too far ({d} > {mx}).", ORANGE); return False
    old = tok.band; tok.band = dest; gs.turn_moved = True
    gs.log(f"Moved {tok.tdef.name}: {old} → {dest}", GREEN if tok.side==Side.US else RED)
    return True

def try_acquire(gs, acq, tgt):
    # Standard validation: one acquire per turn, must target an enemy face-down token
    if gs.turn_acquired: gs.log("Already acquired.", ORANGE); return False
    if acq.side != gs.active_side: gs.log("Not yours!", RED); return False
    if tgt.side == gs.active_side: gs.log("Can't acquire friendly!", RED); return False
    if tgt.face_up: gs.log("Already acquired!", ORANGE); return False
    d = band_dist(acq.band, tgt.band)
    if d > acq.tdef.acq_range: gs.log(f"Out of range ({d}>{acq.tdef.acq_range}).", ORANGE); return False
    needed = tgt.tdef.acq_diff  # difficulty number printed on the target token
    bonus = acq.tdef.acq_bonus  # acquirer's inherent bonus (e.g. AEW gives +2)
    # Enduring enabler can grant a global +1 acquisition bonus
    if acq.side==Side.PRC and any(e.effect=="acq_bonus_all" for e in gs.prc_enb_enduring): bonus+=1
    disadv = any(e.effect=="disadv_acquire_all" for e in
                 (gs.prc_enb_enduring if acq.side==Side.US else gs.us_enb_enduring))
    r = roll_d4(disadvantage=disadv, bonus=bonus)
    gs.log(f"Acquire: {acq.tdef.name}→{tgt.tdef.name} need {needed}, rolled {r}", CYAN)
    gs.turn_acquired = True
    if r >= needed:
        tgt.face_up = True  # flip the token to reveal its identity
        gs.log(f"  >> Revealed: {tgt.tdef.name}", GREEN)
        return True
    gs.log(f"  >> Failed.", RED); return False

def try_shoot(gs, shooter, tgt):
    # Standard validation: one shot per turn, must target an enemy
    if gs.turn_shot: gs.log("Already shot.", ORANGE); return False
    if shooter.side != gs.active_side: gs.log("Not yours!", RED); return False
    if tgt.side == gs.active_side: gs.log("Can't shoot friendly!", RED); return False
    if not tgt.face_up:
        # Tokens at airbases can be shot without acquiring first
        if not (tgt.band in ("us_airbase","us_contingency","prc_airbase")):
            gs.log("Must acquire first!", ORANGE); return False
    d = band_dist(shooter.band, tgt.band)
    # Determine if target is a surface unit (uses different stats than air-to-air)
    is_sfc = tgt.band in ("us_airbase","us_standoff","us_contingency","prc_airbase","prc_standoff") or \
             tgt.tdef.cat in (TokenCat.ADA_MID,TokenCat.ADA_LONG,TokenCat.MISSILE_DEF,TokenCat.SHIP_DDG,TokenCat.SHIP_CG)
    # Select range, hit number, and exploding flag based on target type
    ar = shooter.tdef.sfc_range if is_sfc else shooter.tdef.air_range
    roll_need = shooter.tdef.sfc_roll if is_sfc else shooter.tdef.air_roll
    exploding = shooter.tdef.sfc_exploding if is_sfc else shooter.tdef.air_exploding
    if ar==0: gs.log(f"No {'surface' if is_sfc else 'air'} attack.", ORANGE); return False
    if d > ar: gs.log(f"Out of range ({d}>{ar}).", ORANGE); return False
    disadv = any(e.effect=="disadvantage_shot" for e in
                 (gs.prc_enb_played if shooter.side==Side.US else gs.us_enb_played))
    r = roll_d4(disadvantage=disadv)
    gs.log(f"Shot: {shooter.tdef.name}→{tgt.tdef.name} need {roll_need}+, rolled {r}", CYAN)
    # Winchester: unit runs out of ammo (normal fighters on non-4 roll, UAS on 1-2)
    w = shooter.tdef.winchester
    if w=="normal" and r<4: shooter.winchester=True; gs.log(f"  {shooter.tdef.name} WINCHESTER", ORANGE)
    elif w=="uas" and r<=2: shooter.winchester=True; gs.log(f"  {shooter.tdef.name} WINCHESTER", ORANGE)
    gs.turn_shot = True
    if r >= roll_need:
        gs.log(f"  >> HIT!", GREEN)
        dmg = 1
        # Exploding weapons (bombers) roll again for bonus damage
        if exploding:
            dmg = roll_d4(disadvantage=disadv)
            gs.log(f"  Exploding → {dmg} damage!", GOLD)
        tgt.destroyed = True
        (gs.us_destroyed if shooter.side==Side.US else gs.prc_destroyed).append(tgt)
        gs.log(f"  {tgt.tdef.name} DESTROYED!", RED)
    else:
        gs.log(f"  >> Miss.", RED)
    return True

def winchester_rtb(gs, side):
    base = "us_airbase" if side==Side.US else "prc_airbase"
    # Move any out-of-ammo tokens from the board back to their home airbase
    for t in gs.tokens:
        if t.side==side and t.winchester and not t.destroyed and t.band in BOARD_BANDS:
            t.band = base
            gs.log(f"  {t.tdef.name} RTB (Winchester)", ORANGE)

def score_attrition(gs, side):
    destroyed = gs.us_destroyed if side==Side.US else gs.prc_destroyed
    vp = 0
    for t in destroyed:
        c = t.tdef.cat
        # High-value targets worth 3 VP; all other tokens worth 1 VP
        if c in (TokenCat.SHIP_DDG,TokenCat.SHIP_CG,TokenCat.BOMBER,TokenCat.ADA_MID,
                 TokenCat.ADA_LONG,TokenCat.AEW,TokenCat.MISSILE_DEF): vp+=3
        else: vp+=1
    return vp

def score_interdiction(gs, side):
    destroyed = gs.us_destroyed if side==Side.US else gs.prc_destroyed
    vp = 0
    for t in destroyed:
        c = t.tdef.cat
        # Interdiction rewards destroying strike/command assets more than fighters
        if c in (TokenCat.BOMBER,TokenCat.AEW): vp+=4
        elif c in (TokenCat.SHIP_DDG,TokenCat.SHIP_CG,TokenCat.ADA_MID,TokenCat.ADA_LONG): vp+=3
        else: vp+=2
    return vp

# ══════════════════════════════════════════════════════════════════
#  TUTORIAL STEPS
# ══════════════════════════════════════════════════════════════════
TUTS = [
    ("Welcome to AFWI!", "Air Force Wargame: Indo-Pacific is a tactical wargame where the US and PRC clash in the Indo-Pacific theater.\n\nThis tutorial walks you through Campaign 1: Meeting Engagement.\nClick NEXT to continue."),
    ("The Board", "The board has 5 range bands between the US and PRC bases.\nEach side has an Airbase, a Standoff box, and the US has a Contingency Location.\nThe Cyber Track and Intel Track are shown on the board edges."),
    ("Tokens & Cards", "Tokens represent units (fighters, bombers, ships, ADA). They deploy face-down and must be acquired (flipped) before they can be shot.\n\nSquadron Cards deploy tokens. Enabler Cards provide multi-domain effects.\nMission Cards determine how you score Victory Points."),
    ("ATO Cycle", "Each ATO Cycle:\n1. Select Posture (determines card limits)\n2. Draw Squadron & Enabler cards\n3. Bid for Initiative (d4 roll)\n4. Take turns: Activate squadrons, play enablers, Move-Acquire-Shoot\n5. Both players pass → score VP, clean up"),
    ("Move-Acquire-Shoot", "Each turn you may do M-A-S:\n- MOVE: Move 1 token up to its Move Range in bands\n- ACQUIRE: Roll d4 to flip 1 enemy token (≥ difficulty)\n- SHOOT: Roll d4 to attack 1 acquired enemy (≥ hit number)\n\nActions can use different tokens. You may also pass."),
    ("Winchester & Scoring", "After shooting, roll < 4 → Winchester (out of ammo, must RTB).\nADA tokens never go Winchester.\n\nFor Attrition mission:\n+3 VP per Ship/Bomber/ADA/AEW destroyed\n+2 VP per Squadron Card destroyed\n+1 VP per other token destroyed"),
    ("Ready to Play!", "Click PLAY to start a Meeting Engagement practice game.\n\nTips:\n• Stealth tokens (F-22, J-20B) need a 4 to acquire\n• AEW tokens give +2 acquisition bonus\n• Bombers can shoot from Standoff (range 6, exploding die)"),
]

# ══════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════
class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("AFWI: Indo-Pacific")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.gs = GS()
        self.btns: List[Btn] = []
        self.board_img = None
        self.running = True

    def run(self):
        # Main game loop: process events, then redraw every frame
        while self.running:
            self.clock.tick(FPS)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: self.running = False
                self.handle(ev)
            self.draw()
        pygame.quit(); sys.exit()

    # ── Event handling ──
    def handle(self, ev):
        gs = self.gs
        # Handoff screen blocks all input until the next player clicks through
        if gs.handoff:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                gs.handoff = False
            return
        for b in self.btns:
            if b.update(ev): self.on_btn(b)
        if ev.type == pygame.MOUSEMOTION and gs.phase == Phase.PLAYER_TURN:
            gs.hover_tok = self._tok_at(ev.pos)
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.on_click(ev.pos)
        if ev.type == pygame.MOUSEWHEEL:
            gs.scroll = max(0, gs.scroll - ev.y * 30)

    def on_click(self, pos):
        gs = self.gs
        if gs.phase != Phase.PLAYER_TURN or not gs.sub: return
        tok = self._tok_at(pos)
        band = self._band_at(pos)

        if gs.sub == "move":
            if tok and not gs.sel_tok and tok.side == gs.active_side:
                gs.sel_tok = tok; gs.log(f"Selected {tok.tdef.name}. Click destination band.", CYAN)
            elif gs.sel_tok and band:
                if try_move(gs, gs.sel_tok, band): gs.sel_tok=None; gs.sub=""
            elif gs.sel_tok and not band:
                gs.log("Click on a band to move there.", GRAY)

        elif gs.sub == "acquire":
            if not gs.sel_tok:
                # First click: select your own token as acquirer
                if tok and tok.side == gs.active_side:
                    gs.sel_tok = tok; gs.log(f"Acquirer: {tok.tdef.name}. Now click an enemy token.", CYAN)
                elif tok and tok.side != gs.active_side:
                    gs.log("Select YOUR token first (the acquirer), then click the enemy.", ORANGE)
                else:
                    gs.log("Click one of your tokens to use as acquirer.", GRAY)
            else:
                # Second click: select enemy token to acquire
                if tok and tok.side != gs.active_side:
                    try_acquire(gs, gs.sel_tok, tok); gs.sel_tok=None; gs.sub=""
                elif tok and tok.side == gs.active_side:
                    gs.sel_tok = tok; gs.log(f"Changed acquirer to {tok.tdef.name}. Now click enemy.", CYAN)
                else:
                    gs.log("Click on an enemy token to acquire it.", GRAY)

        elif gs.sub == "shoot":
            if not gs.sel_tok:
                if tok and tok.side == gs.active_side:
                    gs.sel_tok = tok; gs.log(f"Shooter: {tok.tdef.name}. Now click an enemy target.", CYAN)
                elif tok and tok.side != gs.active_side:
                    gs.log("Select YOUR token first (the shooter), then click the enemy.", ORANGE)
                else:
                    gs.log("Click one of your tokens to use as shooter.", GRAY)
            else:
                if tok and tok.side != gs.active_side:
                    try_shoot(gs, gs.sel_tok, tok); gs.sel_tok=None; gs.sub=""
                elif tok and tok.side == gs.active_side:
                    gs.sel_tok = tok; gs.log(f"Changed shooter to {tok.tdef.name}. Now click enemy.", CYAN)
                else:
                    gs.log("Click on an enemy token to shoot at.", GRAY)

    def _tok_at(self, pos):
        # Iterate in reverse so topmost (last-drawn) token is picked first
        for t in reversed(self.gs.tokens):
            if not t.destroyed and t._rect.inflate(6, 6).collidepoint(pos): return t
        return None

    def _band_at(self, pos):
        # Return whichever board region the click landed in
        for loc in ALL_LOCATIONS:
            if loc in _REGIONS and _board_rect(loc).collidepoint(pos): return loc
        return None

    # ── Button dispatch ──
    def on_btn(self, b):
        tag = b.tag; gs = self.gs
        if not tag: return
        if tag == "pvp":
            # Default game: 1 ATO, all missions, all postures, no restrictions
            gs.campaign = CampaignDef("Standard Game","1 ATO, standard rules.",1,["all"],["all"],"","","")
            gs.max_ato = 1; gs.ato_num = 1
            gs.phase = Phase.MISSION_SELECT; gs.side_sel = Side.US
            gs.log("Standard Game: 1 ATO Cycle, all missions & postures available.", CYAN)
        elif tag == "tutorial": gs.phase = Phase.TUTORIAL; gs.tutorial_step = 0
        elif tag == "quit": self.running = False
        elif tag == "main_menu": self.gs = GS()
        elif tag.startswith("miss_"):
            i = int(tag[5:]); avail = self._avail_missions(gs.side_sel); m = avail[i]
            if gs.side_sel == Side.US:
                gs.us_mission = m; gs.log(f"US Mission: {m.name}", US_CLR)
                gs.side_sel = Side.PRC; gs.handoff=True; gs.handoff_side=Side.PRC
                gs.handoff_msg = "Pass to PRC player.\nSelect your Mission Card."
            else:
                gs.prc_mission = m; gs.log(f"PRC Mission: {m.name}", PRC_CLR)
                gs.phase = Phase.ATO_POSTURE; gs.side_sel = Side.US; gs.ato_num = 1
        elif tag.startswith("post_"):
            i = int(tag[5:]); ps = self._avail_postures(gs.side_sel); p = ps[i]
            if gs.side_sel == Side.US:
                gs.us_posture = p; gs.log(f"US Posture: {p.name}", US_CLR)
                gs.side_sel = Side.PRC; gs.handoff=True; gs.handoff_side=Side.PRC
                gs.handoff_msg = f"US chose {p.name}.\nPRC: Select posture."
            else:
                gs.prc_posture = p; gs.log(f"PRC Posture: {p.name}", PRC_CLR)
                self._start_draw()
        elif tag.startswith("spick_"):
            self._pick_sqn(int(tag[6:]))
        elif tag == "sdone": self._done_sqn()
        elif tag.startswith("epick_"):
            self._pick_enb(int(tag[6:]))
        elif tag == "edone": self._done_enb()
        elif tag == "pdone": self._done_place()
        elif tag == "roll_init": self._roll_init()
        elif tag == "roll_intel": self._roll_intel()
        elif tag == "pass": self._do_pass()
        elif tag == "end_turn": self._end_turn()
        elif tag == "move":
            if gs.turn_activated: gs.log("Cannot MAS — already activated a squadron.", ORANGE); return
            self._clear_my_pass(); gs.turn_did_action = True
            gs.sub="move"; gs.sel_tok=None; gs.log("MOVE: Select token, then band.", CYAN)
        elif tag == "acquire":
            if gs.turn_activated: gs.log("Cannot MAS — already activated a squadron.", ORANGE); return
            self._clear_my_pass(); gs.turn_did_action = True
            gs.sub="acquire"; gs.sel_tok=None; gs.log("ACQUIRE: Select your token, then enemy.", CYAN)
        elif tag == "shoot":
            if gs.turn_activated: gs.log("Cannot MAS — already activated a squadron.", ORANGE); return
            self._clear_my_pass(); gs.turn_did_action = True
            gs.sub="shoot"; gs.sel_tok=None; gs.log("SHOOT: Select your token, then target.", CYAN)
        elif tag == "cancel": gs.sub=""; gs.sel_tok=None; gs.log("Cancelled.", GRAY)
        elif tag.startswith("act_"):
            self._activate_sqn(int(tag[4:]))
        elif tag.startswith("penb_"):
            self._play_enb(int(tag[5:]))
        elif tag == "next_ato": self._next_ato()
        elif tag == "end_game": self._end_game()
        elif tag == "tut_next":
            gs.tutorial_step += 1
            if gs.tutorial_step >= len(TUTS): self._start_tut_game()
        elif tag == "tut_play": self._start_tut_game()

    # ── Phase logic ──
    def _avail_missions(self, side):
        ms = self.gs.campaign.missions
        return [m for m in MISSIONS if ("all" in ms or m.name in ms) and (m.sides=="BOTH" or m.sides==side.value)]

    def _avail_postures(self, side):
        ps = self.gs.campaign.postures
        pool = US_POS if side==Side.US else PRC_POS
        return pool if "all" in ps else [p for p in pool if p.name in ps]

    def _start_draw(self):
        gs = self.gs
        # Campaign can pre-assign squadrons (e.g. tutorial), bypassing the pick screen
        if gs.campaign and gs.campaign.us_forced and gs.campaign.us_forced != "":
            for s in US_SQN:
                if s.cid == gs.campaign.us_forced: gs.us_sqn_hand=[s]; break
            for s in PRC_SQN:
                if s.cid == gs.campaign.prc_forced: gs.prc_sqn_hand=[s]; break
            if "No enabler" in (gs.campaign.rules or ""):
                gs.us_enb_hand=[]; gs.prc_enb_hand=[]
                self._auto_place(); return
        gs.phase = Phase.DRAW_CARDS; gs.side_sel = Side.US; gs.show_screen = "sqn"; gs.scroll = 0
        gs.log(f"US: Pick squadron cards (limit {gs.us_posture.sqn_lim}).", US_CLR)

    def _pick_sqn(self, i):
        gs = self.gs; side = gs.side_sel
        pool = US_SQN if side==Side.US else PRC_SQN
        hand = gs.us_sqn_hand if side==Side.US else gs.prc_sqn_hand
        lim = (gs.us_posture if side==Side.US else gs.prc_posture).sqn_lim
        if i >= len(pool): return
        s = pool[i]
        # Toggle: clicking an already-picked card removes it; otherwise add up to limit
        if s in hand:
            hand.remove(s); gs.log(f"  Removed: {s.name}", ORANGE)
        elif len(hand) >= lim:
            gs.log(f"Limit reached ({lim}).", ORANGE)
        else:
            rules = gs.campaign.rules or ""
            if "No 5th gen" in rules and s.is_5th: gs.log("5th gen restricted.",RED); return
            if "No bombers" in rules and s.is_bomber: gs.log("Bombers restricted.",RED); return
            hand.append(s); gs.log(f"  Added: {s.name}", GREEN if side==Side.US else RED)

    def _done_sqn(self):
        gs = self.gs
        if gs.side_sel == Side.US:
            gs.side_sel = Side.PRC; gs.scroll = 0
            gs.handoff=True; gs.handoff_side=Side.PRC; gs.handoff_msg="PRC: Pick squadron cards."
        else:
            if "No enabler" in (gs.campaign.rules or ""):
                self._auto_place(); return
            gs.side_sel = Side.US; gs.show_screen = "enb"; gs.scroll = 0
            gs.handoff=True; gs.handoff_side=Side.US; gs.handoff_msg="US: Pick enabler cards."

    def _pick_enb(self, i):
        gs = self.gs; side = gs.side_sel
        pool = US_ENB if side==Side.US else PRC_ENB
        hand = gs.us_enb_hand if side==Side.US else gs.prc_enb_hand
        lim = (gs.us_posture if side==Side.US else gs.prc_posture).enb_lim
        if i >= len(pool): return
        e = pool[i]
        if e in hand:
            hand.remove(e); gs.log(f"  Removed: {e.name}", ORANGE)
        elif len(hand) >= lim:
            gs.log(f"Limit reached ({lim}).", ORANGE)
        else:
            hand.append(e); gs.log(f"  Added: {e.name}", GREEN if side==Side.US else RED)

    def _done_enb(self):
        gs = self.gs
        if gs.side_sel == Side.US:
            gs.side_sel = Side.PRC; gs.scroll = 0
            gs.handoff=True; gs.handoff_side=Side.PRC; gs.handoff_msg="PRC: Pick enabler cards."
        else:
            self._auto_place()

    def _auto_place(self):
        """Auto-place all squadrons at their default locations."""
        gs = self.gs
        for sd in gs.us_sqn_hand:
            loc = "us_airbase"
            if sd.deploy == "standoff": loc = "us_standoff"
            elif sd.deploy == "airbase": loc = "us_airbase"
            gs.us_sqns.append(LiveSquadron(sdef=sd, location=loc))
        for sd in gs.prc_sqn_hand:
            loc = "prc_airbase"
            if sd.deploy == "standoff": loc = "prc_standoff"
            elif sd.deploy == "airbase": loc = "prc_airbase"
            gs.prc_sqns.append(LiveSquadron(sdef=sd, location=loc))
        gs.log("All squadrons placed at default locations.", CYAN)
        gs.phase = Phase.BID_INITIATIVE

    def _roll_init(self):
        gs = self.gs
        u, p = roll_d4(), roll_d4()
        while u == p: u, p = roll_d4(), roll_d4()  # reroll ties until there's a winner
        gs.log(f"Initiative: US {u}, PRC {p}", GOLD)
        if u > p:
            gs.initiative_winner = Side.US; gs.active_side = Side.US
            gs.us_intel_adv = True; gs.prc_intel_adv = False
            gs.us_cyber = min(4, gs.us_cyber+1)  # winner advances cyber track
            gs.log("US wins! Goes first, Intel Advantage, +1 Cyber.", US_CLR)
        else:
            gs.initiative_winner = Side.PRC; gs.active_side = Side.PRC
            gs.prc_intel_adv = True; gs.us_intel_adv = False
            gs.prc_cyber = min(4, gs.prc_cyber+1)
            gs.log("PRC wins! Goes first, Intel Advantage, +1 Cyber.", PRC_CLR)
        gs.phase = Phase.INTEL_ROLL

    def _roll_intel(self):
        gs = self.gs
        ur = roll_d4(adv=gs.us_intel_adv)
        pr = roll_d4(adv=gs.prc_intel_adv)
        # Roll determines how many enemy enabler cards each side gets to peek at
        us_sees = min(max(ur, 1), len(gs.prc_enb_hand))
        prc_sees = min(max(pr, 1), len(gs.us_enb_hand))
        gs.log(f"Intel Roll: US rolled {ur}, PRC rolled {pr}", CYAN)
        # US sees PRC enablers
        gs.log(f"US reveals {us_sees} PRC enabler(s):", US_CLR)
        for i in range(us_sees):
            if i < len(gs.prc_enb_hand):
                e = gs.prc_enb_hand[i]
                gs.log(f"  - {e.name}: {e.desc}", LTGRAY)
        if len(gs.prc_enb_hand) > us_sees:
            gs.log(f"  ({len(gs.prc_enb_hand) - us_sees} PRC card(s) remain hidden)", DKGRAY)
        # PRC sees US enablers
        gs.log(f"PRC reveals {prc_sees} US enabler(s):", PRC_CLR)
        for i in range(prc_sees):
            if i < len(gs.us_enb_hand):
                e = gs.us_enb_hand[i]
                gs.log(f"  - {e.name}: {e.desc}", LTGRAY)
        if len(gs.us_enb_hand) > prc_sees:
            gs.log(f"  ({len(gs.us_enb_hand) - prc_sees} US card(s) remain hidden)", DKGRAY)
        gs.phase = Phase.PLAYER_TURN; gs.reset_turn()
        gs.consecutive_passes = 0
        gs.log(f"\n{'='*30} {gs.active_side.value}'s Turn {'='*30}", GOLD)

    def _do_pass(self):
        gs = self.gs
        gs.consecutive_passes += 1
        gs.log(f"{gs.active_side.value} passes. ({gs.consecutive_passes}/4 consecutive)", GRAY)
        # Both players must pass twice in a row (4 total) before the ATO ends
        if gs.consecutive_passes >= 4:
            gs.log("4 consecutive passes — ATO ends.", GOLD)
            gs.phase = Phase.ATO_CLEANUP
        else:
            self._switch()

    def _end_turn(self):
        """End turn after taking actions (not a pass — resets consecutive pass counter)."""
        gs = self.gs
        gs.consecutive_passes = 0
        gs.log(f"{gs.active_side.value} ends turn.", LTGRAY)
        self._switch()

    def _switch(self):
        gs = self.gs
        gs.active_side = Side.PRC if gs.active_side==Side.US else Side.US
        gs.reset_turn()
        winchester_rtb(gs, gs.active_side)  # RTB any winchester tokens for the new active side
        gs.log(f"\n{'─'*25} {gs.active_side.value}'s Turn {'─'*25}", GOLD)
        gs.handoff=True; gs.handoff_side=gs.active_side
        gs.handoff_msg=f"Pass to {gs.active_side.value} player."

    def _clear_my_pass(self):
        """Reset consecutive pass counter when any non-pass action is taken."""
        self.gs.consecutive_passes = 0

    def _activate_sqn(self, i):
        gs = self.gs
        sqns = gs.us_sqns if gs.active_side==Side.US else gs.prc_sqns
        if i >= len(sqns): return
        sq = sqns[i]
        # Can only activate one squadron per turn, and not after taking MAS actions
        if sq.activated: gs.log("Already activated.", ORANGE); return
        if sq.destroyed: gs.log("Destroyed.", RED); return
        if gs.turn_activated: gs.log("Already activated a sqn this turn.", ORANGE); return
        if gs.turn_moved or gs.turn_acquired or gs.turn_shot:
            gs.log("Cannot activate — already performed MAS actions.", ORANGE); return
        self._clear_my_pass()
        sq.activated = True; gs.turn_activated = True; gs.turn_did_action = True
        gen_tokens(gs, sq, gs.active_side)  # spawn tokens onto the board
        gs.log(f"Activated {sq.sdef.name}!", GREEN if gs.active_side==Side.US else RED)

    def _play_enb(self, i):
        gs = self.gs
        hand = gs.us_enb_hand if gs.active_side==Side.US else gs.prc_enb_hand
        played = gs.us_enb_played if gs.active_side==Side.US else gs.prc_enb_played
        enduring = gs.us_enb_enduring if gs.active_side==Side.US else gs.prc_enb_enduring
        if i >= len(hand): return
        # Enablers must be played before any other action this turn
        if gs.turn_played_enb: gs.log("Already played enabler this turn.", ORANGE); return
        if gs.turn_did_action: gs.log("Cannot play enabler after activating or MAS.", ORANGE); return
        self._clear_my_pass()
        e = hand[i]
        hand.remove(e); played.append(e)
        if e.enduring: enduring.append(e)  # enduring cards stay active for the rest of the ATO
        gs.turn_played_enb = True
        gs.log(f"Played: {e.name} — {e.desc}", GREEN if gs.active_side==Side.US else RED)
        if e.effect == "cyber_advance":
            # Cyber advance: roll against current cyber track threshold to move up
            rate = gs.us_cyber if gs.active_side==Side.US else gs.prc_cyber
            needed = CYBER_ACCESS.get(rate, 99)
            r = roll_d4()
            gs.log(f"  Cyber: need {needed}, rolled {r}", CYAN)
            if r >= needed:
                if gs.active_side==Side.US: gs.us_cyber=min(4,gs.us_cyber+1)
                else: gs.prc_cyber=min(4,gs.prc_cyber+1)
                gs.log(f"  Cyber Rate advanced!", GREEN)
                if gs.us_cyber>=4 or gs.prc_cyber>=4:
                    gs.log("CYBER RATE 4 — GAME ENDS!", GOLD); gs.phase=Phase.GAME_END  # reaching 4 ends the game
            else: gs.log("  Failed.", RED)

    def _next_ato(self):
        gs = self.gs
        vp_us = score_attrition(gs, Side.US); vp_prc = score_attrition(gs, Side.PRC)
        gs.us_vp += vp_us; gs.prc_vp += vp_prc
        gs.log(f"ATO {gs.ato_num}: US +{vp_us} VP, PRC +{vp_prc} VP", GOLD)
        # Clear all ATO-scoped state before the next cycle
        gs.tokens.clear(); gs.us_enb_played.clear(); gs.prc_enb_played.clear()
        gs.us_destroyed.clear(); gs.prc_destroyed.clear()
        for sq in gs.us_sqns+gs.prc_sqns: sq.activated=False
        gs.us_sqns.clear(); gs.prc_sqns.clear()
        gs.ato_num += 1
        if gs.ato_num > gs.max_ato: gs.phase=Phase.GAME_END; self._end_game()
        else: gs.phase=Phase.ATO_POSTURE; gs.side_sel=Side.US  # loop back to posture selection

    def _end_game(self):
        gs = self.gs
        if gs.phase != Phase.GAME_END:
            gs.us_vp += score_attrition(gs, Side.US)
            gs.prc_vp += score_attrition(gs, Side.PRC)
        gs.phase = Phase.GAME_END
        gs.log(f"GAME OVER! US: {gs.us_vp} VP | PRC: {gs.prc_vp} VP", GOLD)
        w = "US WINS!" if gs.us_vp>gs.prc_vp else ("PRC WINS!" if gs.prc_vp>gs.us_vp else "DRAW!")
        gs.log(w, GREEN if gs.us_vp>gs.prc_vp else RED)

    def _start_tut_game(self):
        gs = self.gs; gs.is_tutorial=False
        # Simplified campaign: 1 ATO, Attrition mission, no enablers, fixed squadrons
        gs.campaign=CampaignDef("Tutorial Game","Meeting Engagement",1,["Attrition"],["Standard"],"No enabler cards.","010","060")
        gs.max_ato=1
        gs.us_mission=MISSIONS[0]; gs.prc_mission=MISSIONS[0]
        gs.us_posture=US_POS[0]; gs.prc_posture=PRC_POS[0]
        for s in US_SQN:
            if s.cid=="010": gs.us_sqn_hand=[s]; gs.us_sqns=[LiveSquadron(s,"us_airbase")]; break
        for s in PRC_SQN:
            if s.cid=="060": gs.prc_sqn_hand=[s]; gs.prc_sqns=[LiveSquadron(s,"prc_airbase")]; break
        gs.us_enb_hand=[]; gs.prc_enb_hand=[]; gs.ato_num=1
        gs.phase=Phase.BID_INITIATIVE; gs.log("Tutorial game ready!", GOLD)

    # ══════════════════════════════════════════════════════════════
    #  DRAWING
    # ══════════════════════════════════════════════════════════════
    def draw(self):
        self.screen.fill((15, 18, 28))  # dark navy background
        gs = self.gs; self.btns.clear()  # rebuild button list each frame
        ph = gs.phase
        if ph == Phase.MAIN_MENU: self._d_menu()
        elif ph == Phase.TUTORIAL: self._d_tutorial()
        elif ph == Phase.MISSION_SELECT: self._d_missions()
        elif ph == Phase.ATO_POSTURE: self._d_postures()
        elif ph == Phase.DRAW_CARDS: self._d_draw()
        elif ph in (Phase.BID_INITIATIVE, Phase.INTEL_ROLL): self._d_init()
        elif ph == Phase.PLAYER_TURN: self._d_play()
        elif ph == Phase.ATO_CLEANUP: self._d_cleanup()
        elif ph == Phase.GAME_END: self._d_end()
        if gs.handoff: self._d_handoff()
        pygame.display.flip()

    def _d_board(self):
        """Draw board.jpg scaled and positioned."""
        if self.board_img is None:
            self.board_img = load_img("board.jpg", (BOARD_DISP_W, BOARD_DISP_H))
        self.screen.blit(self.board_img, (BOARD_X, BOARD_Y))

    def _d_tokens(self):
        """Overlay tokens on the board at correct band positions, plus squadron cards at bases."""
        gs = self.gs; s = self.screen

        # Draw squadron cards centered within their base locations
        for sqn_list, side in [(gs.us_sqns, Side.US), (gs.prc_sqns, Side.PRC)]:
            if not sqn_list: continue
            base_loc = "us_airbase" if side==Side.US else "prc_airbase"
            if base_loc not in _REGIONS: continue
            br = _board_rect(base_loc)
            n = len(sqn_list)
            max_cards = 6
            margin = 6
            gap = 3
            # Calculate card size: fit up to 6 across, leave margins
            usable_w = br.w - margin * 2
            card_w = (usable_w - (max_cards - 1) * gap) // max_cards
            card_h = br.h - margin * 2
            # Center the actual cards horizontally
            total_w = n * card_w + (n - 1) * gap
            start_x = br.left + (br.w - total_w) // 2
            start_y = br.top + (br.h - card_h) // 2
            for idx, sq in enumerate(sqn_list):
                if idx >= max_cards: break
                cx = start_x + idx * (card_w + gap)
                cy = start_y
                if sq.activated:
                    img = load_img(sq.sdef.img, (card_w, card_h), side, "cards")
                else:
                    back = "us_squadron_back.png" if side==Side.US else "prc_squadron_back.png"
                    img = load_img(back, (card_w, card_h), side, "cards")
                s.blit(img, (cx, cy))
                if sq.destroyed:
                    pygame.draw.line(s, RED, (cx, cy), (cx+card_w, cy+card_h), 3)
                    pygame.draw.line(s, RED, (cx+card_w, cy), (cx, cy+card_h), 3)

        # Draw tokens in bands — placed between the band number labels
        tok_sz = 44
        for loc in ALL_LOCATIONS:
            toks = gs.toks_at(loc)
            if not toks or loc not in _REGIONS: continue
            r = _board_rect(loc)
            # For range bands, inset from left/right to avoid overlapping band numbers
            if loc.startswith("band"):
                margin_left = 45   # clear of left band number
                margin_right = 45  # clear of right band number
                margin_top = 8
            else:
                margin_left = 6
                margin_right = 6
                margin_top = 6
            usable_w = r.w - margin_left - margin_right
            cols = max(1, usable_w // (tok_sz + 3))
            for idx, tok in enumerate(toks):
                col = idx % cols; row = idx // cols
                x = r.left + margin_left + col * (tok_sz + 3)
                y = r.top + margin_top + row * (tok_sz + 3)
                if y + tok_sz > r.bottom - 4: y = r.bottom - tok_sz - 4
                tok._rect = pygame.Rect(x, y, tok_sz, tok_sz)
                img_name = tok.tdef.img_f if tok.face_up else tok.tdef.img_b
                img = load_img(img_name, (tok_sz, tok_sz), tok.side, "tokens")
                s.blit(img, (x, y))
                if tok.winchester:
                    pygame.draw.circle(s, RED, (x+tok_sz-7, y+7), 6)
                    txt(s, "W", (x+tok_sz-7, y+7), WHITE, 9, True, True)
                if tok is gs.sel_tok:
                    pygame.draw.rect(s, GOLD, tok._rect.inflate(4,4), 3, border_radius=3)

    def _d_tooltip(self):
        gs = self.gs; tok = gs.hover_tok
        if not tok or tok.destroyed: return
        # Don't reveal stats for face-down enemy tokens
        if tok.side != gs.active_side and not tok.face_up:
            return
        s = self.screen; t = tok.tdef; dr = tok._rect
        # Build stat lines shown in the tooltip popup
        lines = [f"{t.name} ({t.cat.value})", f"Move: {t.move} | Band: {tok.band}"]
        if t.acq_range: lines.append(f"Acquire: Rng {t.acq_range}, +{t.acq_bonus}")
        if t.air_range: lines.append(f"Air: Rng {t.air_range}, {t.air_roll}+{' [expl]' if t.air_exploding else ''}")
        if t.sfc_range: lines.append(f"Surface: Rng {t.sfc_range}, {t.sfc_roll}+{' [expl]' if t.sfc_exploding else ''}")
        if t.stealth: lines.append("STEALTH (acquire=4)")
        if t.has_md: lines.append(f"Missile Def: Rng {t.md_range}")
        lines.append(f"To acquire: {t.acq_diff}+")
        if tok.winchester: lines.append("⚠ WINCHESTER")
        font = pygame.font.SysFont("arial", 13)
        mw = max(font.size(l)[0] for l in lines) + 14
        h = len(lines) * 18 + 8
        x = dr.right + 8; y = dr.top
        # Flip tooltip to left side if it would go off the right edge
        if x + mw > WIDTH: x = dr.left - mw - 8
        if y + h > HEIGHT: y = HEIGHT - h - 4
        pygame.draw.rect(s, (10,10,25), (x,y,mw,h), border_radius=5)
        pygame.draw.rect(s, GOLD, (x,y,mw,h), 1, border_radius=5)
        for i, l in enumerate(lines):
            txt(s, l, (x+7, y+4+i*18), WHITE, 13)

    def _d_side(self):
        """Draw VP panel at top and game log at bottom."""
        s = self.screen; gs = self.gs
        # VP panel: shows score, cyber track, intel status, and live token counts
        draw_panel(s, pygame.Rect(SIDE_X, 8, SIDE_W, 55), PANEL, CYAN)
        txt(s, f"US VP: {gs.us_vp}", (SIDE_X+10,12), US_CLR, 18, True)
        txt(s, f"PRC VP: {gs.prc_vp}", (SIDE_X+10,33), PRC_CLR, 18, True)
        txt(s, f"Cyber US:{gs.us_cyber} PRC:{gs.prc_cyber}", (SIDE_X+170,12), CYAN, 13)
        txt(s, f"Intel US:{'ADV' if gs.us_intel_adv else 'NRM'} PRC:{'ADV' if gs.prc_intel_adv else 'NRM'}",
            (SIDE_X+170,28), GOLD, 13)
        uc = sum(1 for t in gs.tokens if t.side==Side.US and not t.destroyed)
        pc = sum(1 for t in gs.tokens if t.side==Side.PRC and not t.destroyed)
        txt(s, f"Board: US {uc} | PRC {pc}", (SIDE_X+170,44), LTGRAY, 12)
        # Scrolling game log at the bottom of the side panel
        lr = pygame.Rect(SIDE_X, HEIGHT-200, SIDE_W, 195)
        draw_panel(s, lr, (15,18,25), DKGRAY)
        font = pygame.font.SysFont("consolas", 12)
        vis = 14; start = max(0, len(gs.msgs)-vis); y = lr.top+4  # show last 14 messages
        for i in range(start, len(gs.msgs)):
            t, c = gs.msgs[i]
            s.blit(font.render(t[:70],True,c), (SIDE_X+5,y)); y+=13

    def _d_move_highlight(self):
        """Highlight valid move destinations."""
        gs = self.gs; s = self.screen
        if gs.sub!="move" or not gs.sel_tok: return
        mx = gs.sel_tok.tdef.move
        if any(e.effect=="extra_move" for e in (gs.us_enb_played if gs.sel_tok.side==Side.US else gs.prc_enb_played)):
            mx += 1
        for loc in ALL_LOCATIONS:
            if loc not in _REGIONS: continue
            d = band_dist(gs.sel_tok.band, loc)
            if 0 < d <= mx:
                r = _board_rect(loc)
                hl = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                hl.fill((100,255,100,30))
                s.blit(hl, r.topleft)
                pygame.draw.rect(s, GREEN, r, 2, border_radius=2)

    # ── Screen renderers ──
    def _d_menu(self):
        s = self.screen
        # Styled like the player guide cover
        cx = WIDTH // 2
        # Title block
        pygame.draw.line(s, CYAN, (cx-300, 200), (cx+300, 200), 3)
        txt(s, "VIRTUAL", (cx, 260), GOLD, 56, True, True)
        txt(s, "AIR FORCE WARGAME", (cx, 330), CYAN, 48, True, True)
        txt(s, "INDO-PACIFIC", (cx, 390), WHITE, 42, True, True)
        pygame.draw.line(s, CYAN, (cx-300, 430), (cx+300, 430), 3)
        txt(s, "Tyler Brunelle", (cx, 460), GRAY, 18, False, True)
        bw, bh = 260, 50; bx = cx - bw//2
        self.btns += [Btn((bx, 520, bw, bh), "Player vs Player", BLUE, "pvp", fsize=22),
                      Btn((bx, 585, bw, bh), "Tutorial", GREEN, "tutorial", fsize=22),
                      Btn((bx, 650, bw, bh), "Quit", RED, "quit", fsize=22)]
        for b in self.btns: b.draw(s)

    def _d_tutorial(self):
        s = self.screen; gs = self.gs
        step = min(gs.tutorial_step, len(TUTS)-1)
        title, text = TUTS[step]
        draw_panel(s, pygame.Rect(60,30,WIDTH-120,HEIGHT-80), PANEL, CYAN, 10)
        txt(s, title, (WIDTH//2,65), GOLD, 34, True, True)
        y = 120
        for line in text.split("\n"):
            txt(s, line, (100,y), WHITE, 19); y += 28
        bx = WIDTH//2-80
        if gs.tutorial_step < len(TUTS)-1:
            self.btns.append(Btn((bx,HEIGHT-80,160,42),"NEXT",GREEN,"tut_next",fsize=20))
        else:
            self.btns.append(Btn((bx,HEIGHT-80,160,42),"PLAY!",BLUE,"tut_play",fsize=20))
        for b in self.btns: b.draw(s)

    def _d_campaigns(self):
        s = self.screen
        txt(s, "SELECT CAMPAIGN", (WIDTH//2,35), GOLD, 34, True, True)
        y = 90
        for i, c in enumerate(CAMPAIGNS):
            r = pygame.Rect(80,y,WIDTH-160,58)
            draw_panel(s, r, PANEL2, CYAN if i%2==0 else BLUE)
            txt(s, c.name, (100,y+8), WHITE, 20, True)
            txt(s, c.desc, (100,y+32), LTGRAY, 15)
            txt(s, f"{c.ato_cycles} ATO{'s' if c.ato_cycles>1 else ''}", (WIDTH-190,y+18), CYAN, 16, True)
            self.btns.append(Btn((WIDTH-150,y+10,90,38),"Select",BLUE,f"camp_{i}"))
            y += 68
        self.btns.append(Btn((30,HEIGHT-55,110,38),"← Back",DKGRAY,"main_menu",fsize=16))
        for b in self.btns: b.draw(s)

    def _d_missions(self):
        s = self.screen; gs = self.gs; side = gs.side_sel
        c = US_CLR if side==Side.US else PRC_CLR
        txt(s, f"{side.value}: SELECT MISSION", (WIDTH//2,35), c, 30, True, True)
        txt(s, "(Keep secret from opponent!)", (WIDTH//2,68), GRAY, 16, False, True)
        avail = self._avail_missions(side); y = 100
        for i, m in enumerate(avail):
            r = pygame.Rect(80, y, WIDTH-160, 80)
            draw_panel(s, r, PANEL2, c)
            txt(s, m.name, (100, y+10), WHITE, 22, True)
            txt(s, m.desc, (100, y+36), LTGRAY, 15)
            txt(s, m.scoring, (100, y+56), CYAN, 13)
            self.btns.append(Btn((WIDTH-155, y+20, 100, 40), "Choose", c, f"miss_{i}"))
            y += 90
        for b in self.btns: b.draw(s)

    def _d_postures(self):
        s = self.screen; gs = self.gs; side = gs.side_sel
        c = US_CLR if side==Side.US else PRC_CLR
        txt(s, f"{side.value}: SELECT POSTURE", (WIDTH//2,35), c, 30, True, True)
        ps = self._avail_postures(side); y = 90
        for i, p in enumerate(ps):
            r = pygame.Rect(80,y,WIDTH-160,60)
            draw_panel(s, r, PANEL2, c)
            txt(s, p.name, (100,y+8), WHITE, 20, True)
            txt(s, f"Squadrons: {p.sqn_lim}  |  Enablers: {p.enb_lim}", (100,y+32), CYAN, 15)
            txt(s, p.desc, (420,y+32), LTGRAY, 14)
            self.btns.append(Btn((WIDTH-155,y+12,100,36),"Select",c,f"post_{i}"))
            y += 68
        for b in self.btns: b.draw(s)

    def _d_draw(self):
        """Draw card picking screen with column headers."""
        s = self.screen; gs = self.gs; side = gs.side_sel
        c = US_CLR if side==Side.US else PRC_CLR
        is_sqn = gs.show_screen == "sqn"
        pool = (US_SQN if side==Side.US else PRC_SQN) if is_sqn else (US_ENB if side==Side.US else PRC_ENB)
        hand = (gs.us_sqn_hand if side==Side.US else gs.prc_sqn_hand) if is_sqn else \
               (gs.us_enb_hand if side==Side.US else gs.prc_enb_hand)
        posture = gs.us_posture if side==Side.US else gs.prc_posture
        lim = posture.sqn_lim if is_sqn else posture.enb_lim
        kind = "SQUADRON" if is_sqn else "ENABLER"

        # Title
        txt(s, f"{side.value}: Pick {kind} Cards ({len(hand)}/{lim})",
            (WIDTH//2, 25), c, 26, True, True)

        # Column headers
        hdr_y = 55
        col1 = 50; col2 = 370; col3 = 570; col4 = 730
        pygame.draw.line(s, DKGRAY, (30, hdr_y+20), (WIDTH-30, hdr_y+20), 1)
        if is_sqn:
            txt(s, "UNIT", (col1, hdr_y), GOLD, 14, True)
            txt(s, "TOKENS", (col2, hdr_y), GOLD, 14, True)
            txt(s, "ACTIVATION LOCATION", (col3, hdr_y), GOLD, 14, True)
            txt(s, "TYPE", (col4, hdr_y), GOLD, 14, True)
        else:
            txt(s, "NAME", (col1, hdr_y), GOLD, 14, True)
            txt(s, "EFFECT", (350, hdr_y), GOLD, 14, True)
            txt(s, "TYPE", (850, hdr_y), GOLD, 14, True)

        # Card rows
        rh = 46
        y = hdr_y + 25
        for i, item in enumerate(pool):
            if y > HEIGHT - 65: break
            r = pygame.Rect(30, y, WIDTH-60, rh-4)
            picked = item in hand
            bg = (25, 55, 25) if picked else PANEL2
            draw_panel(s, r, bg, c)

            if is_sqn:
                txt(s, item.name, (col1, y+12), GREEN if picked else WHITE, 16, picked)
                txt(s, f"{item.tok_count}x {T[item.tok_key].name}", (col2, y+12), LTGRAY, 14)
                dep = {"band1":"Band 1","standoff":"Standoff","airbase":"Airbase","any":"Any Band"}
                txt(s, dep.get(item.deploy, ""), (col3, y+12), GRAY, 14)
                tags = []
                if item.is_5th: tags.append("[5th Gen]")
                if item.is_bomber: tags.append("[Bomber]")
                if item.is_long: tags.append("[Long Range]")
                if tags:
                    tag_c = CYAN if item.is_5th else ORANGE
                    txt(s, " ".join(tags), (col4, y+12), tag_c, 12)
            else:
                txt(s, item.name, (col1, y+14), GREEN if picked else WHITE, 16, picked)
                txt(s, item.desc, (350, y+14), LTGRAY, 14)
                tags = []
                if item.reaction: tags.append("[Reaction]")
                if item.enduring: tags.append("[Enduring]")
                if item.use == EnablerUse.SINGLE: tags.append("[Single Use]")
                else: tags.append("[Multi Use]")
                txt(s, "  ".join(tags), (850, y+14), YELLOW if item.reaction else ORANGE, 12)

            label = "Remove" if picked else "Pick"
            tag = f"spick_{i}" if is_sqn else f"epick_{i}"
            bc = (120, 40, 40) if picked else c
            self.btns.append(Btn((WIDTH-120, y+6, 80, rh-16), label, bc, tag, fsize=13))
            y += rh

        done_tag = "sdone" if is_sqn else "edone"
        self.btns.append(Btn((WIDTH//2-55, HEIGHT-50, 110, 38), "Done", GREEN, done_tag, fsize=18))
        for b in self.btns: b.draw(s)

    def _d_init(self):
        s = self.screen; gs = self.gs
        self._d_board(); self._d_tokens(); self._d_side()
        cx = BOARD_X + BOARD_DISP_W//2
        ov = pygame.Surface((BOARD_DISP_W, BOARD_DISP_H), pygame.SRCALPHA)
        ov.fill((0,0,0,140)); s.blit(ov, (BOARD_X, BOARD_Y))
        if gs.phase == Phase.BID_INITIATIVE:
            txt(s, "BID FOR INITIATIVE", (cx, BOARD_Y+120), GOLD, 34, True, True)
            txt(s, "Winner: goes first, Intel Advantage, +1 Cyber", (cx, BOARD_Y+160), WHITE, 16, False, True)
            self.btns.append(Btn((cx-70, BOARD_Y+200, 140, 48),"Roll d4!",GOLD,"roll_init",fsize=22))
        else:
            txt(s, "INTELLIGENCE ROLL", (cx, BOARD_Y+120), CYAN, 34, True, True)
            w = gs.initiative_winner.value if gs.initiative_winner else "?"
            txt(s, f"{w} won initiative!", (cx, BOARD_Y+160), GOLD, 18, True, True)
            self.btns.append(Btn((cx-70, BOARD_Y+200, 140, 48),"Roll Intel",CYAN,"roll_intel",fsize=22))
        for b in self.btns: b.draw(s)

    def _d_play(self):
        s = self.screen; gs = self.gs
        self._d_board(); self._d_move_highlight(); self._d_tokens(); self._d_side()

        # Header bar — sized to fit text properly
        c = US_CLR if gs.active_side==Side.US else PRC_CLR
        hr = pygame.Rect(SIDE_X, 70, SIDE_W, 30)
        draw_panel(s, hr, c, c, 4)
        txt(s, f"{gs.active_side.value}'s Turn  —  ATO {gs.ato_num}/{gs.max_ato}",
            (hr.centerx, hr.centery), WHITE, 16, True, True)

        # Sub-phase indicator
        if gs.sub:
            txt(s, f"> {gs.sub.upper()}: select tokens on board", (SIDE_X+10, 106), GOLD, 14, True)

        bx = SIDE_X + 5
        ty = 120

        # ── STEP 1: ENABLER (optional, must be first) ──
        hand = gs.us_enb_hand if gs.active_side==Side.US else gs.prc_enb_hand
        can_play_enb = not gs.turn_played_enb and not gs.turn_did_action and len(hand) > 0
        if hand:
            txt(s, f"Step 1 — Play Enabler ({len(hand)} in hand):", (bx, ty), ORANGE, 15, True)
            ty += 20
            for i, e in enumerate(hand):
                pf = "[R] " if e.reaction else ("[E] " if e.enduring else "-")
                txt(s, f"{pf} {e.name}", (bx+4, ty), WHITE, 14)
                txt(s, e.desc[:45], (bx+8, ty+16), GRAY, 11)
                if can_play_enb:
                    self.btns.append(Btn((bx+360, ty+2, 55, 20), "Play", ORANGE, f"penb_{i}", fsize=11))
                ty += 34
        elif gs.turn_played_enb:
            txt(s, "Enabler played.", (bx, ty), GREEN, 14, True); ty += 20
        else:
            txt(s, "No enabler cards in hand.", (bx, ty), GRAY, 13); ty += 20

        # Separator
        ty += 4
        pygame.draw.line(s, DKGRAY, (bx, ty), (bx+SIDE_W-15, ty), 1); ty += 8

        # ── STEP 2: EITHER Activate Squadron OR Move-Acquire-Shoot ──
        txt(s, "Step 2 — Choose ONE:", (bx, ty), CYAN, 15, True); ty += 22

        # Option A: Activate Squadron
        sqns = gs.us_sqns if gs.active_side==Side.US else gs.prc_sqns
        has_inactive = any(not sq.activated and not sq.destroyed for sq in sqns)
        can_activate = not gs.turn_activated and not gs.turn_moved and not gs.turn_acquired and not gs.turn_shot and has_inactive
        opt_a_c = WHITE if can_activate else DKGRAY
        txt(s, "A) Activate Squadron:", (bx+4, ty), opt_a_c, 14, True); ty += 18
        for i, sq in enumerate(sqns):
            st = "[Active]" if sq.activated else ("[Destroyed]" if sq.destroyed else "[Ready]")
            sc = GREEN if sq.activated else (RED if sq.destroyed else WHITE)
            txt(s, f"  {st}: {sq.sdef.name}", (bx+4, ty), sc, 14)
            txt(s, f"({sq.sdef.tok_count}×{T[sq.sdef.tok_key].name})", (bx+220, ty), GRAY, 12)
            if can_activate and not sq.activated and not sq.destroyed:
                self.btns.append(Btn((bx+370, ty-1, 60, 20), "Deploy", GREEN, f"act_{i}", fsize=11))
            ty += 20

        # Separator
        ty += 16; txt(s, "-- OR --", (bx + SIDE_W//2 - 10, ty), DKGRAY, 13, False, True); ty += 20

        # Option B: Move-Acquire-Shoot
        can_mas = not gs.turn_activated
        opt_b_c = WHITE if can_mas else DKGRAY
        txt(s, "B) Move-Acquire-Shoot:", (bx+4, ty), opt_b_c, 14, True); ty += 22

        btn_y = ty
        if can_mas and not gs.turn_moved:
            self.btns.append(Btn((bx, btn_y, 80, 28), "Move", BLUE, "move", fsize=14))
        if can_mas and not gs.turn_acquired:
            self.btns.append(Btn((bx+90, btn_y, 90, 28), "Acquire", CYAN, "acquire", fsize=14))
        if can_mas and not gs.turn_shot:
            self.btns.append(Btn((bx+190, btn_y, 80, 28), "Shoot", RED, "shoot", fsize=14))
        if gs.sub:
            self.btns.append(Btn((bx+280, btn_y, 70, 28), "Cancel", (100,50,50), "cancel", fsize=12))
        ty = btn_y + 36

        # End Turn / Pass
        pygame.draw.line(s, DKGRAY, (bx, ty), (bx+SIDE_W-15, ty), 1); ty += 8
        did_something = gs.turn_played_enb or gs.turn_did_action
        if did_something:
            self.btns.append(Btn((bx, ty, 100, 30), "End Turn", GREEN, "end_turn", fsize=14))
        else:
            self.btns.append(Btn((bx, ty, 100, 30), "Pass", DKGRAY, "pass", fsize=14))
        if gs.consecutive_passes > 0:
            txt(s, f"({gs.consecutive_passes}/4 consecutive passes)", (bx+110, ty+8), ORANGE, 13)

        self._d_tooltip()
        for b in self.btns: b.draw(s)

    def _d_cleanup(self):
        s = self.screen; gs = self.gs
        draw_panel(s, pygame.Rect(60,30,WIDTH-120,HEIGHT-80), PANEL, GOLD, 10)
        txt(s, f"ATO {gs.ato_num} COMPLETE", (WIDTH//2,60), GOLD, 34, True, True)
        y = 110
        txt(s, f"US destroyed {len(gs.us_destroyed)} PRC tokens", (WIDTH//2,y), US_CLR, 20, False, True)
        txt(s, f"PRC destroyed {len(gs.prc_destroyed)} US tokens", (WIDTH//2,y+28), PRC_CLR, 20, False, True)
        txt(s, f"Score: US {gs.us_vp} VP | PRC {gs.prc_vp} VP", (WIDTH//2,y+65), GOLD, 18, False, True)
        remain = gs.max_ato - gs.ato_num
        if remain > 0:
            txt(s, f"{remain} ATO{'s' if remain>1 else ''} remaining", (WIDTH//2,y+100), WHITE, 16, False, True)
            self.btns.append(Btn((WIDTH//2-70,y+130,140,42),"Next ATO →",GREEN,"next_ato",fsize=20))
        else:
            self.btns.append(Btn((WIDTH//2-70,y+130,140,42),"End Game",GOLD,"end_game",fsize=20))
        for b in self.btns: b.draw(s)

    def _d_end(self):
        s = self.screen; gs = self.gs
        draw_panel(s, pygame.Rect(80,40,WIDTH-160,HEIGHT-80), PANEL, GOLD, 10)
        txt(s, "GAME OVER", (WIDTH//2,80), GOLD, 48, True, True)
        um = gs.us_mission.name if gs.us_mission else "N/A"
        pm = gs.prc_mission.name if gs.prc_mission else "N/A"
        txt(s, f"US Mission: {um}", (WIDTH//2,150), US_CLR, 22, True, True)
        txt(s, f"PRC Mission: {pm}", (WIDTH//2,180), PRC_CLR, 22, True, True)
        txt(s, f"US: {gs.us_vp} VP", (WIDTH//2-100,250), US_CLR, 36, True, True)
        txt(s, f"PRC: {gs.prc_vp} VP", (WIDTH//2+100,250), PRC_CLR, 36, True, True)
        if gs.us_vp>gs.prc_vp: txt(s, "US VICTORY", (WIDTH//2,320), GREEN, 38, True, True)
        elif gs.prc_vp>gs.us_vp: txt(s, "PRC VICTORY", (WIDTH//2,320), RED, 38, True, True)
        else: txt(s, "DRAW", (WIDTH//2,320), YELLOW, 38, True, True)
        self.btns += [Btn((WIDTH//2-130,420,120,45),"Main Menu",BLUE,"main_menu",fsize=18),
                      Btn((WIDTH//2+10,420,120,45),"Quit",RED,"quit",fsize=18)]
        for b in self.btns: b.draw(s)

    def _d_handoff(self):
        # Dim overlay displayed between turns so each player can look away before clicking through
        s = self.screen; gs = self.gs
        dim = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA); dim.fill((0,0,0,220))
        s.blit(dim, (0,0))
        c = US_CLR if gs.handoff_side==Side.US else PRC_CLR
        side_name = gs.handoff_side.value if gs.handoff_side else ""
        pygame.draw.rect(s, c, (WIDTH//2-180,300,360,5), border_radius=2)
        txt(s, f"— {side_name} —", (WIDTH//2,340), c, 46, True, True)
        for i, line in enumerate(gs.handoff_msg.split("\n")):
            txt(s, line, (WIDTH//2,390+i*28), WHITE, 20, False, True)
        pygame.draw.rect(s, c, (WIDTH//2-180,440,360,5), border_radius=2)
        txt(s, "Click anywhere to continue", (WIDTH//2,470), GRAY, 16, False, True)

# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    App().run()
