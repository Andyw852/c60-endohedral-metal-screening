#!/usr/bin/env python3
"""s-block binding energies split into PBE and D3(BJ) parts, with the ionisation-cost trend.

E_PBE = E(sigma->0) - Edisp at the same geometry (Edisp from OUTCAR), so no new calculation is
needed. Binding per metal vs bulk metal: [E(M_n@host) - E(host) - n*mu_M] / n.
"ionisation cost" = sum of the first k ionisation energies (k = 1 alkali, 2 alkaline earth) plus
the experimental cohesive energy of the bulk metal (eV, CRC values).

usage (from the repository root): python3 round3a_2026-11-23/scripts/d3_split_and_trends.py
"""
import glob, gzip, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PILOT = os.path.join(ROOT, 'pilot_2026-11-18', 'calculations')
R2 = os.path.join(ROOT, 'round2_2026-11-19', 'calculations')
R3 = os.path.join(ROOT, 'round3a_2026-11-23', 'calculations')

COST = {'Li': 5.392 + 1.63, 'Na': 5.139 + 1.113, 'K': 4.341 + 0.934, 'Rb': 4.177 + 0.852,
        'Cs': 3.894 + 0.804, 'Be': 9.323 + 18.211 + 3.32, 'Mg': 7.646 + 15.035 + 1.51,
        'Ca': 6.113 + 11.872 + 1.84, 'Sr': 5.695 + 11.030 + 1.72, 'Ba': 5.212 + 10.004 + 1.90}


def read(path):
    t = gzip.open(path, 'rt', errors='replace').read()
    e = float(re.findall(r'energy\(sigma->0\) =\s*(-?\d+\.\d+)', t)[-1])
    d = float(re.findall(r'Edisp \(eV\)\s*(-?\d+\.\d+)', t)[-1])
    return e, d


def natoms(d):
    return sum(int(x) for x in open(os.path.join(d, 'POSCAR')).read().split('\n')[6].split())


REF = {'iso': read(f'{PILOT}/08_REF_isolated_C60_no_metal/OUTCAR.gz'),
       'qHP': read(f'{PILOT}/09_REF_qHP_network_no_metal/OUTCAR.gz'),
       'qTP2': read(f'{PILOT}/10_REF_qTP2_network_no_metal/OUTCAR.gz')}
NMET = {'iso': 1, 'qHP': 2, 'qTP2': 1}


def cases(m):
    """Return {'bulk': (E, Ed, n), 'iso': (E, Ed), 'qHP': ..., 'qTP2': ...} for metal m."""
    if m in ('Li', 'Mg'):
        b = f'{PILOT}/{11 if m == "Li" else 12}_REF_{m}_bulk_metal'
        iso = [f'{PILOT}/01_isolated_C60_Li_inside'] if m == 'Li' else \
              [f'{PILOT}/02_isolated_C60_Mg_inside_0unpaired', f'{PILOT}/03_isolated_C60_Mg_inside_2unpaired']
        net = {'qHP': f'{PILOT}/04_qHP_network_Li_inside_cage' if m == 'Li'
               else f'{R2}/13_qHP_network_Mg_inside_cage_restart_nonmagnetic',
               'qTP2': f'{PILOT}/{"06" if m == "Li" else "07"}_qTP2_network_{m}_inside_cage'}
    else:
        b = glob.glob(f'{R3}/{m}/0_REF_*')[0]
        iso = glob.glob(f'{R3}/{m}/1_isolated_*')
        net = {h: (glob.glob(f'{R3}/{m}/2_{h}_*') or [None])[0] for h in ('qHP', 'qTP2')}
    out = {'bulk': (*read(f'{b}/OUTCAR.gz'), natoms(b)),
           'iso': min(read(f'{d}/OUTCAR.gz') for d in iso)}
    for h, d in net.items():
        if d and os.path.exists(f'{d}/OUTCAR.gz'):
            out[h] = read(f'{d}/OUTCAR.gz')
    return out


print(f"{'metal':5s} {'cost':>6s} | {'host':4s} {'PBE+D3':>7s} {'D3':>6s} {'PBE':>6s}")
for m in sorted(COST, key=lambda k: (k in ('Be', 'Mg', 'Ca', 'Sr', 'Ba'), COST[k])):
    c = cases(m); E, Ed, nb = c['bulk']; mu = (E / nb, Ed / nb)
    for h in ('iso', 'qHP', 'qTP2'):
        if h not in c:
            print(f'{m:5s} {COST[m]:6.2f} | {h:4s}  missing'); continue
        n = NMET[h]
        b = [(c[h][i] - REF[h][i] - n * mu[i]) / n for i in (0, 1)]
        print(f'{m:5s} {COST[m]:6.2f} | {h:4s} {b[0]:7.2f} {b[1]:6.2f} {b[0] - b[1]:6.2f}')
