#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 11:52:15 2017

Print out the matching orbit file given an input SAFE, XML, or datestring

@author: elindsey
"""

import s1_func, argparse

######################## Command-line execution ########################

if __name__ == '__main__':

    # read command line arguments
    parser = argparse.ArgumentParser(description='Print a matching orbit file given an input SAFE filename and orbit directory')
    parser.add_argument('SAFE',type=str,nargs='+',help='SAFE file(s) (or wildcards), required. Format: S1A_IW_SLC__1SDV_20150224T114043_20150224T114111_004764_005E86_AD02.SAFE')
    parser.add_argument('-o','--orbit',type=str,action='append',required=True,help='Path to a directory holding orbit files, required. Repeat option to search multiple directories.')
    args = parser.parse_args()
    
    # get times and a/b for each SAFE file name
    for safe in args.SAFE:
        [sat_ab,sat_mode,image_start,image_end,orbit_num] = s1_func.parse_s1_SAFE_name(safe)
    
        # find and print the most recent matching orbit file
        latest_eof = s1_func.get_latest_orbit_file(sat_ab, image_start, image_end, args.orbit, skip_notfound=False)
        print(safe,latest_eof)
