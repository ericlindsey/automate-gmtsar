#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 11:45:24 2017

@author: elindsey
"""

import os,sys,shutil,glob,datetime,distutils.util #,subprocess,errno
import gmtsar_func

######################## Sentinel-specific functions ########################
# This satellite is a real nightmare for my attempts at standardization 

def get_s1_preproc(py_config):
    s1_use_esd=distutils.util.strtobool(py_config['s1_use_esd'])
    if s1_use_esd:
        s1_preproc='preproc_batch_tops_esd.csh'
    else:
        s1_preproc='preproc_batch_tops.csh'
    return s1_preproc

def find_scenes_s1(s1_subswath,s1_orbit_dirs):
    """
    For Sentinel, data.in is a reference table that links the xml file with the correct orbit file.
    """
    outputlist=[]
    list_of_images=glob.glob('raw_orig/S1*.SAFE/annotation/s1?-iw%s-slc-vv*.xml'%s1_subswath)
    print('found list')
    print(list_of_images)

    for item in list_of_images:
        #make sure we have just the file basename
        xml_name = os.path.basename(item)
        #find latest EOF and create the "long-format" image name containing the EOF
        image_name,eof_name = get_s1_image_and_orbit(xml_name,s1_orbit_dirs)
        # copy this EOF to the raw_orig directory
        command = 'cp %s raw_orig/'%(eof_name)
        gmtsar_func.run_command(command, logging=False)
        # append image to list
        outputlist.append(image_name)
    return outputlist


def find_images_by_orbit(dirlist,s1_orbit_dirs):
    """
    For each Sentinel-1 satellite, find all images that were acquired on the same orbit, and order them by time
    """
    valid_modes = ['IW_SLC'] #we match only IW_SLC data
    
    #dictionaries will keep track of the results
    names       = dict()
    start_times = dict()
    eofs        = dict()
    
    for searchdir in dirlist:
        list_of_images=glob.glob('%s/S1*SAFE'%searchdir)
        print('in',searchdir)
        print('found_list',list_of_images,'\n')
        
        for item in list_of_images:
            # we want the full path and also just the file name
            item=os.path.abspath(item)
            file=os.path.basename(item)
            
            # get A/B, sat. mode, dates, orbit ID from the file name
            [sat_ab,sat_mode,image_start,image_end,orbit_num] = parse_s1_SAFE_name(file)
            print('Read zipfile:',file,sat_ab,sat_mode,image_start,image_end,orbit_num)

            if sat_mode in valid_modes:
                #Find matching EOF
                eof_name = get_latest_orbit_file(sat_ab,image_start,image_end,s1_orbit_dirs,skip_notfound=True)
                if eof_name is not None:
                    print('Got EOF:',eof_name)
                
                    #add A or B to the orbit number and use as the unique ID for identifying orbits
                    ab_orbit='S1%s_%06d'%(sat_ab,orbit_num)
                    if ab_orbit not in names:
                        names[ab_orbit] = []
                        start_times[ab_orbit] = []
                        eofs[ab_orbit] = eof_name
                    elif eof_name != eofs[ab_orbit]:
                        #we've already found one scene from this orbit. check that it matches the same orbit file 
                        print('Error: found two scenes from same orbit number matching different EOFs. Check your data.')
                        sys.exit(1)
                    
                    #keep the images in time order. Find the index of the first time that is later than the image's time
                    timeindx=0
                    for starttime in start_times[ab_orbit]:
                        if starttime < image_start:
                            timeindx+=1
                    names[ab_orbit].insert(timeindx,item)
                    start_times[ab_orbit].insert(timeindx,image_start)
                    print('Added image at position %d for orbit %s'%(timeindx,ab_orbit) )
                    print('List is now %s'%names[ab_orbit])
            print('')
    return names, eofs


def get_latest_orbit_file(sat_ab,imagestart,imageend,s1_orbit_dirs,skip_notfound=True):
    """
    Orbit files have 3 dates: production date, start and end range. Image files have 2 dates: start, end.
    We want to find the latest file (most recent production) whose range includes the range of the image.
    Return string includes absolute path to file.
    """
    eoflist=[]
    eofprodlist=[]

    # add one hour to the image start/end times to ensure we have enough coverage in the orbit file
    imagestart_pad = imagestart - datetime.timedelta(hours=0.5)
    imageend_pad = imageend + datetime.timedelta(hours=0.5)
     
    for s1_orbit_dir in s1_orbit_dirs:
        for item in glob.glob(s1_orbit_dir+"/S1"+sat_ab+"*.EOF"):
            #get basename, and read dates from string
            eof=os.path.basename(item)
            [eofprod,eofstart,eofend] = get_dates_from_eof(eof)
            #check if the EOF validity dates span the entire image
            if eofstart < imagestart_pad and eofend > imageend_pad:
                eoflist.append(os.path.abspath(os.path.join(s1_orbit_dir,eof)))
                #record the production time to ensure we get the most recent one
                eofprodlist.append(eofprod)       
    if eoflist:
        #get the most recently produced valid EOF
        latest_eof = eoflist[eofprodlist.index(max(eofprodlist))]
        
    else:
        if skip_notfound:
            print("Warning: No matching orbit file found for Sentinel-1%s during time %s to %s in %s - skipping"%(sat_ab,imagestart_pad,imageend_pad,s1_orbit_dirs))
            return None
        else:
            print("Error: No matching orbit file found for Sentinel-1%s during time %s to %s in %s"%(sat_ab,imagestart_pad,imageend_pad,s1_orbit_dirs))
            sys.exit(1)
            
    return latest_eof


def parse_s1_SAFE_name(safe_name):
    """
    SAFE file has name like S1A_IW_SLC__1SDV_20150224T114043_20150224T114111_004764_005E86_AD02.SAFE (or .zip)
    Function returns a list of 2 strings, 2 datetime objects and one integer ['A', 'IW_SLC', '20150224T114043','20150224T114111', 004764]
    """
    #make sure we have just the file name
    safe_name = os.path.basename(safe_name)
    #extract string components and convert to datetime objects
    sat_ab   = safe_name[2]
    sat_mode = safe_name[4:10]
    date1    = datetime.datetime.strptime(safe_name[17:32],'%Y%m%dT%H%M%S')
    date2    = datetime.datetime.strptime(safe_name[33:48],'%Y%m%dT%H%M%S')
    orbit_num= int(safe_name[49:55])
    return [sat_ab, sat_mode, date1, date2, orbit_num]


def get_datestring_from_xml(xml_name):
    """
    xml file has name like s1a-iw1-slc-vv-20150121t134413-20150121t134424-004270-005317-001.xml
    We want to return 20150121. 
    """
    #make sure we have just the file basename
    xml_name = os.path.basename(xml_name)
    #parse string by fixed format
    mydate=xml_name[15:23]
    return mydate


def get_date_range_from_xml(xml_name):
    """
    xml file has name like s1a-iw1-slc-vv-20150121t134413-20150121t134424-004270-005317-001.xml
    Function returns a list of 2 datetime objects matching the strings ['20150121T134413','20150121T134424']
    """
    #make sure we have just the file basename
    xml_name = os.path.basename(xml_name)
    #parse string by fixed format
    date1=datetime.datetime.strptime(xml_name[15:30],'%Y%m%dt%H%M%S')
    date2=datetime.datetime.strptime(xml_name[31:46],'%Y%m%dt%H%M%S')
    return [date1,date2]


def get_dates_from_eof(eof_name):
    """
    EOF file has name like S1A_OPER_AUX_POEORB_OPOD_20170917T121538_V20170827T225942_20170829T005942.EOF
    Function returns a list of 3 datetime objects matching the strings ['20170917T121538','20170827T225942','20170829T005942']
    """
    #make sure we have just the file basename
    eof_name = os.path.basename(eof_name)
    #parse string by fixed format
    date1=datetime.datetime.strptime(eof_name[25:40],'%Y%m%dT%H%M%S')
    date2=datetime.datetime.strptime(eof_name[42:57],'%Y%m%dT%H%M%S')
    date3=datetime.datetime.strptime(eof_name[58:73],'%Y%m%dT%H%M%S')
    return [date1,date2,date3]


def get_s1_image_and_orbit(xml_name,s1_orbit_dirs):
    #parse string by fixed format
    sat_ab=xml_name[2].upper()
    [imagestart,imageend]=get_date_range_from_xml(xml_name)
    eof_name = get_latest_orbit_file(sat_ab,imagestart,imageend,s1_orbit_dirs,skip_notfound=False);
    eof_basename = os.path.basename(eof_name)
    image_name = xml_name[:-4]+":"+eof_basename
    return image_name,eof_name


def write_ll_pins(fname, lons, lats, asc_desc):
    """
    Put lat/lon pairs in time order and write to a file.
    Lower latitude value comes first for 'A', while for 'D' higher lat. is first
    """
    if (asc_desc == 'D' and lats[0] < lats[1]) or (asc_desc == 'A' and lats[0] > lats[1]):
        lats.reverse()
        lons.reverse()
    lonlats=['%f %f'%(i,j) for i,j in zip(lons,lats)]
    gmtsar_func.write_list(fname,lonlats)


def create_frame_tops(safelist,eof,llpins,logfile):
    """
    Run the GMTSAR command create_frame_tops.csh to combine bursts within the given latitude bounds
    """
    # copy orbit file to the current directory, required for create_frame_tops.csh
    print(eof)
    shutil.copy2(eof,os.getcwd())
    local_eof=os.path.basename(eof)

    cmd = '/home/share/insarscripts/automate/gmtsar_functions/create_frame_tops.csh %s %s %s 1 %s'%(safelist, local_eof, llpins, logfile)
    #cmd = '~/Dropbox/code/geodesy/insarscripts/automate/gmtsar_functions/create_frame_tops.csh %s %s %s 1 %s'%(safelist, local_eof, llpins, logfile)
    gmtsar_func.run_command(cmd,logging=True)

