#!/bin/bash
#SBATCH --job-name=vp-main
#SBATCH --account=vmap
#SBATCH --partition=vmap
#SBATCH --time=0-03:00:00
##SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=12G
#SBATCH --exclude=node-[0012-0021]

module purge
source ~/.bash_profile
source ../venv/bin/activate

python3.7 vog-run 12
