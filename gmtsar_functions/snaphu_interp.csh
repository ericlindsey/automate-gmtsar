#!/bin/csh -f
#       $Id$
#
#
alias rm 'rm -f'
unset noclobber
#
  if ($#argv < 3) then
errormessage:
    echo ""
    echo "snaphu_interp.csh [GMT5SAR] - Unwrap the phase, after filling masked values with nearest-neighbor interpolation"
    echo " "
    echo "Usage: snaphu.csh correlation_threshold maximum_discontinuity topo_assisted_unwrapping=0/1 [<rng0>/<rngf>/<azi0>/<azif>]"
    echo ""
    echo "       pixels are masked and filled with nearest-neighbor interpolation where correlation is < threshold"
    echo "       maximum_discontinuity enables phase jumps for earthquake ruptures, etc."
    echo "       set maximum_discontinuity = 0 for continuous phase such as interseismic "
    echo "       set topo_assisted_unwrapping = 1 to unwrap twice, the second time after removing a topo-correlated component of the signal. This component is added back afterwards. "
    echo ""
    echo "Example: snaphu.csh .12 40 1 1000/3000/24000/27000"
    echo ""
    echo "Reference:"
    echo "Chen C. W. and H. A. Zebker, Network approaches to two-dimensional phase unwrapping: intractability and two new algorithms, Journal of the Optical Society of America A, vol. 17, pp. 401-414 (2000)."
    exit 1
  endif
#
# prepare the files adding the correlation mask
#
set topo_assisted_unwrapping = $3

if ($topo_assisted_unwrapping == 2) then

    echo "entering second run of snaphu_interp.csh for topo-assisted unwrapping"

else

    if ($#argv > 3 ) then
       #crop to user supplied region_cut
       gmt grdcut mask.grd -R$4 -Gmask_patch.grd
       gmt grdcut corr.grd -R$4 -Gcorr_patch.grd
       gmt grdcut phasefilt.grd -R$4 -Gphase_patch.grd
    else
       ln -s mask.grd mask_patch.grd
       ln -s corr.grd corr_patch.grd
       ln -s phasefilt.grd phase_patch.grd
    endif
    #
    # create landmask
    #
    if (-e landmask_ra.grd) then
      gmt grdsample landmask_ra.grd -Rphase_patch.grd -Glandmask_ra_patch.grd
      #if ($#argv > 3 ) then 
      #else 
      #  gmt grdsample landmask_ra.grd `gmt grdinfo -I phase_patch.grd` -Glandmask_ra_patch.grd
      #endif
      gmt grdmath phase_patch.grd landmask_ra_patch.grd MUL = phase_patch.grd -V
    endif
    #
    # user defined mask 
    #
    if (-e mask_def.grd) then
      gmt grdsample mask_def.grd -Rphase_patch.grd -Gmask_def_patch.grd
      #if ($#argv > 3 ) then
      #  gmt grdcut mask_def.grd -R$3 -Gmask_def_patch.grd
      #else
      #  cp mask_def.grd mask_def_patch.grd
      #endif
      gmt grdmath corr_patch.grd mask_def_patch.grd MUL = corr_patch.grd -V
    endif
    
    gmt grdmath corr_patch.grd $1 GE 0 NAN mask_patch.grd MUL = mask2_patch.grd
    gmt grdmath corr_patch.grd 0. XOR 1. MIN  = corr_patch.grd
    gmt grdmath mask2_patch.grd corr_patch.grd MUL = corr_tmp.grd 
    
    gmt grd2xyz corr_tmp.grd -ZTLf  -do0 > corr.in
    
    #
    # nearest neighbor interpolation with python
    # Modification by E. Lindsey, Feb 2017
    #
endif

echo "interpolating masked values using a nearest neighbor algorithm"
# removed lines:
 # gmt grd2xyz phase_patch.grd -ZTLf -N0 > phase.in
# new lines:
# mask the phase by correlation
gmt grdmath mask2_patch.grd phase_patch.grd MUL = phase_patch_mask.grd
#
# call the python script to do the interpolation (-c option uses 'nccopy -k classic' to convert to netcdf-3)
#python3.5 /Users/elindsey/Dropbox/code/geodesy/insarscripts/automate/gmtsar_functions/nneigh_interp.py phase_patch_mask.grd -o phase_patch_interp.grd -c
python3 /home/share/insarscripts/automate/gmtsar_functions/nneigh_interp.py phase_patch_mask.grd -o phase_patch_interp.grd -c
#python3.5 /home/elindsey/insarscripts/automate/gmtsar_functions/nneigh_interp.py phase_patch_mask.grd -o phase_patch_interp.grd -c
#python3.5 /Volumes/dione/data/test_GMTSAR/nneigh_interp.py phase_patch_mask.grd -o phase_patch_interp.grd -c
#
# convert to input for snaphu
gmt grd2xyz phase_patch_interp.grd -ZTLf -do0 > phase.in
#
# End of modification by E. Lindsey, Feb 2017
#


#
# run snaphu
#
set sharedir = `gmtsar_sharedir.csh`
echo "unwrapping phase with snaphu - higher threshold for faster unwrapping "

if ($2 == 0) then
  snaphu phase.in `gmt grdinfo -C phase_patch.grd | cut -f 10` -f $sharedir/snaphu/config/snaphu.conf.brief -c corr.in -o unwrap.out -v -s -g components.out
else
  sed "s/.*DEFOMAX_CYCLE.*/DEFOMAX_CYCLE  $2/g" $sharedir/snaphu/config/snaphu.conf.brief > snaphu.conf.brief
  sed "s/.*DEFOCONST.*/DEFOCONST  0.5/g" $sharedir/snaphu/config/snaphu.conf.brief > snaphu.conf.brief
  echo "CONNCOMPTHRESH  70" >> snaphu.conf.brief
  snaphu phase.in `gmt grdinfo -C phase_patch.grd | cut -f 10` -f snaphu.conf.brief -c corr.in -o unwrap.out -v -d -g components.out
endif
echo "snaphu - finished"
echo ""
#
# convert to grd
#
gmt xyz2grd unwrap.out -ZTLf -r `gmt grdinfo -I- phase_patch.grd` `gmt grdinfo -I phase_patch.grd` -Gunwrap_nomask.grd
gmt xyz2grd components.out -ZTLu -r `gmt grdinfo -I- phase_patch.grd` `gmt grdinfo -I phase_patch.grd` -Gunwrap_components.grd
#
gmt grdmath unwrap_nomask.grd mask2_patch.grd MUL = tmp.grd
#
# detrend the unwrapped if DEFOMAX = 0 for interseismic
#
#if ($2 == 0) then
#  gmt grdtrend tmp.grd -N3r -Dunwrap.grd
#else
  mv tmp.grd unwrap.grd
#endif
#
# landmask
if (-e landmask_ra.grd) then
  gmt grdmath unwrap.grd landmask_ra_patch.grd MUL = tmp.grd -V
  mv tmp.grd unwrap.grd
endif
#
# user defined mask
#
if (-e mask_def.grd) then
  gmt grdmath unwrap.grd mask_def_patch.grd MUL = tmp.grd -V
  mv tmp.grd unwrap.grd
endif

# added 9/27/2017: remove topo-correlated atmospheric noise, then re-run unwrapping. After it's done, add back the topo-correlated part

if ($topo_assisted_unwrapping == 1) then

    if (-f topo_shift.grd) then
      set dem = topo_shift.grd
    else
      set dem = topo_ra.grd
    endif
    
    #flip and resample DEM to match unwrapped phase region and spacing
    gmt grdmath -V $dem FLIPUD = topo_flip.grd
    gmt grdsample -V topo_flip.grd -Runwrap.grd -Gtopo_resamp.grd
    rm topo_flip.grd
    
    # get DEM points at the locations of the valid LOS values
    gmt grd2xyz -V -s unwrap.grd | gmt grdtrack -V -Gtopo_resamp.grd |awk '{print $4,1,$3}' > topo_1_los.dat
    
    # compute linear regression for best-fitting slope and constant offset
    gmt gmtmath -V -T topo_1_los.dat LSQFIT = topo_correlated_fit.dat
    set topo_atm_slope = `head -n1 topo_correlated_fit.dat`
    echo "got topo-correlated atmosphere slope of $topo_atm_slope radians/meter"
    
    # compute the topo-correlated signal
    gmt grdmath -V $topo_atm_slope topo_resamp.grd MUL = topo_atm_component.grd
    
    # subtract topo-correlated signal and re-wrap phase
    mv phase_patch.grd phase_patch_orig.grd
    gmt grdmath -V phase_patch_orig.grd topo_atm_component.grd SUB PI ADD 2 PI MUL MOD PI SUB = phase_patch.grd

# re-run unwrapping.
# this could run snaphu recursively - please don't set the value 0 to 1 in this line!
/home/share/insarscripts/automate/gmtsar_functions/snaphu_interp.csh $1 $2 2 $4

    # add back the topo correlated noise component
    mv unwrap.grd unwrap_remove_topo.grd
    gmt grdmath -V unwrap_remove_topo.grd topo_atm_component.grd ADD = unwrap.grd

endif

#
#  plot the unwrapped phase
#
gmt grdgradient unwrap.grd -Nt.9 -A0. -Gunwrap_grad.grd
set tmp = `gmt grdinfo -C -L2 unwrap.grd`
set limitU = `echo $tmp | awk '{printf("%5.1f", $12+$13*2)}'`
set limitL = `echo $tmp | awk '{printf("%5.1f", $12-$13*2)}'`
set std = `echo $tmp | awk '{printf("%5.1f", $13)}'`
gmt makecpt -Cseis -I -Z -T"$limitL"/"$limitU"/1 -D > unwrap.cpt
set boundR = `gmt grdinfo unwrap.grd -C | awk '{print ($3-$2)/4}'`
set boundA = `gmt grdinfo unwrap.grd -C | awk '{print ($5-$4)/4}'`
gmt grdimage unwrap.grd -Iunwrap_grad.grd -Cunwrap.cpt -JX6.5i -B"$boundR":Range:/"$boundA":Azimuth:WSen -X1.3i -Y3i -P -K > unwrap.ps
gmt psscale -Dx3.3/-1.5+w5/0.2+h+e -Cunwrap.cpt -B"$std":"unwrapped phase, rad": -O >> unwrap.ps
#   #
#   # clean up
#   #
#   rm tmp.grd corr_tmp.grd unwrap.out tmp2.grd unwrap_grad.grd 
#   rm phase.in corr.in 
#   #
#   #   cleanup more
#   #
#   rm wrap.grd phase_patch.grd mask_patch.grd mask3.grd mask3.out
#   mv corr_patch.grd corr_cut.grd
#   #
#   
