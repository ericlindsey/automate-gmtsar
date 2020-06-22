#!/bin/csh -f
#
# geocode output of the sbas program at specified resolution (vel.grd and disp_YYYYDDD.grd files)
#
# original version created by Eric Lindsey, June 2020

unset noclobber
 
if ( $#argv != 1 ) then 
  echo ""
  echo "USAGE: geocode_sbas.csh resolution"
  echo ""
  echo " Run from inside the SBAS/ directory."
  echo ""
  echo " input: "
  echo "  resolution          --  final output resolution in meters"
  echo ""
  echo " output: "
  echo "  disp_##_ll.grd      --  geocoded cumulative displacement time series (mm) grids"
  echo "  vel_ll.grd          --  geocoded mean velocity (mm/yr) grids "
  echo ""
  echo " example:"
  echo "  geocode_sbas.csh 30"
  exit 1
endif

echo ""
echo "START RUN_SBAS.CSH"
echo ""

#
# create a 'fake' gauss_X file to trick proj_ra2ll.csh into providing the correct resolution.
#
set filtres = `echo $1 |awk '{print $1*4}'`
rm -f gauss_*
touch gauss_$filtres

#
# geocode the output
#
ln -s ../topo/trans.dat .
foreach file (`ls vel.grd disp_???????.grd`)
  echo "geocode $file"
  set file_ll = `basename $file .grd`_ll.grd
  proj_ra2ll.csh trans.dat $file $file_ll
end

