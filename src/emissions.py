#!/usr/bin/python3.7

#This script pulls takes care of emissions inputs into the vog model

__date__ = 'July 2021'
__author__ = 'Nadya Moisseeva (nadya.moisseeva@hawaii.edu)'

import requests
import datetime as dt
import logging
import json
import os
import sys
import pandas as pd
from set_vog_env import *


#logging.getLogger("requests").setLevel(logging.ERROR)

### Inputs ###
#url = 'https://hvo-api.wr.usgs.gov/api/so2emissions?channel=SUMDFW&starttime='
url = 'https://hvo-api.wr.usgs.gov/api/v1/'


### Functions ###

def pull_from_api(url,hvo_subdir,days,select_data,keypath):
	'''
	Set up api call and pull data
	'''
	if hvo_subdir == 'so2emissions':
		api_call = url + hvo_subdir + '/' +  str(days) + 'd'
	elif hvo_subdir == 'flyspec':
		#make specific api call with limited date to avoid massive empty data dump
		now = dt.datetime.utcnow()
		em_start = dt.datetime.strftime(now - dt.timedelta(hours=24*days), '%Y%m%d') + '000000'
		em_end = dt.datetime.strftime(now - dt.timedelta(hours=24*(days-1)), '%Y%m%d') + '000000'
		
		api_call = url + hvo_subdir + '/' + em_start + '/' + em_end
		logging.debug(api_call) 


	login = read_config(keypath)
	response = requests.post(api_call,auth=(login['hvo']['user'],login['hvo']['pwd']),data=json.dumps(select_data))

	return response.json()

def no_data(response):
	'''
	Check if so2 data is available for the given day
	'''

	if response['nr']==0:
		return True
	else:
		return False

def no_daily_ave(response):
	'''
	Check if flyspec so2 data was sufficient for daily average
	'''
	i = -1
	while response['results'][i]['dailybstfluxmean'] == None and abs(i) < response['nr']:
		i = i-1
	
	if response['results'][i]['dailybstfluxmean']  == None:
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

	#return adjusting for HST indexing
	#return offset.days + 1
	return offset.days + 5	#TODO remove this, or confirm this is a reasonable approach

def get_campaign_data(keypath,hvo_subdir,select_data):
	'''
	Run all the steps for pulling campaign emissions form HVO
	'''
	logging.info('...pulling campaign emissions data from HVO-API')

	#check if a forecast date is set in environ
	if 'forecast' in os.environ:
		day = get_days_offset()
		logging.debug('...Number of days offset for emissions pull is {}'.format(day))
	else:
		logging.debug('...No forecast date set, getting the most recent data')
		day = 1

	#loop until we find some data
	while no_data(pull_from_api(url,hvo_subdir,day,select_data,keypath)):
		day = day + 1

	#get the data we need
	response = pull_from_api(url,hvo_subdir,day,select_data,keypath)

	#get the correct index of the record (if forecast mode: use most recent)
	if 'forecast' in os.environ:
		#get all record timestamps 
		nr = int(response['nr'])
		obs_dates = [response['results'][i]['date'] for i in range(nr)]
		obs_datetimes_utc = [dt.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z') for date in obs_dates]

		#use pandas to locate nearest record to emission start datetime and get index
		pdtime = pd.DatetimeIndex(obs_datetimes_utc)
		em_date = dt.datetime.strptime(os.environ['forecast']+'UTC', '%Y%m%d%H%Z') + dt.timedelta(hours=int(os.environ['spinup']))
		logging.debug('...emissions start hour in UTC is {}'.format(em_date))
		record_idx = pdtime.get_loc(em_date, method='nearest')
	else:
		#get the most recent record
		record_idx = -1

	so2 = int(response['results'][record_idx]['so2'])
	obs_date = response['results'][record_idx]['date']
	logging.info('...nearest record found found: {}'.format(obs_date))

	return so2, obs_date

def get_flyspec_data(keypath, hvo_subdir,select_data):
	'''
	Run all the steps for pulling flyspec data from HVO
	'''
	logging.info('...pulling flyspec emissions data from HVO-API')

	#check if a forecast date is set in environ
	if 'forecast' in os.environ:
		day = get_days_offset()
		logging.debug('...Number of days offset for emissions pull is {}'.format(day))
	else:
		logging.debug('...No forecast date set, getting the most recent data')
		day = 1

	#loop until we find some data
	response = pull_from_api(url,hvo_subdir,day,select_data,keypath)
	while no_data(response) or no_daily_ave(response):
		day = day + 1
		response = pull_from_api(url,hvo_subdir,day,select_data,keypath)

	#get the last non-nan value
	i= -1
	while response['results'][i]['dailybstfluxmean'] == None and abs(i) < response['nr']:
		i = i-1

	#set the last averaged record
	so2 = int(response['results'][i]['dailybstfluxmean'])
	obs_date = response['results'][i]['date']
	logging.info('...nearest record found found: {}'.format(obs_date))

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
	tags = json_data['user_defined']['emissions'].keys()
	json_data['emissions'] = {}

	#get emissions for each source
	#for iSrc in range(num_src):
		#tag = 'src' + str(iSrc + 1)
	for iSrc, tag in enumerate(tags):
		emis_settings = json_data['user_defined']['emissions'][tag]

		logging.debug('Getting emissions for {}:'.format(tag))

		#get emissions based on user preferences
		if emis_settings['input'] == 'hvo':
			#pull from hvo-api
			keypath = json_data['user_defined']['keys']
			if emis_settings['stream'] == 'campaign':
				hvo_subdir = 'so2emissions'
				select_data = {'channel': emis_settings['channel'], 'rank': 2, 'timezone': 'UTC', 'series': ['so2']}
				so2, obs_date = get_campaign_data(keypath, hvo_subdir, select_data)
			elif emis_settings['stream'] =='flyspec':
				hvo_subdir = 'flyspec'
				select_data = {'channel': 'FLYA', 'timezone': 'UTC', 'series': ['dailybstfluxmean']}
				so2, obs_date = get_flyspec_data(keypath, hvo_subdir, select_data)
			else:
				logging.critical('ERROR: unrecognized emissions stream: must specify "flyspec"/"campaign". Aborting. ')
				sys.exit()
			logging.info('HVO emissions value: {} tonnes/day'.format(so2))
		elif emis_settings['input'] == 'manual':
			#assign user defined value
			so2 = emis_settings['rate']
			obs_date = 'manual update'
			logging.info('Manual emissions assignment requested: rate = {} tonnes/day)'.format(so2))
		else:
			logging.critical('ERROR: Emissions input not recognized. Availble options are: "hvo","manual"')
			sys.exit()
		#write to main json file
		json_data['emissions'][tag] = {'so2' : so2, 'obs_date': obs_date }

	#update run json
	update_run_json(json_data)

	logging.info('Emissions update completed')

if __name__ == '__main__':
	main()



