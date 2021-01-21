#!/usr/bin/env python3

# -*- coding: utf-8 -*-
"""
Script to unzip a list of Sentinel-1 data

Created on Thu Jan 21 11:51:00 2021

@author: elindsey
"""

import s1_func, argparse

######################## Command-line execution ########################

if __name__ == '__main__':

    # required arguments: a directory or set of directories to search, orbit directories, latitude bounds, and A/D to specify the orbit direction
    parser = argparse.ArgumentParser(description='Unzip Sentinel-1 data to a specified directory')
    parser.add_argument('searchdirs',type=str,nargs='+',help='List of directories (or wildcards) containing .zip files to be unzipped.')
    parser.add_argument('-t','--target',type=str,default='.',help='Target directory to unzip the files into. Will be created if it does not already exist.')
    parser.add_argument('-n','--nproc',type=int,default=1,help='Number of processes to run in parallel, optional (default: 1)')
    # parse
    args = parser.parse_args()

    # unzip images in parallel
    s1_func.unzip_images_to_dir_parallel(args.searchdirs, args.target, args.nproc)


