#!/usr/bin/env python3

# -*- coding: utf-8 -*-
"""
Use SNAP/gpt to combine frames from Sentinel-1 GRDH data, apply a terrain correction, and crop to a specified region.
Input data are GRDH-format .zip files and a WKT-formatted polygon to set the crop region.

Created on Fri Sep 28 12:17:00 2018

@author: elindsey
"""

#import os,sys,subprocess,errno,glob,datetime

import s1_func, argparse, configparser, os.path, subprocess, sys

######################## Command-line execution ########################

if __name__ == '__main__':

    # input arguments: a directory or set of directories to search, orbit directories, and latitude bounds
    parser = argparse.ArgumentParser(description='Combine bursts from several Sentinel-1 scenes into a single frame, given a min/max lat. bound')
    parser.add_argument('config',type=str,help='Config file containing parameters "region", "data_path", "output_path", and "xml_list". region is a WKT-formatted polygon string. E.g. POLYGON((0,0 0,1 1,1 1,0 0,0)). data_path and xml_list may be comma separated.')
    args = parser.parse_args()

    # read config file
    config=configparser.ConfigParser()
    config.optionxform = str #make the config file case-sensitive
    config.read(args.config)
    # read WKT-formatted region
    region=config.get('gpt-config','region')
    output_path=config.get('gpt-config','output_path')
    # data path may be a comma-separated list.
    data_path=[s.strip() for s in config.get('gpt-config','data_path').split(',')]
    # xml files may be a comma-separated list. First file applies to the case of one image found, second one to two images, etc.
    xml_list=[s.strip() for s in config.get('gpt-config','xml_list').split(',')]
    
    # find a list of all scenes and organize them by acquisition date
    print(data_path)
    orbits_dict = s1_func.find_files_by_orbit(data_path)
    print('found %d orbits with data'%len(orbits_dict))
    
    # for each satellite pass
    for ab_orbit in orbits_dict:
        print('working on orbit: %s'%ab_orbit)
        print(orbits_dict[ab_orbit])
        #determine which xml file to use
        if len(orbits_dict[ab_orbit])==1:
            # one file only
            xmlfile=xml_list[0]
            outfile='%s/%s_%s.tif'%(output_path,os.path.basename(orbits_dict[ab_orbit][0])[0:55],os.path.splitext(os.path.basename(xmlfile))[0])
            cmd='/Applications/snap/bin/gpt %s -Pfile1=%s -Pregion="%s" -Poutfile=%s'%(xmlfile,orbits_dict[ab_orbit][0],region,outfile)
        elif len(orbits_dict[ab_orbit])==2:
            # two files only
            xmlfile=xml_list[1]
            outfile='%s/%s_%s.tif'%(output_path,os.path.basename(orbits_dict[ab_orbit][0])[0:55],os.path.splitext(os.path.basename(xmlfile))[0])
            cmd='/Applications/snap/bin/gpt %s -Pfile1=%s -Pfile2=%s -Pregion="%s" -Poutfile=%s'%(xml_list[1],orbits_dict[ab_orbit][0],orbits_dict[ab_orbit][1],region,outfile)
        else:
            print("Error: Too many files for this orbit! Add a new xml file that handles 3 images.")
            sys.exit(1)
        print(cmd)
        if not os.path.isfile(outfile):
            status=subprocess.call(cmd, shell=True)
            if status != 0:
                print('Python encountered an error in the command:')
                print(cmd)
                print('error code:', status)
                #sys.exit(1)
        else:
            print('\nFile %s exists, skipping\n'%outfile)
        
