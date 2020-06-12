#!/bin/csh -f

#run gmtsar_app in each subswath

if ( $#argv > 0 && ( $1 == '-h' || $1 == '--help' ) ) then
  echo "Usage: $0 [batch.config]"
  echo "Runs gmtsar_app for each subswath listed in the config file (e.g. s1_subswath = 1,2,3)"
  echo "if batch.config is given, it will be copied to all subswaths."
  echo "works for ALOS-2 or Sentinel-1. For other satellites, just run gmtsar_app directly."
  exit 1
endif

if ( $#argv == 1 ) then
  set config = $1
else
  set config = batch.config
endif

#check satellite ID: Either ALOS2 or S1
set sat = `grep sat_name $config |awk '{print $3}'`

# find subswaths to process - check the config file and make folders if not already created.
# old: set subswaths = `ls -d F?`
set subswaths = `grep s1_subswath $config |awk '{print $3}' | sed "s/,/ /g"`
echo "Processing subswaths $subswaths"

foreach n ( $subswaths )
  # only create directory if it does not exist
  if ( ! -d F$n ) then
    echo "Creating directory F$n and making links"
    mkdir -p F$n/topo
    cd F$n/topo
    ln -s ../../topo/dem.grd .
    if ( $sat == 'S1' ) then
      mkdir -p ../raw_orig
      cd ../raw_orig
      ln -s ../../raw_orig/* .
    else if ( $sat == 'ALOS2' ) then
      mkdir ../raw
      cd ../raw
      ln -s ../../raw/IMG-HH-*-F$n .
      ln -s ../../raw/LED-* .
    else 
      echo "Error: SAT value $sat not recognized."
      exit 1
    endif 
    cd ../..
  endif

  #copy config file and go to subswath directory
  cp $config F$n
  cd F$n
  pwd

  # set subswath value in this batch.config file
  if ( $sat == 'S1' ) then
    echo "Sentinel - setting s1_subswath value to $n in $config" 
    awk -v n=$n '/s1_subswath/{$3=n}1' $config > $config.temp
    mv $config.temp $config
  endif

  #run gmtsar_app
  #qsub -v config=$config ../run_gmtsar_app.pbs
  python $GMTSAR_APP/gmtsar_app.py $config > run_gmtsar_app.log &

  cd ..
end

