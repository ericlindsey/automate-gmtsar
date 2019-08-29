#!/bin/bash

sat=ALOS2
echo ""
echo "note, assuming SAT=$sat"
echo ""

# run all scripts to create a tar file containing all products needed for use with GIANT
~/Dropbox/code/geodesy/insarscripts/automate/intf_pad.sh unwrap_mask_ll.grd
~/Dropbox/code/geodesy/insarscripts/automate/intf_pad.sh corr_ll.grd
intfdir=`ls intf/ |head -1`
cd intf/$intfdir
prm=`ls *PRM |head -1`
~/Dropbox/code/geodesy/insarscripts/automate/make_los_products.csh unwrap_mask_ll_pad.grd $prm $sat
mv look_?.grd ../../
gmt grdmath look_u.grd ACOS R2D = look_theta.grd
cd ../../
tar -cvzf intf_products.tar.gz intf/*/corr_ll_pad.grd intf/*/unwrap_mask_ll_pad.grd intf/*/phasefilt_mask_ll.* intf/*/unwrap_mask_ll.[k,p]*  topo/master.PRM topo/dem.grd look_*.grd raw/baseline_table.dat intf.in

echo created intf_products.tar.gz

