#!/bin/csh -f
#       $Id$
#
#  Xiaopeng Tong, Mar 2 2010
#  modified by D. Sandwell MAR 11 2010
#  modified by E. Lindsey, R. Salman, S.B. Utami SEP 2016 to include ALOS2
#  modified by E. Lindsey, March 2017 to simplify filename handling of ALOS and ALOS2
#
#  preprocess all the data based on data.in table file and generate:
#  1. raw files
#  2. PRM files
#  3. time-baseline plot for user to create stacking pairs

#  format in data.in table file:
#       line 1: master_name
#       line 2 and below: slave_name

alias rm 'rm -f'
unset noclobber

#
# check the number of arguments
#
  if ($#argv != 3) then 
    echo ""
    echo "Usage: pre_proc_batch.csh SAT data.in batch.config"
    echo "       preprocess a set of images using a common rear_range and radius"
    echo ""
    echo " SAT can be ALOS, ALOS2, TSX, ERS or ENVI (currently not S1 - use preproc_batch_tops.csh instead)"
    echo ""
    echo "       format of data.in is:"
    echo "         line 1: master_name "
    echo "         line 2 and below: slave_name"
    echo ""
    echo "       example of data.in for ALOS is:"
    echo "         IMG-HH-ALPSRP096010650-H1.0__A"
    echo "         IMG-HH-ALPSRP089300650-H1.0__A"
    echo "         IMG-HH-ALPSRP236920650-H1.0__A"
    echo ""
    echo "       example of data.in for ALOS2 (stripmap) is:"
    echo "         IMG-HH-ALOS2026257050-141117-FBDR1.1__A"
    echo "         IMG-HH-ALOS2036607050-150126-FBDR1.1__A"
    echo "         IMG-HH-ALOS2059377050-150629-FBDR1.1__A"
    echo ""
    echo "       example of data.in for ALOS2 (ScanSAR) is:"
    echo "         IMG-HH-ALOS2041113750-150226-WBDR1.1__D-F1"
    echo "         IMG-HH-ALOS2047323750-150409-WBDR1.1__D-F1"
    echo "         IMG-HH-ALOS2063883750-150730-WBDR1.1__D-F1"
    echo ""
    echo "       example of data.in for TSX is:"
    echo "         TSX20100809"
    echo "         TSX20100914"
    echo "         TSX20101122"
    echo ""
    echo "       example of data.in for ERS is:"
    echo "         e1_05783"
    echo "         e1_07787"
    echo "         e1_10292"
    echo ""
    echo "       example of data.in for ENVISAT is:"
    echo "         ENV1_2_127_2925_07195"
    echo "         ENV1_2_127_2925_12706"
    echo "         ENV1_2_127_2925_13207"
    echo ""
    echo "Example: pre_proc_batch.csh ENVI data.in batch.config"
    echo ""
    exit 1
  endif
  
  
  set SAT = $1
  if ($SAT != ALOS && $SAT != ALOS2 && $SAT != TSX && $SAT != ENVI && $SAT != ERS) then
    echo ""
    echo " SAT can be ALOS, ALOS2, TSX, ERS or ENVI"
    echo ""
    exit 1
  endif
  
  echo ""
  echo "START PREPROCESS A STACK OF IMAGES"
  echo ""
#
# read parameters from configuration file
#
  set num_patches = `grep num_patches $3 | awk '{print $3}'`
  set near_range = `grep near_range $3 | awk '{print $3}'`
  set earth_radius = `grep earth_radius $3 | awk '{print $3}'`
  set fd = `grep fd1 $3 | awk '{print $3}'`
  set SLC_factor = `grep SLC_factor $3 | awk '{print $3}'`

  set commandline = ""
  if ($SAT == ERS || $SAT == ENVI) then
    if (!($near_range == "")) then
      set commandline = "$commandline $near_range"
    else
      set commandline = "$commandline 0"
    endif
    if (!($earth_radius == "")) then
      set commandline = "$commandline $earth_radius"
    else
      set commandline = "$commandline 0"
    endif
    if (!($num_patches == "")) then
      set commandline = "$commandline $num_patches"
    else
      set commandline = "$commandline 0"
    endif
    if (!($fd == "")) then
      set commandline = "$commandline $fd"
    else
      set commandline = "$commandline"
    endif

  else if ($SAT == ALOS) then
    if (!($earth_radius == "")) then
      set commandline = "$commandline -radius $earth_radius"
    endif
    if (!($near_range == "")) then
      set commandline = "$commandline -near $near_range"
    endif
    if (!($num_patches == "")) then
      set commandline = "$commandline -npatch $num_patches"
    endif
    if (!($fd == "")) then
      set commandline = "$commandline -fd1 $fd"
    endif

  else if ($SAT == ALOS2) then
    if (!($earth_radius == "")) then
      set commandline = "$commandline -radius $earth_radius"
    endif
    if (!($num_patches == "")) then
      set commandline = "$commandline -npatch $num_patches"
    endif
    if (!($SLC_factor == "")) then
      set commandline = "$commandline -SLC_factor $SLC_factor"
    else
      set commandline = "$commandline -SLC_factor 1.0"
    endif
    
  else if ($SAT == TSX) then
    if ((! $?earth_radius) || ($earth_radius == "")) then
      set earth_radius = 0
    endif
    set commandline = "$commandline $earth_radius 0"

  endif


  echo "preprocess options: "$commandline

#
# open and read data.in table
#

  set line1 = `awk 'NR==1 {print $0}' $2`
  set master = $line1[1]
  echo "preprocess master image: "$master
    
  # ALOS and ALOS2 have a non-standard convention for the image and LED filenames.
  if ($SAT == ALOS) then
    set ledstem = `echo $master | awk '{ print substr($1,8,length($1)-7)}'`
  else if ($SAT == ALOS2 ) then
    set ledstem = `echo $master | awk '{ print substr($1,8,32)}'`
  endif
#
# unpack the master if necessary
#
  if ($SAT == TSX) then
    #
    #TSX preprocessing is just a PRM update. We must start with the SLCs already made - use make_tsx_slc
    #
    #save clean copy of PRM file and use if the script is run again
    if(-e $master.PRM00) then
      cp $master.PRM00 $master.PRM
    else
      cp $master.PRM $master.PRM00
    endif
    #
    #get the min number of lines for all scenes
    #
    set min_lines = `grep num_lines *.PRM | awk '{if(min==""){min=$3}; if($3<min) {min=$3}} END {print min}'`
    echo "set num_lines to "$min_lines
    update_PRM $master.PRM num_lines $min_lines
    update_PRM $master.PRM num_valid_az $min_lines
    update_PRM $master.PRM nrows $min_lines
    #
    #calculate the SC_vel and SC_height
    #set the doppler to be zero
    #
    echo "calculate SC_vel and SC_height, and set doppler to be zero"
    cp $master.PRM $master.PRM0
    calc_dop_orb $master.PRM0 $master.log $commandline
    cat $master.PRM0 $master.log > $master.PRM
    echo "fdd1                    = 0" >> $master.PRM
    echo "fddd1                   = 0" >> $master.PRM

  else if (! -f $master.PRM) then
  
    if ($SAT == ALOS2) then
      ALOS_pre_process_SLC $master LED-$ledstem $commandline

    else if ($SAT == ALOS) then
      ALOS_pre_process $master LED-$ledstem $commandline

    else
      $1_pre_process $master $commandline

    endif 

  endif

  set NEAR = `grep near_range $master.PRM | awk '{print $3}'`
  set RAD = `grep earth_radius $master.PRM | awk '{print $3}'`
  set FD1 = `grep fd1 $master.PRM | awk '{print $3}'`
  set npatch = `grep num_patch $master.PRM | awk '{print $3}'`

  # Note: a custom version of this command is being used. 
  # You must set the variable 'GMTSAR_APP' to the location of the 'automate-gmtsar' folder.
  $GMTSAR_APP/gmtsar_functions/baseline_table.csh $master.PRM $master.PRM >! baseline_table.dat
  $GMTSAR_APP/gmtsar_functions/baseline_table.csh $master.PRM $master.PRM GMT >! table.gmt

#
# loop and unpack the slave image using the same earth radius and near range as the master image
#
  foreach slave (`awk 'NR>1 {print $0}' $2`)
    echo "pre_proc_batch.csh"
    echo "preprocess slave image: "$slave
    
    if ($SAT == TSX) then  
      #TSX preprocessing is just a PRM update. We must start with the SLCs already made - use make_tsx_slc
      #
      #save clean copy of PRM file and use if the script is run again
      if(-e $slave.PRM00) then
        cp $slave.PRM00 $slave.PRM
      else
        cp $slave.PRM $slave.PRM00
      endif
      echo "set num_lines to "$min_lines
      update_PRM $slave.PRM num_lines $min_lines
      update_PRM $slave.PRM num_valid_az $min_lines
      update_PRM $slave.PRM nrows $min_lines
      #calculate the SC_vel and SC_height
      #set the doppler to be zero
      echo "calculate SC_vel and SC_height, and set doppler to be zero"
      cp $slave.PRM $slave.PRM0
      calc_dop_orb $slave.PRM0 $slave.log $commandline
      cat $slave.PRM0 $slave.log > $slave.PRM
      echo "fdd1                    = 0" >> $slave.PRM
      echo "fddd1                   = 0" >> $slave.PRM
      echo "delete extra files"
      rm *.log
      rm *.PRM0

    else if(! -f $slave.PRM) then
    
      if ($SAT == ALOS2) then
        set ledstem = `echo $slave | awk '{ print substr($1,8,32)}'`
        ALOS_pre_process_SLC $slave LED-$ledstem $commandline
        #
        # check the range sampling rate of the slave images and do conversion if necessary
        #
        set rng_samp_rate_m = `grep rng_samp_rate $master.PRM | awk 'NR == 1 {printf("%d", $3)}'`
        set rng_samp_rate_s = `grep rng_samp_rate $slave.PRM | awk 'NR == 1 {printf("%d", $3)}'`
        set t = `echo $rng_samp_rate_m $rng_samp_rate_s | awk '{printf("%1.1f\n", $1/$2)}'`
        if ($t == 1.0) then
         echo "The range sampling rate for master and slave images are: "$rng_samp_rate_m
        else if ($t == 2.0) then
          echo "Convert the slave image from FBD to FBS mode"
          ALOS_fbd2fbs_SLC $slave.PRM $slave"_"FBS.PRM
          echo "Overwriting the old slave image"
          mv $slave"_"FBS.PRM $slave.PRM
          update_PRM $slave.PRM input_file $slave.SLC
          mv $slave"_"FBS.SLC $slave.SLC
        else if  ($t == 0.5) then
          echo "Convert the master image from FBD to FBS mode"
          ALOS_fbd2fbs_SLC $master.PRM $master"_"FBS.PRM
          echo "Overwriting the old master image"
          mv $master"_"FBS.PRM $master.PRM
          update_PRM $master.PRM input_file $master.SLC
          mv $master"_"FBS.SLC $master.SLC
        else
          echo "The range sampling rate for master and slave images are not convertible"
          exit 1
        endif
        cp $slave.PRM $slave.PRM0	
        ALOS_baseline $master.PRM $slave.PRM0 >> $slave.PRM

      else if ($SAT == ALOS) then  # end of if ($SAT == ALOS2)
        set ledstem = `echo $slave | awk '{ print substr($1,8,length($1)-7)}'`
        ALOS_pre_process $slave LED-$ledstem -fd1 $FD1 -near $NEAR -radius $RAD -npatch $npatch
        #
        # check the range sampling rate of the slave images and do conversion if necessary
        #
        set rng_samp_rate_m = `grep rng_samp_rate $master.PRM | awk 'NR == 1 {printf("%d", $3)}'`
        set rng_samp_rate_s = `grep rng_samp_rate $slave.PRM | awk 'NR == 1 {printf("%d", $3)}'`
        set t = `echo $rng_samp_rate_m $rng_samp_rate_s | awk '{printf("%1.1f\n", $1/$2)}'`
        if ($t == 1.0) then
          echo "The range sampling rate for master and slave images are: "$rng_samp_rate_m
        else if ($t == 2.0) then
          echo "Convert the slave image from FBD to FBS mode"
          ALOS_fbd2fbs $slave.PRM $slave"_"FBS.PRM
          echo "Overwriting the old slave image"
          mv $slave"_"FBS.PRM $slave.PRM
          update_PRM $slave.PRM input_file $slave.raw
          mv $slave"_"FBS.raw $slave.raw
        else if  ($t == 0.5) then
          echo "Error: Must use FBS mode image as master"
          exit 1
        else
          echo "Error: The range sampling rate for master and slave images are not convertible"
          exit 1
        endif
      else   # generic processing for other satellites

        $1_pre_process $slave $NEAR $RAD $npatch $FD1

      endif 

    endif

    #get baselines
    # Note: a custom version of this command is being used. 
    # You must set the variable 'GMTSAR_APP' to the location of the 'automate-gmtsar' folder.
    $GMTSAR_APP/gmtsar_functions/baseline_table.csh $master.PRM $slave.PRM >> baseline_table.dat
    $GMTSAR_APP/gmtsar_functions/baseline_table.csh $master.PRM $slave.PRM GMT >> table.gmt

  # end of the loop over slave images
  end

#
# make baseline plots
#

  if ($SAT == ERS || $SAT == ENVI) then
    awk '{print 1992+$1/365.25,$2,$7}' < table.gmt > text
#    awk '{print 1992+$1/365.25,$2,7,$4,$5,$6,$7}' < table.gmt > text
#    awk '{print 1992+$1/365.25,$2,7,-45,$5,$6,$7}' < table.gmt > text
  else if ($SAT == ALOS) then
    awk '{print 2006.5+($1-181)/365.25,$2,$7}' < table.gmt > text
#    awk '{print 2006.5+($1-181)/365.25,$2,9,$4,$5,$6,$7}' < table.gmt > text
  else if ($SAT == TSX) then
    awk '{print 2007+$1/365.25,$2,$7}' < table.gmt > text
  else if ($SAT == ALOS2) then
    awk '{print 2014.5+($1-181)/365.25,$2,$7}' < table.gmt > text
#    awk '{print 2014+($1-181)/365.25,$2,9,$4,$5,$6,$7}' < table.gmt > text
  endif
  set region = `gmt gmtinfo text -C | awk '{print $1-0.5, $2+0.5, $3-500, $4+500}'`
# set region = `minmax text -C | awk '{print $1-0.5, $2+0.5, -1200, 1200}'`
  gmt pstext text -JX8.8i/6.8i -R$region[1]/$region[2]/$region[3]/$region[4] -D0.2/0.2 -X1.5i -Y1i -K -N -F+f8,Helvetica+j5 > stacktable_all.ps
  awk '{print $1,$2}' < text > text2
  gmt psxy text2 -Sp0.2c -G0 -R -JX -Ba1:"year":/a200g00f100:"baseline (m)":WSen -O >> stacktable_all.ps


  echo ""
  echo "END PREPROCESS A STACK OF IMAGES"
  echo ""

#
# clean up the mess
#
  rm text text2

