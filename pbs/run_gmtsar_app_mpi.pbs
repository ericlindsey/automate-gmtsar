#!/bin/bash
#PBS -N gmtsar_app
#PBS -j oe
#PBS -V
#PBS -m abe
#PBS -M komodo
#PBS -l nodes=4:ppn=24
#PBS -q q24

#NOTE:
#options are set in batch.config
# start and endstage:
#1 = preprocessing
#2 = alignment
#3 = making topo_ra
#4 = making interferograms, unwrapping and geocoding

#improvement needed
#for scansar mode, have to set up the subswath folders manually and run this script once in each subswath
#created: Mar 2017 

#set optionns
configfile=batch.config

#load mpi, python and gmtsar
module load openmpi/1.4.5-gnu
module load GMTSAR/5.4/GMT5.4.1-gnu
module load python/3.5.3
module load anaconda/4.4.0-fall3d

Ncpus=`cat $PBS_NODEFILE | wc -l`
mpiOption='-mca btl tcp,sm,self -np'
code='/home/share/insarscripts/automate/gmtsar_app.py'

if [ "$PBS_O_WORKDIR" != "" ]; then

   cd $PBS_O_WORKDIR
   echo Running gmtsar_app.py with MPI on $Ncpus cpus:
   echo `cat $PBS_NODEFILE`
   echo " "
   echo From directory: $PBS_O_WORKDIR
   echo " "

   #run python code with MPI
   mpiexec $mpiOption $Ncpus python3.5 $code --mpi $configfile
   #python3.5 $code $configfile

fi

