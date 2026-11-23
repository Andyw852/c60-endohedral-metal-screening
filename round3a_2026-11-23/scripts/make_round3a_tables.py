#!/usr/bin/env python3
"""Render the Markdown tables for the round-3a report."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "data" / "round3a_summary.json").read_text())
PM = {r["metal"]: r for r in D["per_metal"]}

ORDER = ["Na", "K", "Rb", "Cs", "Ca", "Sr", "Ba", "Be"]
NOTE = {
    "Na": "weakly stable; nearly centred",
    "K": "stable; off-centre 0.5 A",
    "Rb": "stable; off-centre 0.45 A",
    "Cs": "stable; centred; qHP run excluded (stalled)",
    "Ca": "stable, strongly favours qHP; off-centre 1.1-1.25 A",
    "Sr": "stable, strongly favours qHP; off-centre 1.0 A",
    "Ba": "most stable; off-centre 0.7 A",
    "Be": "strongly metastable vs bulk Be; singlet centred, triplet at 1.91 A",
}


def fmt(v, p=3, d="n/a"):
    return ("%." + str(p) + "f") % v if isinstance(v, (int, float)) else d


def per_metal_table():
    lines = []
    lines.append("| Metal | E_bulk/atom (eV) | best iso spin | binding iso (eV) | binding qHP (eV) | binding qTP2 (eV) | poly qHP (eV/2 cages) | poly qTP2 (eV/cage) | disp iso (A) | disp qHP (A) | disp qTP2 (A) | note |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for m in ORDER:
        s = PM[m]
        spin = "n/a"
        if s.get("iso_best_mag") == 0.0:
            spin = "singlet (0)"
        elif s.get("iso_best_mag") == 2.0:
            spin = "2 unpaired"
        elif s.get("iso_best_mag") == 1.0:
            spin = "doublet (1)"
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            m, fmt(s.get("E_bulk_per_atom"), 4), spin, fmt(s.get("binding_iso")),
            fmt(s.get("binding_qHP")), fmt(s.get("binding_qTP2")), fmt(s.get("poly_qHP")),
            fmt(s.get("poly_qTP2")), fmt(s.get("disp_iso")), fmt(s.get("disp_qHP")),
            fmt(s.get("disp_qTP2")), NOTE.get(m, "")))
    (ROOT / "data" / "round3a_per_metal.md").write_text("\n".join(lines) + "\n")
    return "\n".join(lines)


def case_table():
    lines = []
    lines.append("| Case | Complete | E(sigma->0) (eV) | Fmax (eV/A) | mag (uB) | N_ion | n_CC | bond max (A) | stress XX/YY (kB) | metal disp (A) | M-C min (A) |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for c in D["cases"]:
        disps = [c.get("metal1_disp"), c.get("metal2_disp")]
        disps = [d for d in disps if d is not None]
        disp = " / ".join("%.3f" % d for d in disps) if disps else "n/a"
        mcs = [c.get("metal1_mc_min"), c.get("metal2_mc_min")]
        mcs = [m for m in mcs if m is not None]
        mc = " / ".join("%.3f" % m for m in mcs) if mcs else "n/a"
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s / %s | %s | %s |" % (
            c["path"], "yes" if c.get("normal_end") else "**no**",
            fmt(c.get("energy_sigma0"), 5), fmt(c.get("fmax"), 4),
            fmt(c.get("final_mag"), 2), c.get("n_ionic", "n/a"), c.get("n_CC", "-"),
            fmt(c.get("bond_max")), fmt(c.get("stress_xx")), fmt(c.get("stress_yy")),
            disp, mc))
    (ROOT / "data" / "round3a_cases.md").write_text("\n".join(lines) + "\n")
    return "\n".join(lines)


if __name__ == "__main__":
    print(per_metal_table())
    print()
    case_table()
    print("wrote data/round3a_per_metal.md and data/round3a_cases.md")
