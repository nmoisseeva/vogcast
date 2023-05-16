#!/bin/bash
#SBATCH --job-name=vp-wrf
#SBATCH --account=vmap
#SBATCH --partition=vmap
#SBATCH --time=0-06:00:00 ## time format is DD-HH:MM:SS
## task-per-node x cpus-per-task should not typically exceed core count on an individual node
#SBATCH --ntasks=190
##SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=6G
#SBATCH --exclude=node-[0269]
#SBATCH --nodes=10
#SBATCH --ntasks-per-node=19
##SBATCH --mem=64G

#------------------------NOTES-----------------------------------
## All options and environment variables found on schedMD site: http://slurm.schedmd.com/sbatch.html
## Intel MPI manual: https://software.intel.com/en-us/mpi-refman-lin-html
## Some Intel MPI Fabricenvironment variables:  https://software.intel.com/en-us/node/528821

#------------------CONFIGURE TO LOCAL ENVIRONMENT (OPTIONAL)-----------------
source ~/.bash_profile
ulimit -S -s unlimited

# Configure the Intel MPI parameters
export I_MPI_FABRICS=shm:ofi
export I_MPI_PMI_LIBRARY=/lib64/libpmi.so
### FOR QDR NETWORK #####
export FI_PROVIDER=psm
export FI_PSM_TAGGED_RMA=0
export FI_PSM_AM_MSG=1
export FI_PSM_UUID=`uuidgen`
###### ######## ###### ##
#---------------------END OF OPTIONAL CONFIGURATION---------------------

# EXECUTE WRF
srun ./wrf.exe
