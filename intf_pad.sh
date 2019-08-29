#!/bin/bash

if [[ $# -ne 1 ]]; then
  echo "using default filename unwrap_mask_ll.grd"
  fname="unwrap_mask_ll.grd"
else 
  if [[ "$1" == "-h" ]]; then
    echo "usage: $0 [grdfilename] [no intf.in]"
    echo "computes the exterior bounds matching all files intf/*/[name] and pads them all to match"
    echo "default: unwrap_mask_ll.grd"
    echo "if a second argument is given, do not write out the corresponding intf.in file"
    exit 0
  fi
  fname=$1
fi

padfile=$(basename $fname .grd)_pad.grd
echo "reading files intf/*/$fname"
echo "writing files intf/*/$padfile"

bounds=`gmt grdinfo -C intf/*/$fname |cut -f 2-5 |gmt gmtinfo -C | cut -f 1,4,5,8 |awk '{printf("-R%.12f/%.12f/%.12f/%.12f",$1,$2,$3,$4)}'`
echo "computed maximum exterior bounds for all files: $bounds"

echo "deleting old intf.in"
rm intf.in

for dir in  `ls -d intf/*`
do
  if [[ -f $dir/$fname ]]; then
    echo "padding $dir/$fname to $bounds and converting to NetCDF Version 3"
    #gmt grdcut $dir/$fname $bounds -Gtemp.grd
    incr=`gmt grdinfo -I $dir/$fname`
    gmt grd2xyz $dir/$fname -bo | gmt xyz2grd -bi $bounds $incr -r -Gtemp.grd
    nccopy -k classic temp.grd $dir/$padfile
    if [[ $# -lt 2 ]]; then
      echo appending logs_$dir.in to intf.in
      cat logs_$dir.in >> intf.in
    fi
  else
    echo "$dir/$fname not found."
  fi
done
rm temp.grd
