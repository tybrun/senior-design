"""
AFWI Game Data — tokens, cards, campaigns, missions, postures.
Asset paths use the user's directory structure:
  assets/tokens/{us|prc}/filename.png
  assets/cards/{us|prc}/filename.png
  board.jpg (root level)
"""
from enum import Enum, auto
from dataclasses import dataclass

class Side(Enum):
    US = "US"
    PRC = "PRC"

class TokenCat(Enum):
    FIGHTER_5TH = "5th Gen Fighter"
    FIGHTER_4TH = "4th Gen Fighter"
    BOMBER = "Bomber"
    AEW = "AEW"
    UAS_ATTACK = "Attack UAS"
    UAS_RECON = "Recon UAS"
    ADA_MID = "Mid Range ADA"
    ADA_LONG = "Long Range ADA"
    MISSILE_DEF = "Missile Defense"
    SHIP_DDG = "Destroyer"
    SHIP_CG = "Cruiser"

class EnablerUse(Enum):
    SINGLE = "Single Use"
    MULTIPLE = "Multiple Use"

class Phase(Enum):
    MAIN_MENU = auto()
    CAMPAIGN_SELECT = auto()
    MISSION_SELECT = auto()
    ATO_POSTURE = auto()
    DRAW_CARDS = auto()
    PLACE_SQUADRONS = auto()
    BID_INITIATIVE = auto()
    INTEL_ROLL = auto()
    PLAYER_TURN = auto()
    ATO_CLEANUP = auto()
    GAME_END = auto()
    TUTORIAL = auto()

# ── Board bands ──
BOARD_BANDS = ["band1","band2","band3","band4","band5"]
ALL_LOCATIONS = ["us_airbase","us_standoff","us_contingency"] + BOARD_BANDS + ["prc_airbase","prc_standoff"]
BAND_POS = {"us_airbase":0,"us_standoff":0,"us_contingency":0,
            "band1":1,"band2":2,"band3":3,"band4":4,"band5":5,
            "prc_airbase":6,"prc_standoff":6}

def band_dist(a, b):
    return abs(BAND_POS.get(a,0) - BAND_POS.get(b,0))

# ── Data classes ──
@dataclass
class TokenDef:
    key: str; name: str; cat: TokenCat; side: Side
    move: int; acq_range: int; acq_bonus: int; acq_count: int
    air_range: int; air_roll: int; air_exploding: bool
    sfc_range: int; sfc_roll: int; sfc_exploding: bool
    acq_diff: int; standoff: bool; stealth: bool
    has_md: bool; md_range: int; winchester: str; salvos: int
    img_f: str; img_b: str   # relative to assets/tokens/{side}/

@dataclass
class SquadronDef:
    cid: str; name: str; side: Side; tok_key: str; tok_count: int
    dmg_cap: int; deploy: str; img: str   # relative to assets/cards/{side}/
    is_5th: bool = False; is_bomber: bool = False; is_long: bool = False

@dataclass
class EnablerDef:
    cid: str; name: str; side: Side; use: EnablerUse
    reaction: bool; enduring: bool; cyber: bool
    desc: str; effect: str; img: str
    is_sof: bool = False; is_long_missile: bool = False

@dataclass
class MissionDef:
    name: str; sides: str; desc: str; scoring: str

@dataclass
class PostureDef:
    name: str; side: Side; sqn_lim: int; enb_lim: int
    desc: str; is_std: bool = False

@dataclass
class CampaignDef:
    name: str; desc: str; ato_cycles: int
    missions: list; postures: list; rules: str
    us_forced: str; prc_forced: str

# ════════════════════════════════════════════════════════════════════
# TOKEN DEFINITIONS
# img_f/img_b are filenames inside assets/tokens/{us|prc}/
# ════════════════════════════════════════════════════════════════════
_U = Side.US; _P = Side.PRC; _C = TokenCat

T = {
 "f22":     TokenDef("f22","F-22",_C.FIGHTER_5TH,_U,2,2,1,1, 1,2,False, 0,0,False, 4,False,True, False,0,"normal",0, "f22_front.png","f22_back.png"),
 "f16c":    TokenDef("f16c","F-16C",_C.FIGHTER_4TH,_U,2,2,0,1, 1,2,False, 1,2,False, 2,False,False, False,0,"normal",0, "f16c_front.png","f16c_back.png"),
 "b52":     TokenDef("b52","B-52",_C.BOMBER,_U,1,2,0,1, 0,0,False, 6,2,True, 2,True,False, False,0,"normal",0, "b52_front.png","b52_back.png"),
 "us_md":   TokenDef("us_md","Missile Def",_C.MISSILE_DEF,_U,0,2,1,1, 1,2,False, 0,0,False, 2,False,False, True,2,"never",0, "missile_defense_front.png","missile_defense_back.png"),
 "ddg81":   TokenDef("ddg81","DDG-81",_C.SHIP_DDG,_U,1,2,1,1, 3,2,False, 3,2,True, 2,False,False, True,3,"naval",4, "ddg81_guided_missile_destroyer_front.png","ddg81_guided_missile_destroyer_back.png"),
 "us_cg":   TokenDef("us_cg","US Cruiser",_C.SHIP_CG,_U,1,2,1,1, 3,2,False, 3,2,True, 2,False,False, True,3,"naval",4, "guided_missile_cruiser_front.png","guided_missile_cruiser_back.png"),
 "us_recon":TokenDef("us_recon","Recon UAS",_C.UAS_RECON,_U,1,3,0,1, 0,0,False, 0,0,False, 2,False,False, False,0,"never",0, "recon_uas_front.png","recon_uas_back.png"),
 "j20b":    TokenDef("j20b","J-20B",_C.FIGHTER_5TH,_P,2,2,1,1, 1,2,False, 0,0,False, 4,False,True, False,0,"normal",0, "j20b_front.png","j20b_back.png"),
 "j16":     TokenDef("j16","J-16",_C.FIGHTER_4TH,_P,2,2,0,1, 1,2,False, 1,2,False, 2,False,False, False,0,"normal",0, "j16_front.png","j16_back.png"),
 "j15":     TokenDef("j15","J-15",_C.FIGHTER_4TH,_P,2,2,0,1, 1,2,False, 1,2,False, 2,False,False, False,0,"normal",0, "j15_front.png","j15_back.png"),
 "h6k":     TokenDef("h6k","H-6K",_C.BOMBER,_P,1,2,0,1, 0,0,False, 6,2,True, 2,True,False, False,0,"normal",0, "h6k_front.png","h6k_back.png"),
 "prc_aew": TokenDef("prc_aew","AEW",_C.AEW,_P,1,3,2,2, 0,0,False, 0,0,False, 2,True,False, False,0,"never",0, "aew_front.png","aew_back.png"),
 "atk_uas": TokenDef("atk_uas","Attack UAS",_C.UAS_ATTACK,_P,1,2,0,1, 0,0,False, 1,3,False, 2,False,False, False,0,"uas",0, "attack_uas_front.png","recon_uas_back.png"),
 "prc_recon":TokenDef("prc_recon","Recon UAS",_C.UAS_RECON,_P,1,3,0,1, 0,0,False, 0,0,False, 2,False,False, False,0,"never",0, "recon_uas_front.png","recon_uas_back.png"),
 "mid_ada": TokenDef("mid_ada","Mid Range ADA",_C.ADA_MID,_P,0,2,1,1, 1,2,False, 0,0,False, 2,False,False, True,1,"never",0, "mid_range_ada_front.png","mid_range_ada_back.png"),
 "long_ada":TokenDef("long_ada","Long Range ADA",_C.ADA_LONG,_P,0,2,1,1, 3,2,False, 0,0,False, 2,False,False, True,2,"never",0, "long_range_ada_front.png","long_range_ada_back.png"),
 "prc_cg":  TokenDef("prc_cg","PRC Cruiser",_C.SHIP_CG,_P,1,2,1,1, 3,2,False, 3,2,True, 2,False,False, True,3,"naval",4, "guided_missile_cruiser_front.png","guided_missile_cruiser_back.png"),
}

# ════════════════════════════════════════════════════════════════════
# SQUADRON CARDS  (img relative to assets/cards/{side}/)
# ════════════════════════════════════════════════════════════════════
US_SQN = [
 SquadronDef("010","480th Fighter Sqn",_U,"f16c",4,2,"band1","010_480th_fighter_squadron_front.png"),
 SquadronDef("002","94th Fighter Sqn",_U,"f22",4,2,"band1","016_aerial_refueling_ar_front.png",is_5th=True),
 SquadronDef("003","23rd Bomb Sqn",_U,"b52",2,2,"standoff","016_aerial_refueling_ar_front.png",is_bomber=True,is_long=True),
 SquadronDef("001","124th Attack Sqn",_U,"us_recon",4,2,"any","001_124th_attack_squadron_front.png"),
 SquadronDef("005","Missile Def Btry",_U,"us_md",2,2,"airbase","037_maritime_missile_defense_front.png"),
 SquadronDef("006","DDG-81 Group",_U,"ddg81",1,2,"any","037_maritime_missile_defense_front.png"),
 SquadronDef("007","44th Fighter Sqn",_U,"f22",4,2,"band1","016_aerial_refueling_ar_front.png",is_5th=True),
 SquadronDef("008","35th Fighter Sqn",_U,"f16c",4,2,"band1","010_480th_fighter_squadron_front.png"),
 SquadronDef("009","69th Bomb Sqn",_U,"b52",2,2,"standoff","016_aerial_refueling_ar_front.png",is_bomber=True,is_long=True),
 SquadronDef("011","Cruiser Group",_U,"us_cg",1,2,"any","037_maritime_missile_defense_front.png"),
]

PRC_SQN = [
 SquadronDef("060","124th Air Bde",_P,"j16",4,2,"band1","060_124th_air_brigade_front.png"),
 SquadronDef("062","5th Air Bde",_P,"j20b",4,2,"band1","062_5th_air_brigade_front.png",is_5th=True),
 SquadronDef("063","26th Air Bde",_P,"j16",4,2,"band1","063_26th_air_brigade_front.png"),
 SquadronDef("064","126th Air Bde",_P,"j15",4,2,"band1","064_126th_air_brigade_front.png"),
 SquadronDef("061","8th Bomber Div",_P,"h6k",2,2,"standoff","061_8th_bomber_division_front.png",is_bomber=True,is_long=True),
 SquadronDef("058","AEW Regiment",_P,"prc_aew",1,2,"standoff","058_aew_regiment_front.png"),
 SquadronDef("055","UAS Air Rgt",_P,"atk_uas",4,2,"any","055_uas_air_regiment_front.png"),
 SquadronDef("057","UAS Air Bde",_P,"prc_recon",4,2,"any","057_uas_air_brigade_front.png"),
 SquadronDef("059","5th AD Rgt",_P,"mid_ada",2,2,"airbase","059_5th_air_defense_regiment_front.png"),
 SquadronDef("056","3rd AD Bde",_P,"long_ada",2,2,"airbase","056_3rd_air_defense_brigade_front.png"),
]

# ════════════════════════════════════════════════════════════════════
# ENABLER CARDS  (img relative to assets/cards/{side}/)
# ════════════════════════════════════════════════════════════════════
US_ENB = [
 EnablerDef("016","Aerial Refueling",_U,EnablerUse.MULTIPLE,False,False,False,"Place 1 extra sqn on airbase.","extra_squadron","016_aerial_refueling_ar_front.png"),
 EnablerDef("013","Forward Observers",_U,EnablerUse.MULTIPLE,False,True,False,"Acquire +1 target/turn. Enduring.","extra_acquire","013_forward_observers_front.png"),
 EnablerDef("017","Quick Turn",_U,EnablerUse.MULTIPLE,False,False,False,"Remove Winchester from 1 air token.","remove_winchester","017_quick_turn_mobility_front.png"),
 EnablerDef("018","Rapid Resupply",_U,EnablerUse.MULTIPLE,False,False,False,"+1 move band for 1 token.","extra_move","018_rapid_resupply_front.png"),
 EnablerDef("020","Flying Crew Chief",_U,EnablerUse.MULTIPLE,False,True,False,"Contingency auto-gen. Enduring.","contingency_auto","020_flying_crew_chief_front.png"),
 EnablerDef("028","Offensive EW",_U,EnablerUse.MULTIPLE,False,False,False,"1 enemy shoots at disadvantage.","disadvantage_shot","028_offensive_electronic_warfare_ew_front.png"),
 EnablerDef("031","Space Recon",_U,EnablerUse.MULTIPLE,False,False,False,"Acquire anywhere, no range.","global_acquire","031_space_reconnaissance_front.png"),
 EnablerDef("035","Space-Based EW",_U,EnablerUse.MULTIPLE,False,True,False,"All enemy acq at disadvantage. Enduring.","disadv_acquire_all","035_space_based_electronic_warfare_front.png"),
 EnablerDef("041","HIMARS",_U,EnablerUse.MULTIPLE,False,False,False,"Surface atk: Rng 3, 2+, exploding.","himars","041_high_mobility_artillery_rocket_system_himars_front.png"),
 EnablerDef("044","Marine Littoral",_U,EnablerUse.MULTIPLE,False,False,False,"Surface atk: Rng 2, 2+.","mlr","044_marine_littoral_regiment_front.png"),
 EnablerDef("049","Standard Cyber",_U,EnablerUse.MULTIPLE,False,False,False,"Roll d4 >= access → +1 Cyber.","cyber_advance","049_standard_front.png"),
 EnablerDef("051","Attrition Cyber",_U,EnablerUse.MULTIPLE,False,False,False,"Roll d4 >= access → +1 Cyber.","cyber_advance","051_attrition_front.png"),
 EnablerDef("023","Defensive Cyber",_U,EnablerUse.MULTIPLE,True,False,True,"Reaction: Cancel cyber card.","cancel_cyber","023_defensive_cyber_front.png"),
 EnablerDef("015","SOF Cyber Infil",_U,EnablerUse.SINGLE,False,False,True,"Reduce enemy Cyber by 1.","reduce_cyber","015_sof_cyber_infiltration_front.png",is_sof=True),
 EnablerDef("037","Maritime Missile Def",_U,EnablerUse.MULTIPLE,False,False,False,"Deploy naval token.","deploy_naval","037_maritime_missile_defense_front.png"),
]

PRC_ENB = [
 EnablerDef("068","UAS Proliferation",_P,EnablerUse.MULTIPLE,False,False,False,"Generate 2 extra Attack UAS.","extra_uas","068_uas_proliferation_front.png"),
 EnablerDef("070","Ground Radar",_P,EnablerUse.MULTIPLE,False,True,False,"All PRC acq +1. Enduring.","acq_bonus_all","070_ground_based_radar_front.png"),
 EnablerDef("071","Badger Surge",_P,EnablerUse.MULTIPLE,False,False,False,"Activate extra bomber sqn.","extra_bomber","071_badger_surge_front.png"),
 EnablerDef("077","Maritime Strike CM",_P,EnablerUse.MULTIPLE,False,False,False,"Naval sfc atk: Rng 4, 2+, exploding.","cruise_missile","077_maritime_strike_cruise_missile_front.png",is_long_missile=True),
 EnablerDef("081","Offensive Cyber",_P,EnablerUse.MULTIPLE,False,False,True,"Cyber atk augmented by rate.","offensive_cyber","081_offensive_cyber_operations_front.png"),
 EnablerDef("083","Cyber Recon",_P,EnablerUse.MULTIPLE,False,False,True,"Reveal enablers = cyber rate.","cyber_recon","083_cyber_reconnaissance_front.png"),
 EnablerDef("092","Counter Space",_P,EnablerUse.SINGLE,True,False,False,"Reaction: Cancel US space card.","cancel_space","092_counter_space_front.png"),
 EnablerDef("095","Sea Dragon Strike",_P,EnablerUse.MULTIPLE,False,False,False,"Ship atk: Rng 3, 2+, exploding.","naval_strike","095_sea_dragons_strike_front.png"),
 EnablerDef("103","Standard Cyber",_P,EnablerUse.MULTIPLE,False,False,False,"Roll d4 >= access → +1 Cyber.","cyber_advance","103_standard_front.png"),
 EnablerDef("105","Attrition Cyber",_P,EnablerUse.MULTIPLE,False,False,False,"Roll d4 >= access → +1 Cyber.","cyber_advance","105_attrition_front.png"),
 EnablerDef("073","SOF Recon",_P,EnablerUse.SINGLE,False,False,False,"See opponent mission.","reveal_mission","073_sof_reconnaissance_front.png",is_sof=True),
 EnablerDef("098","SOF Recon 2",_P,EnablerUse.SINGLE,False,False,False,"Acquire any target, no range.","sof_acquire","098_sof_reconnaissance_front.png",is_sof=True),
]

# ── Missions ──
MISSIONS = [
 MissionDef("Attrition","BOTH","Destroy enemy assets.","+3 ship/bomber/ADA/AEW, +2 sqn card, +1 other"),
 MissionDef("Counter-Intervention","PRC","Destroy ground forces.","+3 fighter/drone ground, +3 bomber/AEW ground, +1 PLARF card"),
 MissionDef("Economy of Force","BOTH","Conserve forces.","+2 per unactivated unit per ATO"),
 MissionDef("Enforce Rule of Law","US","Project power.","+2 per sqn activated/turn, +1 per enabler token"),
 MissionDef("Interdiction","BOTH","Destroy high-value targets.","+4 bomber/AEW/sqn, +3 ship/ADA, +2 other"),
 MissionDef("Non-Kinetic Dominance","US","Dominate cyber/space.","3×Cyber VP/ATO, +1 per NK card"),
 MissionDef("Three Dominances","PRC","Multi-domain control.","2×Cyber VP/ATO, +3 naval, +1 naval enb, +1 intact sqn"),
]

# ── Postures ──
US_POS = [
 PostureDef("Standard",_U,6,5,"No restrictions.",True),
 PostureDef("ACE",_U,4,6,"Contingency auto-gen."),
 PostureDef("Hedgehog",_U,5,6,"All sqns to airbase."),
 PostureDef("Surge",_U,7,4,"More sqns, fewer enablers."),
]
PRC_POS = [
 PostureDef("Standard",_P,6,5,"No restrictions.",True),
 PostureDef("PLAAF",_P,5,6,"Enablers from PLAAF."),
 PostureDef("PLARF",_P,4,7,"Fewer sqns, more enablers."),
 PostureDef("Surge",_P,7,4,"More sqns, fewer enablers."),
]

# ── Campaigns ──
CAMPAIGNS = [
 CampaignDef("1: Meeting Engagement","Intro — 1 ATO, basic rules.",1,["Attrition"],["Standard"],"No enabler cards.","010","060"),
 CampaignDef("2: Tournament","Competitive 2-ATO.",2,["Attrition"],["Standard"],"Init bid ATO 1 only.","",""),
 CampaignDef("3: Prolonged Combat","5 ATOs, all resources.",5,["all"],["all"],"","",""),
 CampaignDef("4: The World Watches","Int'l opinion.",2,["all"],["all"],"+1 VP air kill (max +2/ATO). No long-range missiles/SOF/bomber sqns.","",""),
 CampaignDef("5: Reserves","Less capability.",2,["all"],["all"],"No 5th gen, no bombers, no long ADA (PRC).","",""),
]

CYBER_ACCESS = {0:2, 1:2, 2:3, 3:4}
