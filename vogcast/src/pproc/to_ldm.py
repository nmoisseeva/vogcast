#!/usr/bin/python3.7
 
# Script for pushing data to LDM on uila 

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="December 2022"

from set_vog_env import *
import logging
import os

### Functions ###

def to_ldm(ldm_path):
	#archiving script: compresses the main run folder and pushes to remote archive
	logging.info(f'Pushing data to uila LDM: {ldm_path}')
	
	#ensure currently in hysplit direcotry
	hys_dir = os.path.join(os.environ['run_dir'], os.environ['forecast'],'hysplit')
	os.chdir(hys_dir)


	#make starge folder on uila ldm server
	ldm_dir = f'/export/uila4/datafeeds/ldm/data/models/vogcast/{os.environ["forecast"]}'
	mkdir_cmd = f'ssh {ldm_path} "mkdir {ldm_dir}"'
	logging.debug(f'Creating remote folder on uila {mkdir_cmd}')
	os.system(mkdir_cmd)


	#push data (requires ssh key) to ladm
	file_list = ['poe_lvl1_SO2.nc','poe_lvl1_SO4.nc','cmean_SO2.nc','cmean_SO4.nc','poe_lvl2_SO2.nc','poe_lvl2_SO4.nc','poe_lvl3_SO2.nc','poe_lvl3_SO4.nc']
	for item in file_list:
		#copy file to uila
		uila_file_path = os.path.join(ldm_dir,item)
		scp_cmd = f'scp {item} {ldm_path}:{uila_file_path}'
		logging.debug(f'...{scp_cmd}')
		os.system(scp_cmd)

		#send to ldm
		ldm_insert = f'~/bin/pqinsert -x -v -l ~/ingestion/ingest_vogcast.log -f EXP {uila_file_path}'
		pq_cmd = f'ssh {ldm_path} "{ldm_insert}"'
		os.system(pq_cmd)	

	return

def main(settings):
	'''
	Main script for pushing to uila ldm
	'''
	
	to_ldm(settings)

	return

 ### Main ###
if __name__ == '__main__':
	main()		
