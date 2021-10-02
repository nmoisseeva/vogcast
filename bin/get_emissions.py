#!/usr/bin/python3.7

#This script pulls takes care of emissions inputs into the vog model

__date__ = 'July 2021'
__author__ = 'Nadya Moisseeva (nadya.moisseeva@hawaii.edu)'

import requests
import datetime as dt
import logging
import json
import os
from set_vog_env import *


#logging.getLogger("requests").setLevel(logging.ERROR)

### Inputs ###
url = 'https://hvo-api.wr.usgs.gov/api/so2emissions?channel=SUMDFW&starttime='
series = '&series=so2' #TODO add comma-delimited options: so2,so2sd,windspeed,winddir,samples

### Functions ###

def pull_from_api(url,days,series,keypath):
	'''
	Set up api call and pull data
	'''
	api_call = url + '-' + str(days) + 'd' + series
	login = read_config(keypath)
	response = requests.get(api_call,auth=(login['hvo']['user'],login['hvo']['pwd']))

	return response

def no_data(response):
	'''
	Check if so2 data is available for the given day
	'''
	if len(response.json()['records']['SUMDFW'])==0:
		return True
	else:
		return False

def get_days_offset():
	'''
	Calculate number of days between now and forecast day
	'''
	now = dt.datetime.now()
	fc_date = dt.datetime.strptime(os.environ['forecast'], '%Y%m%d%H')

	offset = now - fc_date

	return offset.days

def get_hvo_data(keypath):
	'''
	Run all the steps for pulling emissions form HVO
	'''
	logging.info('Pulling the most recent emissions data from HVO-API')

	#check if a forecast date is set in environ
	if 'forecast' in os.environ:
		day = get_days_offset()
	else:
		logging.debug('...No forecast date set, getting the most recent data')
		day = 1

	#loop until we find some data
	while no_data(pull_from_api(url,day,series,keypath)):
		day = day + 1

	#get the data we need
	response = pull_from_api(url,day,series,keypath)
	so2 = int(response.json()['records']['SUMDFW'][-1]['so2'])
	obs_date = response.json()['records']['SUMDFW'][-1]['date']
	logging.info('...most recend data found: %s' %obs_date)

	return so2, obs_date

def main():
	'''
	Main script steps: find most recent day, get data, write out json
	'''
	#read user settings
	json_data = read_run_json()
	emis_settings = json_data['user_defined']['emissions']

	#get emissions based on user preferences
	if emis_settings['input'] == 'hvo':
		#pull from hvo-api
		so2, obs_date = get_hvo_data(emis_settings['keys'])
		logging.info('...HVO emissions value: {} tonnes/day'.format(so2))
	elif emis_settings['input'] == 'manual':
		#assign user defined value
		so2 = emis_settings['rate']
		obs_date = 'manual update'
		logging.info('Manual emissions assignment requested: rate = {} tonnes/day)'.format(so2))
	else:
		logging.critical('ERROR: Emissions input not recognized. Availble options are: "hvo","manual"')

	#write to main json file
	json_data['emissions'] = {'so2' : so2, 'obs_date': obs_date }
	update_run_json(json_data)

	logging.info('Emissions update completed')

if __name__ == '__main__':
	main()



