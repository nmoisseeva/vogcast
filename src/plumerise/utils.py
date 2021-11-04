# September 2021
#nadya.moisseeva@hawaii.edu
#fucntions and utilities

import numpy as np
import json

# find zi
def get_zi(T0,dz):
    r'''
    Retrieve the height of boundary layer top $z_i$, based on gradient of potential temperature lapse rate.
    ...

    Parameters:
    -----------
    T0 : ndarray
        1D array representing potential temperature sounding [K]
    dz : float
        vertical grid spacing [m]

    Returns:
    --------
    $z_i$ : float
        boundary layer height [m]
    '''
    dT = T0[1:]-T0[0:-1]
    gradT = dT[1:] - dT[0:-1]
    surface = round(200/dz)
    zi_idx = np.argmax(gradT[surface:]) + surface                 #vertical level index of BL top
    zi = dz * zi_idx
    return zi


def plume_error(plumes):
    r'''
    Get true and parameterized injection height for a collection of plumes
    ...
    Parameters:
    -----------
    plumes : list
        list containing plume objects


    Returns:
    -------
    zCLmodel : list
        modelled injection height [m]
    zCLtrue : list
        LES-derived injection height [m]
    '''
    zCLmodel, zCLtrue = [],[]
    for plume in plumes:
        estimate = plume.Tau*plume.wf + plume.zs
        zCLmodel.append(estimate)
        zCLtrue.append(plume.zCL)

    return zCLmodel, zCLtrue

def read_json(json_path):
        '''
        Read input json file
        '''
        #open json file
        f = open(json_path)

        #return json opject as a dictionary
        inputs = json.load(f)

        #close file and return settings
        f.close()
        return inputs

def write_json(json_path, json_data):
        '''
        Write json file
        '''
        with open(json_path, 'w') as f:
                f.write(json.dumps(json_data, indent=4))

        return

def compile_output(outdict, case):
        '''
        Fill useful variables for output
        '''
        outdict['zCL'] = case.zCL
        outdict['zi'] = case.zi
        outdict['I'] = case.I
        outdict['penetrative'] = case.penetrative
        outdict['Z'] = case.interpZ.tolist()
        outdict['Cnorm'] = case.profile 

        return outdict