#!/bin/csh -f

# make links for 3-subswath TOPS processing.
# does not set up config file because the 'subswath'
# parameter must be different. copy at run-time.

foreach n ( 1 2 3 )
  mkdir -p F$n/topo
  cd F$n/topo
  ln -s ../../topo/dem.grd .
  mkdir -p ../raw_orig
  cd ../raw_orig
  ln -s ../../raw_orig/* .
  cd ../..
end

if ( ! -f batch.config ) then
  cp $GMTSAR_APP/batch.config .
  cp $GMTSAR_APP/run_gmtsar_app.csh .
endif

