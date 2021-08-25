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

def ensmean():
	'''
	Run ensemble averaging
	'''
	logging.info('...creating ensemble average')

	#move into dispersion working directory, clean up
	os.chdir(os.environ['hys_rundir'])
	os.system('find -type l -delete')

	#TODO check that that dispersion completed

	#link executables
	link_exec('conprob')
	
	#run hysplit averaging utility
	os.system('./conprob -bcdump') 

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
	for iP, pollutant in poe_settings.items():
		#flag for pollutant number
		pflag = '-p{}'.format(str(iP + 1)) 
		#get levels in internal hysplit units (mg/m3)
		raw_lvls = poe_settings[pollutant] / conv[pollutant]
		#flag for concentration levels
		cflag = '-c{}:{}:{}'.format(raw_lvls)
		#run calculation for surface level
		poe_cmd = './conprob -bcdump -z1 {} {}'.format(pflag, cflag)
		logging.debug('...running POE analysis for {}: {}'.format(pollutant, poe_cmd))
		os.system(poe_cmd)

	return
	
def stn_traces(tag, stn_file, conv):
	'''
	Script extracts ensmean concentrations from user-defined stations
	'''
	logging.info('...creating station traces')
	
	#link executables
	link_exec('con2stn')
	#con2stn = os.path.join(os.environ['hys_path'],'exec','con2stn')
	#os.symlink(con2stn, './con2stn')

	#extract station data
	out_file = 'HYSPLIT_so2.{}.{}.txt'.format(os.environ['forecast'],tag)
	con2stn_cmd = './con2stn -p1 -d2 -z2 -c{} -icmean -o{} -s{} -xi'.format(conv,out_file,stn_file)
	os.system(con2stn_cmd)

	#copy to webserver (mkwc)
	#TODO remove hardcoding and link to config json inputs once operational
	mkwc_file = 'hysplit.haw.{}.so2.{}.txt'.format(tag,os.environ['forecast'])
	scp_cmd = 'scp {} vmap@mkwc2.ifa.hawaii.edu:www/hysplit/text/{}'.format(out_file, mkwc_file)
	os.system(scp_cmd)
	logging.debug('...copying station data to mwkc as: {}'.format(mkwc_file))


	return


def to_netcdf(hysfile):
	'''
	Converts hysplit binary to NetCDF
	'''

	logging.info('...converting data to netcdf')	

	#link netcdf converter
	link_exec('con2cdf4')

	#convert ensemble mean to netcdf
	con2cdf4_cmd = './con2cdf4 {} {}.nc'.format(hysfile, hysfile)
	os.system(con2cdf4_cmd)

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

	#create ensemble average, convert it to netcdf
	#ensmean()
	#to_netcdf('cmean')

	#create POE for user-defined thresholds, if requested 
	if 'poe' in pproc_settings.keys():
		get_poe(pproc_settings)
	else:
		#if no PEO plots requested just do ensemble averaging
		ensmean()

	#convert to netcdf	
	to_netcdf('cmean')	

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
			make_con_plots('./cmean.nc', pollutant, 'png', unit_conv[pollutant])
	else:
		logging.info('No plots requested in config file')	

	
	#extras: archive and move to webserver if requested
	if 'extras' in json_data['user_defined'].keys():
		if 'web' in json_data['user_defined']['extras'].keys():
			web_path = json_data['user_defined']['extras']['web']
			logging.debug(web_path)
			to_webserver.main(web_path)
	else:
		logging.info('No copying to webserver requested')


	logging.info('Post-processing complete')


 ### Main ###
if __name__ == '__main__':
	main()		
