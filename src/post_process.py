#!/usr/bin/python3.7
 
# Script for generating hysplit ensemble averages, station traces, POEs, archiving and web display

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

from set_vog_env import *
from pproc.graphics import *
import pproc.to_webserver as web
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
	symlink_force(exec_path, local_path)
	
	return

def ensmean(pproc_settings):
	'''
	Run ensemble averaging
	'''
	#move into dispersion working directory, clean up
	os.chdir(os.environ['hys_rundir'])
	#os.system('find -type l -delete')

	#TODO check that that dispersion completed
	#TODO fix for consistency with POE plots

	#link executables
	link_exec('conprob')
	
	conv = pproc_settings['conversion']

	for iP, pollutant in enumerate(conv.keys()):
		logging.info(f'...creating ensemble average: {pollutant}')
		#flat for pollutant number
		pflag = '-p{}'.format(str(iP + 1))
		#flag for concentration conversion
		xflag = '-x{}'.format(conv[pollutant][0])
		#run calculation for first non-deposition layer (-z2)
		#os.system(f'./conprob -bcdump {pflag} -z2 {xflag}')
		os.system(f'./conprob -bcdump {pflag} {xflag}') 
		to_netcdf('cmean', f'cmean_{pollutant}.nc')		

		#save ncmean for pollutants with requested stn traces
		logging.debug(f'...saving as cmean_{pollutant} for future use')
		os.system(f'mv cmean cmean_{pollutant}')
	return

def get_poe(pproc_settings):
	'''
	Get probabilities of exceedance for all user-defined pollutants and thresholds
	'''
	logging.info('Calculating exceedance probabilities')
	
	#move into dispersion working directory, clean up
	os.chdir(os.environ['hys_rundir'])
	#os.system('find -type l -delete')
	

	#link executables
	link_exec('conprob')

	#get conversion factors and thresholds
	conv = pproc_settings['conversion']
	poe_settings = pproc_settings['poe']

	#TODO what if only one pollutant is requested and it's not the first? indexing is wrong
	#loop through requested pollutants
	for iP, pollutant in enumerate(poe_settings.keys()):
		#flag for pollutant number
		pflag = '-p{}'.format(str(iP + 1)) 
		#flag for concentration conversion
		xflag = '-x{}'.format(conv[pollutant][0])
		lvls = np.sort(poe_settings[pollutant])[::-1]
		#flag for concentration levels
		cflag = '-c{}:{}:{}'.format(lvls[0],lvls[1],lvls[2])
		##run calculation for first non-deposition layer (-z2)
		#poe_cmd = './conprob -bcdump {} {} -z2 {}'.format(pflag,xflag,cflag)
		poe_cmd = './conprob -bcdump {} {} {}'.format(pflag,xflag,cflag)
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



def stn_traces(tag, stn_file):
	'''
	Script extracts ensmean concentrations from user-defined stations
	'''
	logging.info('Creating station traces')
	
	#link executables
	link_exec('con2stn')

	#TODO change station naming
	#extract station data
	out_file = 'hysplit.haw.{}.so2.{}.txt'.format(tag,os.environ['forecast'])
	#con2stn_cmd = './con2stn -d2 -icmean_SO2 -o{} -s{} -xi'.format(out_file,stn_file)
	con2stn_cmd = './con2stn -d2 -icmean_SO2 -o{} -s{} -xi -z2'.format(out_file,stn_file)
	os.system(con2stn_cmd)


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
	os.system('rm *.OK VMSDIST* PARDUMP* MESSAGE* WARNING* *.out *.err *.log > /dev/null 2>&1')

	return


def main():
	'''
	Main script for dispersion post-processing. 
	
	Returns:
	- ensemble-avareged surface concentrations
	- probabilities of exceedance for user-defined thresholds
	- station traces
	'''

	logging.info('===========POST-PROCESSING MODULE=========')

	json_data = read_run_json()
	pproc_settings = json_data['user_defined']['post_process']
	unit_conv = pproc_settings['conversion']
	vert_lvls = json_data['user_defined']['dispersion']['lvls']
	
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
			stn_traces(stn_settings[pollutant]['tag'],stn_settings[pollutant]['stn_file'])
	else:
		logging.info('No station traces requested in config file')

	#os.chdir(os.environ['hys_rundir'])

	#create graphics
	if 'plots' in pproc_settings.keys():
		plot_settings = pproc_settings['plots']
		for pollutant in plot_settings['concentration']:
			con_file = './cmean_{}.nc'.format(pollutant)
			make_con_plots(con_file, pollutant, 'png', unit_conv[pollutant], plot_settings)
		if 'poe' in plot_settings.keys():
			for pollutant in plot_settings['poe']:
				make_poe_plots('./poe_', pollutant, 'png', plot_settings)
		if 'ci' in plot_settings.keys():
			for pollutant in plot_settings['ci']:
				make_ci_contours(f'cmean_{pollutant}.nc', pollutant, vert_lvls, 'png',unit_conv[pollutant],plot_settings['leaflet'])
	else:
		logging.info('No plots requested in config file')	
	
	logging.info('Post-processing complete')

	return

 ### Main ###
if __name__ == '__main__':
	main()		
