#!/usr/bin/env python3
"""Figures for the round-2 report (2026-11-19)."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
D = json.loads((ROOT / "data" / "round2_summary.json").read_text())
P = json.loads((REPO / "pilot_2026-11-18" / "data" / "pilot_summary.json").read_text())
der = P["derived"]
r2 = D["derived"]
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)


def fig_binding():
    labels = ["Li\nisolated C60", "Li\nqHP", "Li\nqTP2",
              "Mg\nisolated C60", "Mg\nqHP", "Mg\nqTP2"]
    vals = [der["binding_Li_isolated"], der["binding_Li_qHP"], der["binding_Li_qTP2"],
            der["binding_Mg_isolated_singlet"], r2["binding_qHP_Mg_nonmagnetic"],
            der["binding_Mg_qTP2"]]
    cols = ["#2b8cbe", "#2b8cbe", "#2b8cbe", "#e6a020", "#e6a020", "#e6a020"]
    fig, ax = plt.subplots(figsize=(8.4, 4.3))
    bars = ax.bar(labels, vals, color=cols, edgecolor="k", linewidth=0.5)
    ax.axhline(0, color="k", lw=1)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + (0.04 if v >= 0 else -0.10),
                "%+.3f" % v, ha="center", fontsize=9)
    ax.set_ylabel("binding energy vs bulk metal (eV per metal)")
    ax.set_title("Updated binding energies: Li and Mg in C60, qHP and qTP2")
    ax.set_ylim(min(vals) - 0.35, max(vals) + 0.35)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_binding_all_hosts.png", dpi=180)
    plt.close(fig)


def fig_poly():
    labels = ["Li in qHP", "Li in qTP2", "Mg in qHP", "Mg in qTP2"]
    vals = [der["poly_Li_qHP"], der["poly_Li_qTP2"],
            r2["poly_effect_qHP_Mg_nonmagnetic"], der["poly_Mg_qTP2"]]
    cols = ["#2b8cbe", "#2b8cbe", "#e6a020", "#e6a020"]
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    bars = ax.bar(labels, vals, color=cols, edgecolor="k", linewidth=0.5)
    ax.axhline(0, color="k", lw=1)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + (0.02 if v >= 0 else -0.05),
                "%+.3f" % v, ha="center", fontsize=9)
    ax.set_ylabel("change in polymerisation energy (eV)")
    ax.set_title("Endohedral metal effect on network stability")
    ax.set_ylim(min(vals) - 0.13, max(vals) + 0.10)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_polymerisation_effects.png", dpi=180)
    plt.close(fig)


def fig_spin():
    labels = ["non-magnetic\n(ISPIN = 1)", "2 unpaired\n(NUPDOWN = 2)"]
    vals = [0.0, r2["E14_minus_E13"]]
    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    bars = ax.bar(labels, vals, color=["#2b8cbe", "#c0392b"], edgecolor="k", linewidth=0.5)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.003, "%.4f eV" % v, ha="center", fontsize=9)
    ax.set_ylabel("energy relative to the non-magnetic state (eV)")
    ax.set_title("qHP + 2 Mg: non-magnetic ground state")
    ax.set_ylim(0, max(vals) * 1.35)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_qhp_mg_spin_states.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    fig_binding()
    fig_poly()
    fig_spin()
    print("wrote figures to", OUT)
