#!/usr/bin/env python3
"""
analyze_round2.py
=================
Analyse the three round-2 runs (2026-11-19):
  13  qHP Mg restart, non-magnetic
  14  qHP Mg restart, NUPDOWN = 2
  15  [Li@C60]+ cation check

The parser and geometry helpers are imported from the pilot analysis script so that
both rounds use identical definitions. Reference energies come from the pilot summary.

Usage:
    python scripts/analyze_round2.py [calculations]
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
ROUND = HERE.parent.parent
REPO = ROUND.parent
sys.path.insert(0, str(REPO / "pilot_2026-11-18" / "scripts"))
import analyze_pilot as ap


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROUND / "calculations"
    outdir = ROUND / "data"
    outdir.mkdir(exist_ok=True)
    pilot = json.loads((REPO / "pilot_2026-11-18" / "data" / "pilot_summary.json").read_text())
    der = pilot["derived"]
    pcase = {c["case"]: c for c in pilot["cases"]}
    e_ref_c60 = der["E_REF_isolated_C60"]
    e_ref_qhp = der["E_REF_qHP"]
    e_bulk_mg = der["E_bulk_Mg_per_atom"]
    e_bulk_li = der["E_bulk_Li_per_atom"]
    e_mg_iso = pcase["02_isolated_C60_Mg_inside_0unpaired"]["energy_sigma0"]

    rows = []
    for d in sorted([p for p in root.iterdir() if p.is_dir()]):
        row = dict(case=d.name)
        inc = ap.parse_incar(d / "INCAR")
        row["ispin"] = inc.get("ISPIN")
        row["nupdown"] = inc.get("NUPDOWN")
        row["nelect_in"] = inc.get("NELECT")
        row["kpar"] = inc.get("KPAR")
        row["sigma"] = inc.get("SIGMA")
        nelm = int(float(inc.get("NELM", 200)))
        steps, nlimit = ap.parse_oszicar(ap.read_text(d / "OSZICAR"), nelm)
        row["n_ionic"] = len(steps)
        row["n_scf_at_nelm"] = nlimit
        if steps:
            row["final_elec"] = steps[-1]["elec"]
            row["final_mag"] = steps[-1]["mag"]
        outcar = d / "OUTCAR"
        if not outcar.exists() and (d / "OUTCAR.gz").exists():
            outcar = d / "OUTCAR.gz"
        out = ap.parse_outcar(ap.read_text(outcar))
        row["normal_end"] = out["normal_end"]
        row["zbrent"] = out["zbrent"]
        row["energy_sigma0"] = out["energy_sigma0"]
        row["fmax"] = out["fmax"]
        row["nelect"] = out["nelect"]
        row["nkpts"] = out["nkpts"]
        if out["stress"]:
            row["stress_xx"] = out["stress"][0]
            row["stress_yy"] = out["stress"][1]
            row["stress_zz"] = out["stress"][2]
        if (d / "CONTCAR").exists():
            lat, sp, cnt, cart, blocks = ap.read_structure(d / "CONTCAR")
            row["species"] = "".join(sp)
            row["natoms"] = len(cart)
            for i, name in enumerate(("a", "b", "c")):
                row["cell_" + name] = float(np.linalg.norm(lat[i]))
            C = blocks.get("C")
            if C is not None:
                nb, coord, lens = ap.carbon_network(C, lat)
                row["n_CC"] = nb
                row["coord_min"] = int(coord.min())
                row["coord_max"] = int(coord.max())
                row["n_coord4"] = int((coord == 4).sum())
                row["n_coord2"] = int((coord == 2).sum())
                row["bond_max"] = float(lens.max()) if len(lens) else None
                metals = [s for s in sp if s != "C"]
                mi = 0
                for metal in metals:
                    for m in blocks[metal]:
                        env = ap.metal_environment(C, lat, m, 60)
                        mi += 1
                        for k, v in env.items():
                            row["metal%d_%s" % (mi, k)] = v
                        row["metal%d_species" % mi] = metal
        rows.append(row)

    by = {r["case"]: r for r in rows}
    e13 = by["13_qHP_network_Mg_inside_cage_restart_nonmagnetic"]["energy_sigma0"]
    e14 = by["14_qHP_network_Mg_inside_cage_restart_2unpaired"]["energy_sigma0"]
    e15 = by["15_isolated_C60_Li_cation_inside_check"]["energy_sigma0"]

    derived = dict(
        E13_qHP_Mg_nonmagnetic=e13,
        E14_qHP_Mg_2unpaired=e14,
        E14_minus_E13=e14 - e13,
        binding_qHP_Mg_nonmagnetic=(e13 - e_ref_qhp - 2 * e_bulk_mg) / 2,
        binding_qHP_Mg_2unpaired=(e14 - e_ref_qhp - 2 * e_bulk_mg) / 2,
        poly_effect_qHP_Mg_nonmagnetic=(e13 - e_ref_qhp) - 2 * (e_mg_iso - e_ref_c60),
        poly_effect_qHP_Mg_2unpaired=(e14 - e_ref_qhp) - 2 * (e_mg_iso - e_ref_c60),
        E15_Li_cation=e15,
        E15_minus_E_REF_C60=e15 - e_ref_c60,
        E15_minus_E_neutral_Li_at_C60=e15 - pcase["01_isolated_C60_Li_inside"]["energy_sigma0"],
    )

    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with open(outdir / "round2_summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    with open(outdir / "round2_summary.json", "w") as fh:
        json.dump(dict(cases=rows, derived=derived), fh, indent=2)

    for r in rows:
        print("%-55s end=%-5s E=%-15s Fmax=%-8s mag=%-6s nCC=%s" % (
            r["case"], r.get("normal_end"), r.get("energy_sigma0"), r.get("fmax"),
            r.get("final_mag"), r.get("n_CC")))
    print("\nDerived:")
    for k, v in derived.items():
        print("  %-40s % .6f" % (k, v))
    print("\nwrote", outdir / "round2_summary.csv")


if __name__ == "__main__":
    main()
