#!/usr/bin/python3.7
 
#This script preps and initializes an ensemble hysplit run


__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

import os
import logging
from set_vog_env import *
import glob
import datetime as dt

 ### Fucntions ###

def link_hysplit():
	'''
	Link and copy hysplit config files and executables
	'''
	#move into dispersion working directory
	os.chdir(os.environ['hys_rundir'])

	#set up necessary configuration files
	os.system('find -type l -delete')
	os.system('rm *.OK VMSDIST* PARDUMP* MESSAGE* WARNING* *.out *.err cdump* CONC.CFG')
	hys_config_path = os.path.join(os.environ['vog_root'],'config','hysplit')
	os.system('cp ' + hys_config_path + '/CONTROL .')
	os.system('cp ' + hys_config_path + '/SETUP.CFG .')

	#link static config files
	os.symlink(hys_config_path + '/CHEMRATE.TXT', 'CHEMRATE.TXT')
	os.symlink(hys_config_path + '/hysplit.slurm', 'hysplit.slurm')

	#link bdyfiles
	#TODO get from wrf: https://www.ready.noaa.gov/documents/TutorialX/html/emit_fine.html
	os.symlink(hys_config_path + '/ASCDATA.CFG', 'ASCDATA.CFG')
	bdy_path = os.path.join(os.environ['hys_path'],'bdyfiles','bdyfiles0p1')
	os.symlink(bdy_path + '/LANDUSE.ASC', 'LANDUSE.ASC')
	os.symlink(bdy_path + '/ROUGLEN.ASC', 'ROUGLEN.ASC')

	#link executable
	hycs_ens = os.path.join(os.environ['hys_path'],'exec','hycs_ens')
	os.symlink(hycs_ens,'./hycs_ens')

	return

def edit_hys_config():
	'''
	Edit hysplit configuration settings for the run
	'''
	#TODO: all this is pretty ugly, look for more elegant ways

	#get settings from run_json
	json_data = read_run_json()
	user = json_data['user_defined']

	#edit CONTROL:date
	fc_date = dt.datetime.strptime(os.environ['forecast'], '%Y%m%d%H')
	hys_date = fc_date + dt.timedelta(hours=int(os.environ['spinup']))
	hys_date_str = hys_date.strftime('%Y %m %d %H')
	sed_command('{YYYY MM DD HH}', hys_date_str, 'CONTROL')
	logging.debug('Dispersion start set to: %s' %hys_date_str)
	#edit CONTROL:source count
	src_cnt = str(json_data['plumerise']['src_cnt'])
	sed_command('{src_cnt}', src_cnt, 'CONTROL')
	logging.debug('Source count set to: %s' %src_cnt)
	#edit CONTROL: hysplit run hours
	hys_hrs = str(user['runhrs'] - int(os.environ['spinup']))
	sed_command('{hys_hrs}', hys_hrs, 'CONTROL')
	logging.debug('Hysplit run hours set to: %s ' %hys_hrs)
	#edit CONTROL max domain
	sed_command('{max_dom}', os.environ['max_dom'], 'CONTROL')
	#copy arl path data into CONTROL
	logging.debug(json_data['arl'])
	sed_command('{arl_paths}', json_data['arl'], 'CONTROL')
	#copy all sources into CONTROL
	sources = json_data['plumerise']['sources']
	sed_command('{sources}', sources, 'CONTROL')
	#offset emissions start from met
	sed_command('{spinup}', '{:02d}'.format(int(os.environ['spinup'])) , 'CONTROL')
	#set vertical motion option
	sed_command('{vert_motion}', str(user['dispersion']['vert_motion']), 'CONTROL')


	#edit SETUP.CFG
	sed_command('{spinup}', os.environ['spinup'], 'SETUP.CFG')
	sed_command('{min_zi}', str(user['dispersion']['min_zi']), 'SETUP.CFG')

	return
	
def sed_command(old_str, new_str, filename):
	'''
	Constructs and runs shell sed command for replacing config tags
	'''
	#construct the command
	sed_cmd = 'sed -i "s/' + old_str + '/' + new_str + '/g" ' + filename

	#run the command
	os.system(sed_cmd)

	return

def run_ensemble():
	'''
	Start the ensemble run
	'''

	#start the run
	logging.info('Submitting hysplit ensemble to slurm')
	os.system('sbatch -W hysplit.slurm')

	#make sure all members completed
	member_cnt = len(glob.glob('./hys_member*.OK'))
	if member_cnt == 27:
		os.system('touch dispersion.OK')

	return

def main():
	'''
	Run dispersion 
	'''
	logging.info('Running dispersion')	
	
	#link config and executables
	link_hysplit()		
	
	#edit config for the run
	edit_hys_config()
	
	#TODO: link carryover vog from previous cycle
	#link_carryover()

	#start the run
	run_ensemble()

	logging.info('Ensemble dispersion run complete')



	return

 ### Main ###

if __name__ == '__main__':
	main()		
