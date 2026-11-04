"""Class names and display colours, read from ``src/config.json``.

The path is resolved relative to this file, so it works from any working directory.
"""

import json
from functools import lru_cache
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.json"


@lru_cache(maxsize=1)
def _load_config() -> dict:
    with CONFIG_PATH.open() as f:
        return json.load(f)


def get_classes() -> list[str]:
    classes = _load_config().get("classes", [])
    if not classes:
        raise ValueError(
            f'No classes found in {CONFIG_PATH}. Example: {{"classes": ["hello", "iloveyou"]}}'
        )
    return list(classes)


def get_colors() -> list[list[int]]:
    """One RGB colour per class (same order as ``get_classes``)."""
    classes = get_classes()
    colors = _load_config().get("colors", [])
    if len(colors) != len(classes):
        raise ValueError(
            f"Please specify one colour per class in {CONFIG_PATH}: "
            f"{len(colors)} colours for {len(classes)} classes."
        )
    return [list(c) for c in colors]


if __name__ == "__main__":
    print(get_classes())
