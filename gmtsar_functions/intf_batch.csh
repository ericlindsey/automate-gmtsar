#!/bin/csh -f 
#       $Id$
#
# intf_batch.csh
# Loop through a list of interferometry pairs
# modified from process2pass.csh
# Xiaopeng Tong D.Sandwell Aug 27 2010 
# modified by E. Lindsey and R. Salman, March 2017 to add ALOS2 and simplify filenames

alias rm 'rm -f'
unset noclobber

# 
  if ($#argv != 3) then 
    echo ""
    echo "Usage: intf_batch.csh SAT intf.in batch.config"
    echo "  make a stack of interferograms listed in intf.in"
    echo ""
    echo " SAT can be ALOS, ALOS2, TSX, ENVI, or ERS" 
    echo ""
    echo " format for intf.in:"
    echo "     reference1_name:repeat1_name"
    echo "     reference2_name:repeat2_name"
    echo "     reference3_name:repeat3_name"
    echo "     ......"
    echo ""
    echo " Example of intf.in for ALOS:"
    echo "    IMG-HH-ALPSRP096010650-H1.0__A:IMG-HH-ALPSRP236920650-H1.0__A"
    echo "    IMG-HH-ALPSRP089300650-H1.0__A:IMG-HH-ALPSRP096010650-H1.0__A"
    echo "    IMG-HH-ALPSRP089300650-H1.0__A:IMG-HH-ALPSRP236920650-H1.0__A"
    echo ""
    echo " Example of intf.in for ALOS2 (stripmap) is:"
    echo "    IMG-HH-ALOS2026257050-141117-FBDR1.1__A:IMG-HH-ALOS2036607050-150126-FBDR1.1__A"
    echo "    IMG-HH-ALOS2026257050-141117-FBDR1.1__A:IMG-HH-ALOS2059377050-150629-FBDR1.1__A"
    echo "    IMG-HH-ALOS2036607050-150126-FBDR1.1__A:IMG-HH-ALOS2059377050-150629-FBDR1.1__A"
    echo ""
    echo " Example of intf.in for ALOS2 (ScanSAR) is:"
    echo "    IMG-HH-ALOS2041113750-150226-WBDR1.1__D-F1:IMG-HH-ALOS2047323750-150409-WBDR1.1__D-F1"
    echo "    IMG-HH-ALOS2041113750-150226-WBDR1.1__D-F1:IMG-HH-ALOS2063883750-150730-WBDR1.1__D-F1"
    echo "    IMG-HH-ALOS2047323750-150409-WBDR1.1__D-F1:IMG-HH-ALOS2063883750-150730-WBDR1.1__D-F1"
    echo ""
    echo " Example of intf.in for ERS is:"
    echo "    e1_05783:e1_07787"
    echo "    e1_05783:e1_10292"
    echo ""
    echo " Example of intf.in for ENVISAT is:"
    echo "    ENV1_2_127_2925_07195:ENV1_2_127_2925_12706"
    echo "    ENV1_2_127_2925_07195:ENV1_2_127_2925_13207"
    echo ""
    echo " batch.config is a config file for making interferograms"
    echo " See example.batch.config for an example"
    echo ""
    exit 1
  endif

  #still checking for SAT, but actually it is an unused parameter.
  set SAT = $1
  if ($SAT != ALOS2 && $SAT != ALOS && $SAT != TSX && $SAT != ENVI && $SAT != ERS) then
    echo ""
    echo " SAT can be ALOS, ALOS2, TSX, ENVI, or ERS"
    echo ""
    exit 1
  endif

#
# make sure the file exists
#
  if (! -f $2) then 
    echo "no input file:" $2
    exit
  endif

  if (! -f $3) then
    echo "no config file:" $3
    exit
  endif
#
# read parameters from configuration file
# 
  set stage = `grep proc_stage $3 | awk '{print $3}'`
  set master = `grep master_image $3 | awk '{print $3}'`
#
# if filter wavelength is not set then use a default of 200m
#
  set filter = `grep filter_wavelength $3 | awk '{print $3}'`
  if ( "x$filter" == "x" ) then
    set filter = 200
    echo " "
    echo "WARNING filter wavelength was not set in config.txt file"
    echo "        please specify wavelength (e.g., filter_wavelength = 200)"
    echo "        remove filter1 = gauss_alos_200m"
  endif
  set dec = `grep dec_factor $3 | awk '{print $3}'` 
  set topo_phase = `grep topo_phase $3 | awk '{print $3}'` 
  set shift_topo = `grep shift_topo $3 | awk '{print $3}'` 
  set threshold_snaphu = `grep threshold_snaphu $3 | awk '{print $3}'`
  set threshold_geocode = `grep threshold_geocode $3 | awk '{print $3}'`
  set region_cut = `grep region_cut $3 | awk '{print $3}'`
  set switch_land = `grep switch_land $3 | awk '{print $3}'`
  set defomax = `grep defomax $3 | awk '{print $3}'`
  set psize = `grep psize $3 | awk '{print $3}'`
  set corr_file = `grep corr_file $3 | awk '{print $3}'`

#new options to assist unwrapping, to be added

  set interp_unwrap = `grep interp_unwrap $3 | awk '{print $3}'`
  set detrend_unwrap = `grep detrend_unwrap $3 | awk '{print $3}'`
  set topo_assisted_unwrapping = `grep topo_assisted_unwrapping $3 | awk '{print $3}'`


##################################
# 1 - start from make topo_ra  #
##################################

if ($stage <= 1) then
  # topo_ra has been moved to its own csh script.
  # no longer dependent on the $SAT parameter!
  #topo_ra.csh $3

  # Note: a custom version of this command is being used. 
  # You must set the variable 'GMTSAR_APP' to the location of the 'automate-gmtsar' folder.
  $GMTSAR_APP/gmtsar_functions/topo_ra.csh $3

endif

##################################################
# 2 - start from make and filter interferograms  #
# 3 - start from unwrap phase and geocode        #
##################################################

if ($stage <= 3) then  #note, stage 2 is defined inside the loop

  echo ""
  echo "START FORM A STACK OF INTERFEROGRAMS"
  echo ""
#
# make working directories
#
  mkdir -p intf/
#
# loop over intf.in
#
  foreach line (`awk '{print $0}' $2`)
    set ref = `echo $line | awk -F: '{print $1}'`
    set rep = `echo $line | awk -F: '{print $2}'`
    set ref_id  = `grep SC_clock_start ./SLC/$ref.PRM | awk '{printf("%d",int($3))}' `
    set rep_id  = `grep SC_clock_start ./SLC/$rep.PRM | awk '{printf("%d",int($3))}' `
    mkdir -p intf/$ref_id"_"$rep_id
    cd intf/$ref_id"_"$rep_id
      
    if ($stage <= 2) then
      echo ""
      echo "INTF.CSH, FILTER.CSH - START"
      echo ""
      cp ../../SLC/$ref.PRM .
      cp ../../SLC/$rep.PRM .
      set refled = `grep led_file $ref.PRM | awk '{print $3}'`
      set repled = `grep led_file $rep.PRM | awk '{print $3}'`
      set refslc = `grep SLC_file $ref.PRM | awk '{print $3}'`
      set repslc = `grep SLC_file $rep.PRM | awk '{print $3}'`
      ln -s ../../raw/$refled .
      ln -s ../../raw/$repled .
      ln -s ../../SLC/$refslc .
      ln -s ../../SLC/$repslc .
      if($topo_phase == 1) then
        if ($shift_topo == 1) then
          ln -s ../../topo/topo_shift.grd .
          intf.csh $ref.PRM $rep.PRM -topo topo_shift.grd
        else
          ln -s ../../topo/topo_ra.grd .
          intf.csh $ref.PRM $rep.PRM -topo topo_ra.grd
        endif
      else
        intf.csh $ref.PRM $rep.PRM
      endif

      #modification, E. Lindsey May 2018 - changeable psize in filter.csh
      if ($psize != "") then
        echo "using psize $psize"
      else
        echo "using default psize of 16"
        set psize = 16
      endif

      # Note: a custom version of this command is being used. 
      # You must set the variable 'GMTSAR_APP' to the location of the 'automate-gmtsar' folder.
      $GMTSAR_APP/gmtsar_functions/filter.csh $ref.PRM $rep.PRM $filter $dec $psize
      #filter.csh $ref.PRM $rep.PRM $filter $dec

      echo "INTF.CSH, FILTER.CSH - END"
      echo ""
      
    endif # end stage 2
    
    # the rest is stage 3

    if ($corr_file != "") then
      echo "moving original correlation file to corr.grd.orig"
      echo "linking user-defined correlation ../../$corr_file as corr.grd"
      mv corr.grd corr.grd.orig
      ln -s ../../$corr_file corr.grd
    endif

    if ($threshold_snaphu != 0 ) then
      if ($region_cut == "") then
        set region_cut = `gmt grdinfo phase.grd -I- | cut -c3-20`
      endif
      if ($switch_land == 1) then
        if (! -f ../../topo/landmask_ra.grd) then
          cd ../../topo
          if ($SAT == ALOS2) then
            landmask_ALOS2.csh $region_cut ##26032020
          else
            landmask.csh $region_cut
          endif
          cd ../intf/$ref_id"_"$rep_id
        endif
        ln -s ../../topo/landmask_ra.grd .
      endif
      if ($interp_unwrap == 1) then
        #set snaphu_cmd = snaphu_interp.csh
        echo "SNAPHU_INTERP.CSH - START"
        # Note: a custom version of this command is being used. 
        # You must set the variable 'GMTSAR_APP' to the location of the 'automate-gmtsar' folder.
        set snaphu_cmd = "$GMTSAR_APP/gmtsar_functions/snaphu_interp.csh"
      else
        echo "SNAPHU.CSH - START"
        set snaphu_cmd = snaphu.csh
        set topo_assisted_unwrapping = ""
      endif
      echo "threshold_snaphu: $threshold_snaphu"
      $snaphu_cmd $threshold_snaphu $defomax $topo_assisted_unwrapping $region_cut

      if ($detrend_unwrap == 1) then
        echo ""
        echo "detrending and unwrapping a second time"
        echo ""
        gmt grdtrend -V unwrap.grd -N3r -Tunwrap_trend.grd -Runwrap.grd
        mv phasefilt.grd phasefilt_orig.grd
        if ($region_cut != "") then
          gmt grdcut phasefilt_orig.grd -R$region_cut -Gphasefilt_orig_patch.grd
        else
          cp phasefilt_orig.grd phasefilt_orig_patch.grd
        endif
        gmt grdmath -V phasefilt_orig_patch.grd unwrap_trend.grd SUB 2 PI MUL MOD PI SUB = phasefilt.grd
        mv unwrap.grd unwrap_nodetrend.grd
        mv unwrap_nomask.grd unwrap_nomask_nodetrend.grd
        $snaphu_cmd $threshold_snaphu $defomax $topo_assisted_unwrapping $region_cut
        echo ""
        echo "adding back trend to unwrap.grd"
        echo ""
        gmt grdmath -V unwrap.grd unwrap_trend.grd ADD = tmp.grd
        mv tmp.grd unwrap.grd
        mv phasefilt.grd phasefilt_detrend.grd
        mv phasefilt_orig.grd phasefilt.grd
      endif

      echo "SNAPHU - END"
    else 
      echo ""
      echo "SKIP UNWRAP PHASE"
    endif

    echo ""
    echo "GEOCODE.CSH - START"
    rm raln.grd ralt.grd
    if ($topo_phase == 1) then
      rm trans.dat
      ln -s  ../../topo/trans.dat . 
      echo "threshold_geocode: $threshold_geocode"
      geocode.csh $threshold_geocode
    else 
      echo "topo_ra is needed to geocode"
      exit 1
    endif
    echo "GEOCODE.CSH - END"
 
    cd ../..

  end # loop of foreach 
endif # stage 2+3

  echo ""
  echo "END FORM A STACK OF INTERFEROGRAMS"
  echo ""

