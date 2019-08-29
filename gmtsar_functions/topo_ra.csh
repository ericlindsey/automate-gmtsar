#!/bin/csh -f
#
# run the topo_ra stage by itself (normally done as part of intf_batch.csh).
# This makes it easier to run all interferograms in parallel.
#
# original version modified from p2p for ALOS-2 by Rino Salman, Dec. 2016
# generic (satellite-independent) version created by Eric Lindsey, Feb. 2017

alias rm 'rm -f'
unset noclobber
# 
  if ($#argv != 1) then 
    echo ""
    echo "Usage: topo_ra.csh batch.config"
    echo ""
    echo " Works for all satellites (ALOS,ALOS2,ENVI,ERS,S1,TSX)"
    echo " Run this from the top directory containing your topo/ and SLC/ folders."
    echo " Master scene must be specified in batch.config via master_image = <master>"
    echo " The script uses parameters found in batch.config as well as in SLC/$master.PRM"
    echo ""
    echo " Example of master for ALOS:"
    echo "    IMG-HH-ALPSRP096010650-H1.0__A"
    echo ""
    echo " Example of master for ALOS2 (SM1, SM2, or SM3 mode):"
    echo "    IMG-HH-ALOS2055603740-150604-FBDR1.1__D"
    echo ""
    echo " Example of master for ALOS2 (WD1 mode):"
    echo "    IMG-HH-ALOS2101143750-160407-WBDR1.1__D-F3"
    echo ""
    echo " Example of master for TSX is:"
    echo "    TSX20100809"
    echo ""
    echo " Example of master for S1 (TOPS mode) is:"
    echo "    S1A20161205_ALL_F2"
    echo ""
    echo " Example of master for ERS is:"
    echo "    e1_05783"
    echo ""
    echo " Example of master for ENVISAT is:"
    echo "    ENV1_2_127_2925_07195"
    echo ""
    exit 1
  endif
  
  echo ""
  echo "START TOPO_RA.CSH"
  echo ""
  
#
# read parameters from configuration file
#
  set master = `grep master_image $1 | awk '{print $3}'`
  set topo_phase = `grep topo_phase $1 | awk '{print $3}'`
  set shift_topo = `grep shift_topo $1 | awk '{print $3}'`
  set switch_land = `grep switch_land $1 | awk '{print $3}'`
  set region_cut = `grep region_cut $1 | awk '{print $3}'`
#
# look for range sampling rate
#
  set SC = `grep SC_identity SLC/$master.PRM | awk '{print $3}'`
  set rng_samp_rate = `grep rng_samp_rate SLC/$master.PRM | awk 'NR == 1 {printf("%d", $3)}'`

  if ( $SC == 10 && $shift_topo == 1 ) then
    echo "Sentinel-1: cannot use shift_topo"
    set shift_topo = 0
  endif

# set the range decimation in units of image range pixel size

  if($rng_samp_rate > 0 && $rng_samp_rate < 25000000) then
    set rng = 1
  else if($rng_samp_rate >= 25000000 && $rng_samp_rate < 72000000 || $SC == 7 ) then
    set rng = 2
  else if($rng_samp_rate >= 72000000) then
    set rng = 4
  else
     echo "range sampling rate out of bounds"
     exit 1
  endif
  echo " topo_ra.csh: range decimation is: " $rng
#
# clean up
#
  cleanup.csh topo
#
# make topo_ra if there is dem.grd
#
  if ($topo_phase == 1) then 
    echo " "
    echo "DEM2TOPO_RA.CSH - START"
    echo "USER SHOULD PROVIDE DEM FILE"
    cd topo
    cp ../SLC/$master.PRM master.PRM
    set led_file = `grep led_file master.PRM | awk '{print $3}'`
    ln -s ../raw/$led_file .
    ln -s ../SLC/amp-$master.grd . 
    if (-f dem.grd) then 
      dem2topo_ra.csh master.PRM dem.grd 
    else 
      echo "no DEM file found: " dem.grd 
      exit 1
    endif
    cd .. 
    echo "DEM2TOPO_RA.CSH - END"
# 
# shift topo_ra
# 
    if ($shift_topo == 1) then 
      echo " "
      echo "OFFSET_TOPO - START"
      cd SLC
      slc2amp.csh $master.PRM $rng amp-$master.grd
      cd ..
      cd topo
      offset_topo amp-$master.grd topo_ra.grd 0 0 7 topo_shift.grd 
      cd ..
      echo "OFFSET_TOPO - END"
    else if ($shift_topo == 0) then 
      echo "shift_topo = 0: NO TOPO_RA SHIFT"
    else 
      echo "Wrong parameter: shift_topo = "$shift_topo
      exit 1
    endif
  else if ($topo_phase == 0) then 
    echo "topo_phase = 0: NO TOPO_RA IS SUBTRACTED"
  else 
    echo "Wrong parameter: topo_phase = "$topo_phase
    exit 1
  endif
  
  if ($switch_land == 1) then
    echo " "
    echo "LANDMASK - START"
    cd topo
    if ($region_cut == "") then
      set region_cut = `gmt grdinfo amp-$master.grd -I- | cut -c3-20`
    endif
    landmask.csh $region_cut
    cd ..
    echo "LANDMASK - END"
  endif
  
  echo ""
  echo "END TOPO_RA.CSH"
  echo ""
