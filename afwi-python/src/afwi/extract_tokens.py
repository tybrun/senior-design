import os
from .loaders import extract_token_images_and_manifest

def main() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    xlsx_path = os.path.join(root, "data", "AFWI_TOKENS_PRINT_N_PLAY.xlsx")
    out_tokens_dir = os.path.join(root, "assets", "tokens")
    out_manifest_path = os.path.join(root, "assets", "token_manifest.json")

    manifest = extract_token_images_and_manifest(xlsx_path, out_tokens_dir, out_manifest_path)
    print(f"Extracted {len(manifest['tokens'])} token images.")
    print(f"Tokens dir: {out_tokens_dir}")
    print(f"Manifest:   {out_manifest_path}")

if __name__ == "__main__":
    main()
