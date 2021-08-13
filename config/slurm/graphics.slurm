#!/bin/bash
#SBATCH --job-name=vp-graphics
#SBATCH --account=vmap
#SBATCH --partition=vmap
#SBATCH --time=0-01:00:00 			## walltime, abbreviated by -t
#SBATCH --error=vp-graphics.%A.err 		## %A - filled with jobid
#SBATCH --output=vp-graphics.%A.out 		## %A - filled with jobid
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=6G
#SBATCH --cpus-per-task=1

source ~/.bash_profile

cd {vogroot}
python3.7 -c 'from graphics import *; make_cont_plot({pollutant})' 
