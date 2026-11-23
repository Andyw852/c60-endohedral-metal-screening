#!/usr/bin/env python3
"""
analyze_round3a.py
==================
Analyse the round-3a s-block campaign (2026-11-23): Ba, Be, Ca, Cs, K, Na, Rb, Sr
inside isolated C60, the qHP network and the qTP2 network, plus bulk references.

The parsers and geometry helpers are shared with the pilot script. Reference energies
(C60, qHP, qTP2) come from the pilot summary, which used identical settings.

Writes data/round3a_cases.csv, data/round3a_per_metal.csv and data/round3a_summary.json.
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


def parse_case(d, metal, kind, rel):
    row = dict(path=rel, metal=metal, kind=kind)
    inc = ap.parse_incar(d / "INCAR")
    row["ispin"] = inc.get("ISPIN")
    row["nupdown"] = inc.get("NUPDOWN")
    row["kpar"] = inc.get("KPAR")
    row["ivdw"] = inc.get("IVDW")
    row["sigma"] = inc.get("SIGMA")
    nelm = int(float(inc.get("NELM", 200)))
    steps, nlimit = ap.parse_oszicar(ap.read_text(d / "OSZICAR"), nelm) if (d / "OSZICAR").exists() else ([], 0)
    row["n_ionic"] = len(steps)
    row["n_scf_at_nelm"] = nlimit
    if steps:
        row["final_elec"] = steps[-1]["elec"]
        row["final_mag"] = steps[-1]["mag"]
    outcar = d / "OUTCAR"
    if not outcar.exists() and (d / "OUTCAR.gz").exists():
        outcar = d / "OUTCAR.gz"
    out = ap.parse_outcar(ap.read_text(outcar))
    row.update(normal_end=out["normal_end"], zbrent=out["zbrent"],
               energy_sigma0=out["energy_sigma0"], fmax=out["fmax"],
               nelect=out["nelect"], nkpts=out["nkpts"])
    if out["stress"]:
        row["stress_xx"] = out["stress"][0]
        row["stress_yy"] = out["stress"][1]
        row["stress_zz"] = out["stress"][2]
    if (d / "CONTCAR").exists():
        lat, sp, cnt, cart, blocks = ap.read_structure(d / "CONTCAR")
        row["species"] = "".join(sp)
        row["counts"] = "/".join(str(c) for c in cnt)
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
            for metal_name in metals:
                for m in blocks[metal_name]:
                    env = ap.metal_environment(C, lat, m, 60)
                    mi += 1
                    for k, v in env.items():
                        row["metal%d_%s" % (mi, k)] = v
                    row["metal%d_species" % mi] = metal_name
    return row


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROUND / "calculations"
    outdir = ROUND / "data"
    outdir.mkdir(exist_ok=True)
    pilot = json.loads((REPO / "pilot_2026-11-18" / "data" / "pilot_summary.json").read_text())
    der = pilot["derived"]
    e_ref_c60 = der["E_REF_isolated_C60"]
    e_ref_qhp = der["E_REF_qHP"]
    e_ref_qtp2 = der["E_REF_qTP2"]

    cases = []
    for mdir in sorted([p for p in root.iterdir() if p.is_dir()]):
        metal = mdir.name
        for d in sorted([p for p in mdir.iterdir() if p.is_dir()]):
            name = d.name
            if name.startswith("0_REF"):
                kind = "bulk"
            elif name.startswith("1_isolated"):
                kind = "iso"
            elif "qHP" in name:
                kind = "qHP"
            elif "qTP2" in name:
                kind = "qTP2"
            else:
                kind = "other"
            rel = "%s/%s" % (metal, name)
            cases.append(parse_case(d, metal, kind, rel))

    metals = sorted(set(c["metal"] for c in cases))
    per_metal = []
    for M in metals:
        rr = [c for c in cases if c["metal"] == M]
        bulk = next((c for c in rr if c["kind"] == "bulk"), None)
        iso_all = [c for c in rr if c["kind"] == "iso"]
        iso = min(iso_all, key=lambda c: c["energy_sigma0"]) if iso_all else None
        qhp = next((c for c in rr if c["kind"] == "qHP"), None)
        qtp2 = next((c for c in rr if c["kind"] == "qTP2"), None)
        s = dict(metal=M)
        s["n_bulk_atoms"] = bulk["natoms"] if bulk else None
        s["E_bulk_total"] = bulk["energy_sigma0"] if bulk else None
        s["E_bulk_per_atom"] = (bulk["energy_sigma0"] / bulk["natoms"]) if bulk else None
        s["bulk_a"] = bulk.get("cell_a") if bulk else None
        s["bulk_b"] = bulk.get("cell_b") if bulk else None
        s["bulk_c"] = bulk.get("cell_c") if bulk else None
        s["bulk_stress_xx"] = bulk.get("stress_xx") if bulk else None
        s["iso_variants"] = len(iso_all)
        s["E_iso_best"] = iso["energy_sigma0"] if iso else None
        s["iso_best_mag"] = iso.get("final_mag") if iso else None
        for c in iso_all:
            mag = c.get("final_mag")
            tag = "singlet" if mag == 0.0 else ("triplet" if mag == 2.0 else "other")
            s["E_iso_" + tag] = c["energy_sigma0"]
        if len(iso_all) == 2:
            s["iso_spin_splitting"] = s.get("E_iso_triplet", 0) - s.get("E_iso_singlet", 0)
        s["E_qHP"] = qhp["energy_sigma0"] if qhp else None
        s["E_qTP2"] = qtp2["energy_sigma0"] if qtp2 else None
        s["qHP_available"] = qhp is not None
        if s["E_bulk_per_atom"] is not None and iso is not None:
            s["binding_iso"] = s["E_iso_best"] - e_ref_c60 - s["E_bulk_per_atom"]
            e_iso_rel = s["E_iso_best"] - e_ref_c60
        else:
            e_iso_rel = None
        if qhp is not None and s["E_bulk_per_atom"] is not None:
            s["binding_qHP"] = (s["E_qHP"] - e_ref_qhp - 2 * s["E_bulk_per_atom"]) / 2
            s["poly_qHP"] = (s["E_qHP"] - e_ref_qhp) - 2 * e_iso_rel
        if qtp2 is not None and s["E_bulk_per_atom"] is not None:
            s["binding_qTP2"] = s["E_qTP2"] - e_ref_qtp2 - s["E_bulk_per_atom"]
            s["poly_qTP2"] = (s["E_qTP2"] - e_ref_qtp2) - e_iso_rel
        for c in rr:
            if c["kind"] == "iso" and (iso is None or c["path"] != iso["path"]):
                continue
            if c["kind"] in ("iso", "qHP", "qTP2"):
                for tag in ("disp", "mc_min"):
                    vals = [c.get("metal1_" + tag), c.get("metal2_" + tag)]
                    vals = [v for v in vals if v is not None]
                    if vals:
                        s["%s_%s" % (tag, c["kind"])] = float(np.mean(vals))
                s["inside_%s" % c["kind"]] = bool(c.get("metal1_inside"))
        per_metal.append(s)

    # ---- write ----------------------------------------------------------
    def write_csv(path, rows, fields):
        with open(path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow(r)

    fields = []
    for r in cases:
        for k in r:
            if k not in fields:
                fields.append(k)
    write_csv(outdir / "round3a_cases.csv", cases, fields)
    pfields = []
    for r in per_metal:
        for k in r:
            if k not in pfields:
                pfields.append(k)
    write_csv(outdir / "round3a_per_metal.csv", per_metal, pfields)
    with open(outdir / "round3a_summary.json", "w") as fh:
        json.dump(dict(cases=cases, per_metal=per_metal,
                       references=dict(E_REF_C60=e_ref_c60, E_REF_qHP=e_ref_qhp, E_REF_qTP2=e_ref_qtp2)),
                  fh, indent=2)

    print("M    Ebulk/at    binding iso   binding qHP   binding qTP2   poly qHP   poly qTP2   disp iso  disp qHP  disp qTP2")
    for s in per_metal:
        def f(v, fmt="% .3f"):
            return fmt % v if isinstance(v, (int, float)) else "  n/a"
        print("%-4s %s %s %s %s %s %s %s %s %s" % (
            s["metal"], f(s.get("E_bulk_per_atom"), "% .4f"), f(s.get("binding_iso")),
            f(s.get("binding_qHP")), f(s.get("binding_qTP2")), f(s.get("poly_qHP")),
            f(s.get("poly_qTP2")), f(s.get("disp_iso")), f(s.get("disp_qHP")), f(s.get("disp_qTP2"))))
    print("\nwrote", outdir / "round3a_cases.csv", "and", outdir / "round3a_per_metal.csv")


if __name__ == "__main__":
    main()
