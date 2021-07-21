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

def setup_hys_dir():
	'''
	Set up and navigate to hyslit subdirectory within main run folder
	'''
	#create subdirectory for hysplit files, clean up
	Path(os.environ['hys_rundir']).mkdir(exist_ok=True)
	os.chdir(os.environ['hys_rundir'])
	os.system('find -type l -delete')
	os.remove('WRFDATA.CFG')
	os.remove('ARLDATA.CFG')
	#TODO check if existing arl files are a problem for overwriting	
	
	#link necessary executables
	arw2arl = os.path.join(os.environ['hys_path'],'exec','arw2arl')
	os.symlink(arw2arl,'./arw2arl')

	return
	
def convert_to_arl():
	'''
	Run the conversion to arl
	'''	
	#get local subdirectories within run folder
	wrf_rundir = os.path.join(os.environ['run_path'],'wrf')

	#loop through all domains
	#lines to write to run json for auto-config of hysplit CONTROL
	lines = ''
	for d in range(1,int(os.environ['max_dom'])+1):
		nc_file = glob.glob(wrf_rundir + '/wrfout_d0' + str(d) + '*')[0]
		logging.debug('Wrfout file: %s' %nc_file)
		arl_file = 'd0' + str(d) + '.arl'

		#run the conversion
		os.system('./arw2arl -i%s -o%s -c1 > arw2arl.log' %(nc_file, os.path.join(os.environ['hys_rundir'],  arl_file)))
		
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

	#TODO: figure out a more elegant way to deal with ITS environment modules
	os.system('source ~/.bash_profile')

	#check for met completion
	if not os.path.isfile(os.path.join(os.environ['run_path'],'wrf','met.OK')):
		loggin.debug(os.path.join(os.environ['run_path'],'wrf','met.OK'))
		logging.critical("Missing met.OK file: ensure meteorology has completed. Aborting.")
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
