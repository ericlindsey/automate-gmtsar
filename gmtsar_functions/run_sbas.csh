#!/bin/csh -f
#
# generate all input tables and run the GMTSAR program sbas
#
# original version created by Eric Lindsey, June 2020

unset noclobber
 
if ( $#argv < 2 ) then 
  echo ""
  echo "USAGE: run_sbas.csh master.PRM unwrap_list.in [smooth_factor] [n_atm]"
  echo ""
  echo " required: "
  echo "  master.PRM          --  master PRM file from which to read parameters such as wavelength"
  echo "  unwrap_list.in      --  list of interferograms to include, simple listing of unwrap.grd files. eg:"
  echo "                          intf_all/2018092_2019104/unwrap.grd"
  echo "                          intf_all/2018092_2019116/unwrap.grd"
  echo "                          ...etc."
  echo " optional: "
  echo "  smooth_factor       --  smoothing factor, default=0"
  echo "  n_atm               --  number of iterations for atmospheric correction, default=0(skip atm correction)"
  echo ""
  echo " output: "
  echo "  disp_##.grd         --  cumulative displacement time series (mm) grids"
  echo "  vel.grd             --  mean velocity (mm/yr) grids "
  echo ""
  echo " example:"
  echo "  run_sbas.csh intf.in 1 5"
  exit 1
endif

echo ""
echo "START RUN_SBAS.CSH"
echo ""

#
# read parameters from configuration file
#
set wavelength = `grep radar_wavelength $1 | awk '{print $3}'`
#set near_range = `grep near_range $1 | awk '{print $3}'`
if ( $#argv > 2 ) then
  set smooth = $3
else
  set smooth = 0
endif
if ( $#argv > 3 ) then
  set n_atm = $4
else
  set n_atm = 0
endif

#
# get x and y dimensions - assume all intfs are the same
#
set firstifg = `head -n1 $2`
set xdim = `gmt grdinfo -C $firstifg | awk '{print $10}'`
set ydim = `gmt grdinfo -C $firstifg | awk '{print $11}'`

#
# TODO: compute incidence angle and center range?
#
# use sbas default values for now:
set incidence = 37
set range = 866000

#
# delete and recreate the SBAS directory
#
rm -rf SBAS
mkdir SBAS
# create an empty file to fill up
touch SBAS/scene.tab

#
# create intf.tab and scene.tab
#
# loop over unwrap files 
foreach unwrap (`awk '{print $0}' $2`)
  set dir = `dirname $unwrap`
  # create intf.tab
  # note, we add ".." to the path because we will run from inside SBAS/
  set unwrap = "../$unwrap"
  set corr = "../$dir/corr.grd"
  set day1 = `basename $dir | cut -f 1 -d _`
  set day2 = `basename $dir | cut -f 2 -d _`
  set matchline = `grep " $day1." raw/baseline_table.dat`
  set numday1 = `echo $matchline | awk '{print $3}'`
  set bperp1 = `echo $matchline | awk '{print $5}'`
  set matchline = `grep " $day2." raw/baseline_table.dat`
  set numday2 = `echo $matchline | awk '{print $3}'`
  set bperp2 = `echo $matchline | awk '{print $5}'`
  set d_bperp = `echo $bperp1 $bperp2 |awk '{print $2-$1}'`
  echo "$unwrap $corr $day1 $day2 $d_bperp" >> SBAS/intf.tab

  #create scene.tab
  # add scenes to scene.tab only if they are not already there
  set line = `grep $day1 SBAS/scene.tab`
  if ( "x$line" == "x" ) then
    echo $day1 $numday1 >> SBAS/scene.tab
  endif
  set line = `grep $day2 SBAS/scene.tab`
  if ( "x$line" == "x" ) then
    echo $day2 $numday2 >> SBAS/scene.tab
  endif
end

#
# get N (num intfs) and S (num scenes)
#
set N = `wc -l SBAS/intf.tab  |awk '{print $1}'`
set S = `wc -l SBAS/scene.tab |awk '{print $1}'`

#
# run from the SBAS directory
#
cd SBAS
set commandline = "intf.tab scene.tab $N $S $xdim $ydim -atm $n_atm -smooth $smooth -wavelength $wavelength -incidence $incidence -range $range -rms -dem"
echo "sbas $commandline"
sbas $commandline

cd ..
echo ""
echo "END RUN_SBAS.CSH"
echo ""
echo "Use geocode_sbas.csh to project the results to latitude, longitude."
echo ""

