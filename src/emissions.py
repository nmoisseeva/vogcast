#!/usr/bin/python3.7

#This script pulls takes care of emissions inputs into the vog model

__date__ = 'July 2021'
__author__ = 'Nadya Moisseeva (nadya.moisseeva@hawaii.edu)'

import requests
import datetime as dt
import logging
import json
import os
import pytz
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

	hst = pytz.timezone("US/Hawaii")
	now = dt.datetime.utcnow()
	fc_date = dt.datetime.strptime(os.environ['forecast'], '%Y%m%d%H')
	offset = now - fc_date

	logging.debug('...offset days (without +1): {}'.format(offset.days))

	#TODO make this more elegant: this accounts for HST and indexing difference
	if fc_date.hour == 0:
		hst_adjust = 2
	elif fc_date.hour == 12:
		hst_adjust = 1

	return offset.days + hst_adjust

def get_hvo_data(keypath):
	'''
	Run all the steps for pulling emissions form HVO
	'''
	logging.info('...pulling the most recent emissions data from HVO-API')

	#check if a forecast date is set in environ
	if 'forecast' in os.environ:
		day = get_days_offset()
		logging.debug('...Historic run: number of days offset for emissions pull is {}'.format(day))
		record_idx = 0
	else:
		logging.debug('...No forecast date set, getting the most recent data')
		day = 1
		record_idx = -1

	#loop until we find some data
	while no_data(pull_from_api(url,day,series,keypath)):
		day = day + 1

	#get the data we need
	response = pull_from_api(url,day,series,keypath)
	so2 = int(response.json()['records']['SUMDFW'][record_idx]['so2'])
	obs_date = response.json()['records']['SUMDFW'][record_idx]['date']
	logging.info('...most recend data found: %s' %obs_date)

	return so2, obs_date

def main():
	'''
	Main script steps: find most recent day, get data, write out json
	'''
	#read user settings
	json_data = read_run_json()

	#get number of emissions sources
	num_src = len(json_data['user_defined']['emissions'])
	json_data['emissions'] = {}

	#get emissions for each source
	for iSrc in range(num_src):
		tag = 'src' + str(iSrc + 1)
		emis_settings = json_data['user_defined']['emissions'][tag]

		logging.debug('...getting emissions for {}:'.format(tag))

		#get emissions based on user preferences
		if emis_settings['input'] == 'hvo':
			#pull from hvo-api
			so2, obs_date = get_hvo_data(emis_settings['keys'])
			logging.info('...HVO emissions value: {} tonnes/day'.format(so2))
		elif emis_settings['input'] == 'manual':
			#assign user defined value
			so2 = emis_settings['rate']
			obs_date = 'manual update'
			logging.info('...manual emissions assignment requested: rate = {} tonnes/day)'.format(so2))
		else:
			logging.critical('ERROR: Emissions input not recognized. Availble options are: "hvo","manual"')

		#write to main json file
		json_data['emissions'][tag] = {'so2' : so2, 'obs_date': obs_date }

	#update run json
	update_run_json(json_data)

	logging.info('Emissions update completed')

if __name__ == '__main__':
	main()



