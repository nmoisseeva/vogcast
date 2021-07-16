#!/bin/bash
#SBATCH --array=1-27
#SBATCH --job-name=vp-hysplit
#SBATCH --account=vmap
#SBATCH --partition=vmap
#SBATCH --time=0-01:00:00 			## walltime, abbreviated by -t
#SBATCH --error=vp-hysplit.%A_%a.err 		## %A - filled with jobid
#SBATCH --output=vp-hysplit.%A_%a.out 		## %A - filled with jobid
#SBATCH --ntasks=1
#SBATCH --mem=4G
#SBATCH --cpus-per-task=1

# usage: sbatch hysplit.slurm #ensemblemember

./hycs_ens ${SLURM_ARRAY_TASK_ID}
touch hys_member.${SLURM_ARRAY_TASK_ID}.OK
