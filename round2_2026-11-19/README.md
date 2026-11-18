# Round 2 (2026-11-19): three calculations

| Folder | Purpose |
|---|---|
| `13_qHP_network_Mg_inside_cage_restart_nonmagnetic` | Restart of pilot case 05 from its CONTCAR, non-magnetic (`ISPIN = 1`) |
| `14_qHP_network_Mg_inside_cage_restart_2unpaired` | Restart of pilot case 05 from its CONTCAR, fixed `NUPDOWN = 2` |
| `15_isolated_C60_Li_cation_inside_check` | [Li@C60]+ (`NELECT = 240`, plain Li POTCAR); Li+ should end up off-centre |

All other settings are identical to the pilot. 13 and 14 add `KPAR = 4` (parallelisation only,
so energies stay comparable). Pass criteria and context: [../PROJECT_STATUS.md](../PROJECT_STATUS.md), section 6.
