# Metals inside C60: isolated cage, then 2D networks (qHP, qTP2)

Each folder is one structural optimization (INCAR, POSCAR, KPOINTS, POTCAR_SPEC).
Every cage contains one metal, which starts slightly off-centre: 1.0 A toward a hexagon in the
isolated cage, 0.8 A along the sheet normal in the networks. A metal started exactly at the
centre feels zero force and never moves, which is what happened in the original 32 runs.

## What to run

**STEP 1: `1_pilot_RUN_FIRST/` (12 runs, all independent, submit together)**

- 01-07: Li and Mg inside the isolated C60, the qHP network and the qTP2 network
  (Mg in the isolated cage is run in two spin states).
- 08-12 (`REF_`): references with no metal, plus bulk Li and Mg. These are needed only for
  binding energies. The three no-metal references are run once and shared by all metals.

**STEP 2: `2_all_metals_RUN_AFTER_PILOT/` (168 runs; one subfolder per metal, run
everything in it)**

- `0_REF_<M>_bulk_metal`: the metal's reference energy.
- `1_isolated_C60_<M>_inside[_Nunpaired]`: the metal inside one C60.
- `2_qHP_` / `2_qTP2_<M>_inside_cage[_high_spin|_low_spin]`: the metal inside the network cages.

Suggested order: s-block metals, then 3d, then 4d.

## Why some metals have more than one run per structure

A structural optimization cannot change the spin state, so metals with several plausible
spin states get one run per state.

- Isolated cage: the number of unpaired electrons is fixed (`_0unpaired`, `_2unpaired`, ...).
  - alkali, Cu, Ag, Zn, Cd: 1 run
  - alkaline-earth metals, Sc, Y, Co, Ni, Rh, Pd: 2 runs
  - Ti V Cr Mn Fe Zr Nb Mo Tc Ru: 3 runs
- Networks: d metals with an atomic moment of 2 or more get a high-spin and a low-spin start.

Keep the lowest-energy result.

## Before running: POTCARs

POTCARs are not included. In each top-level folder, run:

    for d in $(find . -name POTCAR_SPEC -printf '%h\n'); do (cd "$d"; for p in $(cat POTCAR_SPEC); do cat $POTDIR/$p/POTCAR; done > POTCAR); done

with POTDIR set to your PAW_PBE_54 directory. The datasets are the same as in your
32-metal screen; Cs_sv and Ba_sv are new.

## Settings (identical everywhere)

- PBE + D3(BJ), ENCUT 520, spin-polarised, ISYM = 0 (except bulk).
  EDIFF = 1E-5; EDIFFG = -0.02 eV/A (bulk: 1E-4 eV energy criterion). d metals also use LMAXMIX = 4.
  Carbons are randomly displaced by 0.02 A.
- Isolated cage: 22 A box with C60 at the centre (needed for IDIPOL = 4), Gamma point,
  fixed NUPDOWN with the initial moment on the metal, smearing 0.005 eV. Linear mixing is
  used only for d metals. You can use the Gamma-only VASP binary (vasp_gam) here.
- Bulk metals: primitive cell, symmetry on, KSPACING 0.12, Methfessel-Paxton smearing 0.1 eV.
- Networks: **one metal inside every cage**. qTP2: 60 C + 1 M per cell (1 cage).
  qHP: 120 C + 2 M per cell (2 cages, both filled; magnetic metals start with parallel
  moments). c (vacuum, along z)
  is fixed at 25 A, giving at least 18 A of empty space. Only a and b relax
  (`LATTICE_CONSTRAINTS = T T F`, VASP 6.4 or later). Dipole correction along z.
  k-mesh 4x3x1 (qHP) or 4x4x1 (qTP2), about 0.13-0.17 x 2pi/A. Both network cells are primitive: qTP2 has 1 cage;
  qHP needs 2, because its two cages are rotated relative to each other.

## Checks after the pilot

1. The metal is still inside the cage. Record its final distance from the cage centre.
2. Isolated cage: the magnetic moment is a whole number.
3. Networks: c is still 25.0 A, and all 8 carbons per cage that bond to neighbouring cages
   are still bonded.
4. Networks and bulk: the run stops on forces (or energy), not on stress. Check the final
   in-plane stress (XX, YY in the last "in kB" line of OUTCAR). If it is above about 2 kB,
   restart once from CONTCAR.

## Results per metal

Use `energy(sigma->0)` from OUTCAR for every energy, because the smearing differs between
the isolated, network and bulk runs.

- Binding in the isolated cage: E(M@C60) - E(REF C60) - E(REF bulk, per atom)
- Binding in the network, per metal atom:
  [E(network with M) - E(REF network) - n x E(REF bulk, per atom)] / n,
  with n = 1 for qTP2 and n = 2 for qHP
- Also record: the metal position, the moment, and whether the network is metallic.
