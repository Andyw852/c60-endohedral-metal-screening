#!/usr/bin/env python3
"""Figures for the 2026-11-18 pilot report."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "data" / "pilot_summary.json").read_text())
cases = {c["case"]: c for c in D["cases"]}
der = D["derived"]

OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)


def fig_binding():
    labels = ["Li\nisolated C60", "Li\nqHP", "Li\nqTP2", "Mg\nisolated C60", "Mg\nqTP2"]
    vals = [der["binding_Li_isolated"], der["binding_Li_qHP"], der["binding_Li_qTP2"],
            der["binding_Mg_isolated_singlet"], der["binding_Mg_qTP2"]]
    cols = ["#2b8cbe", "#2b8cbe", "#2b8cbe", "#e6a020", "#e6a020"]
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    bars = ax.bar(labels, vals, color=cols, edgecolor="k", linewidth=0.5)
    ax.axhline(0, color="k", lw=1)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + (0.04 if v >= 0 else -0.10),
                "%+.3f" % v, ha="center", fontsize=9)
    ax.set_ylabel("binding energy vs bulk metal (eV per metal)")
    ax.set_title("Binding of one metal atom (positive = metastable vs bulk metal)")
    ax.set_ylim(min(vals) - 0.35, max(vals) + 0.35)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_binding_energies.png", dpi=180)
    plt.close(fig)


def fig_position():
    labels = ["Li\nisolated", "Mg singlet\nisolated", "Mg triplet\nisolated",
              "Li\nqHP", "Li\nqTP2", "Mg\nqTP2", "Mg\nqHP (incomplete)"]
    vals = [cases["01_isolated_C60_Li_inside"]["metal1_disp"],
            cases["02_isolated_C60_Mg_inside_0unpaired"]["metal1_disp"],
            cases["03_isolated_C60_Mg_inside_2unpaired"]["metal1_disp"],
            np.mean([cases["04_qHP_network_Li_inside_cage"]["metal1_disp"],
                     cases["04_qHP_network_Li_inside_cage"]["metal2_disp"]]),
            cases["06_qTP2_network_Li_inside_cage"]["metal1_disp"],
            cases["07_qTP2_network_Mg_inside_cage"]["metal1_disp"],
            np.mean([cases["05_qHP_network_Mg_inside_cage"]["metal1_disp"],
                     cases["05_qHP_network_Mg_inside_cage"]["metal2_disp"]])]
    cols = ["#2b8cbe", "#e6a020", "#e6a020", "#2b8cbe", "#2b8cbe", "#e6a020", "#bbbbbb"]
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    bars = ax.bar(labels, vals, color=cols, edgecolor="k", linewidth=0.5)
    bars[-1].set_hatch("//")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.03, "%.3f" % v, ha="center", fontsize=9)
    ax.set_ylabel("metal displacement from its cage centre (Angstrom)")
    ax.set_title("Relaxed metal position: Li moves off-centre, Mg stays near the centre")
    ax.set_ylim(0, max(vals) * 1.25)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_metal_positions.png", dpi=180)
    plt.close(fig)


def fig_poly():
    labels = ["Li in qHP\n(2 cages)", "Li in qTP2\n(1 cage)", "Mg in qTP2\n(1 cage)"]
    vals = [der["poly_Li_qHP"], der["poly_Li_qTP2"], der["poly_Mg_qTP2"]]
    cols = ["#2b8cbe", "#2b8cbe", "#e6a020"]
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    bars = ax.bar(labels, vals, color=cols, edgecolor="k", linewidth=0.5)
    ax.axhline(0, color="k", lw=1)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + (0.02 if v >= 0 else -0.05),
                "%+.3f" % v, ha="center", fontsize=9)
    ax.set_ylabel("change in polymerisation energy due to the metal (eV)")
    ax.set_title("Negative = endohedral metal makes the network more stable")
    ax.set_ylim(min(vals) - 0.13, max(vals) + 0.10)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_polymerisation_effect.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    fig_binding()
    fig_position()
    fig_poly()
    print("wrote figures to", OUT)
