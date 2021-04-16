#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
Created on Wed Feb 7 10:50:38 2018

@author: elindsey
"""

# python-standard modules
import os,sys,argparse,configparser
import numpy as np
import matplotlib.pyplot as plt

# user-defined modules
import gmtsar_func


def plot_intf_list(SAT,dataDotIn,intf_file,config_file,lines=None,no_label=False,no_color=False,plot_fname='plot_intfs'):
    #get list of scenes, and convert to time/baseline coordinates
    # load baseline table
    table = gmtsar_func.load_baseline_table(SAT)
    #get list of scenes. another S1 special case
    command,scenelist,satname = gmtsar_func.get_intf_scenelist(SAT,table,dataDotIn)
    # create lists/dictionaries from data.in
    intdays={}
    decyears={}
    baselines={}
    dirstems={}
    for i in range(len(table)):
        intdays[scenelist[i]]  = table[i][2]
        decyears[scenelist[i]] = gmtsar_func.gmtsardate_to_decyear(table[i][1])
        baselines[scenelist[i]]= table[i][3]
        dirstems[scenelist[i]] = '%.0f' % np.floor(table[i][1])
    # get list of interferograms
    # load intf list - note np.atleast_2d() is required for the case of only one interferogram.
    intflist = np.atleast_2d(np.genfromtxt(intf_file, delimiter=':',dtype=str))
    newlist=[]
    donelist=[]
    for i in range(len(intflist)):
        dirstem0=dirstems[intflist[i][0]]
        dirstem1=dirstems[intflist[i][1]]
        scene0=intflist[i][0]
        scene1=intflist[i][1]
        pairname='%s_%s'%(dirstem0,dirstem1)    
        unwfile = 'intf/' + pairname + '/unwrap_mask_ll.grd'
        if os.path.isfile(unwfile):
            # keep a separate list of how many are finished
            donelist.append([scene0,scene1])
        else:
            newlist.append([scene0,scene1])

    #create plots
    plt.figure(figsize=(10,6))
    ax=plt.subplot(111)
    # plot all intfs in the two lists
    label1='To do'
    color1='r'
    label2='Finished'
    color2='b'
    if no_color:
        color1='k'
        color2='k'
        label1='Interferograms'
        label2=''
    for pair in intflist:
        ax.plot([decyears[pair[0]],decyears[pair[1]]],[baselines[pair[0]],baselines[pair[1]]],color1,label=label1)
        label1=''   
    for pair in donelist: 
        ax.plot([decyears[pair[0]],decyears[pair[1]]],[baselines[pair[0]],baselines[pair[1]]],color2,label=label2)
        label2=''
    #plot scenes as points
    ax.plot(list(decyears.values()),list(baselines.values()),'b.', label='Scenes')
    ax.plot(decyears[scenelist[0]],baselines[scenelist[0]],'r.',label='Master')
    #TODO: add non-overlapping labels. see e.g. https://stackoverflow.com/questions/19073683/matplotlib-overlapping-annotations-text
    if not no_label:
        for scene in scenelist:
            if SAT =='S1':
                scenedate=scene[3:11]
            else:
                scenedate=scene
            plt.annotate(
                scenedate, xy=(decyears[scene],baselines[scene]), xytext=(-5, 5),
                textcoords='offset points', ha='center', va='bottom')
    if lines:
        for line in lines:
            plt.axvline(x=line)
    #finish and save figure
    ax.legend()
    ax.set_ylabel('Perp. baseline (m)')
    ax.set_xlabel('Time (years)')
    image_fname='%s.png'%plot_fname
    plt.savefig(image_fname)
    print('created figure %s'%image_fname)
    image_fname='%s.pdf'%plot_fname
    plt.savefig(image_fname)
    print('created figure %s'%image_fname)
    
    
if __name__ == '__main__':
    # read command line arguments and parse config file.
    parser = argparse.ArgumentParser(description='Check and plot list of interferograms to be made, or that have been made.')
    parser.add_argument('config',type=str,help='supply name of config file to setup processing options. Required.')
    parser.add_argument('-i','--intf',type=str,help='supply name of intf.in file to use for list of interferograms. If not given, will default to the filename found in the config file (usually intf.in).')
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
    
    if args.intf is None:
        intf_file=config.get('py-config','intf_file')
        if intf_file == '':
            intf_file = 'intf.in'
    else:
        intf_file=args.intf
    
    #require data.in file, and load it
    if not os.path.isfile('raw/data.in'):
        print('Error: Pre-processing has not been run. No data.in found in raw/ directory. Exiting.')
        sys.exit(1)
    dataDotIn=np.genfromtxt('raw/data.in',dtype='str')

    # make plot
    plot_intf_list(SAT,dataDotIn,intf_file,args.config,lines=args.line,no_label=args.no_label, no_color=args.no_color)
    
