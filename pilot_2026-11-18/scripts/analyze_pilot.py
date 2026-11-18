#!/usr/bin/env python3
"""
analyze_pilot.py
================
Analyse the 2026-11-18 pilot VASP runs: Li and Mg inside isolated C60, qHP and qTP2
networks, plus the reference calculations.

Writes data/pilot_summary.csv and data/pilot_summary.json next to this repo folder.

Usage:
    python scripts/analyze_pilot.py <path-to-pilot-folder>
The pilot folder must contain one sub-directory per case with INCAR, POSCAR,
OSZICAR, OUTCAR and (for successful runs) CONTCAR.
"""
import csv
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np

try:
    from scipy.spatial import ConvexHull
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False


def read_text(path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", errors="replace").read()
    return path.read_text(errors="replace")


def parse_incar(path):
    d = {}
    for line in read_text(path).splitlines():
        line = line.split("!")[0].split("#")[0].strip()
        if "=" in line:
            k, v = line.split("=", 1)
            d[k.strip().upper()] = v.strip()
    return d


def read_structure(path):
    lines = read_text(path).splitlines()
    scale = float(lines[1].split()[0])
    lat = np.array([[float(x) for x in lines[i].split()[:3]] for i in range(2, 5)]) * scale
    species = lines[5].split()
    counts = [int(x) for x in lines[6].split()]
    mode = lines[7].strip().lower()
    n = sum(counts)
    coords = np.array([[float(x) for x in lines[8 + k].split()[:3]] for k in range(n)])
    cart = coords * scale if mode.startswith(("c", "k")) else coords @ lat
    offsets = np.cumsum([0] + counts)
    blocks = {s: cart[offsets[i]: offsets[i + 1]] for i, s in enumerate(species)}
    return lat, species, counts, cart, blocks


def parse_oszicar(text, nelm):
    steps = []
    cur = 0
    for line in text.splitlines():
        if re.match(r"^\s*(DAV|RMM):", line):
            cur += 1
            continue
        m = re.match(r"^\s*(\d+)\s+F=\s*([-+0-9.Ee]+)", line)
        if m:
            mm = re.search(r"mag=\s*([-+0-9.Ee]+)", line)
            steps.append(dict(ionic=int(m.group(1)), elec=cur,
                              F=float(m.group(2)),
                              mag=float(mm.group(1)) if mm else None))
            cur = 0
    n_limit = sum(1 for s in steps if s["elec"] == nelm)
    return steps, n_limit


def parse_outcar(text):
    res = dict(normal_end=False, zbrent=False, energy_sigma0=None,
               toten=None, stress=None, nions=None, nelect=None, nkpts=None,
               fmax=None, force_blocks=0)
    lines = text.splitlines()
    for line in lines:
        if "reached required accuracy" in line:
            res["normal_end"] = True
        if "ZBRENT: fatal error" in line:
            res["zbrent"] = True
        m = re.search(r"energy\(sigma->0\)\s*=\s*([-+0-9.Ee]+)", line)
        if m:
            res["energy_sigma0"] = float(m.group(1))
        m = re.search(r"free  energy   TOTEN\s*=\s*([-+0-9.Ee]+)", line)
        if m:
            res["toten"] = float(m.group(1))
        m = re.match(r"^\s*in kB\s+(.*)$", line)
        if m:
            try:
                res["stress"] = [float(x) for x in m.group(1).split()[:6]]
            except ValueError:
                pass
        m = re.search(r"NIONS\s*=\s*(\d+)", line)
        if m:
            res["nions"] = int(m.group(1))
        m = re.search(r"number of electron\s+([-+0-9.Ee]+)", line)
        if m:
            res["nelect"] = float(m.group(1))
        m = re.search(r"NKPTS\s*=\s*(\d+)", line)
        if m:
            res["nkpts"] = int(m.group(1))
    nions = res["nions"]
    idx = [i for i, l in enumerate(lines) if "TOTAL-FORCE (eV/Angst)" in l]
    res["force_blocks"] = len(idx)
    if idx and nions:
        forces = []
        j = idx[-1] + 2
        while j < len(lines) and len(forces) < nions:
            parts = lines[j].split()
            if len(parts) == 6:
                try:
                    forces.append([float(x) for x in parts[3:6]])
                except ValueError:
                    pass
            j += 1
        if len(forces) == nions:
            f = np.asarray(forces)
            res["fmax"] = float(np.linalg.norm(f, axis=1).max())
    return res


def minimum_image(vec, lat):
    frac = vec @ np.linalg.inv(lat)
    frac -= np.round(frac)
    return frac @ lat


def carbon_network(C, lat, cutoff=1.80):
    """Bond count and coordination for the carbon framework (minimum image)."""
    n = len(C)
    dmin = np.full((n, n), np.inf)
    for i in range(n):
        dv = minimum_image(C - C[i], lat)
        dmin[i] = np.linalg.norm(dv, axis=1)
    np.fill_diagonal(dmin, np.inf)
    adj = dmin < cutoff
    coord = adj.sum(axis=1).astype(int)
    iu = np.triu_indices(n, 1)
    lens = dmin[iu][adj[iu]]
    return int(adj.sum() // 2), coord, lens


def metal_environment(C, lat, m, n_cage=60):
    """Nearest-cage analysis with periodic images; returns displacement etc."""
    dv = minimum_image(C - m, lat)
    dist = np.linalg.norm(dv, axis=1)
    idx = np.argsort(dist)[:n_cage]
    unwrapped = m + dv[idx]
    centre = unwrapped.mean(axis=0)
    disp = float(np.linalg.norm(m - centre))
    mc = np.sort(np.linalg.norm(unwrapped - m, axis=1))
    inside = None
    if HAVE_SCIPY:
        try:
            hull = ConvexHull(unwrapped)
            inside = bool(np.all(hull.equations[:, :3] @ m + hull.equations[:, 3] <= 1e-6))
        except Exception:
            pass
    return dict(disp=disp, mc_min=float(mc[0]), mc_mean=float(mc.mean()),
                mc_max=float(mc[-1]), inside=inside)


def main():
    if len(sys.argv) > 1:
        root = Path(sys.argv[1])
    else:
        root = Path.cwd() / "1_pilot_RUN_FIRST"
    outdir = Path.cwd() / "data"
    outdir.mkdir(exist_ok=True)

    rows = []
    for d in sorted([p for p in root.iterdir() if p.is_dir()]):
        row = dict(case=d.name)
        inc = parse_incar(d / "INCAR") if (d / "INCAR").exists() else {}
        row["ediiffg"] = inc.get("EDIFFG")
        row["ediff"] = inc.get("EDIFF")
        row["nelm"] = inc.get("NELM")
        row["ispin"] = inc.get("ISPIN")
        row["sigma"] = inc.get("SIGMA")
        row["nupdown"] = inc.get("NUPDOWN")

        nelm = None
        try:
            nelm = int(float(inc.get("NELM", 200)))
        except Exception:
            pass
        if (d / "OSZICAR").exists() and nelm:
            steps, n_limit = parse_oszicar(read_text(d / "OSZICAR"), nelm)
            row["n_ionic"] = len(steps)
            row["n_scf_at_nelm"] = n_limit
            if steps:
                row["final_elec"] = steps[-1]["elec"]
                row["final_mag"] = steps[-1]["mag"]

        outcar = d / "OUTCAR"
        if not outcar.exists() and (d / "OUTCAR.gz").exists():
            outcar = d / "OUTCAR.gz"
        if outcar.exists():
            out = parse_outcar(read_text(outcar))
            row["normal_end"] = out["normal_end"]
            row["zbrent"] = out["zbrent"]
            row["energy_sigma0"] = out["energy_sigma0"]
            row["toten"] = out["toten"]
            row["fmax"] = out["fmax"]
            row["nelect"] = out["nelect"]
            row["nkpts"] = out["nkpts"]
            if out["stress"]:
                row["stress_xx"] = out["stress"][0]
                row["stress_yy"] = out["stress"][1]
                row["stress_zz"] = out["stress"][2]

        if (d / "CONTCAR").exists():
            try:
                lat, sp, cnt, cart, blocks = read_structure(d / "CONTCAR")
                row["species"] = "".join(sp)
                row["natoms"] = len(cart)
                for i, name in enumerate(("a", "b", "c")):
                    row["cell_" + name] = float(np.linalg.norm(lat[i]))
                C = blocks.get("C")
                if C is not None and len(C) in (60, 120):
                    nb, coord, lens = carbon_network(C, lat)
                    row["n_CC"] = nb
                    row["coord_min"] = int(coord.min())
                    row["coord_max"] = int(coord.max())
                    row["n_coord4"] = int((coord == 4).sum())
                    row["n_coord2"] = int((coord == 2).sum())
                    row["bond_max"] = float(lens.max()) if len(lens) else None
                    metals = [s for s in sp if s != "C"]
                    mi = 0
                    for metal in metals:
                        for k, m in enumerate(blocks[metal]):
                            env = metal_environment(C, lat, m, 60)
                            mi += 1
                            for key, val in env.items():
                                row[f"metal{mi}_{key}"] = val
                            row[f"metal{mi}_species"] = metal
            except Exception as exc:
                row["geom_error"] = str(exc)
        rows.append(row)

    # ---- derived energies -------------------------------------------------
    by_case = {r["case"]: r for r in rows}

    def E(case):
        return by_case[case].get("energy_sigma0")

    ref_iso = E("08_REF_isolated_C60_no_metal")
    ref_qhp = E("09_REF_qHP_network_no_metal")
    ref_qtp2 = E("10_REF_qTP2_network_no_metal")

    def ebulk(case):
        r = by_case[case]
        return r["energy_sigma0"] / r["natoms"]

    e_li_bulk = ebulk("11_REF_Li_bulk_metal")
    e_mg_bulk = ebulk("12_REF_Mg_bulk_metal")

    def binding(case, ref_net, ebulk_atom, n):
        return (E(case) - ref_net - n * ebulk_atom) / n

    derived = {
        "E_bulk_Li_per_atom": e_li_bulk,
        "E_bulk_Mg_per_atom": e_mg_bulk,
        "E_REF_isolated_C60": ref_iso,
        "E_REF_qHP": ref_qhp,
        "E_REF_qTP2": ref_qtp2,
        "binding_Li_isolated": binding("01_isolated_C60_Li_inside", ref_iso, e_li_bulk, 1),
        "binding_Mg_isolated_singlet": binding("02_isolated_C60_Mg_inside_0unpaired", ref_iso, e_mg_bulk, 1),
        "binding_Mg_isolated_triplet": binding("03_isolated_C60_Mg_inside_2unpaired", ref_iso, e_mg_bulk, 1),
        "binding_Li_qHP": binding("04_qHP_network_Li_inside_cage", ref_qhp, e_li_bulk, 2),
        "binding_Li_qTP2": binding("06_qTP2_network_Li_inside_cage", ref_qtp2, e_li_bulk, 1),
        "binding_Mg_qTP2": binding("07_qTP2_network_Mg_inside_cage", ref_qtp2, e_mg_bulk, 1),
        "E_iso_Li_atom_bulk_corrected": None,
    }
    # polymerisation energies relative to isolated M@C60
    e_iso_li = E("01_isolated_C60_Li_inside") - ref_iso
    e_iso_mg = E("02_isolated_C60_Mg_inside_0unpaired") - ref_iso
    derived["poly_pristine_qHP"] = ref_qhp - 2 * ref_iso
    derived["poly_pristine_qTP2"] = ref_qtp2 - ref_iso
    derived["poly_Li_qHP"] = (E("04_qHP_network_Li_inside_cage") - ref_qhp) - 2 * e_iso_li
    derived["poly_Li_qTP2"] = (E("06_qTP2_network_Li_inside_cage") - ref_qtp2) - e_iso_li
    derived["poly_Mg_qTP2"] = (E("07_qTP2_network_Mg_inside_cage") - ref_qtp2) - e_iso_mg

    # ---- write ----------------------------------------------------------
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with open(outdir / "pilot_summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    with open(outdir / "pilot_summary.json", "w") as fh:
        json.dump(dict(cases=rows, derived=derived), fh, indent=2)

    for r in rows:
        print("%-38s end=%-5s E=%-14s Fmax=%-8s mag=%-7s nCC=%s"
              % (r["case"], r.get("normal_end"), r.get("energy_sigma0"),
                 r.get("fmax"), r.get("final_mag"), r.get("n_CC")))
    print("\nDerived:")
    for k, v in derived.items():
        if v is not None:
            print("  %-32s % .6f eV" % (k, v))
    print("\nwrote", outdir / "pilot_summary.csv")


if __name__ == "__main__":
    main()
