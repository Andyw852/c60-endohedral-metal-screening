# Round 3a results, 2026-11-23: s-block metals

This folder contains the round-3a calculations for the eight s-block metals Na, K, Rb, Cs, Ca,
Sr, Ba and Be: bulk references, isolated M@C60 spin states, and the qHP and qTP2 networks.
The Cs qHP run was excluded from the delivered bundle (stalled); all other 35 cases are present,
complete and converged.

The full analysis is in **report/round3a_2026-11-23_results.md**.

## Key results

1. **All s-block metals except Be are stable inside C60 with respect to bulk metal** (negative
   binding). Binding per metal in the qHP network: Ba -1.60, Sr -1.22, Ca -0.95, K -0.74,
   Rb -0.62, Na -0.35 eV; Li -0.02 (pilot), Mg +1.43 (round 2), Be +3.45 eV (metastable).
2. **qHP is the best host** for every metal; the qTP2 binding is typically 0.1-0.6 eV weaker.
3. **Endohedral metals strongly stabilise qHP polymerisation:** Ca -1.37, Sr -1.24, Ba -1.08,
   Na -0.52, K -0.34, Rb -0.31, Be -0.08 eV per two cages. qTP2 is essentially unaffected
   (within +/-0.10 eV).
4. **Metal positions are non-monotonic:** Na (0.06 A) and Cs (0.01 A) are nearly centred;
   K and Rb sit about 0.43-0.55 A off-centre; Ca, Sr and Ba are 0.7-1.25 A off-centre and bind
   to the cage wall (M-C 2.4-2.9 A). Be is centred in the singlet ground state; its higher
   triplet lies 1.91 A off-centre.
5. **Spin states:** Be and Ca prefer the singlet (by 0.299 and 0.050 eV); Sr and Ba prefer the
   2-unpaired state (by 0.028 and 0.004 eV). The Ca/Sr/Ba networks were run non-magnetic.
6. **Cages and networks survive:** 90/188/94 C-C bonds for the isolated cage/qHP/qTP2, no
   coordination change, longest bond 1.626 A, all metals inside their cages, in-plane stress
   below 0.1 kB.

## Caveats

- The bulk references still include D3(BJ) and are slightly contracted (1.5-4 percent) and
  partly stressed (0.2-0.6 kB). The reported binding energies are therefore conservative.
- No free-atom and no exohedral references; the decisive endohedral-vs-exohedral comparison is
  still missing.
- Everything is 0 K.
- The qHP reference is the older ring-opened model; the strong qHP stabilisation by Ca/Sr/Ba
  should be re-checked with a defect-free qHP model.
- Sr/Ba networks deserve a spin-polarised check.
- Cs qHP is missing.

## Contents

    report/round3a_2026-11-23_results.md   full report
    data/round3a_cases.csv / .json         per-case results
    data/round3a_per_metal.csv / .json     per-metal summary
    data/round3a_per_metal.md              Appendix A, generated
    data/round3a_cases.md                  Appendix B, generated
    figures/fig1_binding_s_block.png
    figures/fig2_polymerisation_s_block.png
    figures/fig3_metal_positions_s_block.png
    figures/fig4_spin_states_s_block.png
    calculations/<M>/<case>/               INCAR, POSCAR, KPOINTS, OSZICAR, CONTCAR,
                                           OUTCAR.gz, vasp.log, Slurm files
    audit/file_inventory.json              original file inventory
    audit/README.txt                       original provenance note
    audit/potcar_titles.txt                POTCAR dataset titles (no POTCAR content)
    docs/README_package.txt                original round-3a provenance note
    scripts/analyze_round3a.py             re-derives the data files
    scripts/make_round3a_tables.py         re-renders the tables
    scripts/make_round3a_figures.py        re-draws the figures

## Reproduce

    cd round3a_2026-11-23
    python scripts/analyze_round3a.py
    python scripts/make_round3a_tables.py
    python scripts/make_round3a_figures.py

The scripts import the shared parsers from ../pilot_2026-11-18/scripts/analyze_pilot.py and the
reference energies from ../pilot_2026-11-18/data/pilot_summary.json.

## Data policy

POTCAR, WAVECAR and CHGCAR are not included (VASP licence and size). OUTCAR files are
gzip-compressed and unmodified.
