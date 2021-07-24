#!/usr/bin/python3.7
 
# The  script pulls emissions data from HVO-API

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

from set_vog_env import *
import logging
import json
import os

### Functions ###

def ensmean():
	'''
	Run ensemble averaging
	'''
	logging.debug('...creating ensemble average')

	#move into dispersion working directory, clean up
	os.chdir(os.environ['hys_rundir'])
	os.system('find -type l -delete')

	#TODO check that that dispersion complete

	#link enecutables
	conprob = os.path.join(os.environ['hys_path'],'exec','conprob')
	os.symlink(conprob, './conprob')

	#run hysplit averaging utility
	os.system('./conprob -bcdump') 

	return

def main():
	'''
	Main script for dispersion post-processing. 
	
	Returns:
	- ensemble-avareged surface concentrations
	- probabilities of exceedance for user-defined thresholds
	- station traces
	'''

	logging.info('Running post-processing steps')

	json_data = read_run_json()

	#create ensemble average
	ensmean()

	#create POE for user-defined thresholds, if requested 
	

	#create station traces for user-defined stations, if requested


	#update run json with extra data
	#json_data['emissions'] = {'so2' : so2, 'obs_date': obs_date }
	#update_run_json(json_data)

	logging.info('Post-processing complete')


 ### Main ###
if __name__ == '__main__':
	main()		
