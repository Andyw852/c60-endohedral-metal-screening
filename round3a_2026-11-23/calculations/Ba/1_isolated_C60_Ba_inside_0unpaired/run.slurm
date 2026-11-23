#!/bin/bash
#SBATCH -J Ba_iso_0u
#SBATCH -N 1
#SBATCH --ntasks-per-node=64
#SBATCH -p hfacexclu08
#SBATCH -o %j.out
#SBATCH -e %j.err
set -e
module purge
module load compiler/intel/2021.3.0
module load mpi/intelmpi/2021.3.0
export MKL_DEBUG_CPU_TYPE=5
export MKL_CBWR=AVX2
mpirun -np 64 /public/home/xinyuez2025/vasp6.4.3/vasp.6.4.3/bin/vasp_std > vasp.log 2>&1
