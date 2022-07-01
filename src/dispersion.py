#!/usr/bin/python3.7
 
#This script preps and initializes an ensemble hysplit run


__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

import os
import logging
from set_vog_env import *
import glob
import datetime as dt
from random import randrange

 ### Fucntions ###

def link_hysplit():
	'''
	Link and copy hysplit config files and executables
	'''
	#move into dispersion working directory
	os.chdir(os.environ['hys_rundir'])

	#set up necessary configuration files
	os.system('rm *.OK VMSDIST* PARDUMP* MESSAGE* WARNING* *.out *.err cdump* CONC.CFG > /dev/null 2>&1')
	hys_config_path = os.path.join(os.environ['vog_root'],'config','hysplit')
	os.system('cp ' + hys_config_path + '/CONTROL .')
	os.system('cp ' + hys_config_path + '/SETUP.CFG .')

	#link static config files
	symlink_force(hys_config_path + '/CHEMRATE.TXT', 'CHEMRATE.TXT')
	slurm_config_path = os.path.join(os.environ['vog_root'],'config','slurm')
	symlink_force(slurm_config_path + '/hysplit.slurm', 'hysplit.slurm')

	#link bdyfiles
	#TODO get from wrf: https://www.ready.noaa.gov/documents/TutorialX/html/emit_fine.html
	symlink_force(hys_config_path + '/ASCDATA.CFG', 'ASCDATA.CFG')
	bdy_path = os.path.join(os.environ['hys_path'],'bdyfiles','bdyfiles0p1')
	symlink_force(bdy_path + '/LANDUSE.ASC', 'LANDUSE.ASC')
	symlink_force(bdy_path + '/ROUGLEN.ASC', 'ROUGLEN.ASC')	

	#link executable
	hycs_ens = os.path.join(os.environ['hys_path'],'exec','hycs_ens')
	symlink_force(hycs_ens,'./hycs_ens')
	
	#TODO: this section is for testing existing GFS runs only
	#os.system('mv d01.arl ../meteorology/.') 	#moving to met folder for storage
	#link_gfs_arl = os.path.join(os.environ['run_dir'],'wrf_gfs','L900','wrf0.9km_{}'.format(os.environ['forecast']))
	#link_gfs_arl = os.path.join(os.environ['run_dir'],'wrf_gfs','5km','wrf4.5km_{}'.format(os.environ['forecast']))
	#symlink_force(link_gfs_arl, './d01.arl')
	symlink_force('../meteorology/d01.arl', './d01.arl')

	return

def edit_hys_config(json_data):
	'''
	Edit hysplit configuration settings for the run
	'''
	#TODO: all this is pretty ugly, look for more elegant ways

	#get settings from run_json
	user = json_data['user_defined']

	#edit CONTROL: set start time relative to met
	sed_command('{spinup}', '{:02d}'.format(int(os.environ['spinup'])) , 'CONTROL')
	#edit CONTROL:source count
	src_cnt = str(json_data['plumerise']['src_cnt'])
	sed_command('{src_cnt}', src_cnt, 'CONTROL')
	logging.debug(f'...number of emissions strating points (including vertical) is set to: {src_cnt}')
	#edit CONTROL: hysplit run hours
	hys_hrs = str(user['runhrs'] - int(os.environ['spinup']))
	sed_command('{hys_hrs}', hys_hrs, 'CONTROL')
	logging.debug('...Hysplit run hours set to: %s ' %hys_hrs)
	#edit CONTROL max domain
	sed_command('{max_dom}', os.environ['max_dom'], 'CONTROL')
	#copy arl path data into CONTROL
	sed_command('{arl_paths}', json_data['arl'], 'CONTROL')
	#copy all sources into CONTROL
	sources = json_data['plumerise']['sources']
	sed_command('{sources}', sources, 'CONTROL')
	#set vertical motion option
	sed_command('{vert_motion}', str(user['dispersion']['vert_motion']), 'CONTROL')
	#set vertical levels
	lvls = user['dispersion']['lvls']
	num_lvls = str(len(lvls))
	sed_command('{num_lvls}', num_lvls, 'CONTROL')
	lvls_str = " ". join([str(i) for i in lvls])
	sed_command('{lvls}', lvls_str, 'CONTROL')

	#edit SETUP.CFG	
	sed_command('{freq}', os.environ['freq'], 'SETUP.CFG')
	sed_command('{min_zi}', str(user['dispersion']['min_zi']), 'SETUP.CFG')

	#link carryover vog
	fc_date = dt.datetime.strptime(os.environ['forecast'], '%Y%m%d%H')
	co_date = fc_date - dt.timedelta(hours=int(os.environ['freq']))
	co_date_str = co_date.strftime('%Y%m%d%H')
	carryover_file = os.path.join(user['dispersion']['carryover_path'],'PARINIT.{}'.format(co_date_str))
	if os.path.isfile(carryover_file):
		#os.symlink(carryover_file, 'PARINIT')
		logging.debug('...linking carryover vog from: %s' %carryover_file)
		#loop through ensemble members
		for i in range(1,28):
			#os.symlink(carryover_file, 'PARINIT.{:03d}'.format(i))
			symlink_force(carryover_file, 'PARINIT.{:03d}'.format(i))
	else:
		logging.warning('...WARNING: No carryover found from previous cycle')

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
	logging.info('...submitting hysplit ensemble to slurm')
	os.system('sbatch -W hysplit.slurm')

	#make sure all members completed
	#TODO: needs correction - this doesn't actually ensure successful completion
	member_cnt = len(glob.glob('./hys_member*.OK'))
	if member_cnt == 27:
		os.system('touch dispersion.OK')

def save_carryover(json_data):
	'''
	Save carryover smoke for next run cycle
	'''
	
	#always save .001 as carryover (for reproducible runs)
	parfile = 'PARDUMP.001'
	savefile = 'PARINIT.{}'.format(os.environ['forecast'])
	save_path = os.path.join(json_data['user_defined']['dispersion']['carryover_path'], savefile)

	#make a copy
	os.system('cp {} {}'.format(parfile,save_path))
	logging.debug('...saving carryover: %s as %s' %(parfile, save_path))

	return

def main():
	'''
	Run dispersion 
	'''
	logging.info('=================DISPERSION MODULE=================')	

	#load main run json
	json_data = read_run_json()
	hys_settings = json_data['user_defined']['dispersion']

	#set environmental variables for dispersion
	config_keys = ['freq']
	for key in config_keys:
		set_env_var(hys_settings, key)

	#link config and executables
	link_hysplit()		
	
	#edit config for the run
	edit_hys_config(json_data)
	
	#start the run
	run_ensemble()

	#save carryover smoke
	save_carryover(json_data)

	logging.info('Ensemble dispersion run complete')


	return

 ### Main ###

if __name__ == '__main__':
	main()		
