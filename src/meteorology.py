#!/usr/bin/python3.7
 
#This script runs meteorology for the pipelene options: 'wrf', 'nam', 'none'

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

import os
import logging
from set_vog_env import *
import glob
import met.conv_arl as conv_arl
import datetime as dt


def pull_archived_arl(met_settings):
	'''
	Designtated function to deal with archived arl data, accounting for multi-day rusn
	'''
	#if the run is less than one day, just donwload the single day file
	runhrs = int(os.environ['runhrs'])
	if runhrs < 24:
		arl_file = '{}_hysplit.t{}z.namsa.HI'.format(os.environ['rundate'],os.environ['cycle'])
		os.system('wget -N ftp://anonymous@ftp.arl.noaa.gov/archives/nams/{} -P {}'.format(arl_file,met_settings['arl_path']))
		os.system('ln -sf {} d01.arl'.format(os.path.join(met_settings['arl_path'],arl_file)))
		control_lines = '.\/\\nd01.arl'
		arl_cnt = 1
	#for multiple days, link the files as separate domains (adding logic in dispersion module to account for that)
	else:
		logging.debug('WARNING: multi-day simulation with archived ARL data. Downloading multiple arl files')
		rundays = int(runhrs/24.) + 1
		control_lines = ''
		for d in range(0, rundays):
			fc_date = dt.datetime.strptime(os.environ['forecast'],'%Y%m%d%H')
			arl_date = fc_date + dt.timedelta(hours=24*d)
			date_str = dt.datetime.strftime(arl_date,'%Y%m%d')
			arl_file = '{}_hysplit.t{}z.namsa.HI'.format(date_str,os.environ['cycle'])
			os.system('wget -N ftp://anonymous@ftp.arl.noaa.gov/archives/nams/{} -P {}'.format(arl_file,met_settings['arl_path']))
			dd = d + 1			
			arl_full_path = os.path.join(met_settings['arl_path'],arl_file)
			os.system(f'ln -sf {arl_full_path} d{dd:02}.arl')

			control_lines = control_lines + '.\/\\nd' + f'{dd:02}.arl' + '\\n'

		#remove newline character from the last line
		control_lines = control_lines[:-2]
		arl_cnt = dd

	return control_lines, arl_cnt



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

		#check what kind of arl data to pull: production or archive
		if met_settings['type'] == "prod":
			logging.info('...pulling production ARL data from NOMADS server')
			arl_file = 'hysplit.t{}z.namsf.HI'.format(os.environ['cycle'])
			os.system('wget -N https://nomads.ncep.noaa.gov/pub/data/nccf/com/hysplit/prod/hysplit.{}/{}'.format(os.environ['rundate'],arl_file))
			os.system('ln -sf {} d01.arl'.format(arl_file))
			control_lines = '.\/\\nd01.arl'
			arl_cnt = 1

		elif met_settings['type'] == "archive":
			logging.info('...pulling archived ARL data from NOAA FTP server')
			control_lines, arl_cnt  = pull_archived_arl(met_settings)
			#arl_file = '{}_hysplit.t{}z.namsa.HI'.format(os.environ['rundate'],os.environ['cycle'])
			#os.system('wget -N ftp://anonymous@ftp.arl.noaa.gov/archives/nams/{} -P {}'.format(arl_file,met_settings['arl_path']))
			#os.system('ln -sf {} d01.arl'.format(os.path.join(settings['arl_path'],arl_file))
		else:
			logging.critical('ERROR: missing "type" parameter for ARL data. Available options: "prod"/"archive"')

		#download nam data from arl (already in arl format)
		#logging.info('...pulling data from ARL FTP server')
		#arl_file = '{}_hysplit.t{}z.namsa.HI'.format(os.environ['rundate'],os.environ['cycle'])
		#os.system('wget ftp://anonymous@ftp.arl.noaa.gov/archives/nams/{}'.format(arl_file))
		
		#os.system('ln -sf {} d01.arl'.format(arl_file))

		#update arl path
		#json_data['arl'] = '.\/\\nd01.arl'
		json_data['arl'] = control_lines
		json_data['arl_cnt'] = str(arl_cnt)
		update_run_json(json_data)


	elif met_settings['model'] == 'prerun':
		
		#run wrf to arl conversion 
		logging.info(f"Using existing WRF data: {met_settings['prerun_path']}")
		met_dir = os.path.join(os.environ['run_path'],'meteorology')
		os.system(f'mkdir -p {met_dir}')
		os.system(f'ln -sf {met_settings["prerun_path"]}/wrfout* {met_dir}') 
		conv_arl.main()

if __name__ == '__main__':
        main()
