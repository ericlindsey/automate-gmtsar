#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 11:31:38 2017

@author: elindsey
"""

# python-standard modules
import os,sys,argparse,time,configparser
import numpy as np

#parallel processing modules imported beow

#import multiprocessing
#from mpi4py import MPI
#import mpi4py_map
        
# user-defined modules
import gmtsar_func


# parallel part of the processing is controlled here
def run_parallel(cmds, usempi):
    if usempi:
         # call run_command with MPI map
        mpi4py_map.map(gmtsar_func.run_logged_command, cmds)
    else:
        # call run_command with multiprocessing pool    
        with multiprocessing.Pool(processes=numproc) as pool:
            pool.map(gmtsar_func.run_logged_command, cmds)


##################################
#                                #
#    M A I N    S C R I P T      #
#                                #
################################## 

if __name__ == '__main__':
    
    ################################################
    # Stage 0: Read and check config parameters
    #

    # read command line arguments and parse config file.
    parser = argparse.ArgumentParser(description='Run GMTSAR batch processing. Default automatically determines master, does alignment, and runs all possible interferograms using the python multiprocessing toolbox.')
    parser.add_argument('config',type=str,help='supply name of config file to setup processing options. Required.')
    parser.add_argument('--mpi',action='store_true',help='Use MPI (default: false, uses python multiprocessing library instead).')
    parser.add_argument('--debug',action='store_true',help='Print extra debugging messages (default: false)')
    args = parser.parse_args()

    # read config file
    config=configparser.ConfigParser()
    config.optionxform = str #make the config file case-sensitive
    config.read(args.config)
    # get python-specific options from config file as a dict - note they will all be strings
    py_config=dict(config.items('py-config'))
    
    # Setup MPI (optional) or python multiprocessing pool
    if args.mpi:
        from mpi4py import MPI
        import mpi4py_map
        comm = MPI.COMM_WORLD
        ver  = MPI.Get_version()
        numproc = comm.Get_size()
        rank = comm.Get_rank()
        fstSec  = MPI.Wtime()
    else:
        import multiprocessing
        numproc=int(py_config['num_processors'])
        rank = 0    

    SAT=config.get('py-config','sat_name')
    startstage=config.getint('py-config','startstage')
    endstage=config.getint('py-config','endstage')    
    master=config.get('csh-config','master_image')
    align_file=config.get('py-config','align_file')
    intf_file=config.get('py-config','intf_file')
    restart=config.getboolean('py-config','restart')

    # print config options
    if args.debug:
        print('Running gmtsar_app.py:')
        if args.mpi:
            print('  Using MPI')
        print('  config file:',args.config,'contains the following options')    
        print(config.write(sys.stdout))
    
    # check config options
    
    #default names for files
    if align_file == '':
        align_file = 'align_batch.in'
        
    if intf_file == '':
        intf_file = 'intf.in'
    
    # if master specified in the config file disagrees with existing data.in, we must re-do the pre-processing.
    if master and startstage > 1 and os.path.isfile('raw/data.in'):
        #check master in data.in
        dataDotIn=np.genfromtxt('raw/data.in',dtype='str')
        oldmaster=gmtsar_func.get_master_short_name(SAT,dataDotIn[0])
        if oldmaster != master:
            print('Warning: The master specified in the config file disagrees with the old master in data.in.')
            print('We will re-run starting from pre-processing with the master from the config file.')
            startstage = 1
            restart = True
    
    # if data.in is not found, we must do pre-processing.
    if startstage > 1 and not os.path.isfile('raw/data.in'):
        print('Warning: Pre-processing has not been run, changing startstage to 1')
        startstage = 1
            
    # enforce startstage <= endstage
    if endstage < startstage:
        print('Warning: endstage is less than startstage. Setting endstage = startstage.')
        endstage = startstage
    
    # write the new config file to use for processing

    if rank == 0:
        #logtime is the timestamp added to all logfiles created during this run
        logtime=time.strftime("%Y_%m_%d-%H_%M_%S")
        config_file='batch.run.'+ logtime +'.cfg'
        with open(config_file, 'w') as configfilehandle:
            config.write(configfilehandle)
    else:
        logtime = None
        config_file = None
    if args.mpi:
        logtime = comm.bcast(logtime,root=0)
        config_file = comm.bcast(config_file,root=0)
        
    ################################################
    # Stage 1: Preprocessing
    #
    if startstage <= 1:
        if rank == 0:
            print('\nStage 1: running preprocessing.\n')
            if restart:
                print('restart, deleting file raw/data.in.')
                if os.path.isfile('raw/data.in'):
                    os.remove('raw/data.in')
            gmtsar_func.setup_preproc(SAT,py_config,master)
            gmtsar_func.run_preproc(SAT,py_config,master,config_file)


    ################################################
    # Stage 1.5 (always run): Save updated config file, and read data.in
    #
    if rank == 0:
        #require data.in file
        if not os.path.isfile('raw/data.in'):
            print('Error: Pre-processing has not been run. No data.in found in raw/ directory. Exiting.')
            if args.mpi:
                comm.abort(1)
            sys.exit(1)
        dataDotIn=np.genfromtxt('raw/data.in',dtype='str')
        master=gmtsar_func.get_master_short_name(SAT,dataDotIn[0])
        config.set('csh-config','master_image', master)
        # do not allow proc_stage = 1 (to prevent re-running topo_ra a second time)
        if(config.getint('csh-config','proc_stage') < 2):
           config.set('csh-config','proc_stage', 2)
        with open(config_file, 'w') as configfilehandle:
            config.write(configfilehandle)
    else:
        #other nodes get dummy variables
        dataDotIn = None
        config_file = None 
    if args.mpi:
        #transmit data to all nodes
        dataDotIn = comm.bcast(dataDotIn,root=0)
        config_file = comm.bcast(config_file,root=0)
    

    ################################################
    # Stage 2: Alignment
    #
    if startstage <= 2 and endstage >= 2:
        if rank == 0:
            print('\nStage 2: running alignment.\n')
            if restart:
                print('restart, deleting file %s'%align_file)
                if os.path.isfile(align_file):
                    os.remove(align_file)
            if not os.path.isfile(align_file) or not os.path.isdir('logs_align') or not os.path.isfile('SLC/%s.SLC'%master):
                print('running setup_align: creating a default alignment list with all scenes aligned to master.')
                gmtsar_func.setup_align(SAT,dataDotIn,py_config,align_file,logtime)
            cmds = gmtsar_func.get_align_commands(align_file)
            numalign=len(cmds)
            print('running %d alignments from %s using %d processors.'%(numalign,align_file,numproc))
        else:
            cmds = None
        if args.mpi:
            cmds = comm.bcast(cmds,root=0)
        run_parallel(cmds,args.mpi)
    
    
    ################################################
    # Stage 3: Make topo_ra (Convert topo file to radar coordinates)
    #
    if startstage <= 3 and endstage >= 3:
        if rank == 0:
            print('\nStage 3: running topo_ra.csh.\n')
            if restart:
                print('restart, deleting file topo/topo_shift.grd.')
                if os.path.isfile('topo/topo_shift.grd'):
                    os.remove('topo/topo_shift.grd')
            gmtsar_func.run_topo_ra(SAT,config_file,logtime)
    
    
    ################################################
    # Stage 4: Make interferograms
    #
    if endstage >= 4:
        if rank == 0:
            #if not os.path.isfile('topo/topo_shift.grd'):
            #    print('Error: no topo_shift.grd file found, run stage 3 first. Exiting.')
            #    if args.mpi:
            #        comm.abort(1)
            #    sys.exit(1)
            print('\nStage 4: running interferograms in parallel.\n')
            if restart and config.get('py-config','intf_file') == '' and os.path.isfile(intf_file):
                print('restart, deleting file %s.'%intf_file)
                os.remove(intf_file)
            #setup or read list of all interferogram commands to run
            if not os.path.isfile(intf_file):
                gmtsar_func.setup_intf(SAT,dataDotIn,intf_file,config_file)
            cmds=gmtsar_func.get_intf_commands(SAT,dataDotIn,intf_file,config_file,logtime)
            numintf=len(cmds)
            print('running %d interferograms from file %s using %d processors.'%(numintf,intf_file,numproc))
        else:
            print('skip setup, rank %d'%rank)
            cmds = None
        if args.mpi:
            print('before mpi comm, rank %d'%rank)
            cmds = comm.bcast(cmds,root=0)
            print('after mpi comm, rank %d'%rank)
        run_parallel(cmds,args.mpi)
        print('after run_parallel, rank %d'%rank)
    
    
    ################################################
    # End of gmtsar_app.py
    #
    print("\ngmtsar_app.py is done!\n")
