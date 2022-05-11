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
	
	logging.info('================METEOROLOGY MODULE================')

	#load main run json
	json_data = read_run_json()
	met_settings = json_data['user_defined']['meteorology']

	logging.info('Running meteorology: {}'.format(met_settings['model']))
	
	if met_settings['model'] == 'wrf':

		#set environmental variables for met
		set_env_var(met_settings, 'ibc_path')
		set_env_var(met_settings, 'wps_path')
		set_env_var(met_settings, 'wrf_path')
		#'''
		#locate initial conditions
		ibc = met_settings['ibc']
		logging.info('Input boundary conditions: {}'.format(ibc))
		if ibc == 'historic':
			ok = os.path.join(met_settings['ibc_path'],os.environ['forecast'],'ibc.OK')
			os.system('touch {}'.format(ok))
		else:
			#check for valid input
			if ibc not in ["nam", "gfs"]:
				logging.CRITICAL('ERROR: "{}" not a valid IBC type'.format(ibc))
			download_script_path = os.path.join(os.environ['src'],'met',"get_" + ibc)
			os.system('bash {} -d {} {} > /dev/null'.format(download_script_path,os.environ['rundate'],os.environ['cycle']))

		#run wps
		os.system('bash %s/met/run_wps -d %s %s %s' %(os.environ['src'],os.environ['rundate'],os.environ['runhrs'],os.environ['cycle']))
		logging.info('Completed WPS run')

		#run wrf
		os.system('bash %s/met/run_wrf -d %s %s %s' %(os.environ['src'],os.environ['rundate'],os.environ['runhrs'],os.environ['cycle']))
		logging.info('Completed WRF run')
		#'''
		conv_arl.main()

	elif met_settings['model'] == 'nam':
		
		#create and move into hysplit subdirectory
		conv_arl.create_hys_dir()

		#download nam data from arl (already in arl format)
		logging.info('...pulling data from ARL FTP server')
		arl_file = '{}_hysplit.t{}z.namsa.HI'.format(os.environ['rundate'],os.environ['cycle'])
		os.system('wget ftp://anonymous@ftp.arl.noaa.gov/archives/nams/{}'.format(arl_file))
		os.system('mv {} d01.arl'.format(arl_file))

		#update arl path
		json_data['arl'] = '.\/\\nd01.arl'
		update_run_json(json_data)


if __name__ == '__main__':
        main()
