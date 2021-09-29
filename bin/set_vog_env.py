# Setup environment for the vog model run
#
__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

import os
import json
import sys, getopt
import argparse
import logging
import hjson
 ### Fucntions ###

def read_config(config_path):
	'''
	Read main configuration json file
	'''
	#open json file
	f = open(config_path)

	#return json opject as a dictionary
	settings = hjson.load(f)

	#close file and return settings
	f.close()
	return settings


def set_env_var(settingdict,key):
	'''
	Set enviornment variable using the given dictionary key
	'''

	#check if key exists
	if key not in settingdict.keys():
		logging.warning("$%s not specified in vog.config. Setting to None." %key)
		return

	logging.debug("Setting $%s environmental variable to: %s" %(key,settingdict[key]))

	#set environment
	os.environ[key] = str(settingdict[key])

	return

def parse_inputs():
	'''
	Reads command line inputs to deterine dates and run type
	'''
	parser = argparse.ArgumentParser()
	
	#get mandatory input (config, initialization time)
	parser.add_argument("-c","--config", help="Path (absolute) to run config file", type=str)
	parser.add_argument("cycle", help="Forecast initialization time (e.g. 00, 12 etc)", type=str)

	#get optional date input to run a historic simulation
	parser.add_argument("-d", "--date", help="Historic date to run the simulation for in YYYYMMDD format", type=str, default=None)
	
	args = parser.parse_args()
	return args


def create_run_dir():
	'''
	Set up working directory for the forecast run
	'''
	run_path = os.path.join(os.environ['run_dir'],os.environ['forecast'])
	logging.info("Creating working directory: %s" %run_path)
	os.system('mkdir -p %s' %run_path)	
	return
	
	
def create_run_json(config_path):
	'''
	Create a new json file for controlling the run
	'''
	#get user-defined settings
	user_defined = read_config(config_path)

	#set up copy user data to pipieline-generated json
	pipeline_json = {}
	pipeline_json['user_defined'] = user_defined

	#save pipeline json to the run path
	json_path = os.path.join(os.environ['run_dir'],os.environ['forecast'],'vog_run.json')
	with open(json_path, 'w') as f:
		f.write(json.dumps(pipeline_json, indent=4))
	
	return json_path

def read_run_json():
	'''
	Open run json
	'''
	with open(os.environ['json_path'], 'r') as f:
		json_data = json.load(f)

	return json_data

def update_run_json(json_data):
	'''
	Update run json
	'''
	with open(os.environ['json_path'], 'w') as f:
		f.write(json.dumps(json_data, indent=4))

	return
