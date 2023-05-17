#!/usr/bin/python3.7
 
# Script for generating exposure maps

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
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import cartopy.feature as cfeature

#turn off font warnings for logging
logging.getLogger('matplotlib.font_manager').disabled = True

### Functions ###

def assemble_hourly_data(settings, pollutant, units):
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
	averaged_data = {}

	#loop through all the forecasts
	for fcst in fcst_range:
		
		fcst_tag = dt.datetime.strftime(fcst,'%Y%m%d%H')
		logging.debug('... extracting forecast: {}'.format(fcst_tag))
		#open the pollutant nc file and get time dimensionsi
		#TODO add iterations over multiple pollutants and poe levels
		#NOTE averaging is pretty ugly and might not be needed by all users. Revisit

		try:
			ds = get_nc_data(fcst_tag, settings, pollutant)
		except:
			logging.warning(f'WARNING: forecast missing for {fcst_tag}, skipping!')
			continue


		tdim = get_tdim(ds)

		#set up empty arrays for mean
		fcst_mean = []	

		#loop through availble hours
		for t, time in enumerate(tdim[settings['skiphrs']:]):
			if settings['plot'] == 'poe':
				surface_field = get_surface_poe(ds, pollutant, settings['poe_lvl'], t)	
			elif settings['plot'] == 'concentration':
				z = int(settings['zflag'])
				surface_field = ds.variables[pollutant][t,z,:,:]
			
			#save data to various storage arrays
			fcst_mean.append(surface_field)
			compiled_data[time] = surface_field
		
		#get geographic dimensions
		hyslat = ds.variables['latitude'][:]
		hyslon = ds.variables['longitude'][:]	
		hysdims = {'lats': hyslat, 'lons': hyslon}	
		bounds = [np.min(hyslon), np.max(hyslon),np.min(hyslat), np.max(hyslat)]

		#average forecast data
		fc_mean = np.median(np.array(fcst_mean), 0)
		averaged_data[fcst_tag] = fc_mean

	if 'dump_nc' in settings.keys():
		if settings['dump_nc']=='daily':
			logging.info(f'Averaged (median daily) data dump requested: preparing netcdf output')
			generate_nc_output(averaged_data, hysdims, settings, pollutant, units)
		if settings['dump_nc']=='hourly':
			logging.info(f'Hourly data dump requested: preparing netcdf output')
			generate_nc_output(compiled_data, hysdims, settings, pollutant, units)

	return compiled_data, bounds


def generate_nc_output(save_data, hysdims, settings, pollutant, units):
	'''
	Create an output netcdf file for compiled hourly data
	'''
	zflag = settings['zflag']
	save_path = f'./compile_data_{pollutant}_z{zflag}.nc'

	with nc.Dataset(save_path, 'w') as ncf:	
		#set up dimensions
		time = ncf.createDimension('time', len(save_data.keys()))
		lat = ncf.createDimension('lat', len(hysdims['lats']) )
		lon = ncf.createDimension('lon', len(hysdims['lons']) )

		#add variables
		xtime = ncf.createVariable('xtime', 'i', ('time',))
		xlat = ncf.createVariable('xlat', 'f4', ('lat',))
		xlon = ncf.createVariable('xlon', 'f4', ('lon',))
		values = ncf.createVariable(settings['plot'], 'f4', ('time', 'lat', 'lon',))

		values.units = units[pollutant][1]
		
		#assign values
		xlat[:] = hysdims['lats']
		xlon[:] = hysdims['lons']

		#deal with strings
		#date_str =  nc.stringtochar(averaged_data.keys(), 'S8')
		#xtime[:] = date_str

		for f,fcst_time in enumerate(save_data.keys()):
			values[f,:,:] = save_data[fcst_time][:,:]
			xtime[f] = int(fcst_time)
		logging.debug(xtime[:])
		logging.debug(f'...saving as {save_path}')
	return


def get_nc_data(fcst_tag, settings, pollutant):
	'''
	Locates correct forecast subfolderes, ncfiles and pulls data for given pollutant, lvl, time
	'''
	
	#check if directory exists
	fcst_path = os.path.join(os.environ['run_dir'],fcst_tag,'hysplit') 
	#if os.path.exists(fcst_path) is False:
	#	logging.warning(f'WARNING: {fcst_path} forecast is missing. Skipping!!!.')
	
	#get dataset
	if settings['plot'] == 'poe':
		fcst_file = 'poe_lvl{}_{}.nc'.format(settings['poe_lvl'],pollutant)
	elif settings['plot'] == 'concentration':
		fcst_file = f'cmean_{pollutant}.nc'
	else:
		logging.critical('ERROR: unrecognized plot type requested. Available options: "concentration"/"poe". Aborting!')
		sys.exit()

	nc_path = os.path.join(fcst_path,fcst_file)
	ds = nc.Dataset(nc_path)

	return ds

def get_surface_poe(ds, pollutant,lvl,time):
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


def make_poe_cmap():
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
	#plt.figure()
	#span = np.array([[0, 100]])
	#img = plt.imshow(span, cmap=hazard)
	#plt.gca().set_visible(False)
	#cbar = plt.colorbar(orientation='horizontal', label='Probability of Exceedance (%)', ticks=np.arange(0, 101,10))
	#plt.savefig('./colorbar_hazard.png', dpi=100, bbox_inches = 'tight', pad_inches = 0.1)
	#plt.close()

	return hazard


def plot_hazard(mean_field, bounds, settings, pollutant, units):
	'''
	Create surface hazard plots plots for averaged conditions
	'''

	stamen_terrain = cimgt.Stamen(desired_tile_form='L', style='terrain-background')

	fig_path = os.path.join(os.environ['run_dir'],os.environ['forecast'],'output')
	os.system(f'mkdir -p {fig_path}')
	cm = make_poe_cmap()

	plt.figure()
	ax = plt.axes(projection=ccrs.PlateCarree())
	im = ax.imshow(mean_field, origin='lower',cmap=cm,vmin=0,  extent=bounds, transform=ccrs.PlateCarree(),zorder=5)
	ax.set_extent(bounds, crs=ccrs.Geodetic())
	ax.add_image(stamen_terrain, 7, cmap='gray',alpha=0.4,zorder=2)	
	ax.coastlines(zorder=4)
	ax.add_feature(cfeature.OCEAN,color='white',zorder=3)
	#prettify gridline
	gl = ax.gridlines(crs=ccrs.PlateCarree(),draw_labels=True,linewidth=0.5, color='gray', alpha=0.5, linestyle='--',zorder=10)
	gl.top_labels = False
	gl.right_labels = False

	if settings['plot'] == 'poe':
		save_path = os.path.join(fig_path,'poe_{}_lvl{}_{}_{}.png'.format(pollutant,\
				settings['poe_lvl'], settings['start'], settings['end']))
		ax.set(title = 'MEAN {} POE | {} - {}'.format(pollutant,settings['start'], settings['end']))
		im = ax.imshow(mean_field, origin='lower',cmap=cm,vmin=0, vmax=100, extent=bounds, transform=ccrs.PlateCarree())
		plt.colorbar(im, label = 'POE (%)')
	
	elif settings['plot'] == 'concentration':
		save_path = os.path.join(fig_path,f'conc_{pollutant}_{settings["start"]}_{settings["end"]}.png')
		ax.set(title = f'MEAN {pollutant} CONCENTRATION | {settings["start"]} - {settings["end"]}')
		im = ax.imshow(mean_field, origin='lower',cmap=cm,vmin=0,  extent=bounds, transform=ccrs.PlateCarree())
		plt.colorbar(im, label = f'concentration ({units[pollutant][1]})')
	
	plt.tight_layout()
	
	plt.savefig(save_path, dpi=150)
	plt.close()


	#NOTE keeping this for possible future use: leaflet version of poe plot for web (transparent png, no axes)
	
	##plotting for leaflet display
	#img = plt.imshow(mean_poe,cmap=hazard_cmap, origin='lower', vmin = 0, vmax=100)
	##hide all padding, margins and axes
	#plt.axis('off')
	#plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
	#plt.margins(0,0)
	#plt.gca().xaxis.set_major_locator(plt.NullLocator())
	#plt.gca().yaxis.set_major_locator(plt.NullLocator())

	##save
	#save_path = os.path.join(os.environ['run_dir'],'hazard_{}_lvl{}_{}_{}.png'.format(settings['pollutant'], \
	#			settings['poe_lvl'], settings['start'], settings['end']))
	#plt.savefig(save_path, transparent=True, bbox_inches = 'tight', pad_inches = 0, dpi=200)
	#plt.close()
	
	logging.debug('Hazard map saved as: {}'.format(save_path))
	
	return



def main(settings, units):
	'''
	Create a time-averaged hazard map based on user-specified settings
	'''
	logging.info('Creating hazard maps')
	
	
	#collect data from the user-specified forecast range
	for pollutant in settings['pollutants']:
		compiled_data, bounds  = assemble_hourly_data(settings, pollutant, units)
		mean_field = sum(compiled_data.values()) / int(len(compiled_data.keys()))

		#do plotting
		plot_hazard(mean_field, bounds, settings, pollutant, units)

	return

if __name__ == '__main__':
	main(settings)
