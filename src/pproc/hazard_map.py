#!/usr/bin/python3.7
 
# Script for generating colormaps, plots and other graphics

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="February 2022"

from set_vog_env import *
import logging
import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from scipy.ndimage import gaussian_filter
import datetime as dt
import pandas as pd
import os
import sys
from pproc.graphics import get_tdim
#import cartopy.crs as ccrs

#turn off font warnings for logging
logging.getLogger('matplotlib.font_manager').disabled = True

### Functions ###

def assemble_hourly_data(settings):
	'''
	Compile an array of hourly data for the entire analysys period
	'''
	logging.info('... assembling forecast data')

	#create a time dimension
	data_range = pd.date_range(settings['start'],settings['end'],freq='1h')
	
	#create a list of forecasts in the data range
	fcst_range = pd.date_range(settings['start'],settings['end'],freq=settings['freq'])

	#create storage dictionary
	compiled_data = {}

	#loop through all the forecasts
	for fcst in fcst_range:
		
		fcst_tag = dt.datetime.strftime(fcst,'%Y%m%d%H')
		logging.debug('... extracting forecast: {}'.format(fcst_tag))
		#open the pollutant nc file and get time dimensionsi
		#TODO add iterations over multiple pollutants and poe levels

		try:
			ds = get_nc_data(fcst_tag, settings['pollutant'], settings['poe_lvl'])
		except:
			logging.warning('WARNING: poe data missing for {}, skipping!'.format(fcst_tag))
			continue

		tdim = get_tdim(ds)
		
		#loop through availble hours
		for t, time in enumerate(tdim):
			surface_poe = get_surface_field(ds, settings['pollutant'], settings['poe_lvl'], t)	
			compiled_data[time] = surface_poe
	return compiled_data


def get_nc_data(fcst_tag, pollutant, lvl):
	'''
	Locates correct forecast subfolderes, ncfiles and pulls data for given pollutant, lvl, time
	'''
	
	#check if directory exists
	fcst_path = os.path.join(os.environ['run_dir'],fcst_tag,'hysplit') 
	if os.path.exists(fcst_path) is False:
		logging.CRITICAL('ERROR: {} forecast is missing. Aborting.'.format(fcst_path))
		sys.exit()
	
	#get dataset
	fcst_file = 'poe_lvl{}_{}.nc'.format(lvl,pollutant)
	nc_path = os.path.join(fcst_path,fcst_file)
	ds = nc.Dataset(nc_path)

	return ds

def get_surface_field(ds, pollutant,lvl,time):
	'''
	Get data for correct pollutant and time dealing with hysplit naming
	'''

	#deal with Hysplit's weird naming: -p1 has keys CM00 etc, -pX uses pollutnat as key
	hys_keys = ['CM01', 'CM10', 'CM00']
	try:
		surface_poe = ds.variables[hys_keys[int(lvl-1)]][time,0,:,:]
	except:
		surface_poe = ds.variables[pollutant][time,0,:,:]


	return surface_poe

def make_hazard_cmap():
	'''
	Create a colormap for POE
	'''
	#colornames = ['green','gold','orangered','crimson']
	colornames = ['yellowgreen','gold','orangered','crimson','darkviolet']

	#add transparancy
	hazard_cm = colors.LinearSegmentedColormap.from_list('hazard', colornames, N=256)
	hazard_cmA = hazard_cm(np.arange(hazard_cm.N))
	alphas = list(np.linspace(0,1,5)) + [1] * 251
	hazard_cmA[:,-1] = alphas	

	hazard = colors.LinearSegmentedColormap.from_list('hazard',hazard_cmA)
	
	#save colormbar if ncessary - dumps strange log output
	plt.figure()
	span = np.array([[0, 100]])
	img = plt.imshow(span, cmap=hazard)
	plt.gca().set_visible(False)
	cbar = plt.colorbar(orientation='horizontal', label='Probability of Exceedance (%)', ticks=np.arange(0, 101,10))
	plt.savefig('./colorbar_hazard.png', dpi=100, bbox_inches = 'tight', pad_inches = 0.1)
	plt.close()

	return hazard


def plot_hazard(mean_poe, hazard_cmap,  settings):
	'''
	Create surface hazard plots plots for averaged conditions
	'''

	##plotting using cartopy
	##TODO this is hardcoded: remove for future and provide as input
	##NOTE: consider adding bounds in hysplit step (calculate from settings)
	#bounds =   (-160.5, -154.5, 18.25, 22.75)

	##plot as separate figure (assumes lat/lon coordiantes from HYSPLIT)
	#plt.figure()
	#ax = plt.axes(projection=ccrs.PlateCarree())
	#im = ax.imshow(mean_poe, origin='lower',cmap=hazard_cmap,vmin=0, vmax=100, extent=bounds, transform=ccrs.PlateCarree())	
	#ax.coastlines(resolution='50m',color='grey', linewidth=0.5)
	#ax.gridlines(draw_labels=True)
	#plt.colorbar()
	#plt.title('ANALYSIS PERIOD: {} - {}'.format(settings['start'], settings['end']))
	
	#plotting for leaflet display
	img = plt.imshow(mean_poe,cmap=hazard_cmap, origin='lower', vmin = 0, vmax=100)
	#hide all padding, margins and axes
	plt.axis('off')
	plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
	plt.margins(0,0)
	plt.gca().xaxis.set_major_locator(plt.NullLocator())
	plt.gca().yaxis.set_major_locator(plt.NullLocator())

	#save
	save_path = os.path.join(os.environ['run_dir'],'hazard_{}_lvl{}_{}_{}.png'.format(settings['pollutant'], \
				settings['poe_lvl'], settings['start'], settings['end']))
	plt.savefig(save_path, transparent=True, bbox_inches = 'tight', pad_inches = 0, dpi=200)
	#plt.savefig('./{}.{}'.format(time,fmt), dpi=200, bbox_inches = 'tight', pad_inches = 0)
	plt.close()
	
	logging.debug('Hazard map saved as: {}'.format(save_path))
	
	return



def main(settings):
	'''
	Create a time-averaged hazard map based on user-specified settings
	'''
	logging.info('Creating hazard maps')
	
	#collect data from the user-specified forecast range
	compiled_data = assemble_hourly_data(settings)	
	mean_poe = sum(compiled_data.values()) / int(len(compiled_data.keys()))

	#do plotting
	hazard_cmap = make_hazard_cmap()
	plot_hazard(mean_poe, hazard_cmap,  settings)

	return

if __name__ == '__main__':
	main(settings)
