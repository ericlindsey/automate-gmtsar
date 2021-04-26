GMTSAR APP: An automated GMTSAR workflow in python
------------

This repository contains a set of python and modified C-shell scripts that should make using GMTSAR much more user-friendly. 
All the manual creation of files and selection of processing parameters is handled by python, and the user only has to interact at a few points to run the next command.
See the instructions below for an example with Sentinel-1 data.

Eric Lindsey, last updated Feb 2021

**Setup and installation:**

Latest tests: works with GMTSAR 6.0 and Python 3.8.

Run the command 'setup_gmtsar_app.sh' to add the $GMTSAR_APP environment variable to your shell.
This will print out an export command you can put in your .zshrc or .bashrc to include this variable automatically.

**Processing Sentinel InSAR data -- GMTSAR_app workflow**

Summary of steps

1. a. Download data for a chosen track using sentinel_query_download.py

   b. Download a DEM (from <http://topex.ucsd.edu/gmtsar/demgen/>)

2.  Combine the frames to fit your desired latitude bounds using cat_s1.py

3.  a. Set up your processing directory with the DEM and links to the raw data using setup_tops.sh
    
    b. Download the most recent AUX_CAL files from <https://qc.sentinel1.copernicus.eu/>

4.  Generate SLCs and radar geometry with gmtsar_app.py, startstage = 1, endstage = 3

5.  Generate interferograms with gmtsar_app.py, startstage = 4, endstage = 4

6.  QC and modify the parameters as needed.

7.  Generate timeseries with run_sbas.csh.


**1. a. Searching for and downloading data using 'sentinel\_query\_download.py'**

Get this script from the separate repository at: (<https://github.com/ericlindsey/sentinel_query_download>).

This script uses the ASF Vertex web API to search for data archived at
ASF. Then it can automatically download that data from either the AWS
public dataset, or from ASF. It is general-purpose and can be used to
find any SAR data archived there, not just Sentinel.

The basic method is to first visit the ASF Vertex website
(<https://search.asf.alaska.edu/#/>), and find the data you are
looking for visually. By copying a few things from this page to the config file, we can construct an API query that will
duplicate your GUI search, and then automatically download the images.

For example, let's say I want to download all the data from a descending
track over Albuquerque: First, I go to the website and create a search box
around the city. I should make the box slightly taller in the
north-south direction than I really need, so that if any frames have
partial coverage we make sure to get their next consecutive frame as
well.

From the search, I decide to use Path 56. Now, I can construct the API query commands using a simple config file:

    [api_search]
    platform = Sentinel-1A,Sentinel-1B
    processingLevel = SLC
    beamMode = IW
    intersectsWith = POLYGON((103.1197 0.3881,104.5655 0.3881,104.5655 2.263,103.1197 2.263,103.1197 0.3881))
    relativeOrbit = 18
    
    [download]
    download_site = ASF
    nproc = 2
    
    [asf_download]
    http-user = ****
    http-password = ****

Note that I just copied the polygon coordinates from the web GUI, after
drawing the box there -- this is the easiest way to generate this
polygon, though you can also type it manually if you prefer. There are
also many other options for search parameters, such as start and end
date:

    start = 2017-12-01T00:00:00UTC
    end = 2018-01-30T00:00:00UTC

These can be useful for finding data associated with an earthquake, for
example, or for updating the data for a track you already downloaded
earlier. See the example config file and more detailed information at the sentinel_query_download repository.

We run the query with the command:

    python sentinel_query_download.py sentinel_query.config --verbose

This returns all matching images that are stored as a .csv, and with the --verbose option prints out a summary to the screen.

Now, we should be ready to start the data download. We need to make sure
the config file has a few extra settings under the headings "download" and "asf_download".
A username and password is the most important thing for ASF downloads, and we can also set the script to run several downloads in parallel.
But note that running too many may slow down each one's progress, particularly if you are using a spinning hard drive!

We can now run the above python command with the option --download. Note
though, that this will occupy your terminal window for many hours, and if you are
logged out for any reason, it will halt the download. If this happens, don't panic, just run the same command again. Fortunately, wget enables
re-starting interrupted downloads so it should pick up where it left off.

Downloads from ASF take anywhere from 5-20 minutes per image. So this process will likely take overnight, or possibly longer. Running in parallel with
'nproc' may speed this up, but the optimal number of parallel downloads to run has not been tested.

Finally, it should be noted that you can also generate a download script
directly from the Vertex website -- click 'add images to queue by type',
choose L1 SLC, then view the queue and click to generate a python
download script. You can run this directly, or edit it as needed.

Note that wget is very smart about not re-downloading existing files, so
if you have kept your data in the same place, you can simply re-run a duplicate query with no 'stop' date to get the
latest scenes.

We're done for now -- move on to the next downloading step, and then
come back in the morning to check the results!


**1. b. Downloading a DEM**

We need a high-resolution Digital Elevation Model (DEM) for our
processing. It has to be corrected to ellipsoid height (standard DEMs
are referenced to the geoid instead), and it needs to be in a
GMTSAR-readable format (GMT .grd file). The simplest way to get such a
file is to go to the GMTSAR website and create a custom DEM:
<http://topex.ucsd.edu/gmtsar/demgen/>. Select 'SRTM1' and enter a wide
lat/lon range that exceeds the size of your image (but not too far). 

Click 'generate' and then download the file when it is ready. Unzip the
tar file, and keep only the file 'dem.grd'. The rest can be discarded.
Upload this to komodo (eg. using scp) and place it with a descriptive
enclosing folder name (don't change the file name) under
/home/data/INSAR_processing/dems.

Notes:

- Be sure to select 'SRTM1' for the highest resolution.

- Maximum size is 4x4 degrees. If you need a larger area, first download several regions and then use 'grdblend' or 'grdpaste' to combine them. The downloaded zip file contains a script that provides an example of how to do this.

**2. Combining the frames: using cat_s1.py**

Now that you have downloaded the data from ASF, you may notice several images have been downloaded for each date, in different directories beginning with F (e.g. F585, F590). The reason is that our search polygon might have extended across several image "frames" that ESA uses to break up the data into manageable file sizes along an orbit, and the download script will automatically get both images.

Unfortunately, the early Sentinel-1 data (before 2017) had no consistent frame boundary, so for our long-term processing, to get a consistent image size we have to separate the individual 'bursts' (sub-frames) and then generate our own self-consistent "frame" for InSAR processing. This is done using cat\_s1.py, which invokes the GMTSAR command create_frame_tops.csh.

You can copy the script 'run_cat_s1.sh' to your working directory and edit it as needed. The important things to set:

direction - D or A. This must match your data (Descending or Ascending). If you are confused, check the information on the ASF site. Normally, Descending data frames are tilted toward the Northeast, while Ascending frames are tilted toward the Northwest. 

lon/lat pins - these define the corners of a box we want to include in our processing.

nproc - number of processes to run in parallel. Probably 1 if the data are all on the same hard drive. On a server with faster I/O, you could use 2-4.

Running this command will take a while, since it has to unzip the data and write the images back out to disk.


**3. Setting up files**

**a. Setting up your processing directory**

This is a short step. GMTSAR expects the raw data and DEM to be in a specific directory structure, with one directory for each subswath (F1, F2, F3). You generally want to name your top directory something useful, like the name of the path and your area. Then make two sub-folders: topo/ and raw_orig/:

    $ cd my_processing_directory
    $ mkdir topo
    $ mkdir raw_orig

Place your dem.grd file (do not re-name it!) from step 2 in the topo/ directory.

Under raw_orig, link all the cropped .SAFE folders that you created in step 3:

    $ cd raw_orig
    $ ln -s ../../crop/*SAFE .

Now, run the command 'setup_tops.csh' from your processing directory, which will create the subswath folders F1, F2, F3 and links inside them:

    $ cd ..
    $ $GMTSAR_APP/setup_tops.csh

That's it! Ready for the next step.

**b. Update your AUX_CAL files**

The Sentinel-1 processing workflow requires an additional XML file for each satellite, named s1[a,b]\_aux_cal.xml. These files can be found at <https://qc.sentinel1.copernicus.eu/>. You should download the most recent file, and extract the .xml files from the .TGZ file, then place them in the orbit folder defined in your config file (see step 4, below). This used to be an automatic step when ESA allowed these files to be found via an API, but this API is no longer working, so we have to do this manually. Fortunately the AUX_CAL files are updated rarely, only every few months or so.

**4. Generate SLCs and radar geometry using gmtsar\_app.py**

We have finally finished setting up the data, and now we are ready to start processing. The first stage is to get the images into a format that makes them ready to be interfered. We call these aligned and pre-processsed images "SLC" for Single-Look-Complex. This is the full resolution complex image, in radar coordinates, stored in a matrix that has been precisely aligned to match a 'master' image. After this step, interferometry is just complex multiplication.

When you ran setup_tops.csh in the last step, it copied two files to your directory in addition to creating the F1/ etc. directories. These are batch.config and run_tops_subswaths.csh.

The first file, batch.config, contains the configuration parameters we need to set up. For now, the important values to check we set correctly are:

    sat_name = S1
    s1_subswath = 1,2,3
    s1_orbit_dir = (valid path on your system with writable permissions)
    startstage = 1
    endstage = 3
    num_processors = 1

Notes:
 - Sat name must be exactly 'S1'.
 - Set the list of subswaths you wish to run as a comma-separated list. E.g. '1,2,3' or '2,3' or '1'.
 - For the orbit directory, this should be an absolute path.
 - startstage and endstage control which GMTSAR steps are run. These are: 1=preprocessing, 2=alignment, 3=radar geometry, 4=interferograms. Since 1-3 must be run first, and these are not done in parallel, while step 4 is run in paralel, it makes sense to do 1-3 with num_processors=1, then run step 4 later with more processors (see next section). But the code will still work fine if you run 1-4 all at once and request a larger number of processors. The extra processors will not be used until step 4 is reached.
 - If you are running on a server via PBS, note that you should set your PBS script to use only one CPU here as well. See the section on PBS jobs below for more.

Now, we can easily submit a job for all requested subswaths:

    $ ./run_tops_subswaths.csh

This will give us a message that 3 jobs have been started. This step typically takes a few hours, depending on the number of scenes and how large they are.

**5. Generate interferograms using gmtsar\_app.py**

If the last stage ran correctly, you should see a subdirectory 'SLC' in each of the 3 subswath directories, with files consisting of an SLC image (e.g.
'S1A20171210_ALL_F1.SLC'), a matching parameter file ('.PRM'), and an orbit file ('.LED') for each of the SAR scenes. For Sentinel, these will actually
be links to files in the raw/ directory, while for other satellites the files will be physically located here.

There will also be several files in the topo/ directory for each subswath, including 'trans.dat' -- this is the translation table between radar and geographic coordinates that will be used to geocode our interferograms.

If everything looks correct and there were no errors in the .log files, we are ready to make some interferograms. Change a few config parameters in our top-level batch.config file before running:

    startstage = 4
    endstage = 4
    max_timespan = 48
    intf_min_connectivity = 1
    threshold_snaphu = 0.2
    num_processors = 4

If we want to check that our interferogram-generation settings are good,
we can first run 'plot_intf_list.py' to generate the intf.in list and make a
figure showing the connectivity:

    $ python $GMTSAR_APP/plot_intf_list.py batch.config

Look at the file 'intfs.png' and adjust your settings as necessary.

Note: Each interferogram (for each subswath) always runs on one CPU. Here, we'll require 12 processors (4 CPUs \*3 subswaths), but if we have less than 12 CPUs, this will be overkill and things won't actually run as fast as promised. On a laptop you may want to run one subswath at a time to get results done for that region more quickly, or else run things on a server.

Once everything is set, run gmtsar again for all subswaths:

    $ ./run_tops_subswaths.csh

In this example, we will run just the interferogram stage (stage 4), in this case with a maximum timespan of 48 days, and it will skip the unwrapping stage (snaphu threshold set to zero). Each interferogram should take just 10-15 minutes to run.

Next, we will need to look at the interferograms, and decide on our processing parameters. This is where art blends with science...


**6. QC and modify the interferogram processing parameters**

We need to look at our interferograms, decide what went wrong (if
anything), and determine what we need to do to fix things. This part is
a little open-ended, but there are two basic steps that we should always
follow: inspecting the phase images for good coherence and accurate
processing, and inspecting the unwrapped images for unwrapping errors.

To look at a large number of images, the simplest option is to use the
program 'gthumb' which can view many image files at once. GMTSAR
automatically produces .png files of the geocoded, masked phase called
'phasefilt\_mask\_ll.png'. Thus, we can use:

    $ gthumb intf/*/phasefilt_mask_ll.png

This will open up all the images in a thumbnail view, and you can click
on one at a time or use the arrows to flip through them. Inspect for any
images that are a different size (indicating a burst mismatch in the raw
data), are blank or have zero correlation (indicating an alignment
failure), or that have any other obvious artifacts. There's no set
formula here, and fortunately there shouldn't be much to see if
everything went correctly.

You can also inspect the images to see if it looks like the poorly
correlated pixels have been properly masked out. If the images are
mostly blank, you might need to compare the un-masked images. These are
not geocoded by default, but you can go select a particular directory
and use 'gs phasefilt.ps' to look at the unmasked image in radar
coordinates.

You can also use the program 'ncview' to look at the data files (.grd)
directly. For example, it may help to open up a correlation file and
look at the range of values in well-correlated and poorly-correlated
areas, to determine a better threshold to use.

There are several options for improving the unwrapping results:

1. Reduce threshold_snaphu. Good values for Sentinel data are usually in the range 0.2 - 0.4, while for other
satellites it may be smaller, in the range of 0.1 - 0.2. 
Note that unwrapping will be skipped if threshold_snaphu is '0.0' but not if it is '0'. 

2. Change interp_unwrap. This should generally be set to 1 because it greatly speeds
up the process, but in rare cases it may be better to turn it off.

3. Turn on detrend_unwrap or topo_assisted_unwrapping. These are 2-stage
unwrapping options that slow the process down quite a bit (the image has
to be unwrapped twice) but can improve results if you are finding a lot
of unwrapping errors. detrend_unwrap is particularly helpful for ALOS-2
data that often have big ramps, while topo_assisted_unwrapping is
useful for volcanoes or other areas that commonly have a large
tropospheric delay that is correlated with topography. If you find some
interferograms have unwrapping errors, you may wish to create a subset
of your intf.in list for images to run again with these options, but
it's a good idea to set them both to 0 for the first run.

Also, if you have already run all of the interferograms without
unwrapping and none of the filtering options have changed, you can save
some time in this step using

    proc_stage = 3

However, be careful with this option because it will cause GMTSAR to use whatever 'phasefilt.grd' was in the intf directory, and will not check or re-create this file if any other options have changed.


**7. Create timeseries using run_sbas.csh**

This is a simple code that generates the input files for the GMTSAR program 'sbas' and then runs it. You will need to check the help message for 'sbas' to see all the options available for this code. Basic usage is as follows:

1. list out the unwrap.grd files you want to include. To list all of them, simply do

       ls intf/*/unwrap.grd > unwrap_list.in
    
Modify this list as needed, e.g. if there are bad images you wish to exclude, simply delete that line from the list.

2. Choose your smoothing factor and n_atm values. Generally 0 is a good first case. Smoothing factor applies temporal smoothing to the timeseries for each pixel, and n_atm > 0 will run the Tymofyeyeva & Fialko method for reducing atmospheric noise by common-scene-stacking. 

3. Now run: for example, with 0 for both parameters:

       $GMTSAR_APP/gmtsar_functions/run_sbas.csh topo/master.PRM unwrap_list.in 0 0
    
Depending on the size and number of images, this will take several hours (or possibly days). A future improvement would be to enable this to run in parallel.

**Congratulations, you're done!**

**About orbits:**

The orbit file is used to compute the exact position of a SAR satellite
in space during the time the image was taken, which is needed for
computing topographic effects and geo-coding the data. It is also needed
to provide the precise timing information to determine how the frames
match up when we combine them in step 3.

The Sentinel-1 satellites have two types of orbit files: Precise and
Restituted. Precise orbits (Precise Orbit Ephemeris, or POE) are
typically generated about 2 weeks after the image was acquired, once the
precise GPS orbits have been published by the IGS. The files are usually
valid for 1 day, and have a name format like this:

S1A_OPER_AUX_POEORB_OPOD_20141023T123724_V20141001T225944_20141003T005944.EOF

The filename lists the satellite (S1A), type of orbit (POEORB), and threed dates. The first date is the file's production date, and the second two dates (after
the 'V') specify the range of validity. For example, the file above is valid from 2014 Oct 01, 22:59:44 until 2014 Oct 03, 00:59:44.

Restituted orbits (RES) are generated rapidly, but have a slightly lower
accuracy. If we are using data acquired within the last 2 weeks, these
will be our only option. Their name format is similar, but the validity
range is much smaller, usually only a few hours:

S1B_OPER_AUX_RESORB_OPOD_20180101T053144_V20180101T011536_20180101T043306.EOF

gmtsar_app.py is able to read these file formats and tell which one is the most recent and accurate version to use -- if multiple files are
available for a given scene, the precise orbit with the most recent production date will be used. If none are found on your system, gmtsar_app.py will request the most recent orbit file from ESA. The code will also request the most recent aux_cal.xml file from ESA as well.

**Notes on running jobs on PBS clusters**

PBS clusters like those used at EOS are powerful computers comprised of
many individual computers (nodes), and controlled by a
"head node" which handles all the login terminals from the
various users, and schedules the jobs submitted to the various compute
nodes.

The EOS systems use "modules" to handle the many different software
programs that have been installed for various users. For our purposes
(processing Sentinel-1 data), we need to load the correct module before
running any commands. This can be done by (for example, on Gekko as of
May 2019):

    $ module load gmtsar/5.6_gmt5.4.4
    $ module load python/3/intel/2018u3

Komodo and Gekko use the PBS system to schedule jobs submitted to
various "queues". The queues we typically use are named: q12, q16,q24,
and dque on Komodo, and q32 on Gekko. If you want to run a processing
job interactively, don't run it directly on the "Head Node" (the default
terminal you have logged into) -- that will cause a slowdown for all
users! First, you should start an interactive job: on Komodo,

    $ qsub --I

On Gekko, due to the resource-tracking system, you need to include your
Project ID also:

    $ qsub --I -P eos_ehill

Now we are logged in to one of the compute nodes via ssh; this functions
like a brand-new terminal session. Check that you change back to the
same directory you were working in, and load any necessary modules,
before running your command.

If you want to run the job in the background, use 'qsub'. You will need
to create a script that runs your desired command, and then put some
configuration options at the top. For Gekko, a simple script might look
like this:

    #!/bin/bash
    #PBS -N gmtsar_app
    #PBS -P eos_ehill
    #PBS -q q32
    #PBS -l walltime=120:00:00
    #PBS -l select=1:ncpus=32
    module load python/3/intel/2018u3
    module load gmtsar/5.6_gmt5.4.4
    python gmtsar_app.py batch.config >& $PBS_JOBID.log
    
Note, the hash (\#) is important here -- this is not a comment; the job scheduler (PBS) reads these lines as special commands.

To use only one cpu, you can use the following:

    #PBS -l nodes=1:ppn=1#shared


