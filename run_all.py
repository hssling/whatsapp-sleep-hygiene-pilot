"""Reproduce every number, table and figure of the article from the de-identified data.

    python run_all.py

Writes results/results.json, results/tables/*.csv and results/figures/Figure 1-3 (.tif and .jpg).
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from sleeppilot import analysis, figures, tables  # noqa: E402


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if math.isnan(float(o)) else float(o)
    return o


def main():
    R, w = analysis.run()
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "results.json").write_text(json.dumps(clean(R), indent=2), encoding="utf-8")
    tables.write_all(R, out / "tables")
    figures.figure1(R, out / "figures")
    figures.figure2(w, out / "figures")
    figures.figure3(R, out / "figures")
    p = R["primary"]
    print(f"Primary: PSQI change {p['mean_diff']:.2f} (95% CI {p['ci_low']:.2f} to {p['ci_high']:.2f}), n = {p['n']}")
    print("Outputs written to", out)


if __name__ == "__main__":
    main()
