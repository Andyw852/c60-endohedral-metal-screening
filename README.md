# Endohedral metals in C60 and qHP/qTP fullerene networks

**Project status, goals and next steps (Chinese): [PROJECT_STATUS.md](PROJECT_STATUS.md)**

This repository contains an independent audit of a 32-metal "endohedral metal in C60"
screening campaign and a feasibility assessment for using endohedral M@C60 units as
building blocks of qHP/qTP fullerene networks.

The full analysis is in **report/endohedral_c60_network_feasibility_report.md**.
The first corrected endohedral calculations (Li and Mg, isolated C60, qHP and qTP2) are in
**pilot_2026-11-18/report/pilot_2026-11-18_results.md**.

## Key findings

1. **The 20 / 6 / 6 classification is numerically correct.** An independent re-parse of
   the delivered OUTCAR, OSZICAR and CONTCAR files reproduces every final force, every
   SCF-at-NELM count, every termination mode and the 90-bond cage check.
2. **It is not evidence of endohedral stability.** All 32 metals stayed within 0.001 A
   of the exact cage centre (largest 0.00095 A, Fe); 18 of the 20 "passing" systems
   stopped after five or fewer ionic steps, and four stopped after one step. An atom at
   the inversion centre of an Ih-symmetric C60 has zero force by symmetry, so a
   force-based relaxator cannot distinguish a minimum from a saddle or a maximum.
3. **The cage survives all 32 attempts** (90 C-C bonds, all carbons three-coordinated),
   so the 20 are a valid candidate shortlist for a rigorous stability study.
4. **The qHP/qTP route is plausible but must be re-sequenced:** first prove a true
   endohedral minimum and a site preference over exohedral binding, then prove that the
   metal survives polymerisation, and only then build the network. The decisive
   comparison is endohedral versus exohedral energy at the same composition.

## Pilot results (2026-11-18)

Twelve calculations (Li and Mg inside isolated C60, qHP and qTP2, plus references) were
run from off-centre starts with fixed spin states. Eleven finished; the qHP Mg run was
cancelled and is not converged.

- **The method fix works.** Li moves off-centre (1.50 A in the isolated cage, 1.33-1.43 A
  in the networks), while Mg relaxes back to the centre (0.02 A isolated, 0.01 A in qTP2).
  The original centre-start screen could not have seen this difference.
- **The networks survive one metal per cage at 0 K.** 188 C-C bonds (qHP) and 94 (qTP2)
  are preserved, no carbon changes coordination, the longest C-C bond is 1.62 A, and the
  in-plane stress is below 0.5 kB.
- **Energies (PBE+D3, versus bulk metal):** Li in qHP -0.020 eV per Li, Li in isolated
  C60 +0.244, Li in qTP2 +0.261; Mg in isolated C60 +1.506, Mg in qTP2 +1.392. Li makes
  qHP polymerisation more favourable by 0.53 eV per two cages.
- **Caveats:** the bulk references include D3(BJ) and are not fully converged, no free-atom
  references were calculated, the qHP reference is the older ring-opened model, the qHP Mg
  run is missing, and the exohedral competitors have not yet been computed. See the pilot
  report for the full discussion and next steps.

## Repository layout

    report/
        endohedral_c60_network_feasibility_report.md    main English report
    data/
        screening_summary.csv / .json                   per-system audit table
        screening_table.md                              generated table (Appendix A)
        network_geometry.csv / network_table.md          generated table (Appendix D)
        accounting.txt, collection_manifest.json,
        existing_inventory.json, queue.txt              original bundle metadata
    calculations/
        center32_screen/                                19 new centre-start runs
        pilot_Li_Fe/, batch_20261016/, batch_20261021/,
        batch_20261023/, stage4_20261106/,
        stage5_controlled_20261109/, Mg_center_m0_tight_s002/
                                                        13 reused calculations
    network_reference/
        *.POSCAR                                        qHP/qTP and Mg2C60 reference cells
        band_gaps/*.json                                PBEsol/HSE band summaries
    figures/
        fig1_force_convergence.png
        fig2_symmetry_trap.png
        fig3_scf_history.png
        fig4_cage_breathing.png
    scripts/
        audit_screening.py                              independent audit
        network_geometry.py                             network descriptors
        make_figures.py                                 figures
        make_tables.py                                  Markdown tables
    docs/
        32种金属C60中心初筛汇报.docx                      original Chinese source report
    pilot_2026-11-18/
        report/pilot_2026-11-18_results.md              pilot report (Li/Mg, C60/qHP/qTP2)
        data/pilot_summary.csv / .json                  machine-readable pilot results
        data/pilot_table.md                             generated run table
        figures/fig1..fig3                              binding, positions, polymerisation
        calculations/<case>/                            INCAR, POSCAR, KPOINTS, OSZICAR,
                                                        CONTCAR, OUTCAR.gz, vasp.log
        audit/, docs/, scripts/                         provenance, inputs, analysis scripts

## Reproducing the audit

Requirements: Python 3.9 or newer, numpy, matplotlib; scipy is optional (used only for
the point-in-cage convex-hull test) and matplotlib is needed only for the figures.

    python scripts/audit_screening.py
    python scripts/network_geometry.py
    python scripts/make_figures.py
    python scripts/make_tables.py

The audit script writes data/screening_summary.csv and data/screening_summary.json.
The tables in the report are generated by make_tables.py from those CSV files, so the
report and the machine-readable data cannot drift apart.

## Data provenance and caveats

- The 32-metal calculations were delivered as the bundle
  "review_center32_final_20261116_102102_870377" and are copied here unchanged, except that
  the original archive itself is not duplicated.
- The pilot calculations were delivered as "pilot_all_for_senior_20261118_151225_993533".
  OUTCAR files are gzip-compressed here; POTCAR files are excluded from both data sets.
- POTCAR, WAVECAR and CHGCAR files are not included, following the original bundle policy
  (POTCAR licensing and file size).
- The original bundle README notes that historical reuse flags must be reviewed, especially
  for V, Fe, Co and Zr, and that the records do not by themselves certify convergence.
- No new density-functional calculations were performed for this audit. All conclusions
  about stability that go beyond the delivered data are clearly marked as recommendations
  or as proposed calculations in the report.

## License and citation

This is unpublished research material. No open licence is granted at this stage; please
contact the authors before reusing the data or the text. If you cite this work, cite the
report file and this repository.
