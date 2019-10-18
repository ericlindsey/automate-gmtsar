#!/bin/bash

sat=S1
echo ""
echo "note, assuming SAT=$sat"
echo ""

cshdir=/home/share/insarscripts/automate/

# run all scripts to create a tar file containing all products needed for use with GIANT
$cshdir/intf_pad.sh unwrap_mask_ll.grd
unw=`ls intf/*/unwrap_mask_ll_pad.grd |head -n1`

# we have only one correlation file. Don't pad it many times.
#$cshdir/intf_pad.sh corr_ll.grd -R$unw


intfdir=`ls intf/ |head -1`
cd intf/$intfdir

# pad a single correlation file once, here.
gmt grd2xyz corr_ll.grd -bo | gmt xyz2grd -bi -Runwrap_mask_ll_pad.grd -r -Gtemp.grd
nccopy -k classic temp.grd ../../corr_ll_pad.grd
rm temp.grd


prm=`ls *PRM |head -1`
$cshdir/make_los_products.csh unwrap_mask_ll_pad.grd $prm $sat
mv look_?.grd ../../
cd ../../

gmt grdmath look_u.grd ACOS R2D = look_theta.grd
#tar -cvzf intf_products.tar.gz corr_ll_pad.grd intf/*/unwrap_mask_ll_pad.grd intf/*/phasefilt_mask_ll.* intf/*/unwrap_mask_ll.[k,p]*  topo/master.PRM topo/dem.grd look_*.grd raw/baseline_table.dat intf.in
tar -cvzf intf_products.tar.gz corr_ll_pad.grd intf/*/unwrap_mask_ll_pad.grd topo/master.PRM look_*.grd raw/baseline_table.dat intf.in

echo created intf_products.tar.gz

