#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
Created on Wed Feb 7 10:50:38 2018

@author: elindsey
"""

# python-standard modules
import os,sys,argparse,configparser
import numpy as np

# user-defined modules
import gmtsar_func
    
if __name__ == '__main__':
    
    # read command line arguments and parse config file.
    parser = argparse.ArgumentParser(description='Check and plot list of interferograms to be made, or that have been made.')
    parser.add_argument('config',type=str,help='supply name of config file to setup processing options. Required.')
    parser.add_argument('-l','--line',type=float,action='append',required=False,help='Plot a vertical line at this decimal year. May repeat as many times as desired.')
    parser.add_argument('--no-label',action='store_true',help='Do not plot scene names (default: plot labels for each scene)')
    args = parser.parse_args()

    
    print('Creating plot of interferograms using parameters in config file %s'%args.config)
    
    # read config file
    config=configparser.ConfigParser()
    config.optionxform = str #make the config file case-sensitive
    config.read(args.config)
    
    # get options from config file
    intf_file=config.get('py-config','intf_file')
    SAT=config.get('py-config','sat_name')
        
    if intf_file == '':
        intf_file = 'intf.in'
    
    #require data.in file, and load it
    if not os.path.isfile('raw/data.in'):
        print('Error: Pre-processing has not been run. No data.in found in raw/ directory. Exiting.')
        sys.exit(1)
    dataDotIn=np.genfromtxt('raw/data.in',dtype='str')

    # setup or read list of all interferogram commands to run, and make plot
    gmtsar_func.setup_intf(SAT,dataDotIn,intf_file,args.config,lines=args.line,no_label=args.no_label)
