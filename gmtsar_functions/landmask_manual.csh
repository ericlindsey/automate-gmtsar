#!/bin/csh -f
#       $Id$

# make a landmask 

#
if ($#argv < 1) then
  echo ""
  echo "Usage: landmask.csh kmlfile [region_cut[0/10600/0/27648]]"
  echo ""
  echo "    make a landmask in radar coordinates "
  echo "NOTE: The region_cut can be specified in batch.config file"
  echo ""
  exit 1
endif

echo ""
echo "MAKE MANUAL MASK -- START"
echo ""

if (! -f $1 ) then
  echo "error: KML file not found"
  exit 1
endif

gmt kml2gmt $1 > topo/$1.dat


cd topo

# assumes topo_ra has been run
if ($2 == "") then
  set region_cut = `gmt grdinfo amp-*.grd -I- | cut -c3-20`
else
  set region_cut = $2
endif
if ($region_cut == "") then
  echo "error: need to run topo_ra first"
  exit 1
endif

#gmt grdlandmask -Glandmask.grd `gmt grdinfo -I- dem.grd` `gmt grdinfo -I dem.grd`  -V -NNaN/1 -Df

gmt grdmask $1.dat -Glandmask.grd `gmt grdinfo -I- dem.grd` `gmt grdinfo -I dem.grd` -V -NNaN/1/1



proj_ll2ra.csh trans.dat landmask.grd landmask_ra.grd
# if the landmask region is smaller than the region_cut pad with NaN
gmt grd2xyz landmask_ra.grd -bo > landmask_ra.xyz
gmt xyz2grd landmask_ra.xyz -bi -r -R$region_cut `gmt grdinfo -I landmask_ra.grd` -Gtmp.grd 
mv tmp.grd landmask_ra.grd
gmt grdsample landmask_ra.grd -Gtmp.grd -R$region_cut -I4/8 -nl+t0.1
mv tmp.grd landmask_ra.grd

# cleanup
rm landmask.grd landmask_ra.xyz

cd ..

echo "MAKE MANUAL MASK -- END"
#
