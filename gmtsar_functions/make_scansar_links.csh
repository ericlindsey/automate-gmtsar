#!/bin/csh -f 
#
# make_scansar_links.csh
# link ALOS2 files ending in -F1, -F2, etc to separate directories for processing
# created by E. Lindsey, March 2017

alias rm 'rm -f'
unset noclobber

 
if ($#argv < 1) then 
  echo ""
  echo "Usage: make_scansar_links.csh batch.config [copy]"
  echo ""
  echo "  link ALOS2 files ending in -F1, -F2, etc to separate directories for processing."
  echo "  optional second argument 'copy' will copy the batch.config instead of linking it."
  echo ""
exit 1
endif

if ( ! -f $1 ) then
  echo "error: batch.config file $1 not found"
  exit 1
endif

foreach F ( F1 F2 F3 F4 F5 )
  echo linking files for $F
  mkdir -p $F/topo
  mkdir -p $F/raw
  cd $F
  if ( $2 == copy ) then
    cp ../$1 .
  else
    ln -s ../$1 .
  endif
  cd topo
  ln -s ../../topo/dem.grd .
  cd ../raw
  ln -s ../../raw/LED* .
  ln -s ../../raw/*$F .
  cd ../..
end

