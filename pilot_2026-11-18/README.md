# Pilot results, 2026-11-18: Li and Mg inside C60, qHP and qTP2

This folder contains the first corrected endohedral calculations of the project: 12 VASP
runs of Li and Mg inside an isolated C60 and inside the qHP and qTP2 2D networks, plus the
five reference calculations.

The full analysis is in **report/pilot_2026-11-18_results.md**.

## Key results

1. **The method fix works.** With the metal started 1.0 A (isolated cage) or 0.8 A (networks)
   off-centre and integer electronic occupations, Li moves further off-centre
   (1.50 A isolated, 1.33-1.43 A in the networks; Li-C 2.17-2.26 A), while Mg relaxes back
   to the cage centre (0.02 A isolated, 0.01 A in qTP2; Mg-C 3.52-3.58 A).
2. **Mg has two spin states:** the singlet is 0.699 eV below the triplet; the singlet is
   centred and the triplet is 1.06 A off-centre.
3. **The networks survive one metal per cage at 0 K:** 188 C-C bonds for qHP, 94 for qTP2,
   no coordination changes, longest C-C bond 1.62 A, c = 25.0 A fixed, in-plane stress
   below 0.5 kB.
4. **Energies (PBE+D3, relative to bulk metal):** Li in qHP -0.020 eV per Li; Li in
   isolated C60 +0.244; Li in qTP2 +0.261; Mg in isolated C60 +1.506; Mg in qTP2 +1.392.
   Li makes qHP polymerisation more favourable by 0.53 eV per two cages.
5. **One run is missing:** case 05 (Mg in qHP) was cancelled and is not converged.
6. **Caveats:** the bulk references include D3(BJ) and are not fully relaxed; no free-atom
   references were calculated; the qHP reference is the older ring-opened model; the
   exohedral competitors have not been computed; everything is 0 K.

## Contents

    report/pilot_2026-11-18_results.md    full report
    data/pilot_summary.csv / .json        machine-readable per-case results
    data/pilot_table.md                   generated run table (Appendix A)
    figures/fig1_binding_energies.png
    figures/fig2_metal_positions.png
    figures/fig3_polymerisation_effect.png
    calculations/<case>/                  INCAR, POSCAR, KPOINTS (where present),
                                           OSZICAR, CONTCAR, OUTCAR.gz, vasp.log,
                                           POTCAR_SPEC, pilot_input_record.json,
                                           Slurm submission/status files
    audit/file_inventory.json             original file inventory
    audit/slurm_status.txt                original Slurm accounting
    docs/original_README.md               input definitions used to generate the runs
    docs/README_package.txt               provenance notes of the delivered bundle
    scripts/analyze_pilot.py              re-derives data/pilot_summary.*
    scripts/make_pilot_table.py           re-renders data/pilot_table.md
    scripts/make_pilot_figures.py         re-draws the figures

## Reproduce

    cd pilot_2026-11-18
    python scripts/analyze_pilot.py calculations
    python scripts/make_pilot_table.py
    python scripts/make_pilot_figures.py

Requires Python 3.9+, numpy, matplotlib; scipy is optional (used only for the
point-in-cage convex-hull test).

## Data policy

POTCAR, WAVECAR and CHGCAR are not included (VASP licence and file size). OUTCAR files are
gzip-compressed. The original zip archive of the delivered bundle is not duplicated here;
this folder is a curated, POTCAR-free copy of it. The OUTCARs are unmodified.
