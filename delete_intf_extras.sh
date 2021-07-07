cd intf
for pair in `ls -d *_*`; do
    cd $pair
    rm -f unwrap_grad.grd
    rm -f los_grad.grd
    rm -f mask2_patch.grd
    rm -f phase_patch_mask.grd
    rm -f corr_tmp.grd
    rm -f los.grd
    rm -f mask2.grd
    rm -f amp.grd
    rm -f unwrap_mask.grd
    rm -f display_amp.grd
    rm -f phase_mask.grd
    rm -f mask.grd
    rm -f unwrap_nomask.grd
    rm -f mask3.grd
    rm -f filtcorr.grd
    rm -f amp1.grd
    rm -f amp2.grd
    rm -f imagfilt.grd
    rm -f realfilt.grd
    rm -f phase_patch_interp.grd
    rm -f imag_tmp.grd
    rm -f real_tmp.grd
    rm -f corr.in
    rm -f phase.in
    rm -f unwrap.out
    rm -f unwrap.ps
    rm -f los.pdf
    rm -f phase.pdf
    rm -f components.out
    rm -f phase_mask.pdf
    rm -f display_amp.pdf
    rm -f corr.pdf
    rm -f phase_mask_ll.grd
    rm -f unwrap_ll.grd
    rm -f phasefilt.pdf
    rm -f phasefilt_mask.pdf
    rm -f unwrap_mask.pdf
    cd ..
done
