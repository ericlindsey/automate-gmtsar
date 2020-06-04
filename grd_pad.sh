#!/bin/bash

if [[ $# -lt 1 ]]; then
    echo "usage: $0 grdfilenames"
    echo "computes the exterior bounds of all files and pads them all to match"
    exit 1
fi
echo "Begin intf_pad.sh"

bounds=`gmt grdinfo -C $@ |cut -f 2-5 |gmt gmtinfo -C | cut -f 1,4,5,8 |awk '{printf("-R%.12f/%.12f/%.12f/%.12f",$1,$2,$3,$4)}'`
echo "computed maximum exterior bounds for all files: $bounds"

for file in $@
do 
    padfile=$(basename $file .grd)_pad.grd
    echo "reading file $fname"
    echo "writing file $padfile"

    incr=`gmt grdinfo -I $file`
    gmt grd2xyz $file -bo | gmt xyz2grd -bi $bounds $incr -r -G$padfile
done

echo "End intf_pad.sh"
