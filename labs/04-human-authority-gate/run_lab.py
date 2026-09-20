"""Run the frozen Lab 04 fixture matrix and write its compact report."""
from __future__ import annotations

import json
from pathlib import Path
import sys

LAB_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB_ROOT / "src"))

from human_authority_gate.runner import run_frozen_experiment


if __name__ == "__main__":
    result = run_frozen_experiment()
    output = LAB_ROOT / "results" / "measured_results.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(output)
