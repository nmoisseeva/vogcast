#!/usr/bin/python3.7
 
#Script converst wrf output to hysplit arl format

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

import os
import sys
from pathlib import Path
import logging
import glob
from set_vog_env import *

 ### Fucntions ###

def create_hys_dir():
	'''
	Create a hysplit subdirectory within main run folder, if necessary 
	'''
	#create subdirectory for hysplit files, clean up
	Path(os.environ['hys_rundir']).mkdir(exist_ok=True)
	os.chdir(os.environ['hys_rundir'])
	#os.system('find -type l -delete')

	return

def setup_hys_dir():
	'''
	Set up and navigate to hyslit subdirectory within main run folder
	'''
	create_hys_dir()
	
	try:
		os.remove('ARLDATA.CFG')
	except:
		pass

	#link conversion table
	wrfcfg = os.path.join(os.environ['vog_root'],'config','hysplit','WRFDATA.CFG')	
	#os.symlink(wrfcfg, 'WRFDATA.CFG')
	symlink_force(wrfcfg, 'WRFDATA.CFG')

	#link necessary executables
	arw2arl = os.path.join(os.environ['hys_path'],'exec','arw2arl')
	#os.symlink(arw2arl,'./arw2arl')
	symlink_force(arw2arl,'./arw2arl')

	return
	
def convert_to_arl():
	'''
	Run the conversion to arl
	'''	
	#get local subdirectories within run folder
	wrf_rundir = os.path.join(os.environ['run_path'],'meteorology')

	#loop through all domains
	#lines to write to run json for auto-config of hysplit CONTROL
	lines = ''
	for d in range(1,int(os.environ['max_dom'])+1):
		#clean up old config
		if d > 1:
			try:
				os.remove('ARLDATA.CFG')
			except:
				logging.critical('ERROR: WRF to ARL conversion failed, check logs in "hysplit" subforlder')
				sys.exit()
		
		
		nc_file = glob.glob(wrf_rundir + '/wrfout_d0' + str(d) + '*')[0]
		logging.debug('Wrfout file: %s' %nc_file)
		arl_file = 'd0' + str(d) + '.arl'

		#run the conversion
		os.system('./arw2arl -i%s -o%s -c1 > arw2arl_d0%s.log' %(nc_file, os.path.join(os.environ['hys_rundir'],  arl_file), d))
		
		lines = lines + '.\/\\n' + arl_file + '\\n'

	#remove newline character from the last line
	lines = lines[:-2]

	#append run json with arl file information
	json_data = read_run_json()
	json_data['arl'] = lines
	update_run_json(json_data)

	return

def main():
	'''
	Perform all the conversion steps
	'''
	logging.info('Running conversion to ARL format')	

	#check for met completion
	met_path = os.path.join(os.environ['run_path'],'meteorology','wrfout*')
	if len(glob.glob(met_path))==0:
	#if not os.path.isfile(met_ok):
		logging.critical("ERROR: Did not find and wrfout files. Ensure met is availble. Aborting.")
		sys.exit()
		
	#set up hysplit directory
	setup_hys_dir()

	#convert
	convert_to_arl()
	logging.info('arw2arl conversion is complete')

	return

 ### Main ###

if __name__ == '__main__':
	main()		
