# Round 2 results, 2026-11-19: qHP Mg spin states and [Li@C60]+

> **Note (review, 2026-11-21):** three caveats repeated below are outdated. (1) The qHP reference
> is **not** ring-opened: every carbon keeps three bonds in its own cage (the "two-coordinated"
> count came from bonds to the periodic image of the same cage). (2) Removing D3 from the bulk
> references only would mix functionals; the PBE-only numbers are obtained from `Edisp` instead
> (`pilot_2026-11-18/scripts/d3_decomposition.py`). (3) Free-atom references are not needed; bulk
> metal is the relevant chemical potential. Status and next steps: [PROJECT_STATUS.md](../PROJECT_STATUS.md).

This folder completes the two open branches of the 2026-11-18 pilot: the qHP-network Mg
calculations (restarted from the cancelled pilot case 05) and the closed-shell [Li@C60]+
calibration.

The full analysis is in **report/round2_2026-11-19_results.md**.

## Key results

1. **All three runs completed** (13, 14, 15), with no SCF step at NELM and final forces
   below 0.02 eV/A.
2. **The qHP Mg ground state is non-magnetic.** The non-magnetic restart (13) is 0.0655 eV
   below the 2-uB state (14). Both Mg atoms sit at their cage centres (0.014-0.022 A) with
   Mg-C 3.47-3.88 A. The 0.47 A displacement in the cancelled pilot run was not converged.
3. **The [Li@C60]+ calibration passes:** closed-shell cation (moment 0.00 uB), Li off-centre
   by 1.479 A, Li-C minimum 2.285 A, 90 intact C-C bonds. This matches the neutral Li@C60
   case (1.497 A, 2.260 A) and the experimental Li+@C60 behaviour.
4. **Updated binding energies vs bulk metal:** Li in qHP -0.020 eV; Li in isolated C60
   +0.244; Li in qTP2 +0.261; Mg in qHP +1.428; Mg in qTP2 +1.392; Mg in isolated C60
   +1.506. Li is about 1.45 eV per atom more favourable than Mg in qHP.
5. **Polymerisation effect:** Li in qHP -0.528 eV per two cages; Mg in qHP -0.157; Li in
   qTP2 +0.017; Mg in qTP2 -0.114. Both metals stabilise the networks relative to isolated
   M@C60, strongly so for Li in qHP.
6. **Caveats unchanged:** bulk references include D3(BJ) and are not fully converged; no
   free-atom references; 0 K only; qHP reference is the older ring-opened model; no
   exohedral competitors; the cation energy is from a charged cell and is not used as a
   binding energy.

## Contents

    report/round2_2026-11-19_results.md   full report
    data/round2_summary.csv / .json       machine-readable per-case results
    data/round2_table.md                  generated run table (Appendix A)
    figures/fig1_binding_all_hosts.png
    figures/fig2_polymerisation_effects.png
    figures/fig3_qhp_mg_spin_states.png
    calculations/<case>/                  INCAR, POSCAR, KPOINTS, OSZICAR, CONTCAR,
                                          OUTCAR.gz, input record, POTCAR_SPEC, Slurm files
    audit/file_inventory.json             original file inventory
    audit/slurm_status.txt                original Slurm accounting
    docs/original_README.md               round-2 input definitions
    docs/README_package.txt               provenance notes of the delivered bundle
    scripts/analyze_round2.py             re-derives data/round2_summary.*
    scripts/make_round2_table.py          re-renders data/round2_table.md
    scripts/make_round2_figures.py        re-draws the figures

## Reproduce

    cd round2_2026-11-19
    python scripts/analyze_round2.py
    python scripts/make_round2_table.py
    python scripts/make_round2_figures.py

The scripts import the shared parsers from ../pilot_2026-11-18/scripts/analyze_pilot.py
and read the pilot reference energies from ../pilot_2026-11-18/data/pilot_summary.json.

## Data policy

POTCAR, WAVECAR and CHGCAR are not included (VASP licence and size). OUTCAR files are
gzip-compressed and unmodified.
