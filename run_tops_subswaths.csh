#!/bin/csh -f

#run gmtsar_app in each subswath

if ( $#argv > 0 && ( $1 == '-h' || $1 == '--help' ) ) then
  echo "Usage: $0 [batch.config]"
  echo "Runs gmtsar_app for each subswath that has been set up (ls F?)"
  echo "if batch.config is given, it will be copied to all subswaths."
  exit 1
endif

# find subswaths to process - check the config file and make folders if not already created.
# old: set subswaths = `ls -d F?`
set subswaths = `grep s1_subswath $config |awk '{print $3}'`
echo "Processing subswaths $subswaths"
foreach n (`echo $subswaths | sed "s/,/ /g"`)
  # only create folder if it does not exist
  if ( ! -d F$n ) then
    echo "Creating subfolder F$n and making links"
    mkdir -p F$n/topo
    cd F$n/topo
    ln -s ../../topo/dem.grd .
    mkdir -p ../raw_orig
    cd ../raw_orig
    ln -s ../../raw_orig/* .
    cd ../..
  endif
end

foreach F ( $subswaths ) 
  if ( $#argv == 1 ) then
    echo "copying user-specified config: $1"
    cp $1 $F
    set config = $1
  else
    echo "copying batch.config from top directory"
    cp batch.config $F
    set config = "batch.config"
  endif
  cd $F
  pwd
  set sat = `grep sat_name $config |awk '{print $3}'`
  if ( $sat == 'S1' ) then
    set n = `echo $F |sed 's/F//'`
    echo "Sentinel - setting s1_subswath value to $n in $config" 
    awk -v n=$n '/s1_subswath/{$3=n}1' $config > $config.temp
    mv $config.temp $config
  endif

  #run gmtsar_app
  #qsub -v config=$config ../run_gmtsar_app.pbs
  python $GMTSAR_APP/gmtsar_app.py $config

  cd ..
end
