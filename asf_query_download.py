#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Use ASF API to search and download granules given search parameters found in a config file.

Created on Fri Oct 13 11:10:47 2017

@author: elindsey
"""

import configparser,argparse,requests,csv,subprocess,time,os,errno,glob

# implement shell 'mkdir -p' to create directory trees with one command, and ignore 'directory exists' error
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

if __name__ == '__main__':
    
 
    # read command line arguments and parse config file.
    parser = argparse.ArgumentParser(description='Use http requests and wget to search and download data from the ASF archive, based on parameters in a config file.')
    parser.add_argument('config',type=str,help='supply name of config file to setup processing options. Required.')
    parser.add_argument('--download',action='store_true',help='Download the resulting scenes (default: false)')
    args = parser.parse_args()

    # read config file
    config=configparser.ConfigParser()
    config.optionxform = str #make the config file case-sensitive
    config.read(args.config)
    # use the stem of the config file in the output log filename
    config_base = os.path.splitext(args.config)[0]
    
    #parse the config options directly into a query... this may be naive
    
    # get options from config file
    arg_list=config.items('api_search')
    #join as a single argument string
    arg_str='&'.join('%s=%s'%(item[0],item[1]) for item in arg_list)
    #add extra option for csv format.
    arg_str=arg_str+'&output=csv'
    
    #should contain username, password, and any other needed wget options
    wget_options=config.items('download')
    #join as a single argument string
    wget_str=' '.join('--%s=%s'%(item[0],item[1]) for item in wget_options)
        
    #form them into a query
    baseurl='https://api.daac.asf.alaska.edu/services/search/param?'
    argurl=baseurl + arg_str
    
    print('\nRunning ASF API query:')
    print(argurl + '\n')

    #run the request
    r=requests.post(argurl)
    
    #log the results
    logtime=time.strftime("%Y_%m_%d-%H_%M_%S")
    query_log='%s_%s.csv'%(config_base,logtime)
    with open(query_log,'w')as f:
        print('Query result saved to %s'%query_log)
        f.write(r.text)
        
    # parse result into a list of granules, figure out the correct path,
    # and download each one.
    # wget -c option will cause existing files to be automatically skipped
    # (but this causes some overhead; better to tune the query to avoid these files)
    reader = csv.DictReader(r.text.splitlines())
    rows=list(reader)
    numscenes=len(rows)
    if numscenes > 0:
        print("Found %s scenes." %numscenes)
        for row in rows:
            print('Scene %s, Path %s / Frame %s' %(row['Granule Name'], row['Path Number'], row['Frame Number']))
        if args.download:
            orig_dir=os.getcwd()
            for row in rows:
                path_dir='P' + row['Path Number']
                # check if any filename matching the granule exists
                if len(glob.glob('%s/%s.*'%(path_dir,row['Granule Name']))) > 0:
                    print('File exists, skipping')
                else:
                    print('Downloading granule ', row['Granule Name'], 'to directory', path_dir)
                    #run wget command
                    mkdir_p(path_dir)
                    os.chdir(path_dir)
                    cmd='wget -c -q --no-check-certificate ' + wget_str + ' ' + row['URL']
                    print(cmd)
                    status=subprocess.call(cmd, shell=True)
                    os.chdir(orig_dir)
    else:
        print("No scenes found.")

