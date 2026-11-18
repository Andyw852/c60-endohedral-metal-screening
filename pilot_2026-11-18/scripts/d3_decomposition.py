#!/usr/bin/env python3
"""Split the pilot binding and polymerisation energies into PBE and D3(BJ) parts.

VASP prints the D3 energy ("Edisp (eV)") in OUTCAR, so E_PBE = E(sigma->0) - Edisp at the
same (PBE+D3) geometry. No new calculation is needed. The bulk references keep their PBE+D3
lattice, so the "PBE" column is PBE evaluated on PBE+D3 geometries; relaxing bulk Li/Mg without
D3 changes it by only a few meV per atom.

usage: python3 d3_decomposition.py [calculations_dir]
"""
import gzip, os, re, sys

CALC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'calculations')


def read(case):
    with gzip.open(os.path.join(CALC, case, 'OUTCAR.gz'), 'rt', errors='replace') as f:
        txt = f.read()
    e0 = float(re.findall(r'energy\(sigma->0\) =\s*(-?\d+\.\d+)', txt)[-1])
    ed = float(re.findall(r'Edisp \(eV\)\s*(-?\d+\.\d+)', txt)[-1])
    return e0, ed


E = {k: read(k) for k in sorted(os.listdir(CALC)) if os.path.isdir(os.path.join(CALC, k))}
tot = lambda k: E[k][0]
d3 = lambda k: E[k][1]
mu = {'Li': ('11_REF_Li_bulk_metal', 1), 'Mg': ('12_REF_Mg_bulk_metal', 2)}  # (case, atoms in bulk cell)
REF = {'isolated': '08_REF_isolated_C60_no_metal', 'qHP': '09_REF_qHP_network_no_metal',
       'qTP2': '10_REF_qTP2_network_no_metal'}

# (label, case, host, metal, n metals)
rows = [('Li@C60', '01_isolated_C60_Li_inside', 'isolated', 'Li', 1),
        ('Mg@C60 (singlet)', '02_isolated_C60_Mg_inside_0unpaired', 'isolated', 'Mg', 1),
        ('Mg@C60 (triplet)', '03_isolated_C60_Mg_inside_2unpaired', 'isolated', 'Mg', 1),
        ('Li@qHP (2 Li)', '04_qHP_network_Li_inside_cage', 'qHP', 'Li', 2),
        ('Li@qTP2', '06_qTP2_network_Li_inside_cage', 'qTP2', 'Li', 1),
        ('Mg@qTP2', '07_qTP2_network_Mg_inside_cage', 'qTP2', 'Mg', 1)]


def binding(f, case, host, m, n):
    bulk, nb = mu[m]
    return (f(case) - f(REF[host]) - n * f(bulk) / nb) / n


print('Binding energy per metal vs bulk metal (eV)')
print(f"{'system':18s} {'PBE+D3':>8s} {'D3 part':>8s} {'PBE only':>9s}")
for lab, case, host, m, n in rows:
    b, bd = binding(tot, case, host, m, n), binding(d3, case, host, m, n)
    print(f'{lab:18s} {b:8.3f} {bd:8.3f} {b - bd:9.3f}')

print('\nPolymerisation effect of the metal: [E(M@net)-E(net)] - k[E(M@C60)-E(C60)] (eV per cell)')
iso = {'Li': '01_isolated_C60_Li_inside', 'Mg': '02_isolated_C60_Mg_inside_0unpaired'}
for lab, case, host, m, n in rows:
    if host == 'isolated':
        continue
    f = lambda g: (g(case) - g(REF[host])) - n * (g(iso[m]) - g(REF['isolated']))
    print(f'{lab:18s} PBE+D3 {f(tot):7.3f}   D3 part {f(d3):7.3f}   PBE only {f(tot) - f(d3):7.3f}')

print('\nPristine network relative to isolated C60 (eV per cage)')
for host, k in (('qHP', 2), ('qTP2', 1)):
    f = lambda g: (g(REF[host]) - k * g(REF['isolated'])) / k
    print(f'{host:5s} PBE+D3 {f(tot):7.3f}   D3 part {f(d3):7.3f}   PBE only {f(tot) - f(d3):7.3f}')
