#!/usr/bin/python3.7

#This script pulls takes care of emissions inputs into the vog model

__date__ = 'July 2021'
__author__ = 'Nadya Moisseeva (nadya.moisseeva@hawaii.edu)'

import requests
import datetime as dt
import logging
import json
import os
import pandas as pd
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

	return response.json()

def no_data(response):
	'''
	Check if so2 data is available for the given day
	'''
	if response['nr']==0:
		return True
	else:
		return False

def get_days_offset():
	'''
	Calculate number of days between now and forecast day
	'''

	now = dt.datetime.utcnow()
	fc_date = dt.datetime.strptime(os.environ['forecast'], '%Y%m%d%H')
	offset = now - fc_date

	#add offset to account for HST and API indexing
	hst_adjust = 2

	return offset.days + hst_adjust

def get_hvo_data(keypath):
	'''
	Run all the steps for pulling emissions form HVO
	'''
	logging.info('...pulling emissions data from HVO-API')

	#check if a forecast date is set in environ
	if 'forecast' in os.environ:
		day = get_days_offset()
		logging.debug('...Historic run: number of days offset for emissions pull is {}'.format(day))
	else:
		logging.debug('...No forecast date set, getting the most recent data')
		day = 1

	#loop until we find some data
	while no_data(pull_from_api(url,day,series,keypath)):
		day = day + 1

	#get the data we need
	response = pull_from_api(url,day,series,keypath)

	#get the correct index of the record (if forecast mode: use most recent)
	if 'forecast' in os.environ:
		#get all record timestamps manually adding UTC offset (HVO data is in HST)
		nr = int(response['nr'])
		obs_dates = [response['records']['SUMDFW'][i]['date']+' -1000' for i in range(nr)]
		obs_datetimes_utc = [dt.datetime.strptime(date, '%Y-%m-%d %H:%M:%S %z').astimezone(dt.timezone.utc) for date in obs_dates]

		#use pandas to locate nearest record to emission start datetime and get index
		pdtime = pd.DatetimeIndex(obs_datetimes_utc)
		em_date = dt.datetime.strptime(os.environ['forecast']+'UTC', '%Y%m%d%H%Z') + dt.timedelta(hours=int(os.environ['spinup']))
		logging.debug('...emissions start hour in UTC is {}'.format(em_date))
		record_idx = pdtime.get_loc(em_date, method='nearest')
		#nearest = min(obs_datetimes, key=lambda d: abs(d - date))
	else:
		#get the most recent record
		record_idx = -1

	so2 = int(response['records']['SUMDFW'][record_idx]['so2'])
	obs_date = response['records']['SUMDFW'][record_idx]['date']
	logging.info('...nearest record found found: %s HST' %obs_date)

	return so2, obs_date

def main():
	'''
	Main script steps: find most recent day, get data, write out json
	'''
	logging.info('===========EMISSIONS MODULE============')

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



