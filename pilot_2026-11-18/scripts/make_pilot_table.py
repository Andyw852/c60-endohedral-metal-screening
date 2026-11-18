#!/usr/bin/env python3
"""Render the Markdown run table for the 2026-11-18 pilot report."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "data" / "pilot_summary.json").read_text())

lines = []
lines.append("| Case | Complete | E(sigma->0) (eV) | Fmax (eV/A) | mag (uB) | n_ion | SCF@NELM | metal disp (A) | M-C min (A) | n_CC | stress XX/YY (kB) |")
lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
for c in D["cases"]:
    name = c["case"]
    comp = "yes" if c.get("normal_end") else "**no**"
    e = c.get("energy_sigma0")
    f = c.get("fmax")
    mag = c.get("final_mag")
    ni = c.get("n_ionic")
    scf = c.get("n_scf_at_nelm")
    disp = c.get("metal1_disp")
    mc = c.get("metal1_mc_min")
    ncc = c.get("n_CC")
    sx = c.get("stress_xx"); sy = c.get("stress_yy")
    def fmt(v, p=3, d="n/a"):
        return ("%." + str(p) + "f") % v if isinstance(v, (int, float)) else d
    lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s / %s |" % (
        name, comp, fmt(e, 5), fmt(f, 4), fmt(mag, 3),
        ni if ni is not None else "n/a", scf if scf is not None else "n/a",
        fmt(disp, 3), fmt(mc, 3), ncc if ncc is not None else "-",
        fmt(sx, 3), fmt(sy, 3)))
(ROOT / "data" / "pilot_table.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
