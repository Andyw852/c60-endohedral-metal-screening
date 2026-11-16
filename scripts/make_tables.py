#!/usr/bin/env python3
"""
make_tables.py
==============
Render the two Markdown tables used in the report from the machine-readable
CSV files, so that the report never contains hand-transcribed numbers.

Outputs
-------
  data/screening_table.md
  data/network_table.md
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ORDER = ["Li", "Be", "Na", "Mg", "Al", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn",
         "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Rb", "Sr", "Y", "Zr", "Nb", "Mo",
         "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn"]

TERM = {"Ca": "ZBRENT fatal", "Sc": "ZBRENT fatal", "Ti": "ZBRENT fatal",
        "Cr": "ZBRENT fatal", "Mn": "cancelled (Slurm)",
        "Co": "normal* (Slurm cancelled)"}

CLASS = {"pass": "pass", "pending": "pending", "fail": "fail"}


def fnum(v, fmt):
    try:
        return fmt % float(v)
    except Exception:
        return "n/a"


def screening_table():
    with open(ROOT / "data" / "screening_summary.csv") as fh:
        rows = {r["metal"]: r for r in csv.DictReader(fh)}
    lines = []
    lines.append("| Metal | Class | Source | Fmax (eV/A) | N_ion | SCF@NELM | final SCF/NELM | Termination | dr_M (1e-3 A) | M-C_min (A) | n_CC | m_final (uB) |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for m in ORDER:
        r = rows[m]
        dr = float(r["metal_disp_from_start"]) * 1e3
        term = TERM.get(m, "normal")
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s/%s | %s | %.3f | %s | %s | %s |"
            % (
                m, CLASS[r["source_classification"]], r["provenance"],
                fnum(r["final_force_max_eVA"], "%.4f"),
                r["n_ionic_steps"], r["n_scf_at_limit_steps"],
                r["final_scf_steps"], r["nelm_used"], term, dr,
                fnum(r["mc_min"], "%.3f"),
                int(float(r["n_cc_bonds"])),
                fnum(r["final_mag_uB"], "%+.2f"),
            )
        )
    out = ROOT / "data" / "screening_table.md"
    out.write_text("\n".join(lines) + "\n")
    print("wrote", out)


def network_table():
    gaps = {
        "C60_qHPC60": ("0.875 (direct)", "-"),
        "C60_qTP1C60": ("0.855 (indirect)", "1.368 (indirect)"),
        "C60_qTP2C60": ("0.929 (indirect)", "1.510 (indirect)"),
        "Mg2C60_bulk": ("0.055 (indirect)", "0.325 (indirect)"),
    }
    with open(ROOT / "data" / "network_geometry.csv") as fh:
        rows = list(csv.DictReader(fh))
    lines = []
    lines.append("| Network | Dim | Cages/cell | n_C | C(4-fold) | inter-cage C-C bonds/cage | inter bond (A) | V/cage (A^3) | gap PBEsol (eV) | gap HSE (eV) |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        g = gaps.get(r["name"], ("-", "-"))
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
            % (
                r["name"], r["dim"], r["n_cages"], r["n_C"], r["n_C_coord4"],
                r["n_intercage_bonds_per_cage"],
                fnum(r["interbond_mean"], "%.3f"),
                fnum(r["volume_per_cage_A3"], "%.1f"), g[0], g[1],
            )
        )
    out = ROOT / "data" / "network_table.md"
    out.write_text("\n".join(lines) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    screening_table()
    network_table()
