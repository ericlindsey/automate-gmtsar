#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 16:50:38 2021

@author: elindsey
"""

# python-standard modules
import os,sys,argparse,configparser
import numpy as np

# user-defined modules
import gmtsar_func
import plot_intf_list
    
if __name__ == '__main__':
    # read command line arguments and parse config file.
    parser = argparse.ArgumentParser(description='Create plan and plot list of interferograms to be made, or that have been made.')
    parser.add_argument('config',type=str,help='supply name of config file to setup processing options. Required.')
    parser.add_argument('-i','--intf',type=str,default='intf_plan.in',help='supply name of intf.in file to use for list of interferograms. (Default: intf_plan.in).')
    parser.add_argument('-l','--line',type=float,action='append',required=False,help='Plot a vertical line at this decimal year. May repeat as many times as desired.')
    parser.add_argument('--no-label',action='store_true',help='Do not plot scene names (default: plot labels for each scene)')
    parser.add_argument('--no-color',action='store_true',help='Do not plot finished/unfinished interferograms in different colors (default: blue for finished, red for unfinished)')
    args = parser.parse_args()

    print('Creating plot of interferograms using parameters in config file %s'%args.config)
    
    # read config file
    config=configparser.ConfigParser()
    config.optionxform = str #make the config file case-sensitive
    config.read(args.config)
    
    # get options from config file
    SAT=config.get('py-config','sat_name')
    
    #require data.in file, and load it
    if not os.path.isfile('raw/data.in'):
        print('Error: Pre-processing has not been run. No data.in found in raw/ directory. Exiting.')
        sys.exit(1)
    dataDotIn=np.genfromtxt('raw/data.in',dtype='str')

    # create plan, ignoring what has been done so far
    gmtsar_func.setup_intf(SAT,dataDotIn,args.intf,args.config,skip_finished=False)

    # make plot
    plot_intf_list.plot_intf_list(SAT,dataDotIn,args.intf,args.config,lines=args.line,no_label=args.no_label, no_color=args.no_color, plot_fname='plan_intf')
    
