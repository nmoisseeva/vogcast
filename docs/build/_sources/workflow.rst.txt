.. _workflow:

Workflow Configuration
======================


.. .. code-block:: python

..   >>> inputs[case.name]
..   {'sounding': array([...]),
..   'I': float,
..   'zCL': float,
..   'zCL': float,
..   'penetrative': boolean}


Configuration Settings
-------------------------------
The main configuration file ``vog.config`` uses `hjson <https://hjson.github.io/>`_ format. The table below details the availble options for each module of the framework. Where ``str`` arguments are requested use single/double quotes. Block comments ``/*  */`` for masking unused options are also permitted. Sample ``vog.config`` file is located in the main repository directory. 

When defining emissions sources, ensure the same user-defined tags (denoted **<KEY>** in the table below) are used for both ``source`` and ``emissions`` module blocks. Multiple sources are permitted. 

.. _vog-config-table:

+------------------+-----+--------------------------------------------------------------+
| Parameter        |Type | Description                                                  |
+==================+=====+==============================================================+
| **vog_root**     | str | path to VogCast directory                                    |
+------------------+-----+--------------------------------------------------------------+
| **run_dir**      | str | path to working directory for storing run data               |
+------------------+-----+--------------------------------------------------------------+
| **runhrs**       | int | total simulation length in hours                             |
+------------------+-----+--------------------------------------------------------------+
| **max_dom**      | int | total number of meteorological domains                       |
+------------------+-----+--------------------------------------------------------------+
| **spinup**       | int | spinup hours (from beginning of met)                         |
+------------------+-----+--------------------------------------------------------------+
| **rerun**        | bool| flag for partial rerun using existing ``vog_run.json``       |
+------------------+-----+--------------------------------------------------------------+
| **modules**      | list| which modules to re-run (optional for reruns only)           |
+------------------+-----+--------------------------------------------------------------+
| **keys**         | str | path to api credentials (optional for HVO-API access)        |
+------------------+-----+--------------------------------------------------------------+
| **'meteorology'**                                                                     |
+------------------+-----+--------------------------------------------------------------+
| **model**        | str | | meteorological input model: *'wrf'/'nam'/'prerun'*         |
|                  |     | | *wrf*: run WRF model                                       |
|                  |     | | *nam*: use NAM forecast analysis data                      |
|                  |     | | *prerun*: use existing ``wrfout_*`` files                  |
+------------------+-----+--------------------------------------------------------------+
| **wrf_path**     | str | path to WRF model (model: *'wrf'*)                           |
+------------------+-----+--------------------------------------------------------------+
| **wps_path**     | str | path to WPS (model: *'wrf'*)                                 |
+------------------+-----+--------------------------------------------------------------+
| **ibc_path**     | str | path to initial conditions (model: *'wrf'*)                  |
+------------------+-----+--------------------------------------------------------------+
| **ibc**          | str | ibc analysis type: *nam/gfs/historic* (model: *'wrf'*)       |
+------------------+-----+--------------------------------------------------------------+
| **type**         | str | | type of arl file: *'prod'/'archive'* (model: *'nam'*)      |
|                  |     | | *prod*: production/current data                            |
|                  |     | | *archive*: historic data                                   |
+------------------+-----+--------------------------------------------------------------+
| **arl_path**     | str | local path to store arl data (model: *'nam'*)                |
+------------------+-----+--------------------------------------------------------------+
| **prerun_path**  | str | path to ``wrfout_*`` files (model : *'prerun'*)              |
+------------------+-----+--------------------------------------------------------------+
| **'source'**                                                                          |
+------------------+-----+--------------------------------------------------------------+
| **<KEY>**        | user-defined tag for emission source (e.g. VENT1)                  |
+------------------+-----+--------------------------------------------------------------+
| **lat**          |float| emissions source lat                                         |
+------------------+-----+--------------------------------------------------------------+
| **lon**          |float| emissions source lon                                         |
+------------------+-----+--------------------------------------------------------------+
| **pr_model**     | str | | plume-rise model: *'static_area'/'cwipp'*                  |
|                  |     | | *static_area*: constant height emissions                   |
|                  |     | | *cwipp*: dynamic plume-rise model (requires WRF met)       |
+------------------+-----+--------------------------------------------------------------+
| **height**       | int | emissions height in m (pr_model: *static_area*)              |
+------------------+-----+--------------------------------------------------------------+
| **area**         | int | emissions area in sqm (pr_model: *static_area*)              |
+------------------+-----+--------------------------------------------------------------+
| **method**       | str | | intensity algorithm: *'hc'/'mass'* (pr_model: *cwipp*)     |
|                  |     | | *mass*: based on mass flux                                 |
|                  |     | | *hc*: based on heat transfer                               |
+------------------+-----+--------------------------------------------------------------+
| **gas_fractions**| dict| plume composition {H2O,CO2,SO2} as decimal (by mol, optional)|
+------------------+-----+--------------------------------------------------------------+
| **vent_params**  | str | | vent parameter source: *'prescribed'/'flir'*               |
|                  |     | | (pr_model: *cwipp*)                                        |
|                  |     | | *prescribed*: user-defined temperature/area                |
|                  |     | | *flir*: use thermal imagery (VMAP only)                    |
+------------------+-----+--------------------------------------------------------------+
| **flir_path**    | str | path to thermal images (VMAP only, vent_params: *flir*)      |
+------------------+-----+--------------------------------------------------------------+
| **temperature**  | int | lava surface temperature in degC (vent_params: *prescribed*) |
+------------------+-----+--------------------------------------------------------------+
| **area**         | int | lava surface are in m2 (vent_params: *prescribed*)           |
+------------------+-----+--------------------------------------------------------------+
| **'emissions'**                                                                       |
+------------------+-----+--------------------------------------------------------------+
| **<KEY>**        | user-defined tag for emission source (e.g. VENT1)                  |
+------------------+-----+--------------------------------------------------------------+
| **input**        | str | | source of emissions data: *'hvo'/'manual'*                 |
|                  |     | | *hvo*: use HVO-API (permission required)                   |
|                  |     | | *manual*:  prescribed emission rate                        |
+------------------+-----+--------------------------------------------------------------+
| **rate**         | int | SO2 emission rate in tonnes/day (input: *manual*)            |
+------------------+-----+--------------------------------------------------------------+
| **'dispersion'**                                                                      |
+------------------+-----+--------------------------------------------------------------+
| **hys_path**     | str | path to HYSPLIT model                                        |
+------------------+-----+--------------------------------------------------------------+
|**carryover_path**| str | path to carryover vog HYSPLIT binary files                   |
+------------------+-----+--------------------------------------------------------------+
| **freq**         | int | forecast cycle frequency in hours (for carryover dump)       |
+------------------+-----+--------------------------------------------------------------+
| **vert_motion**  | int | HYSPLIT vertical motion setting                              |
+------------------+-----+--------------------------------------------------------------+
| **min_zi**       | int | minimum mixing depth in meters                               |
+------------------+-----+--------------------------------------------------------------+
| **numpar**       | int | particle count per source (x5 for 'cwipp' sources)           |
+------------------+-----+--------------------------------------------------------------+
| **lvls**         | list| vertical output levels in m AGL (include 0 for deposition)   |
+------------------+-----+--------------------------------------------------------------+
| **'post_process'**                                                                    |
+------------------+-----+--------------------------------------------------------------+
| **conversion**   | dict| | conversions for comparsion with obs (model assumes mg/m3)  |
|                  |     | | for each pollutant: format [factor, 'unit name']           |
|                  |     | | eg: SO2 : [0.38,'ppm']                                     |
+------------------+-----+--------------------------------------------------------------+
| **peo**          | list| exceedance thresholds (3 max) in obs units (optional)        |
+------------------+-----+--------------------------------------------------------------+
| **stns**         | str | | extract station traces for a pollutant(optional)           |
|                  |     | | *tag*: file naming tag                                     |
|                  |     | | *stn_file*: path to stations location file                 |
+------------------+-----+--------------------------------------------------------------+
| **plots**        | dict| | which plots to create for which pollutant                  |
|                  |     | | *concentration*: ensemble mean surface concentration       |
|                  |     | | *poe*: probability of exceeedance plots                    |
|                  |     | | *ci*: column-integrated shading (qualitative currently)    |
|                  |     | | *smooth*: smooth plots (default = true)                    |
|                  |     | | *leaflet*: make transparent pngs for web (default = false) |
+------------------+-----+--------------------------------------------------------------+
| **'extras'** (optional)                                                               |
+------------------+-----+--------------------------------------------------------------+
| **hazard_map**   | dict| | generate a hazard map (optional)                           |
|                  |     | | *pollutants*: which pollutants to plot (list of str)       |
|                  |     | | *plot*: plot type  *'concentration'/'poe'*                 |
|                  |     | | *start*: analysis period start date in UTC ('YYYY-mm-DD')  |
|                  |     | | *end*: analysis period end date in UTC ('YYYY-mm-DD')      |
|                  |     | | *freq*: cycle frequency in pandas format (e.g. '12h')      |
|                  |     | | *skiphrs*: number of hrs to exclude from dispersion start  |
|                  |     | | *dump_nc*: save compiled data as netcdf: *'hourly'/'daily'*|
|                  |     | | *zflag*: vertical level to extract (0 for deposition)      |
|                  |     | | *poe_lvl*: exceedance threshold to plot ('poe' plots only) |
+------------------+-----+--------------------------------------------------------------+


Running VogCast
----------------

The framework is ran by executing a python ``vog-run`` script located in ``<vog_root>/src/vog-run`` as follows:

.. code-block:: console

  >>> python <path to vog-run> -c <path to vog.config> -d <date> <cycle>

For example, to run a 0Z forecast for 2020-01-01:

.. code-block:: console

  >>> python /home/user/vogcast/src/vog-run -c /home/user/runs/vog.config -d 20200101 0


If running operationally for current day, the date flag can be omitted (using 12Z cycle as example):

.. code-block:: console

  >>> python /home/user/vogcast/src/vog-run -c /home/user/runs/vog.config 12

Each run will create a storage directory named ``YYYYmmDDCC``, in location specified under ``run_dir`` by the user. If ``rerun`` is set to ``false``, yet directory under a matching name already exists, VogCast will overwrite its contents and generate a new ``vog_run.json`` file controlling the parameters of the simulation.  
If set to ``true``, the framework will use existing ``vog_run.json`` and only overwite the contents of modules specified in ``modules``  in ``vog.config``.