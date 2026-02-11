import json
import os
import hashlib
from typing import Any, Dict

import openpyxl


def extract_token_images_and_manifest(xlsx_path: str, out_tokens_dir: str, out_manifest_path: str) -> dict:
    """Extract embedded token images from the print-n-play XLSX.

    It writes PNGs into out_tokens_dir and creates a manifest JSON like:
    {"tokens": [{"id": "US_001", "side": "US", "image_path": "assets/tokens/...png"}, ...]}

    NOTE: the XLSX does NOT contain the token stats as text, so stats come from token_stats.json.
    """

    os.makedirs(out_tokens_dir, exist_ok=True)

    wb = openpyxl.load_workbook(xlsx_path)
    manifest = {"tokens": []}

    for sheet_name, side in [("BLUE", "US"), ("RED", "PRC")]:
        if sheet_name not in wb.sheetnames:
            continue

        ws = wb[sheet_name]
        images = getattr(ws, "_images", [])
        for idx, img in enumerate(images, start=1):
            data = img._data()
            sha = hashlib.sha1(data).hexdigest()[:10]
            filename = f"{side.lower()}_{idx:03d}_{sha}.png"
            rel_path = os.path.join("assets", "tokens", filename)
            abs_path = os.path.join(out_tokens_dir, filename)

            with open(abs_path, "wb") as f:
                f.write(data)

            token_id = f"{side}_{idx:03d}"
            manifest["tokens"].append(
                {
                    "id": token_id,
                    "name": token_id,  # placeholder; you can rename later
                    "side": side,
                    "image_path": rel_path,
                }
            )

    with open(out_manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_token_manifest(manifest_path: str) -> dict:
    return load_json(manifest_path)


def load_token_stats(stats_path: str) -> dict:
    """Loads your hand-entered token stats.

    Format:
    {
      "tokens": {
        "US_001": {"name": "F-22", "category": "FIGHTER_5G", "move": 2, ...},
        "PRC_005": {...}
      }
    }
    """
    if not os.path.exists(stats_path):
        # allow the game to run even before you've created token_stats.json
        return {"tokens": {}}
    return load_json(stats_path)
