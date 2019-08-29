#!/bin/bash

# make links for 3-subswath TOPS processing,
# and copy config file with subswath numbered correctly.

for n in {1..3}
do
  mkdir -p F$n/topo
  cd F$n/topo
  ln -s ../../topo/dem.grd .
  mkdir -p ../raw_orig
  cd ../raw_orig
  ln -s ../../raw_orig/* .
  cd ../..
  cp batch.config F$n/
  echo "Setting s1_subswath value to $n in batch.config" 
  sed -i '' "/s1_subswath/s/[0-9]$/${n}/" F$n/batch.config
done

