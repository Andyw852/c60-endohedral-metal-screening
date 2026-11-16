#!/usr/bin/env python3
"""
network_geometry.py
===================
Geometric characterisation of the reference qHP / qTP fullerene networks that
the endohedral-metal route is supposed to feed into.

For every POSCAR in network_reference/ the script reports

  * cell parameters, volume and number of cages per cell,
  * dimensionality (2D layer / 1D chain / 3D) inferred from vacuum gaps,
  * the carbon coordination histogram, which separates molecular (n=3) from
    polymer-junction (n=4) carbon atoms,
  * the number of [2+2] inter-cage links per cage and their bond lengths,
  * for Mg2C60: Mg-C and Mg-Mg distances.

A [2+2] cycloaddition between two fullerene cages adds two C-C bonds and
turns four carbon atoms (two per cage) from three- to four-coordinated.
The inter-cage bonds are therefore exactly the bonds whose two endpoints are
both four-coordinated.  No cage assignment is required, which makes the
analysis robust for periodic networks.

Outputs
-------
  data/network_geometry.csv

Usage
-----
  python scripts/network_geometry.py
"""

import csv
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "network_reference"

CAGE_SIZE = {
    "C20_qHPC20": (20, 0),
    "C20_qTPC20-b": (20, 0),
    "C20_qTPC20-r": (20, 0),
    "C24_qHPC24": (24, 0),
    "C24_qTPC24": (24, 0),
    "C36_qHPC36-D6h": (36, 0),
    "C36_qTP2C36-D2d": (36, 0),
    "C60_qHPC60": (60, 0),
    "C60_qTP1C60": (60, 0),
    "C60_qTP2C60": (60, 0),
    "Mg2C60_bulk": (60, 2),
}

BOND_CUTOFF = 1.80


def read_structure(path):
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
    if mode.startswith(("c", "k")):
        cart = coords * scale
    else:
        cart = coords @ lat
    offsets = np.cumsum([0] + counts)
    blocks = {s: cart[offsets[i]:offsets[i + 1]] for i, s in enumerate(species)}
    return lat, species, counts, cart, blocks


def min_image_matrix(cart, lat):
    """Pairwise minimum-image distance matrix."""
    shifts = np.array(
        [[i, j, k] for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)]
    ) @ lat
    n = len(cart)
    dmin = np.full((n, n), np.inf)
    for i in range(n):
        d = np.linalg.norm(cart[None, :, :] + shifts[:, None, :] - cart[i], axis=2)
        dmin[i] = d.min(axis=0)
    np.fill_diagonal(dmin, np.inf)
    return dmin


def vacuum_gaps(cart, lat):
    gaps = []
    for i in range(3):
        others = [lat[j] for j in range(3) if j != i]
        normal = np.cross(others[0], others[1])
        normal /= np.linalg.norm(normal)
        height = abs(np.dot(lat[i], normal))
        proj = cart @ normal
        gaps.append(height - (proj.max() - proj.min()))
    return np.asarray(gaps)


def main():
    rows = []
    for name, (cage_size, n_mg) in CAGE_SIZE.items():
        path = REF / (name + ".POSCAR")
        if not path.exists():
            print("WARNING: missing", path)
            continue
        lat, species, counts, cart, blocks = read_structure(path)
        volume = abs(np.linalg.det(lat))
        C = blocks["C"]
        n_c = len(C)
        n_cage = n_c / cage_size

        D = min_image_matrix(C, lat)
        A = D < BOND_CUTOFF
        coord = A.sum(axis=1).astype(int)
        n_total = int(coord.sum() // 2)

        # inter-cage bonds: both endpoints four-coordinated
        iu = np.triu_indices(n_c, 1)
        pair_len = D[iu]
        both4 = (coord[iu[0]] == 4) & (coord[iu[1]] == 4)
        inter = pair_len[both4 & (pair_len < BOND_CUTOFF)]
        mol = pair_len[(pair_len < BOND_CUTOFF) & ~(both4 & (pair_len < BOND_CUTOFF))]

        gaps = vacuum_gaps(C, lat)
        n_vac = int((gaps > 6.0).sum())
        dim = {0: "3D", 1: "2D", 2: "1D", 3: "0D"}[n_vac]

        row = dict(
            name=name,
            n_cages=int(round(n_cage)),
            n_C=n_c,
            n_Mg=n_mg,
            dim=dim,
            a=float(np.linalg.norm(lat[0])),
            b=float(np.linalg.norm(lat[1])),
            c=float(np.linalg.norm(lat[2])),
            volume_A3=float(volume),
            volume_per_cage_A3=float(volume / n_cage),
            vacuum_a=float(gaps[0]),
            vacuum_b=float(gaps[1]),
            vacuum_c=float(gaps[2]),
            n_CC_bonds=n_total,
            n_CC_bonds_per_cage=float(n_total / n_cage),
            n_C_coord2=int((coord == 2).sum()),
            n_C_coord3=int((coord == 3).sum()),
            n_C_coord4=int((coord == 4).sum()),
            n_intercage_bonds=len(inter),
            n_intercage_bonds_per_cage=float(len(inter) / n_cage),
            interbond_min=float(inter.min()) if len(inter) else None,
            interbond_max=float(inter.max()) if len(inter) else None,
            interbond_mean=float(inter.mean()) if len(inter) else None,
            molbond_min=float(mol.min()) if len(mol) else None,
            molbond_max=float(mol.max()) if len(mol) else None,
        )

        if n_mg:
            Mg = blocks["Mg"]
            d = np.linalg.norm(C[:, None, :] - Mg[None, :, :], axis=-1)
            row["Mg_C_min"] = float(d.min())
            row["Mg_C_mean"] = float(d.mean())
            row["Mg_Mg_dist"] = (
                float(np.linalg.norm(Mg[0] - Mg[1])) if n_mg == 2 else None
            )

        rows.append(row)

    out = ROOT / "data" / "network_geometry.csv"
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print("network, dim, nC, n2, n3, n4, interbonds/cage, inter d (A), V/cage")
    for r in rows:
        idm = r["interbond_mean"] if r["interbond_mean"] else float("nan")
        print(
            "%18s %3s %4d %3d %4d %4d %12.1f %7.3f %9.1f"
            % (
                r["name"], r["dim"], r["n_C"], r["n_C_coord2"],
                r["n_C_coord3"], r["n_C_coord4"],
                r["n_intercage_bonds_per_cage"], idm, r["volume_per_cage_A3"],
            )
        )
    for r in rows:
        if "Mg_C_min" in r:
            print(
                "\n%s: Mg-C min = %.3f A, mean = %.3f A, Mg-Mg = %.3f A"
                % (r["name"], r["Mg_C_min"], r["Mg_C_mean"], r["Mg_Mg_dist"])
            )
    print("\nwrote", out)


if __name__ == "__main__":
    main()
