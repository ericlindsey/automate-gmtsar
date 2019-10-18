#!/bin/bash

sat=ALOS
echo ""
echo "note, assuming SAT=$sat"
echo ""

cshdir=/home/share/insarscripts/automate/

# run all scripts to create a tar file containing all products needed for use with GIANT
$cshdir/intf_pad.sh unwrap_mask_ll.grd
unw=`ls intf/*/unwrap_mask_ll_pad.grd |head -n1`
$cshdir/intf_pad.sh corr_ll.grd -R$unw

intfdir=`ls intf/ |head -1`
cd intf/$intfdir
prm=`ls *PRM |head -1`
$cshdir/make_los_products.csh unwrap_mask_ll_pad.grd $prm $sat
mv look_?.grd ../../
cd ../../
gmt grdmath look_u.grd ACOS R2D = look_theta.grd
nccopy -k classic look_theta.grd tmp
mv tmp look_theta.grd
tar -czf intf_products.tar.gz intf/*/corr_ll_pad.grd intf/*/unwrap_mask_ll_pad.grd intf/*/phasefilt_mask_ll.* intf/*/unwrap_mask_ll.[k,p]*  topo/master.PRM topo/dem.grd look_*.grd raw/baseline_table.dat intf.in

echo created intf_products.tar.gz

