#!/usr/bin/env python3
"""Render the Markdown run table for the round-2 report."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "data" / "round2_summary.json").read_text())

NOTES = {
    "13_qHP_network_Mg_inside_cage_restart_nonmagnetic": "ground state; both Mg centred",
    "14_qHP_network_Mg_inside_cage_restart_2unpaired": "+65 meV above 13; both Mg centred",
    "15_isolated_C60_Li_cation_inside_check": "closed-shell cation; Li+ off-centre",
}

lines = []
lines.append("| Case | Complete | E(sigma->0) (eV) | Fmax (eV/A) | mag (uB) | n_ion | SCF@NELM | metal disp (A) | M-C min (A) | n_CC | stress XX/YY (kB) | Note |")
lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")

def fmt(v, p=3, d="n/a"):
    return ("%." + str(p) + "f") % v if isinstance(v, (int, float)) else d

for c in D["cases"]:
    disps = [c.get("metal1_disp"), c.get("metal2_disp")]
    disps = [d for d in disps if d is not None]
    disp = " / ".join("%.3f" % d for d in disps) if disps else "n/a"
    mcs = [c.get("metal1_mc_min"), c.get("metal2_mc_min")]
    mcs = [m for m in mcs if m is not None]
    mc = " / ".join("%.3f" % m for m in mcs) if mcs else "n/a"
    lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s / %s | %s |" % (
        c["case"], "yes" if c.get("normal_end") else "**no**",
        fmt(c.get("energy_sigma0"), 5), fmt(c.get("fmax"), 4),
        fmt(c.get("final_mag"), 2), c.get("n_ionic", "n/a"), c.get("n_scf_at_nelm", "n/a"),
        disp, mc, c.get("n_CC", "-"), fmt(c.get("stress_xx"), 3), fmt(c.get("stress_yy"), 3),
        NOTES.get(c["case"], "")))

(ROOT / "data" / "round2_table.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
