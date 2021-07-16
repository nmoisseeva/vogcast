#!/usr/bin/python3.7
 
#Script converst wrf output to hysplit arl format

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

import os
import sys
from pathlib import Path
import logging
import glob

 ### Fucntions ###

def create_hys_dir():
	'''
	Set up and navigate to hyslit subdirectory within main run folder
	'''
	#create subdirectory for hysplit files, clean up
	Path(os.environ['hys_rundir']).mkdir(exist_ok=True)
	os.chdir(os.environ['hys_rundir'])
	os.system('find -type l -delete')
	
	return
	
def link_hys_files():
	'''
	Link necessary hysplit files
	'''
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
	for d in range(1,os.environ['met']['max_dom']+1):
		nc_file = glob.glob(wrf_rundir + '/wrfout_d0' + str(d))
		print('found %s' %nc_file)
		arl_file = os.environ['hys_rundir'] + '/d0' + str(d) + '.arl'
		print('saving as: %s' %arl_file)

		#run the conversion
		os.system('./arw2arl -i%s -o%s -c1' %(nc_file, arl_file))

def main():
	'''
	Perform all the conversion steps
	'''
	logging.info('Running conversion to ARL format')	

	#TODO: figure out a more elegant way to deal with ITS environment modules
	os.system('source ~/.bash_profile')


	#check for met completion
	if not os.path.isfile(os.path.join(os.environ['run_path'],'wrf','met.OK')):
		logging.critical("Missing met.OK file: ensure meteorology has completed. Aborting.")
		sys.exit()
		
	#set up hysplit directory
	create_hys_dir()
	link_hys_files()

	#convert
	convert_to_arl()
	logging.info('arw2arl conversion is complete')

	return

 ### Main ###

if __name__ == '__main__':
	main()		
