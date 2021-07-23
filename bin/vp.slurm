#!/bin/bash
#SBATCH --job-name=vp-main
#SBATCH --account=vmap
#SBATCH --partition=vmap
#SBATCH --time=0-03:00:00
##SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=6G

module purge
source ~/.bash_profile

python3.7 vog-run -d 20210102 12
