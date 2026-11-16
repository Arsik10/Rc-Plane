"""Shared helpers: load the design that the calculator produced."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_design():
    path = ROOT / "sizing" / "design.json"
    if not path.exists():
        from sizing import design_calc
        design_calc.main()
    return json.loads(path.read_text())
