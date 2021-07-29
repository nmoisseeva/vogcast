#!/usr/bin/python3.7
 
# Script for generating hysplit ensemble averages, station traces and POEs

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

	#TODO check that that dispersion completed

	#link executables
	conprob = os.path.join(os.environ['hys_path'],'exec','conprob')
	os.symlink(conprob, './conprob')

	#run hysplit averaging utility
	os.system('./conprob -bcdump') 

	return

def stn_traces(tag,stn_file):
	'''
	Script extracts ensmean concentrations from user-defined stations
	'''
	logging.debug('...creating station traces')

	#link executables
	con2stn = os.path.join(os.environ['hys_path'],'exec','con2stn')
	os.symlink(con2stn, './con2stn')

	#extract station data
	out_file = 'HYSPLIT_so2.{}.{}.txt'.format(os.environ['forecast'],tag)
	con2stn_cmd = './con2stn -p1 -d2 -z2 -icmean -o{} -s{} -xi'.format(out_file,stn_file)
	os.system(con2stn_cmd)

	#copy to mkwc for web
	logging.debug('...copying data to mwkc')
	mkwc_file = 'hysplit.haw.{}.so2.{}.txt'.format(tag,os.environ['forecast'])
	scp_cmd = 'scp {} vmap@mkwc2.ifa.hawaii.edu:www/hysplit/text/{}'.format(out_file, mkwc_file)
	print(scp_cmd)
	os.system(scp_cmd)

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
	pproc_settings = json_data['user_defined']['post_process']['stns']
	stn_traces(pproc_settings['tag'],pproc_settings['stn_file'])

	#update run json with extra data
	#json_data['emissions'] = {'so2' : so2, 'obs_date': obs_date }
	#update_run_json(json_data)


	logging.info('Post-processing complete')


 ### Main ###
if __name__ == '__main__':
	main()		
