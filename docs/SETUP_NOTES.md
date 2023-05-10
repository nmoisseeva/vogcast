#HYSPLIT INSTALL
Must install from source, if using intel-based packages through modules
Edit Makefile.inc to correct modules-based paths (use symlink to Makefile.inc.intel)
Purge prior to loading NetCDF-Fotran modules: default will result in errors

#WRF-SFIRE INSTALL
Git repository is here: https://github.com/openwfm/WRF-SFIRE
Configure for dmpar w/ Intel

#WPS INSTALL
Git repository is here: https://github.com/wrf-model/WPS
Configure for smpar w/ Intel - looks like dmpar needs OpemMPI to be installed with intel? 
Supporting data (wrfgeog) is separate. Must edit wrf config files in vog-pipline to point namelist.wps to correct location - perhaps need to move that to input json

#VOG-PIPELINE
Directories not pushed to remote: venv, vmap and run
Python venv: additional requirements to standard ITS environmnet:
	* wrf-python
	* hjson
	* netcdf4
	* matplotlib
	* (optional for dev work) ipython
