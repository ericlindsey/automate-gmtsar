#!/bin/csh -f

#make links for 5-subswath ALOS-2 WD1 processing.
#does not set up config file.

foreach n ( 1 2 3 4 5 )
  mkdir -p F$n/topo
  cd F$n/topo
  ln -s ../../topo/dem.grd .
  mkdir ../raw
  cd ../raw
  ln -s ../../raw/IMG-HH-*-F$n .
  ln -s ../../raw/LED-* .
  cd ../..
end

