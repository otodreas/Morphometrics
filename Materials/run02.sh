#!/bin/bash
#SBATCH -N 1
#SBATCH --cpus-per-task=1          # increase if models support parallelism
#SBATCH --mem=16G
#SBATCH -t 65:00:00
#SBATCH -J table1_bench
#SBATCH --mail-user=sara.behnamian@sund.ku.dk
#SBATCH --mail-type=FAIL,END

source /opt/software/mamba/23.3.1/etc/profile.d/conda.sh
conda activate base

cd /projects/prohaska/people/bmj860/Morph/Morphometric-Analysis
python scripts/02_Advanced_Morphometric_Classification.py