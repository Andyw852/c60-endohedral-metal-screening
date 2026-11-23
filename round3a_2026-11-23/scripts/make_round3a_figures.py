#!/usr/bin/env python3
"""Figures for the round-3a s-block report (2026-11-23)."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "data" / "round3a_summary.json").read_text())
PM = {r["metal"]: r for r in D["per_metal"]}
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)

ALK = ["Na", "K", "Rb", "Cs"]
AE = ["Ca", "Sr", "Ba"]


def fig_binding():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6), gridspec_kw={"width_ratios": [4.2, 1.1]})
    metals = ALK + AE
    x = np.arange(len(metals))
    w = 0.26
    keys = [("binding_iso", "isolated C60", "#8fbcd4"),
            ("binding_qHP", "qHP", "#2b8cbe"),
            ("binding_qTP2", "qTP2", "#e6a020")]
    for i, (k, lab, col) in enumerate(keys):
        vals = [PM[m].get(k, np.nan) for m in metals]
        ax1.bar(x + (i - 1) * w, vals, w, label=lab, color=col, edgecolor="k", linewidth=0.4)
    ax1.axhline(0, color="k", lw=1)
    ax1.set_xticks(x)
    ax1.set_xticklabels(metals)
    ax1.set_ylabel("binding energy vs bulk metal (eV per metal)")
    ax1.set_title("s-block metals in C60 and its 2D networks")
    ax1.legend(fontsize=8)
    ax1.grid(True, axis="y", alpha=0.3)
    ax1.set_ylim(-1.75, 0.35)
    ax1.text(0.02, 0.04, "negative = stable against bulk metal + empty host",
             transform=ax1.transAxes, fontsize=8)
    # Be panel
    be = PM["Be"]
    vals = [be.get("binding_iso"), be.get("binding_qHP"), be.get("binding_qTP2")]
    cols = ["#8fbcd4", "#2b8cbe", "#e6a020"]
    bars = ax2.bar(["iso", "qHP", "qTP2"], vals, color=cols, edgecolor="k", linewidth=0.4)
    ax2.axhline(0, color="k", lw=1)
    for b, v in zip(bars, vals):
        ax2.text(b.get_x() + b.get_width() / 2, v + 0.03, "%.2f" % v, ha="center", fontsize=8)
    ax2.set_ylim(3.3, 3.6)
    ax2.set_title("Be (separate scale)")
    ax2.set_ylabel("binding (eV)")
    fig.tight_layout()
    fig.savefig(OUT / "fig1_binding_s_block.png", dpi=180)
    plt.close(fig)


def fig_poly():
    metals = ALK + AE
    x = np.arange(len(metals))
    w = 0.36
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    vals1 = [PM[m].get("poly_qHP", np.nan) for m in metals]
    vals2 = [PM[m].get("poly_qTP2", np.nan) for m in metals]
    ax.bar(x - w / 2, vals1, w, label="qHP (per 2 cages)", color="#2b8cbe", edgecolor="k", linewidth=0.4)
    ax.bar(x + w / 2, vals2, w, label="qTP2 (per cage)", color="#e6a020", edgecolor="k", linewidth=0.4)
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(metals)
    ax.set_ylabel("change in polymerisation energy (eV)")
    ax.set_title("Endohedral metal effect on network stability (negative = stabilising)")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_polymerisation_s_block.png", dpi=180)
    plt.close(fig)


def fig_position():
    metals = ALK + AE + ["Be"]
    x = np.arange(len(metals))
    w = 0.26
    fig, ax = plt.subplots(figsize=(8.8, 4.2))
    keys = [("disp_iso", "isolated C60", "#8fbcd4"),
            ("disp_qHP", "qHP", "#2b8cbe"),
            ("disp_qTP2", "qTP2", "#e6a020")]
    for i, (k, lab, col) in enumerate(keys):
        vals = [PM[m].get(k, np.nan) for m in metals]
        ax.bar(x + (i - 1) * w, vals, w, label=lab, color=col, edgecolor="k", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(metals)
    ax.set_ylabel("metal displacement from the cage centre (A)")
    ax.set_title("Relaxed metal positions: a non-monotonic trend across the s block")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_metal_positions_s_block.png", dpi=180)
    plt.close(fig)


def fig_spin():
    rows = []
    for m in ["Be", "Ca", "Ba", "Sr"]:
        s = PM[m]
        rows.append((m, s["E_iso_triplet"] - s["E_iso_singlet"]))
    rows.sort(key=lambda t: t[1])
    labels = [m for m, _ in rows]
    vals = [v for _, v in rows]
    cols = ["#2b8cbe" if v > 0 else "#e6a020" for v in vals]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    bars = ax.bar(labels, vals, color=cols, edgecolor="k", linewidth=0.4)
    ax.axhline(0, color="k", lw=1)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + (0.008 if v >= 0 else -0.018),
                "%+.4f" % v, ha="center", fontsize=8)
    ax.set_ylabel("E(triplet) - E(singlet) of isolated M@C60 (eV)")
    ax.set_title("Spin-state ordering of the isolated cage (negative = triplet lower)")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_spin_states_s_block.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    fig_binding()
    fig_poly()
    fig_position()
    fig_spin()
    print("wrote figures to", OUT)
