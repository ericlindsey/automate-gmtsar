#!/bin/csh -f
#       $Id$
#
# Modified from filter.csh
# Run Goldstein filter on phase.grd with user-input parameters
#
#
  alias rm 'rm -f'
  gmt set IO_NC4_CHUNK_SIZE classic
#
#
# set grdimage options
#
  set scale = "-JX6.5i"
  set thresh = "5.e-21"
  gmt set COLOR_MODEL = hsv
  gmt set PROJ_LENGTH_UNIT = inch

  if ($#argv != 2) then
errormessage:
    echo ""
    echo "Usage: goldstein_filter.csh alpha psize"
    echo ""
    echo " Apply goldstein filter to phase image."
    echo " "
    echo " alpha -  strength of goldstein exponent (default: 0.5)"
    echo " psize - filter window size (default: 16)"
    echo " "
    echo "Example: goldstein_filter.csh 0.8 32"
    echo ""
    exit 1
  endif
  echo "goldstein_filter.csh"

#
# set variables for plotting
#
  set scale = "-JX6.5i"
  set boundR = `gmt grdinfo display_amp.grd -C | awk '{print ($3-$2)/4}'`
  set boundA = `gmt grdinfo display_amp.grd -C | awk '{print ($5-$4)/4}'`
#
# flip mask
#
  mv mask.grd mask_tmp.grd 
  gmt grdmath mask_tmp.grd FLIPUD = mask.grd
#
#  make the Werner/Goldstein filtered phase
#
  echo "filtering phase..."
  phasefilt -imag imagfilt.grd -real realfilt.grd -amp1 amp1.grd -amp2 amp2.grd -alpha $1 -psize $2 
  gmt grdedit filtphase.grd `gmt grdinfo mask.grd -I- --FORMAT_FLOAT_OUT=%.12lg` 
  gmt grdmath filtphase.grd mask.grd MUL FLIPUD = phasefilt.grd
  rm filtphase.grd
  gmt grdimage phasefilt.grd $scale -B"$boundR":Range:/"$boundA":Azimuth:WSen -Cphase.cpt -X1.3 -Y3 -P -K > phasefilt.ps
  gmt psscale -D3.3/-1.5/5/0.2h -Cphase.cpt -B1.57:"phase, rad": -O >> phasefilt.ps
#
# flip mask
#
  mv mask_tmp.grd mask.grd 

