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
	averaged_data = {}

	#loop through all the forecasts
	for fcst in fcst_range:
		
		fcst_tag = dt.datetime.strftime(fcst,'%Y%m%d%H')
		logging.debug('... extracting forecast: {}'.format(fcst_tag))
		#open the pollutant nc file and get time dimensionsi
		#TODO add iterations over multiple pollutants and poe levels
		#NOTE averaging is pretty ugly and might not be needed by all users. Revisit

		try:
			ds = get_nc_data(fcst_tag, settings)
		except:
			logging.warning(f'WARNING: forecast missing for {fcst_tag}, skipping!')
			continue


		tdim = get_tdim(ds)
		pollutant = settings['pollutant']

		#set up empty arrays for mean, in case save is requested
		fcst_mean = []	

		#loop through availble hours
		for t, time in enumerate(tdim):
			if settings['plot'] == 'poe':
				surface_field = get_surface_poe(ds, pollutant, settings['poe_lvl'], t)	
			elif settings['plot'] == 'concentration':
				surface_field = ds.variables[pollutant][t,0,:,:]
			
			#save data to various storage arrays
			fcst_mean.append(surface_field)
			compiled_data[time] = surface_field
		
		#get geographic dimensions
		hyslat = ds.variables['latitude'][:]
		hyslon = ds.variables['longitude'][:]	
		hysdims = {'lats': hyslat, 'lons': hyslon}	

		#average forecast data
		fc_mean = np.mean(np.array(fcst_mean), 0)
		averaged_data[fcst_tag] = fc_mean

	if 'dump_nc' in settings.keys():
		logging.info(f'Averaged data dump requested: preparing netcdf output {settings["dump_nc"]}')
		generate_nc_output(averaged_data, hysdims, settings)


	return compiled_data


def generate_nc_output(averaged_data, hysdims, settings):
	'''
	Create an output netcdf file for compiled hourly data
	'''

	with nc.Dataset(settings['dump_nc'], 'w') as ncf:	
		#set up dimensions
		time = ncf.createDimension('time', len(averaged_data.keys()))
		lat = ncf.createDimension('lat', len(hysdims['lats']) )
		lon = ncf.createDimension('lon', len(hysdims['lons']) )

		#add variables
		xtime = ncf.createVariable('xtime', 'i', ('time',))
		xlat = ncf.createVariable('xlat', 'f4', ('lat',))
		xlon = ncf.createVariable('xlon', 'f4', ('lon',))
		values = ncf.createVariable(settings['plot'], 'f4', ('time', 'lat', 'lon',))

		if 'cbar_units' in settings.keys():
			values.units = settings['cbar_units']
		
		#assign values
		xlat[:] = hysdims['lats']
		xlon[:] = hysdims['lons']

		#deal with strings
		#date_str =  nc.stringtochar(averaged_data.keys(), 'S8')
		#xtime[:] = date_str

		for f,fcst_tag in enumerate(averaged_data.keys()):
			values[f,:,:] = averaged_data[fcst_tag][:,:]
			xtime[f] = int(fcst_tag)
		logging.debug(xtime[:])
		
	return


def get_nc_data(fcst_tag, settings):
	'''
	Locates correct forecast subfolderes, ncfiles and pulls data for given pollutant, lvl, time
	'''
	
	#check if directory exists
	fcst_path = os.path.join(os.environ['run_dir'],fcst_tag,'hysplit') 
	#if os.path.exists(fcst_path) is False:
	#	logging.warning(f'WARNING: {fcst_path} forecast is missing. Skipping!!!.')
	
	pollutant = settings['pollutant']
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


def plot_hazard(mean_field, settings):
	'''
	Create surface hazard plots plots for averaged conditions
	'''

	#TODO this is hardcoded: remove for future and provide as input
	#NOTE: consider adding bounds in hysplit step (calculate from settings)
	bounds =   [-160.5, -154.5, 18.25, 22.75]
	#stamen_terrain = cimgt.Stamen(desired_tile_form='L', style='terrain-background')


	#plot as separate figure (assumes lat/lon coordiantes from HYSPLIT)
	#plt.figure()
	#ax = plt.axes(projection=ccrs.PlateCarree())
	#im = ax.imshow(mean_poe, origin='lower',cmap=hazard_cmap,vmin=0, vmax=100, extent=bounds, transform=ccrs.PlateCarree())	
	#ax.coastlines(resolution='50m',color='grey', linewidth=0.5)
	#plt.colorbar()
	#plt.title('ANALYSIS PERIOD: {} - {}'.format(settings['start'], settings['end']))
        
	fig_path = os.path.join(os.environ['run_dir'],os.environ['forecast'],'output')
	os.system(f'mkdir -p {fig_path}')
	pollutant = settings['pollutant']
	cm = make_poe_cmap()

	plt.figure()
	ax = plt.axes(projection=ccrs.PlateCarree())
	#ax = plt.axes(projection=stamen_terrain.crs)
	im = ax.imshow(mean_field, origin='lower',cmap=cm,vmin=0,  extent=bounds, transform=ccrs.PlateCarree())
	ax.set_extent(bounds, crs=ccrs.Geodetic())
	#ax.add_image(stamen_terrain, 5, cmap='gray',alpha=0.4)	
	#ax.coastlines()
	#ax.add_feature(cfeature.OCEAN,color='white')
	#prettify gridline
	gl = ax.gridlines(crs=ccrs.PlateCarree(),draw_labels=True,linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
	gl.top_labels = False
	gl.right_labels = False

	if settings['plot'] == 'poe':
		save_path = os.path.join(fig_path,'poe_{}_lvl{}_{}_{}.png'.format(pollutant,\
				settings['poe_lvl'], settings['start'], settings['end']))
		ax.set(title = 'MEAN {} POE | {} - {}'.format(pollutant,settings['start'], settings['end']))
		im = ax.imshow(mean_field, origin='lower',cmap=cm,vmin=0, vmax=100, extent=bounds, transform=ccrs.PlateCarree())
		plt.colorbar(label = 'POE (%)')
	
	elif settings['plot'] == 'concentration':
		save_path = os.path.join(fig_path,f'conc_{pollutant}_{settings["start"]}_{settings["end"]}.png')
		ax.set(title = f'MEAN {pollutant} CONCENTRATION | {settings["start"]} - {settings["end"]}')
		im = ax.imshow(mean_field, origin='lower',cmap=cm,vmin=0,  extent=bounds, transform=ccrs.PlateCarree())
		#plt.colorbar(label = f'concentration ({settings["cbar_units"]})')
	
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



def main(settings):
	'''
	Create a time-averaged hazard map based on user-specified settings
	'''
	logging.info('Creating hazard maps')
	
	#collect data from the user-specified forecast range
	compiled_data = assemble_hourly_data(settings)
	mean_field = sum(compiled_data.values()) / int(len(compiled_data.keys()))

	#do plotting
	plot_hazard(mean_field, settings)

	return

if __name__ == '__main__':
	main(settings)
