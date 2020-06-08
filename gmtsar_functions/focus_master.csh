#!/bin/csh -f 
#       $Id$

# Focus the master image, and/or copy it to the SLC directory
# To be used prior to align_batch.csh when run in parallel.

#
# check the number of arguments 
# 
  if ($#argv != 1) then 
    echo ""
    echo "Usage: focus_master.csh master"
    echo ""    
    echo ""
    echo "Example: focus_master.csh IMG-HH-ALPSRP055750660-H1.0__A"
    echo ""
    exit 1
  endif


  mkdir -p SLC
  cleanup.csh SLC
  cd SLC
  
  set master = $1
  cp ../raw/$master.PRM .
  set ledfile = `grep led_file $master.PRM | awk '{print $3}'`
  ln -s ../raw/$ledfile .
  
  if (-f ../raw/$master.raw) then
    # we have raw-type data
    ln -s ../raw/$master.raw .
    sarp.csh $master.PRM >& focus_$master.log
  else if (-f ../raw/$master.SLC) then
    cp ../raw/$master.SLC . 
  endif
  
  update_PRM $master.PRM SLC_file $master.SLC
  cd ..

