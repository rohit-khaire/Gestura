"""Add new signs to the project in one step.

    python src/utils/add_signs.py stop yes good ok water

Appends the names to ``src/config.json`` (classes + a display colour each) and updates
``ACTIVE_SIGNS`` in ``Frontend/src/lib/phrases.js`` so both sides stay in sync. New signs are always
APPENDED - the order is the class-id order of your trained weights, so never reorder existing ones.

IMPORTANT: after this the old weights no longer match config.json. Collect + label data for the
new signs, then fine-tune with ``python src/train.py --resume pretrained/4426_model.pt --expand-head``
(see docs/ADD_SIGNS.md). Don't deploy the new config without the new weights.
"""

import argparse
import json
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
CONFIG = SRC / "config.json"
PHRASES_JS = SRC.parents[1] / "Frontend" / "src" / "lib" / "phrases.js"

# Distinct, readable colours (RGB) handed out to new signs in turn.
PALETTE = [
    [235, 87, 87], [155, 81, 224], [47, 128, 237], [242, 201, 76],
    [39, 174, 96], [86, 204, 242], [242, 153, 74], [233, 30, 99],
    [0, 150, 136], [121, 85, 72],
]
ACTIVE_RE = re.compile(r"export const ACTIVE_SIGNS = \[[^\]]*\];")


def normalise(name: str) -> str:
    """'Thumbs Up' -> 'thumbsup' (lower-case letters and digits only, matching the existing labels)."""
    cleaned = re.sub(r"[^a-z0-9]", "", name.lower())
    if not cleaned:
        raise ValueError(f"{name!r} is not a usable sign name")
    return cleaned


def add_signs(names, config_path=CONFIG, phrases_path=PHRASES_JS) -> dict:
    config_path = Path(config_path)
    config = json.loads(config_path.read_text())
    classes, colors = list(config["classes"]), [list(c) for c in config["colors"]]

    added = []
    for name in map(normalise, names):
        if name in classes or name in added:
            continue
        added.append(name)
        classes.append(name)
        colors.append(PALETTE[(len(classes) - 1) % len(PALETTE)])

    result = {"added": added, "classes": classes, "missing_translations": [], "frontend_updated": False}
    if not added:
        return result

    config_path.write_text(json.dumps({"classes": classes, "colors": colors}, indent=2) + "\n")

    phrases_path = Path(phrases_path)
    if phrases_path.exists():
        source = phrases_path.read_text()
        if ACTIVE_RE.search(source):
            literal = "[" + ", ".join(json.dumps(c) for c in classes) + "]"
            phrases_path.write_text(ACTIVE_RE.sub(lambda _: f"export const ACTIVE_SIGNS = {literal};", source, count=1))
            result["frontend_updated"] = True
        result["missing_translations"] = [
            n for n in added if not re.search(rf"^\s*{re.escape(n)}\s*:\s*\{{", source, re.MULTILINE)
        ]
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("names", nargs="+", help="sign names, e.g. stop yes good")
    args = p.parse_args()

    result = add_signs(args.names)
    if not result["added"]:
        print("Nothing to add - those signs are already in config.json.")
        return
    print(f"Added {len(result['added'])} sign(s): {', '.join(result['added'])}")
    print(f"Classes now ({len(result['classes'])}): {', '.join(result['classes'])}")
    print("Frontend ACTIVE_SIGNS updated." if result["frontend_updated"]
          else f"Could not find ACTIVE_SIGNS in {PHRASES_JS} - edit it by hand to match.")
    if result["missing_translations"]:
        print("Add translations in Frontend/src/lib/phrases.js (PHRASES) for: "
              + ", ".join(result["missing_translations"]))
    print("Next: collect + label images, then train with --resume ... --expand-head (docs/ADD_SIGNS.md).")


if __name__ == "__main__":
    main()
