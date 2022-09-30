INSTALLING PYTHON PACKAGES ON MANA
===================================

* start an interactive sesssion

* activate (create first, if necessary) the virtual environment
	`source venv/bin/activate`

* run pip
	`python3 -m pip install [packagename]`

* deactivate


Loaded from cluter modules
-------------------------
SciPy
NumPy


Specific installs
-----------------
matplotlib
bs4
pymatreader
datetime
pandas
wrf-python
linecache
netCDF4
cartopy
sklearn

Which modules use what? 
----------------------
Just making a start now... Need to go back and complete this list

* FLIR output processing
	- bs4 (decodes hvo html page to get available file listings)
	- pymatreader (read matlab files)
* configuration
	- hjson (decodes human-friendly json files)
	- datetime
* data analysis and nearest date search functionality
	- pandas
* wrf analysis
	- wrf-python
* stn data extraction from arl files
	- linecache
* graphics
	- cartopy
	- matplotlib
* cwipp
	- sklearn (nearest neighbour search)


