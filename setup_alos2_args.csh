#!/bin/csh -f

#make links for 5-subswath ALOS-2 WD1 processing.
#does not set up config file.

if ($#argv != 2) then
  echo "usage: $0 dem.grd path_to_raw"
  exit 1
endif

mkdir topo; cd topo
ln -s $1 .
cd ..

mkdir raw; cd raw
ln -s $2/LED* .
ln -s $2/IMG-HH* .
cd ..

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

cp  /home/share/insarscripts/automate/batch.config .
cp  /home/share/insarscripts/automate/runall.csh .
cp  /home/share/insarscripts/automate/run_gmtsar_app.pbs .

