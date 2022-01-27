#!/bin/bash
#SBATCH --job-name=vp-main
#SBATCH --account=vmap
#SBATCH --partition=vmap
#SBATCH --time=0-06:00:00
##SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=12G
#SBATCH --exclude=node-[0012-0021]

module purge
source ~/.bash_profile 
source ../venv/bin/activate


python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20210930 00
#python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20210930 12
#python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211001 00
#python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211001 12
#python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211002 00
#python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211002 12
#python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211003 00
#python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211003 12
#python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211004 00
#python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211004 12
#python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211005 00
#python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211005 12
#python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211006 00
#python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211006 12
#python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211007 00
##python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211007 12
