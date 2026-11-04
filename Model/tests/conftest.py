import sys
from pathlib import Path

# The code in src/ uses flat imports (`from model import DETR`), so put it on the path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
