#!/usr/bin/env python

### Import modules ###
#
import argparse
import os.path
import subprocess
import numpy as np
import scipy.interpolate
import grd_io

### Define functions ###
#
def nneigh_interp(x,y,z):
    mask=~np.isnan(z)
    datvalid=z[mask]
    xx, yy = np.meshgrid(x,y)
    xyvalid = np.vstack(( np.ravel(xx[mask]), np.ravel(yy[mask]) )).T
    interpr = scipy.interpolate.NearestNDInterpolator( xyvalid, datvalid )
    interpdata = interpr(xx,yy)
    return interpdata    

def plot_grid(data,title):
    datamasked=np.ma.masked_invalid(data)
    plt.figure()
    plt.pcolormesh(datamasked)
    plt.title(title)
    plt.colorbar()
    

### Command-line operation ###
#
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Use nearest neighbor interpolation to fill NaN values in a GMT grid file. ')
    parser.add_argument('infile',type=str,help='Input filename')
    parser.add_argument('-o','--outfile',type=str,default='',help='Output filename (default: adds _interp to end of input filename)')
    parser.add_argument('-p','--plots',action='store_true',help='Whether to plot pre- and post-interpolation results (defualt: False)')
    parser.add_argument('-l','--lonlat',action='store_true',help='Read lonlat values from grid instead of xy (defualt: False)')
    parser.add_argument('-c','--ncconvert',action='store_true',help='First use nccopy -k classic to convert to a NetCDF-3 readable file. If set to false, ensure your file is already NetCDF-3. (default: False)')
    args = parser.parse_args()

    print(args)

    if args.outfile=='':
        #get default output filename
        filebase,fileext=os.path.splitext(args.infile)
        args.outfile='%s_interp%s'%(filebase,fileext)
    
    if args.ncconvert:
        #convert to NetCDF-3 file type   
        subprocess.call('nccopy -k classic %s temp_nc3.grd'%args.infile, shell=True)
        datfile='temp_nc3.grd'
    else:
        datfile=args.infile

    if args.lonlat:
        grdnaming='lonlat'
    else:
        grdnaming='xy'
        
    #read input file
    x,y,z=grd_io.read_grd(datfile, naming=grdnaming)

    if args.ncconvert:
        #remove temporary NetCDF-3 file   
        os.remove('temp_nc3.grd')
        
    #do nearest neighbor interpolation
    interpdata=nneigh_interp(x,y,z)

    #write output file
    grd_io.write_grd(x,y,interpdata,args.outfile, naming=grdnaming)

    if args.plots:
        import matplotlib.pyplot as plt
        plot_grid(z,'input data')
        plot_grid(interpdata,'interpolated data')
        plt.show()
