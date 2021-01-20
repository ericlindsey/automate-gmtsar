**Processing Sentinel InSAR data -- GMTSAR\_app workflow**

Eric Lindsey, last updated Jan 2021

Summary of steps

1.  Download data for a chosen track using sentinel\_query\_download.py

2.  Update the archive of orbits using update\_orb.sh (in orbit
    directories)

3.  Download a DEM (from <http://topex.ucsd.edu/gmtsar/demgen/>)

4.  Combine the frames to fit your desired latitude bounds using
    cat\_s1a.py

5.  Set up your processing directory with the DEM and links to the raw
    data using setup\_tops.sh

6.  Run gmtsar\_app.py on a single node with endstage = 3 to generate
    SLCs and radar geometry

7.  Run gmtsar\_app.py on several nodes with startstage = 4 and endstage
    = 4 without unwrapping

8.  QC and modify the interferogram list as needed -- remove badly
    correlated ones and add any missing connections. Decide on
    processing parameters, correlation masking method. Re-run step 7 as
    needed.

9.  Run gmtsar\_app stage 4 with proc\_stage = 3 and with unwrapping

10. QC the final interferograms, re-do steps as needed

A detailed description follows. Expected time duration of the steps:

1.  \~1 day

2.  \~10 minutes

3.  \~1 day

4.  \~30 minutes

5.  \~seconds

6.  \~1-4 hours

7.  \~1-4 hours

8.  Manually done. Hours to days

9.  \~ 1 day

10. Manual, hours to days

In the best case, the total run time is about 4 days, but the manual
interaction required is only a few hours over that period. In a
worst-case scenario, steps 8 and 10 may never converge to a satisfying
solution, leading the user to re-run the interferograms until the heat
death of the universe. Some steps can be run in parallel; e.g. all the
downloading steps (1-3) can be done at the same time.

**Preliminary: Notes on running jobs on the Komodo and Gekko clusters**

The Komodo and Gekko clusters are powerful computers comprised of
several dozen individual computers (nodes) each, and controlled by a
single "head node" which handles all the login terminals from the
various users, and schedules the jobs submitted to the various compute
nodes.

Both systems use "modules" to handle the many different software
programs that have been installed for various users. For our purposes
(processing Sentinel-1 data), we need to load the correct module before
running any commands. This can be done by (for example, on Gekko as of
May 2019):

\$ module load gmtsar/5.6\_gmt5.4.4

\$ module load python/3/intel/2018u3

Komodo and Gekko use the PBS system to schedule jobs submitted to
various "queues". The queues we typically use are named: q12, q16,q24,
and dque on Komodo, and q32 on Gekko. If you want to run a processing
job interactively, don't run it directly on the "Head Node" (the default
terminal you have logged into) -- that will cause a slowdown for all
users! First, you should start an interactive job: on Komodo,

\$ qsub --I

On Gekko, due to the resource-tracking system, you need to include your
Project ID also:

\$ qsub --I -P eos\_ehill

Now we are logged in to one of the compute nodes via ssh; this functions
like a brand-new terminal session. Check that you change back to the
same directory you were working in, and load any necessary modules,
before running your command.

If you want to run the job in the background, use 'qsub'. You will need
to create a script that runs your desired command, and then put some
configuration options at the top. For Gekko, a simple script might look
like this:

\#!/bin/bash

\#PBS -N gmtsar\_app

\#PBS -P eos\_ehill

\#PBS -q q32

\#PBS -l walltime=120:00:00

\#PBS -l select=1:ncpus=32

module load python/3/intel/2018u3

module load gmtsar/5.6\_gmt5.4.4

python gmtsar\_app.py batch.config \>& \$PBS\_JOBID.log

**1. Searching and downloading data using
'sentinel\_query\_download.py'**

**\
**This script uses the ASF Vertex web API to search for data archived at
ASF. Then it can automatically download that data from either the AWS
public dataset, or from ASF. It is general-purpose and can be used to
find any SAR data archived there, not just Sentinel.

The basic method is to first visit the ASF Vertex website
(<https://vertex.daac.asf.alaska.edu/>), and find the data you are
looking for visually. Then construct an API query config file that will
duplicate your GUI search, and then finally set the -download flag.

For example, let's say I want to download all the data from a descending
track over Singapore: First, I go to the website and create a search box
around the city (note that the box cannot be too small, or it sometimes
throws an error). I should make the box slightly taller in the
north-south direction than I really need, so that if any frames have
partial coverage we make sure to get their next consecutive frame as
well.

![](./media/image1.png){width="5.763888888888889in"
height="3.271349518810149in"}

From comparing the map to the panel on the right, I can determine that
the best descending path to use is 18, and I can verify that by
constraining the search to this path on the left side:

![](./media/image2.png){width="5.763888888888889in"
height="3.2751399825021874in"}

Now, construct the API query commands using a simple config file:

\[api\_search\]

platform = Sentinel-1A,Sentinel-1B

processingLevel = SLC

beamMode = IW

polygon = 103.5,0.77,104.17,0.77,104.17,1.95,103.5,1.95,103.5,0.77

relativeOrbit=18

Note that I just copied the polygon coordinates from the web GUI, after
drawing the box there -- this is the easiest way to generate this
polygon, though you can also type it manually if you prefer. There are
also many other options for search parameters, such as start and end
date:

start = 2017-12-01T00:00:00UTC

end = 2018-01-30T00:00:00UTC

These can be useful for finding data associated with an earthquake, for
example, or for updating the data for a track you already downloaded
earlier. A full list of commands and an interactive API search sandbox
can be found at <https://www.asf.alaska.edu/get-data/api/>.

Also, a warning: the frame numbers occasionally appear to be different
between the Vertex website and the API results. So, I do not recommend
using the frame number field in your query.

We run the query with the command:

\$ python3.5 sentinel\_query\_download.py asf\_query.config

This returns several hundred lines that are stored as a .csv, with a
header line like this:

\"Granule Name\",\"Platform\",\"Sensor\",\"Beam Mode\",\"Beam Mode
Description\",\"Orbit\",\"Path Number\",\"Frame Number\",\"Acquisition
Date\",\"Processing Date\",\"Processing Level\",\"Start Time\",\"End
Time\",\"Center Lat\",\"Center Lon\",\"Near Start Lat\",\"Near Start
Lon\",\"Far Start Lat\",\"Far Start Lon\",\"Near End Lat\",\"Near End
Lon\",\"Far End Lat\",\"Far End Lon\",\"Faraday Rotation\",\"Ascending
or Descending?\",\"URL\",\"Size (MB)\",\"Off Nadir Angle\",\"Stack
Size\",\"Baseline Perp.\",\"Doppler\"

(During this example, I also noticed that sometimes I do not get exactly
the same number of results with the API as with the GUI. I'm not sure
about the reason for this... the two methods may interpret the polygon
slightly differently, or perhaps the GUI is returning some non-IW/SLC
images? In any case, if our polygon is larger than the area we are
really interested in, it should be OK.)

Now, we should be ready to start the data download. We need to make sure
the config file has a few extra settings under the heading "download".
In this case, we set download\_site to 'both' to try AWS first, then
ASF. We can also set the script to run several downloads in parallel.
But note that running too many may slow down each one's progress!

\[download\]

download\_site = both

nproc = 2

If the data are coming from ASF, we also have to make sure that a valid
ASF username and password are included in the config file, under the
heading "asf\_download":

\[asf\_download\]

http-user =

http-password =

(Enter your own username and password here). The easiest way to run this
is just to run the python command with the option \--download. Note
though, that this will hang our terminal for many hours, and if we are
logged out for any reason, it will halt the download (but, wget enables
re-starting interrupted downloads, so this is not so bad). Another
option is to use the 'qsub' command to submit this to the cluster as an
independent job. On Gekko, this looks like:

\$ qsub
/home/share/insarscripts/download/sentinel\_query/sentinel\_query\_download.pbs
--v config=sentinel\_query.config -v download=true

Note the slightly different command-line argument structure: --v
var=value passes a variable name and value into the script when it is
run via PBS, the job scheduler. If you forget this option, the job will
start normally but finish right away with an error message. It pays to
check your job status (with 'qstat' or 'showq') after a few minutes to
see that the download actually started! The screen output of the job
will usually be stored in your working directory (the location where you
ran the script from), with a filename matching the job ID that you get
when submitting the job.

In this case, we have \~140 images which is about 600 GB of data. This
will take a variable amount of time, depending on where it is run:

\- From AWS, on Gekko's head node: \~2 hrs, \~1 min per scene

\- From AWS, on Gekko via qsub: \~23.5 hrs, \~10 min per scene

\- If downloading from ASF instead of AWS: \~35 hrs, 15 min per scene

So this will likely take overnight, or possibly longer. In one recent
case, each image took about 30 min to download. Running in parallel with
'nproc' may speed this up, but the optimal number of parallel downloads
to run has not been tested.

Finally, it should be noted that you can also generate a download script
directly from the Vertex website -- click 'add images to queue by type',
choose L1 SLC, then view the queue and click to generate a python
download script. You can run this directly, or edit it as needed. You
may need to do this sometimes to fill in images that were downloaded
with an error, as it is sometimes a little easier to add individual
images to the queue with the GUI.

Note that wget is very smart about not re-downloading existing files, so
you can simply re-run a duplicate query with no 'stop' date to get the
latest scenes.

We're done for now -- move on to the other downloading steps, and then
come back in the morning to check the results!

**\
**

**2. Updating orbits: using update\_orb.sh**

This is an easy step. We have to maintain a local archive of the
satellite orbit information, as it is not included in the raw data that
we downloaded above. Simply go to the following directory and run this
command:

\$ cd /home/data/INSAR/S1A/POD/s1qc.asf.alaska.edu

\$ ./update\_all\_orbits.sh

If this is run regularly, it should take just a few minutes to get the
latest orbit files.

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

S1A\_OPER\_AUX\_POEORB\_OPOD\_20141023T123724\_V20141001T225944\_20141003T005944.EOF

The first date is the production date, and the second two dates (after
the 'V') specify the range of validity.

Restituted orbits (RES) are generated rapidly, but have a slightly lower
accuracy. If we are using data acquired within the last 2 weeks, these
will be our only option. Their name format is similar, but the validity
range is much smaller, usually only a few hours:

S1B\_OPER\_AUX\_RESORB\_OPOD\_20180101T053144\_V20180101T011536\_20180101T043306.EOF

gmtsar\_app.py is able to read these file formats and tell which one is
the most recent and accurate version to use -- if both types are
available for a given scene, the precise orbit will be used.

**3. Downloading a DEM**

We need a high-resolution Digital Elevation Model (DEM) for our
processing. It has to be corrected to ellipsoid height (standard DEMs
are referenced to the geoid instead), and it needs to be in a
GMTSAR-readable format (GMT .grd file). The simplest way to get such a
file is to go to the GMTSAR website and create a custom DEM:
<http://topex.ucsd.edu/gmtsar/demgen/>. Select 'SRTM1' and enter a wide
lat/lon range that exceeds the size of your image (but not too far). For
example:

![](./media/image3.png){width="5.763888888888889in"
height="5.055087489063867in"}

Click 'generate' and then download the file when it is ready. Unzip the
tar file, and keep only the file 'dem.grd'. The rest can be discarded.
Upload this to komodo (eg. using scp) and place it with a descriptive
enclosing folder name (don't change the file name) under
/home/data/INSAR\_processing/dems.

Notes:

\- Be sure to select 'SRTM1'

\- Maximum size is 4x4 degrees. If you need a larger area, first
download several regions and then use 'grdblend' or 'grdpaste' to
combine them. The downloaded zip file contains a script that provides an
example of how to do this.**\
**

**3. Combining the frames: using cat\_s1a.py**

Now that you have downloaded the data from ASF, you have to unzip all
the files. This may take a few hours, depending how many images there
are. From the directory where the zip files are located, run:

\$ /home/share/insarscripts/unzip/run\_unzip\_s1a.sh \*zip

This will automatically submit a job to run the unzip command on each
file.

You may notice several images have been downloaded for each date, in
different directories beginning with F (e.g. F585, F590). The reason is
that our search polygon might have extended across several image
"frames" that break up the data into manageable file sizes along an
orbit, and the download script will automatically get both images.

Unfortunately, a frustrating fact of life with Sentinel data is that
there is no consistent frame boundary (although it has become more
consistent since 2017) so for our long-term processing, to get a
consistent image size we have to separate the individual 'bursts'
(sub-frames) and then generate our own self-consistent "frame" for InSAR
processing. This is done using cat\_s1a.py, which invokes the GMTSAR
command create\_frame\_tops.csh.

To get the list of command-line arguments for cat\_s1a.py, run

\$ python /home/share/insarscripts/automate/cat\_s1a.py \--help

usage: cat\_s1a.py \[-h\] -o ORBIT -l LONLAT -d DIRECTION

searchdirs \[searchdirs \...\]

Combine bursts from several Sentinel-1 scenes into a single frame, given
a

min/max lat. bound

positional arguments:

searchdirs List of directories (or wildcards) containing SAFE

files to be combined.

optional arguments:

-h, \--help show this help message and exit

-o ORBIT, \--orbit ORBIT

Path to a directory holding orbit files, required.

Repeat option to search multiple directories.

-l LONLAT, \--lonlat LONLAT

Lon/Lat pins for the crop script in the GMT R-argument

format lon1/lat1/lon2/lat2, required.

-d DIRECTION, \--direction DIRECTION

Orbit direction (A/D), required.

The lon/lat pins define the corners of a box we want to include in our
processing.

We should run this on the cluster, so we can create a PBS script to do
this. First, copy the example script (run\_cat\_s1.pbs) to our
processing directory. For example:

\$ mkdir -p
/home/data/INSAR\_processing/S1A/singapore\_testcase/cropped\_images

\$ cd
/home/data/INSAR\_processing/S1A/singapore\_testcase/cropped\_images

\$ cp /home/share/insarscripts/automate/run\_cat\_s1.pbs .

Now edit this file and change the line that defines 'code' to run the
command we need. In this particular case, we would set (note we set the
paths to the raw data, orbit files (once each for precise and
restituted), the lat/lon coordinates, and we set the direction 'A' to
denote this is an ascending track.):

code="python /home/share/insarscripts/automate/cat\_s1a.py
/home/data/INSAR/S1A/P018/F\* -o
/home/data/INSAR/S1A/POD/s1qc.asf.alaska.edu/aux\_poeorb -o
/home/data/INSAR/S1A/POD/s1qc.asf.alaska.edu/aux\_resorb -l
130.9/31.8/130.9/33.6 --d A"

(Note, this is all on one line!) This will take from minutes up a few
hours, depending on the number of scenes and the size of the area you
want to include. When it's finished, we should have a set of new,
cropped frames ready to use for processing!

**5. Setting up your processing directory**

This is a short step. GMTSAR expects the raw data and DEM to be in a
specific directory structure, with one directory for each subswath (F1,
F2, F3). You generally want to name your top directory something useful,
like the name of the path and your area. Then make two sub-folders:
topo/ and raw\_orig/:

\$ cd P156\_kumamoto

\$ ls

topo raw\_orig

Place your dem.grd file (do not re-name it!) from step 4 in the topo/
directory.

Under raw\_orig, link all the cropped .SAFE folders that you created in
step 3:

\$ cd raw\_orig

\$ ln --s /userdata/home/data/INSAR/S1A/kumamoto/P156/Fcrop/\*SAFE .

Now, run the command 'setup\_tops.csh' to create the subswath links:

\$ /home/share/insarscripts/automate/setup\_tops.csh

That's it! Ready for the next step.

**6. Generate SLCs and radar geometry using gmtsar\_app.py**

We have finally finished setting up the data, and now we are ready to
start processing. The first stage is to get the images into a format
that makes them ready to be interfered. We call these aligned and
pre-processsed images "SLC" for Single-Look-Complex. This is the full
resolution complex image, in radar coordinates, stored in a matrix that
has been precisely aligned to match a 'master' image. After this step,
interferometry is just complex multiplication.

First, copy 3 files from /home/share/insarscripts/automate:

\$ cp /home/share/insarscripts/automate/batch.config .

\$ cp /home/share/insarscripts/automate/runall.csh .

\$ cp /home/share/insarscripts/automate/run\_gmtsar\_app.pbs .

The first file, batch.config, contains the configuration parameters we
need to set up. For now, the important values to set correctly are:

sat\_name = S1

s1\_orbit\_dir =
/home/data/INSAR/S1A/POD/s1qc.asf.alaska.edu/aux\_poeorb/,/home/data/INSAR/S1A/POD/s1qc.asf.alaska.edu/aux\_resorb/

startstage = 1

endstage = 3

num\_processors = 1

(Note, the s1\_orbit\_dir entries should all be on one single long
line).

\* There is one other important parameter to set here, which is related
to a bug in GMTSAR:

shift\_topo = 0

The reason for this is that GMTSAR will not correctly create a shifted
topography file for Sentinel data, although this is a required step for
other satellites. By skipping this step, we use the timing information
directly to compute the radar topography, rather than a
cross-correlation.

The many other options in this file will be used later. Note that we set
num\_processors to 1 here because the preprocessing and alignment stages
do not run in parallel for Sentinel (they do for the other satellites).
For this reason, we also set the following two lines in
run\_gmtsar\_app.pbs:

\#PBS -l nodes=1:ppn=1\#shared

\#PBS -q q24

The hash (\#) is important here -- this is not a comment; the job
scheduler (PBS) actually reads them. If there are not enough q24 nodes
free, change 'q24' to q16 or q12, depending on which queue has more free
nodes.

Now, we can easily submit a job for all 3 subswaths using 'runall.csh':

\$ ./runall.csh

This will give us a message that 3 jobs have been submitted. This step
typically takes from 2 - 6 hours, depending on the number of scenes, but
could be longer.

**\
**

**7. Generate initial interferograms using gmtsar\_app.py**

If the last stage ran correctly, you should see a subdirectory 'SLC' in
each of the 3 subswath directories, containing an image (e.g.
'S1A20171210\_ALL\_F1.SLC'), a parameter file ('.PRM'), and an orbit
file ('.LED') for each of the radar acquisitions. (These will actually
be links to files in the raw/ directory, since GMTSAR expects to find
them under SLC/.)

There will also be several files in the topo/ directory for each
subswath, including 'trans.dat' -- this is the translation table between
radar and geographic coordinates that will be used to geocode our
interferograms.

If everything is there, we are ready to make some interferograms. Change
a few config parameters in our top-level batch.config file before
running:

startstage = 4

endstage = 4

max\_timespan = 48

intf\_min\_connectivity = 1

threshold\_snaphu = 0

If we want to check that our interferogram-generation settings are good,
we can run 'plot\_intf\_list.py' to generate the intf.in list and make a
figure showing the connectivity:

\$ python3.5 /home/share/insarscripts/automate/plot\_intf\_list.py
batch.config

Look at the file 'intfs.ps' using the command 'gs', or download the pdf
file to view on your computer. Then change your settings as necessary.

If we have a lot of interferograms to run, we might want to use more
than one processing node, so that we can use more than 24 processors. In
that case, copy 'run\_gmtsar\_app\_mpi.pbs' from the scripts directory
and then set:

\#PBS -l nodes=2:ppn=24

\#PBS -q q24

Notes:

\- Each interferogram always runs on only one processor. Here, we've set
it to use 48 processors (2\*24), so if we have less than 48
interferograms to run, this will run them all simultaneously.

\- If you want to use more than 1 node, you must use the MPI version of
the PBS job submitter script.

\- If you're running all 3 subswaths at the same time, this setting
would take 6 total nodes -- make sure there are enough nodes free, or
some of your jobs will have to wait in the queue.

Once everything is set, run gmtsar\_app.py for all subswaths:

\$ ./runall.csh

This will run just the interferogram stage (stage 4), in this case with
a maximum timespan of 48 days, and it will skip the unwrapping stage
(snaphu threshold set to zero). Each interferogram should take just
10-15 minutes to run.

Next, we will need to look at the interferograms, and decide on our
processing parameters. This is where art blends with science...

**\
**

**8. QC and modify the interferogram processing parameters**

We need to look at our interferograms, decide what went wrong (if
anything), and determine what we need to do to fix things. This part is
a little open-ended, but there are two basic steps that we should always
follow: inspecting the phase images for good coherence and accurate
processing, and inspecting the unwrapped images for unwrapping errors.

To look at a large number of images, the simplest option is to use the
program 'gthumb' which can view many image files at once. GMTSAR
automatically produces .png files of the geocoded, masked phase called
'phasefilt\_mask\_ll.png'. Thus, we can use:

\$ gthumb intf/\*/phasefilt\_mask\_ll.png

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
and use 'gv phasefilt.ps' to look at the unmasked image in radar
coordinates.

You can also use the program 'ncview' to look at the data files (.grd)
directly. For example, it may help to open up a correlation file and
look at the range of values in well-correlated and poorly-correlated
areas, to determine a better threshold to use.

Second, you should check all the unwrapped images to make sure there are
no unwrapping errors. Detecting an unwrapping error is somewhat
subjective (if it was easy, the computer wouldn't make any errors!) but
they are often obvious. Some examples are included below. If you find
any, there are a few options: you can increase the correlation threshold
to mask out more bad values, and re-run the processing to hopefully fix
the error, or you can simply delete that interferogram. As long as you

**\
**

**9. Generate final unwrapped interferograms using gmtsar\_app.py**

Once we have modified intf.in, decided on your correlation threshold and
filtering, and fixed any other bugs, we're ready to generate the final
unwrapped interferograms. We just need to set the following config
parameters in our top-level batch.config:

threshold\_snaphu = 0.1 (for example)

interp\_unwrap = 1

detrend\_unwrap = 0

topo\_assisted\_unwrapping = 0

Note that unwrapping will be skipped if threshold\_snaphu is zero. In
step 8 above, you should have tried some experiments to determine the
value you want to use for this parameter.

The other parameters are used to control how the unwrapping is done.

interp\_unwrap is used to greatly speed up unwrapping and should
generally always be set to 1, unless you are testing its functionality.
It will mask decorrelated areas and fill them with a nearest-neighbor
interpolation, which is required for preserving the wrapped phase
relationships between the coherent pixels that remain. This option
generally speeds unwrapping by a factor of 5 to 100.

detrend\_unwrap and topo\_assisted\_unwrapping are optional 2-stage
unwrapping options that slow the process down quite a bit (the image has
to be unwrapped twice) but can improve results if you are finding a lot
of unwrapping errors. detrend\_unwrap is particularly helpful for ALOS-2
data that often have big ramps, while topo\_assisted\_unwrapping is
useful for volcanoes or other areas that commonly have a large
tropospheric delay that is correlated with topography. If you find some
interferograms have unwrapping errors, you may wish to create a subset
of your intf.in list for images to run again with these options, but
it's a good idea to set them both to 0 for the first run.

Also, if you have already run all of the interferograms without
unwrapping and none of the filtering options have changed, you can save
some time in this step using

proc\_stage = 3

However, be careful with this option because it will cause GMTSAR to use
whatever 'phasefilt.grd' was in the intf directory to start the
unwrapping process, and will not check or re-create this file if any
other options have changed.

**\
**

**10. QC and modify the unwrapped interferograms**

As above, we need to look individually at our results and decide what
worked and what didn't.
