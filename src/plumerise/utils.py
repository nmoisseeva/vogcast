# September 2021
#nadya.moisseeva@hawaii.edu
#fucntions and utilities

import numpy as np
import json


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
