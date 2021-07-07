#!/bin/bash

#make alos links
if [[ $# -lt 3 ]]; then
  echo "Usage: $0 base_data_path Path Frame [dem]"
  echo run from top level directory containing your dem, or give full dem path as third argument
  echo 
  exit 1
fi

datapath=$1
path=$2
frame=$3

if [[ -f $4 ]]; then
  dem=$4
else
  curr=`pwd`
  dem=$curr/dem.grd
  config=$curr/batch.config
  pbs=$curr/run_gmtsar_app.pbs
fi

mkdir -p $path/$frame/topo 
cd $path/$frame/topo
ln -s $dem . 
cd ../ 
cp $config .
cp $pbs .
mkdir -p raw 
cd raw
ln -s $1/$path/$frame/IMG-HH* .
ln -s $1/$path/$frame/LED* .

