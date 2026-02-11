import csv
import hashlib
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OLD_TOKEN_MANIFEST = ROOT / "assets" / "token_manifest.json"
OLD_CARD_MANIFEST  = ROOT / "assets" / "card_manifest.json"   # if you make one later
MAP_CSV            = ROOT / "data" / "asset_rename_map.csv"

OUT_TOKENS_FRONT = ROOT / "assets" / "tokens" / "fronts"
OUT_TOKENS_BACK  = ROOT / "assets" / "tokens" / "backs"

def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_map(csv_path: Path):
    m = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m[(row["kind"].strip(), row["old"].strip())] = row["new"].strip()
    return m

def ensure_dirs():
    OUT_TOKENS_FRONT.mkdir(parents=True, exist_ok=True)
    OUT_TOKENS_BACK.mkdir(parents=True, exist_ok=True)

def main():
    ensure_dirs()
    rename_map = load_map(MAP_CSV)

    # Load existing token manifest produced by your extractor
    manifest = json.loads(OLD_TOKEN_MANIFEST.read_text(encoding="utf-8"))

    # 1) Dedupe all token FRONT images by content hash
    #    Keep one canonical file per unique image content.
    seen_hash_to_newpath = {}

    new_tokens = []
    for t in manifest["tokens"]:
        token_id = t["id"]             # e.g., "PRC_012"
        img_path = ROOT / t["image_path"]  # e.g., assets/tokens/PRC_012_front.png

        # What should this token be called?
        key = ("token", token_id)
        if key not in rename_map:
            raise SystemExit(f"Missing mapping for token id {token_id} in {MAP_CSV}")
        slug = rename_map[key]  # e.g., "prc_aew"

        h = file_hash(img_path)
        if h not in seen_hash_to_newpath:
            out_path = OUT_TOKENS_FRONT / f"{slug}.png"
            shutil.copy2(img_path, out_path)
            seen_hash_to_newpath[h] = out_path
        # else: duplicate image → do not copy again

        # Build cleaned token entry
        new_tokens.append({
            "id": token_id,
            "slug": slug,
            "side": t.get("side"),
            "front_image": str(seen_hash_to_newpath[h].relative_to(ROOT)).replace("\\", "/"),
            # Shared backs (no duplicates):
            "back_image": "assets/tokens/backs/prc_token_back.png" if t.get("side") == "PRC"
                         else "assets/tokens/backs/us_token_back.png",
        })

    # 2) Write a cleaned manifest your game uses going forward
    cleaned = {"tokens": new_tokens}
    out_manifest = ROOT / "assets" / "token_manifest_clean.json"
    out_manifest.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")
    print(f"Wrote {out_manifest}")

if __name__ == "__main__":
    main()
