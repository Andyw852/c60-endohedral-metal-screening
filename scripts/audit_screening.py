#!/usr/bin/env python3
"""
audit_screening.py
==================
Independent audit of the 32-metal "endohedral metal in C60, center start"
screening bundle (review_center32_final_20261116_102102_870377).

The script re-derives, from the raw VASP files shipped in the bundle:

  * job / termination status      (normal end, ZBRENT line-search death, NELM hit)
  * ionic and electronic step counts
  * final maximum force (from the last TOTAL-FORCE block of OUTCAR)
  * final geometry metrics        (metal displacement from the cage centre,
                                   metal-carbon distances, cage radius,
                                   C-C connectivity and carbon coordination,
                                   point-in-cage test)
  * key INCAR settings            (EDIFF, EDIFFG, POTIM, NELM, ISPIN, ENCUT)

Outputs
-------
  data/screening_summary.csv
  data/screening_summary.json

Usage
-----
  python scripts/audit_screening.py            # run from repo root
"""

import csv
import gzip
import json
import math
import re
from pathlib import Path

import numpy as np

try:
    from scipy.spatial import ConvexHull
    HAVE_SCIPY = True
except Exception:                                    # pragma: no cover
    HAVE_SCIPY = False

ROOT = Path(__file__).resolve().parent.parent
CALC = ROOT / "calculations"

# ---------------------------------------------------------------------------
# system table: metal -> (relative path, provenance, classification in source report)
# ---------------------------------------------------------------------------
SYSTEMS = [
    # metal, path, provenance, source classification
    ("Li", "pilot_Li_Fe/Li/center/m3",                       "reused", "pass"),
    ("Be", "center32_screen/Be",                              "new",    "pass"),
    ("Na", "batch_20261016/Na/Na/center/m1",                  "reused", "pass"),
    ("Mg", "Mg_center_m0_tight_s002",                         "reused", "pass"),
    ("Al", "center32_screen/Al",                              "new",    "pass"),
    ("K",  "batch_20261021/K/K/center/m1",                    "reused", "pass"),
    ("Ca", "center32_screen/Ca",                              "new",    "fail"),
    ("Sc", "center32_screen/Sc",                              "new",    "fail"),
    ("Ti", "center32_screen/Ti",                              "new",    "fail"),
    ("V",  "stage5_controlled_20261109/V_center_m3_matchM1",  "reused", "pending"),
    ("Cr", "center32_screen/Cr",                              "new",    "fail"),
    ("Mn", "center32_screen/Mn",                              "new",    "fail"),
    ("Fe", "pilot_Li_Fe/Fe/center/m1",                        "reused", "pending"),
    ("Co", "batch_20261023/Co/Co/center/m3",                  "reused", "pending"),
    ("Ni", "center32_screen/Ni",                              "new",    "fail"),
    ("Cu", "batch_20261023/Cu/Cu/center/m1",                  "reused", "pass"),
    ("Zn", "batch_20261023/Zn/Zn/center/m2",                  "reused", "pass"),
    ("Ga", "center32_screen/Ga",                              "new",    "pass"),
    ("Rb", "center32_screen/Rb",                              "new",    "pass"),
    ("Sr", "batch_20261021/Sr/Sr/center/m2",                  "reused", "pass"),
    ("Y",  "center32_screen/Y",                               "new",    "pass"),
    ("Zr", "stage4_20261106/Zr_center_m2_tight_s002",         "reused", "pending"),
    ("Nb", "center32_screen/Nb",                              "new",    "pending"),
    ("Mo", "stage4_20261106/Mo_center_m4_tight_s002",         "reused", "pass"),
    ("Tc", "center32_screen/Tc",                              "new",    "pending"),
    ("Ru", "center32_screen/Ru",                              "new",    "pass"),
    ("Rh", "center32_screen/Rh",                              "new",    "pass"),
    ("Pd", "center32_screen/Pd",                              "new",    "pass"),
    ("Ag", "stage4_20261106/Ag_center_m1_tight_s002",         "reused", "pass"),
    ("Cd", "center32_screen/Cd",                              "new",    "pass"),
    ("In", "center32_screen/In",                              "new",    "pass"),
    ("Sn", "center32_screen/Sn",                              "new",    "pass"),
]

FMAX_THRESHOLD = 0.02      # eV/Angstrom (EDIFFG = -0.02 in the new runs)
CC_BOND_CUTOFF = 1.80      # Angstrom, same criterion as the source report
BOX = 22.0                 # Angstrom, cubic cell used for the isolated molecule


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def read_text_maybe_gz(path: Path) -> str:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", errors="replace") as fh:
            return fh.read()
    return path.read_text(errors="replace")


def first_existing(folder: Path, name: str):
    plain = folder / name
    gz = folder / (name + ".gz")
    if plain.exists():
        return plain
    if gz.exists():
        return gz
    return None


def parse_incar(path: Path) -> dict:
    out = {}
    if path is None or not path.exists():
        return out
    for line in path.read_text(errors="replace").splitlines():
        line = line.split("#")[0].split("!")[0].strip()
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip().upper()] = v.strip()
    return out


def parse_oszicar(text: str):
    """Return (list of ionic steps, number of electronic steps in trailing unfinished block)."""
    steps = []
    cur = 0
    pat_el = re.compile(r"^\s*(DAV|RMM):\s*(\d+)")
    pat_ion = re.compile(
        r"^\s*(\d+)\s+F=\s*([-+0-9.Ee]+)\s+E0=\s*([-+0-9.Ee]+)\s+"
        r"d E\s*=\s*([-+0-9.Ee]+)\s+mag=\s*([-+0-9.Ee]+)"
    )
    for line in text.splitlines():
        if pat_el.match(line):
            cur += 1
            continue
        m = pat_ion.match(line)
        if m:
            steps.append(
                dict(
                    ionic=int(m.group(1)),
                    electronic=cur,
                    F=float(m.group(2)),
                    E0=float(m.group(3)),
                    dE=float(m.group(4)),
                    mag=float(m.group(5)),
                )
            )
            cur = 0
    return steps, cur


def parse_outcar(text: str):
    """Extract the pieces of OUTCAR needed for the audit."""
    res = dict(
        nions=None,
        nelect=None,
        normal_end=False,
        zbrent=False,
        scf_aborts=0,
        toten=None,
        force_max=None,
        forces=None,
        n_force_blocks=0,
    )
    lines = text.splitlines()
    for line in lines:
        if res["nions"] is None:
            m = re.search(r"NIONS\s*=\s*(\d+)", line)
            if m:
                res["nions"] = int(m.group(1))
                continue
        if res["nelect"] is None:
            m = re.search(r"number of electron\s+([-+0-9.Ee]+)", line)
            if m:
                res["nelect"] = float(m.group(1))
                continue
        if "reached required accuracy" in line:
            res["normal_end"] = True
        if "ZBRENT: fatal error" in line:
            res["zbrent"] = True
        if "aborting loop EDIFF was not reached" in line:
            res["scf_aborts"] += 1
        if "free  energy   TOTEN" in line:
            m = re.search(r"=\s*([-+0-9.Ee]+)\s*eV", line)
            if m:
                res["toten"] = float(m.group(1))

    # last force block
    nions = res["nions"]
    idx = None
    for i, line in enumerate(lines):
        if "TOTAL-FORCE (eV/Angst)" in line:
            idx = i
            res["n_force_blocks"] += 1
    if idx is not None and nions:
        forces = []
        j = idx + 2
        while j < len(lines) and len(forces) < nions:
            parts = lines[j].split()
            if len(parts) == 6:
                try:
                    vals = [float(x) for x in parts]
                    forces.append(vals[3:6])
                except ValueError:
                    pass
            j += 1
        if len(forces) == nions:
            f = np.asarray(forces, dtype=float)
            res["forces"] = f
            res["force_max"] = float(np.linalg.norm(f, axis=1).max())
    return res


def read_structure(path: Path):
    """Read a VASP POSCAR/CONTCAR (VASP-5 style, Cartesian or Direct)."""
    lines = path.read_text(errors="replace").splitlines()
    scale = float(lines[1].split()[0])
    lat = np.array([[float(x) for x in lines[i].split()[:3]] for i in range(2, 5)]) * scale
    species = lines[5].split()
    counts = [int(x) for x in lines[6].split()]
    mode = lines[7].strip().lower()
    n = sum(counts)
    coords = np.array(
        [[float(x) for x in lines[8 + k].split()[:3]] for k in range(n)], dtype=float
    )
    if mode.startswith(("c", "k")):          # Cartesian
        cart = coords * scale
    else:                                     # Direct
        cart = coords @ lat
    return dict(lat=lat, species=species, counts=counts, cart=cart, n=n)


def min_image(vec, lat):
    """Minimum-image convention for an orthorhombic/near-orthorhombic cell."""
    frac = vec @ np.linalg.inv(lat)
    frac -= np.round(frac)
    return frac @ lat


def cage_metrics(cart, n_c=60):
    """Geometry metrics for C60 + one endohedral atom (last atom)."""
    C = cart[:n_c]
    M = cart[n_c]
    centre = C.mean(axis=0)
    r = np.linalg.norm(C - centre, axis=1)
    disp = float(np.linalg.norm(M - centre))

    # metal-carbon distances (molecule is inside the box; plain distances fine)
    d_mc = np.linalg.norm(C - M, axis=1)

    # C-C connectivity
    dcc = np.linalg.norm(C[:, None, :] - C[None, :, :], axis=-1)
    np.fill_diagonal(dcc, 1e9)
    bonds = dcc[np.triu_indices(n_c, 1)]
    bonded = bonds[bonds < CC_BOND_CUTOFF]
    adj = (dcc < CC_BOND_CUTOFF).astype(int)
    coord = adj.sum(axis=1)

    inside = None
    if HAVE_SCIPY:
        try:
            hull = ConvexHull(C)
            inside = bool(np.all(hull.equations[:, :3] @ M + hull.equations[:, 3] <= 1e-6))
        except Exception:
            inside = None

    return dict(
        cage_radius_mean=float(r.mean()),
        cage_radius_std=float(r.std()),
        cage_radius_min=float(r.min()),
        cage_radius_max=float(r.max()),
        metal_disp_from_centre=disp,
        mc_min=float(d_mc.min()),
        mc_mean=float(d_mc.mean()),
        mc_max=float(d_mc.max()),
        n_mc_lt_2p5=int((d_mc < 2.5).sum()),
        n_mc_lt_3p0=int((d_mc < 3.0).sum()),
        n_cc_bonds=float(len(bonded)),
        cc_min=float(bonded.min()) if len(bonded) else None,
        cc_max=float(bonded.max()) if len(bonded) else None,
        cc_mean=float(bonded.mean()) if len(bonded) else None,
        cc_std=float(bonded.std()) if len(bonded) else None,
        n_cc_gt_1p65=int((bonded > 1.65).sum()) if len(bonded) else 0,
        n_cc_lt_1p25=int((bonded < 1.25).sum()) if len(bonded) else 0,
        c_coord_min=int(coord.min()),
        c_coord_max=int(coord.max()),
        n_c_wrong_coord=int((coord != 3).sum()),
        inside_cage=inside,
    )


def main():
    rows = []
    for metal, rel, provenance, source_class in SYSTEMS:
        folder = CALC / rel
        row = dict(
            metal=metal,
            source_path=rel,
            provenance=provenance,
            source_classification=source_class,
            folder_exists=folder.exists(),
        )
        if not folder.exists():
            rows.append(row)
            continue

        incar_path = folder / "INCAR"
        incar = parse_incar(incar_path)
        row.update(
            incar_encut=incar.get("ENCUT"),
            incar_ediff=incar.get("EDIFF"),
            incar_ediffg=incar.get("EDIFFG"),
            incar_potim=incar.get("POTIM"),
            incar_nelm=incar.get("NELM"),
            incar_ispin=incar.get("ISPIN"),
            incar_ibrion=incar.get("IBRION"),
            incar_magmom=incar.get("MAGMOM"),
            incar_isif=incar.get("ISIF"),
            incar_sigma=incar.get("SIGMA"),
            incar_addgrid=incar.get("ADDGRID"),
        )
        # initial moment assigned to the metal atom (last entry of MAGMOM)
        if incar.get("MAGMOM"):
            try:
                row["initial_metal_magmom"] = float(incar["MAGMOM"].split()[-1])
            except Exception:
                row["initial_metal_magmom"] = None

        nelm = None
        try:
            nelm = int(float(incar.get("NELM", 200)))
        except Exception:
            pass
        row["nelm_used"] = nelm

        # --- OSZICAR -----------------------------------------------------
        oszic_path = folder / "OSZICAR"
        if oszic_path.exists():
            steps, trailing = parse_oszicar(oszic_path.read_text(errors="replace"))
            row["n_ionic_steps"] = len(steps)
            row["n_trailing_electronic_steps"] = trailing
            if nelm:
                at_limit = [s["ionic"] for s in steps if s["electronic"] == nelm]
                row["n_scf_at_limit_steps"] = len(at_limit)
                row["scf_at_limit_ionic_steps"] = ";".join(str(i) for i in at_limit)
                row["max_electronic_steps"] = max(
                    (s["electronic"] for s in steps), default=None
                )
            row["final_scf_steps"] = steps[-1]["electronic"] if steps else None
            row["final_scf_at_nelm"] = (
                (steps[-1]["electronic"] == nelm) if (steps and nelm) else None
            )
            row["final_mag_uB"] = steps[-1]["mag"] if steps else None
            row["final_F_oszicar_eV"] = steps[-1]["F"] if steps else None
        else:
            row["n_ionic_steps"] = None

        # --- OUTCAR ------------------------------------------------------
        outcar_path = first_existing(folder, "OUTCAR")
        if outcar_path is not None:
            out = parse_outcar(read_text_maybe_gz(outcar_path))
            row["normal_end"] = out["normal_end"]
            row["zbrent_fatal"] = out["zbrent"]
            row["scf_abort_warnings"] = out["scf_aborts"]
            row["nions"] = out["nions"]
            row["nelect"] = out["nelect"]
            row["toten_eV"] = out["toten"]
            row["final_force_max_eVA"] = out["force_max"]
            row["n_force_blocks"] = out["n_force_blocks"]
            row["outcar_final_metal_force"] = (
                float(np.linalg.norm(out["forces"][-1])) if out["forces"] is not None else None
            )
            if out["forces"] is not None and out["nions"] == 61:
                cf = np.linalg.norm(out["forces"][:60], axis=1)
                row["outcar_final_max_c_force"] = float(cf.max())
        else:
            row["normal_end"] = None

        # --- final geometry (CONTCAR) ------------------------------------
        contcar_path = folder / "CONTCAR"
        if contcar_path.exists():
            try:
                st = read_structure(contcar_path)
                row["contcar_natoms"] = st["n"]
                row["contcar_species"] = "".join(st["species"])
                if st["n"] == 61 and st["counts"] == [60, 1]:
                    m = cage_metrics(st["cart"])
                    row.update(m)
                    # displacement of the metal relative to its (centred) start
                    poscar_path = folder / "POSCAR"
                    if poscar_path.exists():
                        st0 = read_structure(poscar_path)
                        row["metal_disp_from_start"] = float(
                            np.linalg.norm(st["cart"][60] - st0["cart"][60])
                        )
                        row["max_c_disp_from_start"] = float(
                            np.linalg.norm(st["cart"][:60] - st0["cart"][:60], axis=1).max()
                        )
            except Exception as exc:
                row["geometry_error"] = str(exc)

        rows.append(row)

    # --- derived flags ---------------------------------------------------
    for r in rows:
        f = r.get("final_force_max_eVA")
        r["force_below_0p02"] = (f is not None and f <= FMAX_THRESHOLD)
        r["scf_clean_final"] = (
            r.get("final_scf_steps") is not None
            and r.get("nelm_used") is not None
            and r["final_scf_steps"] < r["nelm_used"]
        )
        r["scf_clean_all_steps"] = (
            r.get("n_scf_at_limit_steps") == 0
            if r.get("n_scf_at_limit_steps") is not None
            else None
        )
        r["geometry_intact"] = (
            r.get("n_cc_bonds") is not None
            and abs(r["n_cc_bonds"] - 90) < 1e-6
            and r.get("c_coord_min") == 3
            and r.get("c_coord_max") == 3
        )
        probe = r.get("n_ionic_steps")
        r["symmetry_trap_probe"] = (
            probe is not None
            and probe <= 3
            and r.get("metal_disp_from_start") is not None
            and r["metal_disp_from_start"] < 0.02
        )

    # --- write -----------------------------------------------------------
    data_dir = ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    csv_path = data_dir / "screening_summary.csv"
    fieldnames = []
    for r in rows:
        for k in r:
            if k not in fieldnames:
                fieldnames.append(k)
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    json_path = data_dir / "screening_summary.json"
    with open(json_path, "w") as fh:
        json.dump(rows, fh, indent=2)

    # --- console report --------------------------------------------------
    print(f"{'metal':>4} {'cls':>7} {'prov':>6} {'ion':>4} {'scf':>4} {'hit':>3} "
          f"{'Fmax':>7} {'disp':>6} {'MCmin':>6} {'nCC':>4} {'end':>5} {'zbr':>4}")
    for r in rows:
        print(
            f"{r['metal']:>4} {r.get('source_classification',''):>7} "
            f"{r.get('provenance',''):>6} "
            f"{str(r.get('n_ionic_steps')):>4} {str(r.get('final_scf_steps')):>4} "
            f"{str(r.get('n_scf_at_limit_steps')):>3} "
            f"{r.get('final_force_max_eVA') if r.get('final_force_max_eVA') is not None else float('nan'):7.4f} "
            f"{r.get('metal_disp_from_centre') if r.get('metal_disp_from_centre') is not None else float('nan'):6.3f} "
            f"{r.get('mc_min') if r.get('mc_min') is not None else float('nan'):6.3f} "
            f"{str(r.get('n_cc_bonds')):>4} "
            f"{str(r.get('normal_end')):>5} {str(r.get('zbrent_fatal')):>4}"
        )
    print(f"\nwrote {csv_path}")
    print(f"wrote {json_path}")


if __name__ == "__main__":
    main()
