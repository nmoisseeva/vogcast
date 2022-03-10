#!/bin/bash
#SBATCH --job-name=vp-main
#SBATCH --account=vmap
#SBATCH --partition=vmap
#SBATCH --time=0-12:00:00
##SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=12G
#SBATCH --exclude=node-[0012-0021]

module purge
source ~/.bash_profile 
source ../venv/bin/activate

sed -i s/"freq : 12"/"freq : 16"/g ../vog.config
sed -i s/"spinup : 6"/"spinup : 2"/g ../vog.config
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20210930 00
: <<'END'

sed -i s/"freq : 16"/"freq : 12"/g ../vog.config
sed -i s/"spinup : 2"/"spinup : 6"/g ../vog.config
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20210930 12

sed -i s/"temperature: 350"/"temperature: 200"/g ../vog.config
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211001 00


sed -i s/"520000"/"540000"/g ../vog.config
sed -i s/"temperature: 200"/"temperature: 300"/g ../vog.config
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211001 12
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211002 00
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211002 12
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211003 00
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211003 12
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211004 00

sed -i s/"540000"/"520000"/g ../vog.config
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211004 12
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211005 00

python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211005 12
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211006 00


sed -i s/"520000"/"400000"/g ../vog.config
sed -i s/"temperature: 300"/"temperature: 250"/g ../vog.config
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211006 12
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211007 00

sed -i s/"400000"/"200000"/g ../vog.config
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211007 12
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211008 00
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211008 12


sed -i s/"temperature: 250"/"temperature: 150"/g ../vog.config
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211009 00
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211009 12
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211010 00


sed -i s/"200000"/"300000"/g ../vog.config
sed -i s/"temperature: 150"/"temperature: 250"/g ../vog.config
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211010 12



sed -i s/"300000"/"150000"/g ../vog.config
sed -i s/"temperature: 250"/"temperature: 300"/g ../vog.config
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211011 00
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211011 12
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211012 00
python3 vog-run -c /home/moisseev/dev/vog-pipeline/vog.config -d 20211012 12

END
