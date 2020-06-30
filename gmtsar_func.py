#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 11:31:38 2017

@author: elindsey
"""

# python-standard modules
import os,sys,errno,subprocess,time,itertools,shutil,glob,configparser,distutils.util 
import matplotlib.pyplot as plt
import numpy as np

# user-defined
import s1_func

#import alos1_func,alos2_func


# general outline: first, setup command files:
# setup_preproc : call satellite-specific commands to set up data.in
# setup_align: simple method based on data.in. Does not handle supermaster setup. 
# setup_intf : uses parameters to choose which interferograms will be made

# the rest simply run GMTSAR-standard commands:
# run_preproc
# run_align (parallel)
# run_topo_ra
# run_intf (parallel)


#####################################
#                                   #
# Environement-dependent variables  #
#            Edit here              #
#                                   #
#####################################


##### Use default GMT5SAR csh functions:

# cshpath=''

##### Specify your own path to customized c-shell functions (pre_proc_batch.csh, align_batch.csh, topo_ra.csh, intf_batch.csh, snaphu_interp.csh)
cshpath=os.path.join(os.environ['GMTSAR_APP'], 'gmtsar_functions')


###########################################
#                                         #
# Satellite-dependent functions           #
# Edit here when adding a satellite       #
# Note, there are many more in s1_func.py #
#                                         #
###########################################
   
     
###########################################
# Sentinel-1
#
def edit_xml_for_s1_preproc(py_config):
    # hand-edit the xml files for each scene

    dataDotIn=np.genfromtxt('raw/data.in',dtype='str')
    list_of_xml=[s.split(':')[0] for s in dataDotIn]
    s1_orbit_dirs=[s.strip() for s in py_config['s1_orbit_dir'].split(',')]

    for item in list_of_xml:
        sat_ab=item[0:3] #get sentinel 1A or 1B
        auxfile=s1_func.get_s1_auxfile(sat_ab,s1_orbit_dirs)
        mydate=s1_func.get_datestring_from_xml(item)
        command='''
                   MYFILE=`ls raw_orig/*%s*/manifest.safe`
                   awk 'NR>1 {print $0}' < $MYFILE > tmp_file
                   cat raw_orig/*%s*/annotation/%s.xml tmp_file %s > raw/%s.xml
                   rm -f tmp_file
                '''%(mydate,mydate,item,auxfile,item)
        #note, the aux-cal files (for S1A and S1B) must be manually placed in some folder,
        #for now we use the "cshpath" folder specified above... this is ugly
        run_command(command, logging=False)


def get_master_long_name(s1_subswath,s1_orbit_dirs,master):
    #S1 is a special case - the lines in data.in do not match the filenames and orbit names.
    #we start with something like S1A20161205_ALL_F2, and need to get the long name matching xml:eof
    #we look for files in the SAFE directories that match the date, and reconstruct the name from that
    masterdate=master[3:11]
    filename=glob.glob('raw_orig/S1*.SAFE/annotation/s1?-iw%s-slc-vv-%s*.xml'%(s1_subswath,masterdate))[0]
    xml_name=os.path.basename(filename)
    long_master,eof_name = s1_func.get_s1_image_and_orbit(xml_name,s1_orbit_dirs)
    return long_master


def get_master_short_name(SAT,scene):
    if SAT == 'S1':
        #S1 is a special case - the lines in data.in do not match the filenames and orbit names.
        # We want the corresponding scene name (e.g. S1A20170629_ALL_F3) from a line of data.in, which looks like xml:eof
        #we look for PRM files in raw/, then crop off the 'raw/' and '.PRM' to get the name.        
        mydate=s1_func.get_datestring_from_xml(scene)
        filename=glob.glob('raw/*%s_ALL_F?.PRM'%mydate)[0]
        scenename=os.path.splitext(os.path.basename(filename))[0]
        return scenename
    else:
        #most satellites are simple
        return scene


def get_intf_scenelist(SAT,table,dataDotIn):
    if SAT=='S1':    
        command = cshpath+'/intf_tops.csh'
        scenelist=[el[0].astype(str) for el in table]
        satname=''
    else:
        command = cshpath+'/intf_batch.csh'
        scenelist=dataDotIn
        satname=SAT
    return command,scenelist,satname


###########################################
# TerraSAR-X / TanDEM-X
#
def setup_raw_tsx():
    #the raw files come in folders with a name like 'dims_op*/TSX-1.SAR.L1B/TSX*/'.
    #We have to find these files and convert them to GMTSAR-readable SLC format
    xmllist=glob.glob('dims_op*/TSX*/TSX*/*.xml')
    if len(xmllist)>0:
        print('Creating %d SLC files from the TSX raw images'%len(xmllist))
        pwd=os.getcwd()
        for xmlfile in xmllist:
            #get the xml name and cd to the directory where it is found
            dirname=os.path.dirname(xmlfile)
            xmlname=os.path.basename(xmlfile)
            os.chdir(dirname)
            #tsxdate will be our scene ID name, in the format 'TSXYYYYMMDD'
            tindex=xmlname.index('T',2)
            tsxdate='TSX%s'%xmlname[tindex-8:tindex]
            #find the actual image
            imagename=glob.glob('IMAGEDATA/*.cos')[0]
            #convert the image to SLC with associated files (PRM, LED)
            cmd='make_slc_tsx %s %s %s'%(xmlname,imagename,tsxdate)
            run_command(cmd, logging=False)
            #extend the orbit file
            cmd='extend_orbit %s.LED tmp 3. ; mv tmp %s.LED'%(tsxdate,tsxdate)
            run_command(cmd, logging=False)
            #move the files we just created to our raw/ directory and go back there.
            for f in glob.glob('%s.*'%tsxdate):
                print("move %s to %s"%(f,pwd))
                shutil.move(f,pwd)
            os.chdir(pwd)
    else:
        print('Error: no .xml files found, unable to create SLCs')
        sys.exit(1)

def find_scenes_tsx():
    #look for scenes in the raw directory. If none are found, we make the SLCs first
    os.chdir('raw')
    files=glob.glob('*.SLC')
    if len(files)==0:
        #didn't find any SLCs. Have to make them first
        setup_raw_tsx()
        files=glob.glob('*.SLC')
    #our scene names are just the basename of the SLC files
    scenes=[os.path.splitext(file)[0] for file in files]
    os.chdir('..')
    return scenes

###########################################
# ALOS-1
#    
# deal with ALOS issue of dual polarization scenes, which cannot be used as master.
def find_scenes_alos():
    # we infer the file type based on file size (single-pol scenes are approx. 700MB, dual-pol are 350MB)
    singlelist=[]
    duallist=[]
    os.chdir('raw')
    file=glob.glob('IMG-HH*__?')
    for i in range(len(file)):
        file_i=os.stat(file[i]).st_size
        if file_i > 600000000: # all single-pol files have size > 600 MB 
            singlelist=np.append(singlelist,'%s'%(file[i]))
        else:
            duallist=np.append(duallist,'%s'%(file[i]))
    os.chdir('..')
    return singlelist,duallist

###########################################
# ALOS-2
# 
# simple method to get a list of files. Can make one of these functions for each satellite.
def find_scenes_alos2():
    singlelist=[]
    os.chdir('raw')
    file=glob.glob('IMG-HH*__?') + glob.glob('IMG-HH*__?-F?')
    for i in range(len(file)):
        singlelist=np.append(singlelist,'%s'%(file[i]))
    os.chdir('..')
    return singlelist

###########################################
# Envisat
# 
# simple method to get a list of files. Can make one of these functions for each satellite.
def find_scenes_envi():
    singlelist=[]
    os.chdir('raw')
    file=glob.glob('*.baq')
    for i in range(len(file)):
        stem=file[i].split('.')[0]
        singlelist=np.append(singlelist,stem)
    os.chdir('..')
    return singlelist

###########################################
# ERS
# 
# simple method to get a list of files. Can make one of these functions for each satellite.
def find_scenes_ers():
    singlelist=[]
    os.chdir('raw')
    # ERS data file must end with 5 numbers (orbit ID) and then .dat
    file=glob.glob('*' + ('[0-9]'*5) + '.dat')
    for i in range(len(file)):
        stem=file[i].split('.')[0]
        singlelist=np.append(singlelist,stem)
    os.chdir('..')
    return singlelist

###########################################
# Choose which satellite function to call
# 
def setup_preproc(SAT, py_config, master=''):
    # setup pre-processing file
    # First, get list of scenes. Note ALOS-1 issue of dual-pol, S1 special cases
    duallist=[]
    if SAT == 'ALOS':
        datalist,duallist=find_scenes_alos()
    elif SAT == 'ALOS2':
        datalist=find_scenes_alos2()
    elif SAT == 'ENVI':
        datalist=find_scenes_envi()
    elif SAT == 'ERS':
        datalist=find_scenes_ers()
    elif SAT == 'S1':
        s1_subswath=py_config['s1_subswath']
        s1_orbit_dirs=[s.strip() for s in py_config['s1_orbit_dir'].split(',')]
        datalist=s1_func.find_scenes_s1(s1_subswath,s1_orbit_dirs)
        if master:
            #convert master to the data.in-style name for S1
            master=get_master_long_name(s1_subswath,s1_orbit_dirs,master)
    elif SAT == 'TSX':
        datalist=find_scenes_tsx()
    else:
        print('Error: Satellite (%s) not yet implemented'%SAT)
        sys.exit(1)
    # put master at the top of the list, if specified
    if master:
        if any([master in i for i in datalist]):
            #move to the front of the list
            datalist = np.delete(datalist,np.argwhere(datalist==master),axis=0)
            datalist = np.insert(datalist,0,master)
        elif any([master in i for i in duallist]):
            print('Error: Specified master %s is dual-polarization. Exiting.'%master)
            sys.exit(1)
        else:
            print('Error: Specified master %s not found in raw/ directory. Exiting.'%master)
            sys.exit(1)
    #even if no master was specified, append dual-pol scenes at the end, so they cannot be master accidentally
    finallist=np.append(datalist,duallist)
    mkdir_p('raw')
    np.savetxt('raw/data.in',finallist,fmt='%s')
    
def focus_master(SAT,master):
    focus_cmd = " %s/focus_master.csh %s"%(cshpath,master)
    run_command(focus_cmd, logging=False)
    
#find the indices of the orbit number in the scene name string (for align stage)
def get_orbit_index(SAT,stem):
    if SAT == 'ALOS':
        return slice(13,18)
    elif SAT == 'ALOS2':
        return slice(12,17)
    elif SAT == 'TSX':
        return slice(0,len(stem))
    elif SAT == 'ERS' or SAT == 'ENVI':
        return slice(len(stem)-5,len(stem))
    else:
        print('Error: Satellite (%s) not yet implemented'%SAT)
        sys.exit(1)


############################
#                          #
#  Setup files for GMTSAR  #
#                          #
############################


# setup the list of alignment commands to be run. Simple version: all scenes to master; master is assumed to be first in list
def setup_align(SAT,dataDotIn,py_config,align_file,logtime=''):
    # create align.in with list of commands, and focus master image
    alignlist=[]
    if SAT=='S1':
        if distutils.util.strtobool(py_config['s1_use_esd']):
            s1_preproc='preproc_batch_tops_esd.csh'
        else:
            s1_preproc='preproc_batch_tops.csh'
        s1_esd_mode = py_config['s1_esd_mode']
        #Sentinel alignment cannot be done in parallel...yet!
        alignlist=np.append(alignlist,'cd raw ; %s data.in ../topo/dem.grd 2 %s ; cd .. align_%s.log'%(s1_preproc,s1_esd_mode,logtime))

    else:
        command = cshpath+'/align_batch.csh'
        orbit_indx=get_orbit_index(SAT,dataDotIn[0])
        scansar=distutils.util.strtobool(py_config['scansar'])
        if scansar:
            scan='scan'
        else:
            scan=''
        # make a log directory
        mkdir_p('logs_align')
        for i in range(1,len(dataDotIn)):
            # extracting line from data.in
            pairname='%s_%s'%(dataDotIn[i][orbit_indx],dataDotIn[0][orbit_indx])
            alignlist=np.append(alignlist,'%s %s logs_align/%s.in parallel %s logs_align/%s_%s.log'%(command,SAT,pairname,scan,pairname,logtime))
            #create a 1-line 'align.in' batch file for each pair        
            with open('logs_align/%s.in'%(pairname), 'w') as f:
                f.write('%s:%s:%s\n'%(dataDotIn[0],dataDotIn[i],dataDotIn[0]))
        print('align_file', align_file)
        #before we run in parallel, focus the master image (if needed)
        focus_master(SAT,dataDotIn[0])
    np.savetxt(align_file,alignlist,fmt='%s')
    return alignlist


# read interferogram list and generate the small files and commands needed
def get_intf_commands(SAT,dataDotIn,intf_file,intf_config,logtime):
    # make a log directory
    mkdir_p('logs_intf')
    # load baseline table
    table = load_baseline_table(SAT)
    #get list of scenes. another S1 special case
    command,scenelist,satname = get_intf_scenelist(SAT,table,dataDotIn)
    # create lists/dictionaries from data.in
    dirstems={}
    for i in range(len(table)):
        dirstems[scenelist[i]] = '%.0f' % np.floor(table[i][1])
    # load intf list - note np.atleast_2d() is required for the case of only one interferogram.
    intflist = np.atleast_2d(np.genfromtxt(intf_file, delimiter=':',dtype=str))
    intf_commandlist=[]
    for i in range(len(intflist)):
        dirstem0=dirstems[intflist[i][0]]
        dirstem1=dirstems[intflist[i][1]]
        scene0=intflist[i][0]
        scene1=intflist[i][1]
        pairname='%s_%s'%(dirstem0,dirstem1)    
        intf_commandlist=np.append(intf_commandlist,'%s %s logs_intf/%s.in %s logs_intf/%s_%s.log'%(command,satname,pairname,intf_config,pairname,logtime))
        #create mini intf.in files 
        with open('logs_intf/%s.in'%(pairname), 'w') as f:
            f.write('%s:%s\n'%(scene0,scene1))
    return intf_commandlist
    

# setup the interferogram list, according to optional thresholds. May optionally skip any for which 'unwrap.grd' is already found to exist.
def setup_intf(SAT,dataDotIn,intf_file,intf_config,lines=None,no_label=False):
    print('Setting up interferogram list using config parameters.')
    # read parameters from config file:
    config=configparser.ConfigParser()
    config.read(intf_config)
    max_baseline=config.getint('py-config','max_baseline')
    max_timespan=config.getint('py-config','max_timespan')
    skip_finished=config.getboolean('py-config','skip_finished')    
    intf_min_connectivity=config.getint('py-config','intf_min_connectivity')
    # load baseline table
    table = load_baseline_table(SAT)
    #get list of scenes. another S1 special case
    command,scenelist,satname = get_intf_scenelist(SAT,table,dataDotIn)
    # create lists/dictionaries from data.in
    intdays={}
    decyears={}
    baselines={}
    dirstems={}
    for i in range(len(table)):
        intdays[scenelist[i]]  = table[i][2]
        decyears[scenelist[i]] = gmtsardate_to_decyear(table[i][1])
        baselines[scenelist[i]]= table[i][3]
        dirstems[scenelist[i]] = '%.0f' % np.floor(table[i][1])
    # create a list of all combinations of interferograms that meet the threshold criteria
    intflist=[]
    donelist=[]
    it=itertools.combinations(scenelist,2)
    for el in it:
        if(decyears[el[1]] < decyears[el[0]]):
            # switch the order of the scenes to enforce time0 < time1
            scene0,scene1 = el[1],el[0]
        else:
            scene0,scene1 = el[0],el[1]
        ifg_dir = dirstems[scene0] + '_' + dirstems[scene1]
        unwfile = 'intf/' + ifg_dir + '/phasefilt_mask_ll.grd'
        if (not (os.path.isfile(unwfile) and skip_finished)) and (np.abs(baselines[scene0] - baselines[scene1]) <= max_baseline) and (np.abs(intdays[scene0] - intdays[scene1]) <= max_timespan):
            # we run the interferogram, unless it is both done and we set skip_finished
            intflist.append([scene0,scene1])
        if os.path.isfile(unwfile):
            # keep a separate list of how many are finished
            donelist.append([scene0,scene1])
    # check for min_connectivity
    if intf_min_connectivity > 0:
        dayslist = table['day']
        for scene in scenelist:
            # find number of times the scene is 1st and last
            firstcount = 0
            lastcount = 0              
            intfarray=np.array(intflist)
            donearray=np.array(donelist)
            if len(intfarray) > 0:
                firstcount += (intfarray[:,0]==scene).sum()
                lastcount += (intfarray[:,1]==scene).sum()
            if len(donearray) > 0:
                firstcount += (donearray[:,0]==scene).sum()
                lastcount += (donearray[:,1]==scene).sum()
            if scene != min(intdays) and lastcount < 1:
                #scene is not first, so it should appear second in the list at least once
                #get a sorted list of the scenes that appear before this one
                nextdays = np.sort(dayslist[np.where(dayslist < intdays[scene])])[::-1]
                #check if they are included already, and if not, add them
                for day in nextdays:
                    nextscene = list(intdays.keys())[list(intdays.values()).index(day)]
                    pair = [nextscene,scene]
                    if pair not in intflist and pair not in donelist:
                        print('adding %s to intflist to preserve backward connectivity'%pair)
                        intflist.append(pair)
                        break    
            if scene != max(intdays) and firstcount < 1:
                #scene is not last. so it should appear first in the list at least once
                #get a sorted list of the scenes that appear after this one
                nextdays = np.sort(dayslist[np.where(dayslist > intdays[scene])])
                #check if they are included already, and if not, add them
                for day in nextdays:
                    nextscene = list(intdays.keys())[list(intdays.values()).index(day)]
                    pair = [scene,nextscene]
                    if pair not in intflist and pair not in donelist:
                        print('adding %s to intflist to preserve forward connectivity'%pair)
                        intflist.append(pair)
                        break
    # print number of interferograms
    if skip_finished:    
        print(('Found ' + '%d'%len(donelist) + ' interferograms to skip, finished'))
    print(('Found ' + '%d'%len(intflist) + ' interferograms to do'))
    # write intf_file
    with open(intf_file, 'w') as f:
        for i in range(len(intflist)):
            f.write('%s:%s\n'%(intflist[i][0],intflist[i][1]))


    # currently not plotting. These scripts need an overhaul

    #plot scenes, and intflist / donelist as lines
    #plot_intfs(intflist,donelist,scenelist,decyears,baselines,lines=lines,no_label=no_label)
    #gmt version - works only for ALOS or S1
#    plot_created_intfs(max_timespan, max_baseline, SAT)
#
#def plot_created_intfs(max_timespan, max_baseline, SAT):
#    baselinetable='raw/baseline_table.dat'
#    plot_intfs_cmd = " %s/plot_created_intfs.csh %s %d %d %s"%(cshpath,baselinetable,max_timespan,max_baseline,SAT)
#    print('%s'%plot_intfs_cmd)
#    run_command(plot_intfs_cmd, logging=False)


# def plot_intfs(intflist,donelist,scenelist,decyears,baselines,lines=None,no_label=False):    
#     #create plots
#     ax=plt.subplot(111)
#     # plot all intfs in the two lists
#     label1='To do'
#     for pair in intflist:
#         ax.plot([decyears[pair[0]],decyears[pair[1]]],[baselines[pair[0]],baselines[pair[1]]],'b',label=label1)
#         label1=''   
#     label2='Finished'
#     for pair in donelist: 
#         ax.plot([decyears[pair[0]],decyears[pair[1]]],[baselines[pair[0]],baselines[pair[1]]],':r',label=label2)
#         label2=''
#     #plot scenes as points
#     ax.plot(list(decyears.values()),list(baselines.values()),'b.')
#     ax.plot(decyears[scenelist[0]],baselines[scenelist[0]],'r.',label='Master')
#     #TODO: add non-overlapping labels. see e.g. https://stackoverflow.com/questions/19073683/matplotlib-overlapping-annotations-text
#     if not no_label:
#         for scene in scenelist:
#             plt.annotate(
#                 scene, xy=(decyears[scene],baselines[scene]), xytext=(-5, 5), size=6,
#                 textcoords='offset points', ha='center', va='bottom')
#     if lines:
#         for line in lines:
#             plt.axvline(x=line)
#     #finish and save figure
#     ax.legend()
#     ax.set_ylabel('Perp. baseline (m)')
#     ax.set_xlabel('Time (years)')
#     image_fname='intfs.ps'
#     plt.savefig(image_fname)
#     print('created figure %s'%image_fname)
#     image_fname='intfs.pdf'
#     plt.savefig(image_fname)
#     print('created figure %s'%image_fname)
    

def load_baseline_table(SAT):
    # load baseline table
    baselinetable='raw/baseline_table.dat'
    # check for missing baseline_table.dat - sometimes it is deleted by preproc_batch_tops_esd.csh
    if not os.path.isfile(baselinetable) and os.path.isfile('raw/baseline_table_backup.dat'):
        shutil.copy2('raw/baseline_table_backup.dat',baselinetable)
    if os.path.isfile(baselinetable):
        table=np.loadtxt(baselinetable,usecols=(0,1,2,4),dtype={'names': ('orbit','yearday','day','bperp'), 'formats': ('S100','f16', 'f4', 'f16')})    
        if SAT == 'S1':
            # for this satellite, the first entry of baseline_table is now the XML file and not the 'short' PRM name. 
            # we have to replace that value with the short PRM name for the 'orbit' entry in the dictionary.
            for item in table:
                xmlname = item['orbit'].astype(str)
                shortname = get_master_short_name(SAT,xmlname)
                item['orbit']=shortname
    else:
        print('did not find baseline table!')
        sys.exit(1)
    print(table)
    return table


#############################
#                           #
#    Preprocessing steps    #
#                           #
#############################


# run pre-processing, twice if no master was specified (to choose a central master scene)
def run_preproc(SAT,py_config,master,configfile):
    if master:
        print('run preprocessing using user-specified master: %s'%master)
    else:
        print('Master not specified, running initial preprocessing step to determine master.')
        exec_preproc_command(SAT,py_config,configfile)
        print('Identifying most central scene to use as master.')
        master=choose_master_image(SAT)
        print('run preprocessing again using automatically selected master: %s'%master)
    exec_preproc_command(SAT,py_config,configfile)


# create and call the pre-processing command
def exec_preproc_command(SAT,py_config,configfile):
    if SAT == 'S1':
        # read parameters from config file:
        s1_subswath=py_config['s1_subswath']
        #modify the XML files for Sentinel
        edit_xml_for_s1_preproc(py_config)
        #make links and call preproc_batch_tops.csh (no option for esd here, since we won't use it)
        command ='''
                    cleanup.csh raw
                    cd raw
                    ln -s ../raw_orig/*EOF .
                    ln -s ../raw_orig/*/measurement/*iw%s*tiff .
                    preproc_batch_tops.csh data.in ../topo/dem.grd 1 >& preprocess_%s.log
                    cp baseline_table.dat baseline_table_backup.dat
                    cd ..
                    '''%(s1_subswath,time.strftime("%Y_%m_%d-%H_%M_%S"))
        run_command(command, logging=False)
    elif SAT == 'TSX':
        #almost generic but we don't run cleanup.
        command='''
                   cd raw
                   %s/pre_proc_batch.csh %s data.in ../%s >& preprocess_%s.log
                   cd ..
                '''%(cshpath,SAT,configfile,time.strftime("%Y_%m_%d-%H_%M_%S"))
        run_command(command, logging=False)
    else:
        #run the generic pre_proc_batch.csh for all other satellites
        command='''
                   cleanup.csh raw
                   cd raw
                   %s/pre_proc_batch.csh %s data.in ../%s >& preprocess_%s.log
                   cd ..
                '''%(cshpath,SAT,configfile,time.strftime("%Y_%m_%d-%H_%M_%S"))
        run_command(command, logging=False)


# after running the baseline calculation from the first pre_proc_batch,
# choose a new master that is close to the median baseline and timespan.
def choose_master_image(SAT):    
    # load baseline table
    baselineFile = np.genfromtxt('raw/baseline_table.dat',dtype=str)
    time = baselineFile[:,1].astype(float)
    baseline = baselineFile[:,4].astype(float)
 
    #GMTSAR (currently) guarantees that this file has the same order of lines as baseline_table.dat.
    #so we assume this to be true in the following.
    #a more complete way would be to match the orbit IDs between data.in and baseline_table.dat (not implemented)
    dataDotIn=np.genfromtxt('raw/data.in',dtype='str').tolist()
    
    # calculate shortest distance from median to scenes
    consider_time=True
    if consider_time:
        time_baseline_scale=1 #arbitrary scaling factor, units of (days/meter)
        sceneDistance = np.sqrt(((time-np.median(time))/time_baseline_scale)**2 + (baseline-np.median(baseline))**2)
    else:
        sceneDistance = np.sqrt((baseline-np.median(baseline))**2)
    
    # ALOS-1 only: exclude dual-pol scenes
    if SAT == 'ALOS':
        singlelist,duallist=find_scenes_alos()
        for scene in duallist:
            dualsceneID=dataDotIn.index(scene)
            sceneDistance[dualsceneID]=np.inf #lazy way to remove this scene from consideration for master

    #find the (first) scene with minimum distance
    masterID=np.argmin(sceneDistance)
    masterName=dataDotIn[masterID]

    # put masterId in the first line of data.in
    dataDotIn.pop(masterID)
    dataDotIn.insert(0,masterName)
    
    os.rename('raw/data.in','raw/data.in.old')
    np.savetxt('raw/data.in',dataDotIn,fmt='%s')
    return masterName
    

#############################
#                           #
#   Run commands on shell   #
#                           #
#############################


# run topo_ra step on command line
def run_topo_ra(SAT,config_file,logtime):
    if SAT=='S1':
        #make some links because S1 processing bizarrely does not have an SLC folder
        mkdir_p('SLC')
        command='''
                   cd SLC
                   ln -s ../raw/*ALL*SLC .
                   ln -s ../raw/*ALL*PRM .
                   ln -s ../raw/*ALL*LED .
                   cd ..
                '''    
        run_command(command,logging=False)
        
    command=cshpath+"/topo_ra.csh %s topo_ra_%s.log"%(config_file,logtime)
    run_command(command)

# read list of commands from a file as an array
def get_align_commands(infile):
    #read each line of the input file and convert to a command. Return a list of commands as strings.
    commands=[]
    with open(infile) as f:
        for line in f:
            command = line.strip()
            commands.append(command)
    return commands



def run_command(command, logging=True):
    """
    Use subprocess.call to run a command.
    Default assumes last argument is the log file, and removes it from the command (danger!).
    """
    print('running', command)
    if logging:
        #remove last argument and open it as log file
        logfile=command.split()[-1]
        cmd=' '.join(command.split()[0:-1])
        with open(logfile,'w') as outFile:
            status=subprocess.call(cmd, shell=True, stdout=outFile, stderr=outFile)
    else:
        #no logging, just run command as-is
        status=subprocess.call(command, shell=True)
    if status != 0:
        print('Python encountered an error in the command:')
        print(command)
        print('error code:', status)
        sys.exit(1)
              
        
#############################
#                           #
#      Other functions      #
#                           #
#############################

def gmtsardate_to_decyear(date):
    year=int(str(date)[0:4])
    days=float(str(date)[4:])
    if (year % 4 == 0 and year % 400 != 0):
        yeardays=366
    else:
        yeardays=365
    return year + days/yeardays

def pad_string_zeros(num):
    if num<10:
        numstring="0"+str(num);
    else:
        numstring=str(num);
    return numstring;

def get_file_from_path(path):
    file=path.split('/')[-1]
    return file

def write_list(fname,strlist):
    """
    write a list of strings to a file
    """
    with open(fname,'w') as f:
        f.write('\n'.join(strlist))
        f.write('\n')
              
def mkdir_p(path):
    """
    Implement shell 'mkdir -p' to create directory trees with one command, and ignore 'directory exists' error
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

