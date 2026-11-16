#!/usr/bin/env python3
"""
make_figures.py
===============
Figures for the endohedral-C60 screening audit.

Inputs
------
  data/screening_summary.csv

Outputs
-------
  figures/fig1_force_convergence.png
  figures/fig2_symmetry_trap.png
  figures/fig3_scf_history.png

Usage
-----
  python scripts/make_figures.py
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent

COLORS = {
    "pass": "#2b8cbe",
    "pending": "#e6a020",
    "fail": "#c0392b",
}
LABELS = {
    "pass": "pass (20)",
    "pending": "pending (6)",
    "fail": "fail / cancelled / SCF-limited (6)",
}


def load():
    with open(ROOT / "data" / "screening_summary.csv") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for k in ("final_force_max_eVA", "metal_disp_from_start",
                  "n_ionic_steps", "n_scf_at_limit_steps",
                  "max_c_disp_from_start"):
            try:
                r[k] = float(r[k])
            except Exception:
                r[k] = np.nan
    return rows


def fig1(rows):
    order = sorted(rows, key=lambda r: r["final_force_max_eVA"])
    fig, ax = plt.subplots(figsize=(11, 4.6))
    x = np.arange(len(order))
    vals = [r["final_force_max_eVA"] for r in order]
    cols = [COLORS[r["source_classification"]] for r in order]
    bars = ax.bar(x, vals, color=cols, edgecolor="k", linewidth=0.4)
    ax.set_yscale("log")
    ax.axhline(0.02, color="k", ls="--", lw=1)
    ax.text(0.5, 0.0225, "EDIFFG = -0.02 eV/A (force threshold)", ha="left", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([r["metal"] for r in order], fontsize=8)
    ax.set_ylabel("final max force (eV/A)")
    ax.set_title("Final maximum force of the 32 centre-start M@C60 relaxations")
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLORS[k]) for k in ("pass", "pending", "fail")]
    ax.legend(handles, [LABELS[k] for k in ("pass", "pending", "fail")], fontsize=8, loc="upper left")
    ax.grid(True, axis="y", which="both", alpha=0.25)
    fig.tight_layout()
    out = ROOT / "figures" / "fig1_force_convergence.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    print("wrote", out)


def fig2(rows):
    order = sorted(rows, key=lambda r: r["metal_disp_from_start"])
    fig, ax = plt.subplots(figsize=(9.4, 7.2))
    y = np.arange(len(order))
    vals = [max(r["metal_disp_from_start"], 1e-15) for r in order]
    cols = [COLORS[r["source_classification"]] for r in order]
    ax.barh(y, vals, left=1e-15, color=cols, edgecolor="k", linewidth=0.35)
    ax.set_xscale("log")
    ax.set_xlim(1e-15, 2e-2)
    ax.axvline(0.01, color="k", ls="--", lw=1)
    ax.text(0.012, 0.5, "0.01 A", fontsize=8, rotation=90, va="bottom")
    ax.set_yticks(y)
    ax.set_yticklabels(
        [r["metal"] + "  (" + str(int(r["n_ionic_steps"])) + " steps)" for r in order],
        fontsize=7,
    )
    ax.set_xlabel("metal displacement from the cage centre (A, log scale)")
    ax.set_title("Largest displacement is 0.00093 A: the metal never leaves the centre")
    ax.grid(True, axis="x", alpha=0.3, which="both")
    fig.tight_layout()
    out = ROOT / "figures" / "fig2_symmetry_trap.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    print("wrote", out)


def fig3(rows):
    order = sorted(rows, key=lambda r: r["n_scf_at_limit_steps"], reverse=True)
    order = [r for r in order if r["n_scf_at_limit_steps"] > 0]
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    x = np.arange(len(order))
    ax.bar(x, [r["n_scf_at_limit_steps"] for r in order],
           color=[COLORS[r["source_classification"]] for r in order], edgecolor="k", linewidth=0.4)
    for i, r in enumerate(order):
        ax.text(i, r["n_scf_at_limit_steps"] + 0.3,
                "%d/%d" % (r["n_scf_at_limit_steps"], r["n_ionic_steps"]),
                ha="center", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([r["metal"] for r in order], fontsize=8)
    ax.set_ylabel("ionic steps with SCF at the NELM limit")
    ax.set_title("Electronic-convergence history (labels: SCF-limited / total ionic steps)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLORS[k]) for k in ("pass", "pending", "fail")]
    ax.legend(handles, [LABELS[k] for k in ("pass", "pending", "fail")], fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    out = ROOT / "figures" / "fig3_scf_history.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    print("wrote", out)


def fig4(rows):
    order = sorted(rows, key=lambda r: r["max_c_disp_from_start"])
    fig, ax = plt.subplots(figsize=(9.4, 7.2))
    y = np.arange(len(order))
    vals = [max(r["max_c_disp_from_start"], 1e-14) for r in order]
    cols = [COLORS[r["source_classification"]] for r in order]
    ax.barh(y, vals, left=1e-14, color=cols, edgecolor="k", linewidth=0.35)
    ax.set_xscale("log")
    ax.set_xlim(1e-14, 1.0)
    ax.axvline(0.026, color="k", ls="--", lw=1)
    ax.text(0.030, 0.5, "0.026 A = largest C displacement", fontsize=8, rotation=90, va="bottom")
    ax.set_yticks(y)
    ax.set_yticklabels([r["metal"] for r in order], fontsize=7)
    ax.set_xlabel("maximum carbon displacement from the starting geometry (A, log scale)")
    ax.set_title("Only a weak, totally symmetric cage breathing is sampled (max 0.026 A)")
    ax.grid(True, axis="x", alpha=0.3, which="both")
    fig.tight_layout()
    out = ROOT / "figures" / "fig4_cage_breathing.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    print("wrote", out)


def main():
    (ROOT / "figures").mkdir(exist_ok=True)
    rows = load()
    fig1(rows)
    fig2(rows)
    fig3(rows)
    fig4(rows)


if __name__ == "__main__":
    main()
