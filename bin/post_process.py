#!/usr/bin/python3.7
 
# Script for generating hysplit ensemble averages, station traces, POEs, archiving and web display

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

from set_vog_env import *
from graphics import*
import to_webserver
import logging
import json
import os

### Functions ###

def link_exec(hysexec):
	'''
	Function to link hysplit executables into a local directory
	'''

	#create path to file
	exec_path =  os.path.join(os.environ['hys_path'], 'exec', hysexec)
	local_path = './{}'.format(hysexec)

	#create symlink
	try:
		os.symlink(exec_path, local_path)
	except:
		os.remove(local_path)
		os.symlink(exec_path, local_path)
	return

def ensmean(pproc_settings):
	'''
	Run ensemble averaging
	'''
	#move into dispersion working directory, clean up
	os.chdir(os.environ['hys_rundir'])
	os.system('find -type l -delete')

	#TODO check that that dispersion completed
	#TODO fix for consistency with POE plots

	#link executables
	link_exec('conprob')
	
	for iP, pollutant in enumerate(pproc_settings['conversion']):
		logging.info('...creating ensemble average: {}'.format(pollutant))
		pflag = '-p{}'.format(str(iP + 1))
		#run hysplit averaging utility
		os.system('./conprob -bcdump {}'.format(pflag)) 
		to_netcdf('cmean', 'cmean_{}.nc'.format(pollutant))		

		#save ncmean for pollutants with requested stn traces
		logging.debug('...saving as cmean_{} for future use'.format(pollutant))
		os.system('mv cmean cmean_{}'.format(pollutant))
	return

def get_poe(pproc_settings):
	'''
	Get probabilities of exceedance for all user-defined pollutants and thresholds
	'''
	logging.info('...calculating exceedance probabilities')
	
	#move into dispersion working directory, clean up
	os.chdir(os.environ['hys_rundir'])
	os.system('find -type l -delete')
	
	#TODO check that that dispersion completed

	#link executables
	link_exec('conprob')

	#get conversion factors and thresholds
	conv = pproc_settings['conversion']
	poe_settings = pproc_settings['poe']

	#loop through requested pollutants
	for iP, pollutant in enumerate(poe_settings.keys()):
		#flag for pollutant number
		pflag = '-p{}'.format(str(iP + 1)) 
		#flag for concentration conversion
		xflag = '-x{}'.format(conv[pollutant])
		lvls = np.sort(poe_settings[pollutant])[::-1]
		#flag for concentration levels
		cflag = '-c{}:{}:{}'.format(lvls[0],lvls[1],lvls[2])
		#run calculation for first non-deposition layer (-z2)
		poe_cmd = './conprob -bcdump {} {} -z2 {}'.format(pflag,xflag,cflag)
		logging.debug('...running POE analysis for {}: {}'.format(pollutant, poe_cmd))
		os.system(poe_cmd)

		#convert output to netcdf
		to_netcdf('cmean', 'cmean_{}.nc'.format(pollutant))
		to_netcdf('cmax01', 'poe_lvl1_{}.nc'.format(pollutant))
		to_netcdf('cmax10', 'poe_lvl2_{}.nc'.format(pollutant))
		to_netcdf('cmax00', 'poe_lvl3_{}.nc'.format(pollutant))

		#save ncmean for pollutants with requested stn traces
		logging.debug('...saving as cmean_{} for future use'.format(pollutant))
		os.system('mv cmean cmean_{}'.format(pollutant))

	return

def stn_traces(tag, stn_file, conv):
	'''
	Script extracts ensmean concentrations from user-defined stations
	'''
	logging.info('...creating station traces')
	
	#TODO extend this to multiple pollutants: corrently assumes SO2

	#link executables
	link_exec('con2stn')

	#extract station data
	out_file = 'HYSPLIT_so2.{}.{}.txt'.format(os.environ['forecast'],tag)
	con2stn_cmd = './con2stn -d2 -icmean_SO2 -o{} -s{} -xi'.format(out_file,stn_file)
	os.system(con2stn_cmd)

	#copy to webserver (mkwc)
	#TODO remove hardcoding and link to config json inputs once operational
	mkwc_file = 'hysplit.haw.{}.so2.{}.txt'.format(tag,os.environ['forecast'])
	scp_cmd = 'scp {} vmap@mkwc2.ifa.hawaii.edu:www/hysplit/text/{}'.format(out_file, mkwc_file)
	os.system(scp_cmd)
	logging.debug('...copying station data to mwkc as: {}'.format(mkwc_file))

	return


def to_netcdf(hysfile, ncfile):
	'''
	Converts hysplit binary to NetCDF
	'''

	logging.info('...saving netcdf: {}'.format(ncfile))	

	#link netcdf converter
	link_exec('con2cdf4')

	#convert ensemble mean to netcdf
	con2cdf4_cmd = './con2cdf4 {} {}'.format(hysfile, ncfile)
	os.system(con2cdf4_cmd)

	return

def clean_hysdir():
	#clean up dispersion folder

	logging.debug('...cleaning up HYSPLIT direcotry')
	os.system('find -type l -delete')
	os.system('rm *.OK VMSDIST* PARDUMP* MESSAGE* WARNING* *.out *.err *.log cdump* > /dev/null 2>&1')

	return

def archive(archive_path):
	#archiving script: compresses the main run folder and pushes to remote archive
	logging.info('...compressing data and pushing to remote archive')
	logging.warning('...this step may take a LONG time')
	
	#move out of forecast direcotry
	os.chdir(os.environ['run_dir'])

	#run tar command - THIS WILL BE SLOW
	tar_cmd = 'tar -zcf {}TEST.tar.gz {}'.format(os.environ['forecast'], os.environ['forecast'])
	os.system(tar_cmd)

	#push archived data to remote set by user (requires ssh key)
	scp_cmd = 'scp {}TEST.tar.gz {}'.format(os.environ['forecast'],archive_path)
	logging.debug('...copying to remote: {}'.format(scp_cmd))
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
	pproc_settings = json_data['user_defined']['post_process']
	unit_conv = pproc_settings['conversion']
	set_env_var(json_data['user_defined']['dispersion'],'hys_path')

	#create POE for user-defined thresholds, if requested 
	if 'poe' in pproc_settings.keys():
		get_poe(pproc_settings)
	else:
		#if no PEO plots requested just do ensemble averaging
		ensmean(pproc_settings)


	#create station traces for user-defined stations, if requested
	if 'stns' in pproc_settings.keys():
		stn_settings = pproc_settings['stns']
		for pollutant in stn_settings:
			stn_traces(stn_settings[pollutant]['tag'],stn_settings[pollutant]['stn_file'], unit_conv[pollutant])
	else:
		logging.info('No station traces requested in config file')


	#create graphics
	#TODO move graphics and plotting into a separate module to run in parallel
	if 'plots' in pproc_settings.keys():
		plot_settings = pproc_settings['plots']
		for pollutant in plot_settings['concentration']:
			con_file = './cmean_{}.nc'.format(pollutant)
			make_con_plots(con_file, pollutant, 'png', unit_conv[pollutant])
		if 'poe' in plot_settings.keys():
			for pollutant in plot_settings['poe']:
				make_poe_plots('./poe_', pollutant, 'png')
	else:
		logging.info('No plots requested in config file')	

	
	#extras: archive and move to webserver if requested
	if 'extras' in json_data['user_defined'].keys():
		extras = json_data['user_defined']['extras']
		if 'web' in extras.keys():
			to_webserver.main(extras['web'])
		if 'archive' in extras.keys():
			#clean up before archiving
			clean_hysdir()
			archive(extras['archive'])
	else:
		logging.info('No copying to webserver requested')

	logging.info('Post-processing complete')


 ### Main ###
if __name__ == '__main__':
	main()		
