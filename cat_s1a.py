#!/usr/bin/env python3

# -*- coding: utf-8 -*-
"""
Script to combine frames from Sentinel-1 that are slightly offset from each other into a single consistent frame
Input data are SAFE files and a pair of (lon,lat) points

Created on Mon Oct 23 10:43:44 2017

@author: elindsey
"""

#import os,sys,subprocess,errno,glob,datetime

import s1_func, gmtsar_func, argparse

######################## Command-line execution ########################

if __name__ == '__main__':

    # input arguments: a directory or set of directories to search, orbit directories, and latitude bounds
    parser = argparse.ArgumentParser(description='Combine bursts from several Sentinel-1 scenes into a single frame, given a min/max lat. bound')
    parser.add_argument('searchdirs',type=str,nargs='+',help='List of directories (or wildcards) containing SAFE files to be combined.')
    parser.add_argument('-o','--orbit',type=str,action='append',required=True,help='Path to a directory holding orbit files, required. Repeat option to search multiple directories.')
    parser.add_argument('-l','--lonlat',type=str,required=True,help='Lon/Lat pins for the crop script in the GMT R-argument format lon1/lat1/lon2/lat2, required.')
    parser.add_argument('-d','--direction',type=str,required=True,help='Orbit direction (A/D), required.')
    args = parser.parse_args()

    # read lons/lats into arrays
    lonlats=[float(i) for i in args.lonlat.split('/')]
    lons=lonlats[0::2]
    lats=lonlats[1::2]

    
    #dirlist=['/home/data/INSAR/S1A/gede/P47/F609','/home/data/INSAR/S1A/gede/P47/F610','/home/data/INSAR/S1A/gede/P47/F613','/home/data/INSAR/S1A/gede/P47/F614','/home/data/INSAR/S1A/gede/P47/F615']
    #s1_orbit_dirs=['/home/data/INSAR/S1A/POD/s1qc.asf.alaska.edu/aux_poeorb']
    #lats=[-6.1,-7.4]
    #lons=[106.9,106.9]
    #asc_desc='D'
    
    # find a list of all scenes and organize them by orbit number
    [images_by_orbit, eofs] = s1_func.find_images_by_orbit(args.searchdirs, args.orbit)
    
    print('found %d orbits'%len(images_by_orbit))
    
    # for each satellite pass
    for ab_orbit in images_by_orbit:
        print('working on orbit %s'%ab_orbit)
        print('images: %s'%images_by_orbit[ab_orbit])
        print('EOF: %s'%eofs[ab_orbit])
        
        # write file list and lat,lon pairs in time order
        safe_fname = 'SAFE_filelist_%s.txt'%ab_orbit
        ll_fname = 'two_pins.ll'
        gmtsar_func.write_list(safe_fname, images_by_orbit[ab_orbit])
        s1_func.write_ll_pins(ll_fname, lons, lats, args.direction) #args.direction is 'A' or 'D' and determines time-ordering of latitudes
        
        # run create_frame_tops.csh
        s1_func.create_frame_tops(safe_fname, eofs[ab_orbit], ll_fname, 'log_%s.txt'%ab_orbit)

