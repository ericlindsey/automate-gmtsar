#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard imports
import argparse,configparser,os,sys

# user-defined modules
import s1_func

if __name__ == "__main__":
    # update both s1a and s1b aux_cal files, and place them in the first listed orbit directory found in config file value 's1_orbit_dir'.
    parser = argparse.ArgumentParser(description='Update Sentinel-1 aux-cal files for use with GMTSAR or other InSAR processing software.')
    parser.add_argument('input',type=str,help='supply either: (1) folder in which to download files, or (2) name of batch.config file containing the option s1_orbit_dir')
    args = parser.parse_args()

    if os.path.isfile(args.input):
        # get the orbit file name. The use of configparser here is a bit of overkill
        config=configparser.ConfigParser()
        config.optionxform = str #make the config file case-sensitive
        config.read('batch.config')
        # get python-specific options from config file as a dict - note they will all be strings
        py_config=dict(config.items('py-config'))
        s1_orbit_dirs=[s.strip() for s in py_config['s1_orbit_dir'].split(',')]
    elif os.path.isdir(args.input):
        s1_orbit_dirs=[args.input]
    else:
        print('Error: must supply either an existing folder or config file as input.')
        sys.exit(1)
    
    for sat_ID in ['s1a','s1b']:
        # use force_update to get a new aux cal file
        auxfile = s1_func.get_s1_auxfile(sat_ID,s1_orbit_dirs,force_update=True)
        print('updated',auxfile)

