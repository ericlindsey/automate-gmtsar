#!/bin/csh -f 
#       $Id$

# Align a stack of SLC images
# can be used to do stacking and time-series analysis

# Xiaopeng Tong, Aug 27 2010
# Modified for simplified file names and ALOS2 capability, E. Lindsey, March 2017
# Modified for TSX, E. Lindsey, August 2017
#
  if ($#argv < 2) then
    echo ""
    echo "Usage: align_batch.csh SAT align.in [parallel] [scan]"
    echo "  align a set of images listed in align.in file"
    echo ""
    echo " SAT can be ALOS, ALOS2, TSX, ENVI, or ERS"
    echo " For S1, use preproc_batch_tops.csh with mode 2"
    echo ""
    echo "  format of align.in:"
    echo "    master_name:slave_name:supermaster_name"
    echo ""
    echo "  example of align.in for ALOS is:"
    echo "   IMG-HH-ALPSRP096010650-H1.0__A:IMG-HH-ALPSRP089300650-H1.0__A:IMG-HH-ALPSRP096010650-H1.0__A"
    echo "   IMG-HH-ALPSRP096010650-H1.0__A:IMG-HH-ALPSRP236920650-H1.0__A:IMG-HH-ALPSRP096010650-H1.0__A" 
    echo "  "
    echo "  example of align.in for ERS is:"
    echo "  e1_05783:e1_07787:e1_05783"
    echo "  e1_05783:e1_10292:e1_05783"
    echo ""
    echo "  example of align.in for ENVISAT is:"
    echo "  ENV1_2_127_2925_07195:ENV1_2_127_2925_12706:ENV1_2_127_2925_07195"
    echo "  ENV1_2_127_2925_07195:ENV1_2_127_2925_13207:ENV1_2_127_2925_07195"
    echo ""
    echo "Example: align_batch.csh ALOS align.in "
    echo ""
    echo "For ALOS2, if mode is ScanSAR, specify extra option 'scan'"
    echo ""
    echo "When running in parallel, specify extra option 'parallel' to prevent deleting SLC files"
    echo ""
    exit 1
  endif
    
  set SAT = $1
  if ($SAT != ENVI && $SAT != ERS && $SAT != TSX && $SAT != ALOS && $SAT != ALOS2) then
    echo ""
    echo " SAT can be ALOS, ALOS2, TSX, ENVI, or ERS "
    echo ""
    exit 1
  endif
  
#
# check for scansar mode
#
  if ( $SAT == ALOS2 && ($3 == scan || $4 == scan) ) then
    set mode = scan
  else
    set mode = ""
  endif
#
# make working directories
#
  mkdir -p SLC/
# 
# clean up , unless this is a 'parallel' job
#
  if ($3 != parallel && $4 != parallel) then
    echo ""
    echo "START ALIGN_BATCH.CSH"
    echo ""
    cleanup.csh SLC
  else
    echo ""
    echo "START PARALLEL ALIGN_BATCH.CSH - skip cleanup"
    echo ""
  endif

#
# loop start focus and align SLC images 
# 
  foreach line (`awk '{print $0}' $2`)
    set master = `echo $line | awk -F: '{print $1}'`
    set slave = `echo $line | awk -F: '{print $2}'`
    set supermaster = `echo $line | awk -F: '{print $3}'`
    if ($master != "" && $slave != "" && $supermaster != "") then
      echo "Align $slave to $master via $supermaster - START"
      echo ""
      #
      #  create an alignment subdirectory inside SLC and create links
      #
      set align_dir = SLC/align_$slave
      mkdir -p $align_dir
      cd $align_dir
      if (-f ../../raw/$master.raw && -f ../../raw/$slave.raw) then
        # we have raw-type data
        if (-f ../$master.SLC) then
          ln -s ../$master.SLC .
          cp ../$master.PRM .
        else
          #master was not yet focused - it will be done in align.csh below.
          cp ../../raw/$master.PRM .
          ln -s ../../raw/$master.raw .
        endif 
        ln -s ../../raw/$slave.raw . 
	  else if (-f ../../raw/$master.SLC && -f ../../raw/$slave.SLC) then
	    # we have SLC-only data
	    if (! -f ../$master.SLC) then
          cp ../../raw/$master.SLC ../
          cp ../../raw/$master.PRM ../
        endif
	    cp ../$master.PRM . 
	    ln -s ../$master.SLC . 
        ln -s ../../raw/$slave.SLC .
      endif
      cp ../../raw/$slave.PRM .
      cp ../../raw/$supermaster.PRM .
      set masterled = `grep led_file $master.PRM | awk '{print $3}'`
      set slaveled = `grep led_file $slave.PRM | awk '{print $3}'`
      ln -s ../../raw/$masterled . 
      ln -s ../../raw/$slaveled .
      #
      #  need to add the SLC_file name to the master PRM's
      #
      update_PRM.csh $master.PRM SLC_file $master.SLC
      update_PRM.csh $supermaster.PRM SLC_file $supermaster.SLC
      #
      #  now run align.csh
      #
     #align.csh $SAT $master $slave $supermaster $mode
     
# hard-coded paths during testing
#/Users/elindsey/Dropbox/code/geodesy/insarscripts/automate/gmtsar_functions/align.csh $SAT $master $slave $supermaster $mode
#/home/elindsey/insarscripts/automate/gmtsar_functions/align.csh $SAT $master $slave $supermaster $mode
/home/share/insarscripts/automate/gmtsar_functions/align.csh $SAT $master $slave $supermaster $mode
#/Volumes/dione/data/test_GMTSAR/align.csh $SAT $master $slave $supermaster $mode

      if (! -f ../$master.SLC) then
        #master was focused for the first time
        mv $master.SLC ../
        cp $master.PRM ../
      endif
      mv $slave.SLC ../
      cp $slave.PRM ../
      cd ../..
      echo ""
      echo "Align $slave to $master via $supermaster - END"
    else 
      echo ""
      echo "Wrong format in align.in"
      echo ""
      exit 1
    endif
  end

  echo ""
  echo "END ALIGN_BATCH.CSH"
  echo ""

