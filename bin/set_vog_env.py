# Setup environment for the vog model run
#
__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

import os
import json
import sys, getopt
import argparse
import logging

 ### Fucntions ###

def read_config(config_path):
	"""
	Read main configuration json file
	"""
	#open json file
	f = open(config_path)

	#return json opject as a dictionary
	settings = json.load(f)

	#close file and return settings
	f.close()
	return settings


def set_env_var(settingdict,key):
	"""
	Set enviornment variable using the given dictionary key
	"""

	#check if key exists
	if key not in settingdict.keys():
		logging.warning("$%s not specified in vog.config. Setting to None." %key)
		return

	logging.debug("Setting $%s environmental variable to: %s" %(key,settingdict[key]))

	#set environment
	os.environ[key] = str(settingdict[key])

	return

def parse_inputs():
	"""
	Reads command line inputs to deterine dates and run type
	"""
	parser = argparse.ArgumentParser()
	
	#get mandatory input (initialization time)
	parser.add_argument("cycle", help="Forecast initialization time (e.g. 00, 12 etc)", type=str)

	#get optional date input to run a historic simulation
	parser.add_argument("-d", "--date", help="Historic date to run the simulation for in YYYYMMDD format", type=str, default=None)
	
	args = parser.parse_args()
	return args


def create_run_dir(forecast):
	"""
	Set up working directory for the forecast run
	"""
        #run_path = os.environ["run_dir"] + '/' + forecast
	run_path = os.path.join(os.environ["run_dir"],forecast)
	logging.info("Creating working directory: %s" %run_path)
	os.system('mkdir -p %s' %run_path)	
	return
	
	
	
