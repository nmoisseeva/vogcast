#!/usr/bin/python3.7
 
#This script runs meteorology for the pipelene options: 'wrf', 'nam', 'none'

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

import os
import logging
from set_vog_env import *
import glob
import met.conv_arl as conv_arl


def main():

	#load main run json
	json_data = read_run_json()
	met_settings = json_data['user_defined']['meteorology']

	logging.info('Running meteorology: {}'.format(met_settings['model']))
	
	if met_settings['model'] == 'wrf':

		#set environmental variables for met
		set_env_var(met_settings, 'ibc_path')
		set_env_var(met_settings, 'wps_path')
		set_env_var(met_settings, 'wrf_path')

		#download initial conditionsi
		#TODO check for existing files before downloading, create ibc.OK
		os.system('bash %s//met/get_nam -d %s %s > /dev/null' %(os.environ['src'],os.environ['rundate'],os.environ['cycle']))

		#run wps
		os.system('bash %s/met/run_wps -d %s %s %s' %(os.environ['src'],os.environ['rundate'],os.environ['runhrs'],os.environ['cycle']))
		logging.info('Completed WPS run')

		#run wrf
		os.system('bash %s/met/run_wrf -d %s %s %s' %(os.environ['src'],os.environ['rundate'],os.environ['runhrs'],os.environ['cycle']))
		logging.info('Completed WRF run')

		conv_arl.main()

	elif met_settings['model'] == 'none':
	
		#update run json with path to existing arl files
		json_data['arl'] = met_settings['arl_paths']
		update_run_json(json_data)

	elif met_settings['model'] == 'nam':
		
		#TODO nam runs will go here
		#download nam data from arl (already in arl format)
		#update arl path
		logging.debug('NAM-based runs will go here')


if __name__ == '__main__':
        main()