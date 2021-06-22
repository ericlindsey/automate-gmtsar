import sys,argparse
import s1_func

# auto-download of orbit files from ESA's Copernicus GNSS products API
# original credit to https://github.com/asjohnston-asf/s1qc-orbit-api/blob/master/src/main.py
# modified to work with new API by E. Lindsey, April 2021

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Find and download a Sentinel-1 Orbit file (Precise or Restituted) matching an input Granule file (SAFE or zip format)')
    parser.add_argument('granule',type=str,help='supply name of granule for which to find a matching orbit. Required. Example: S1A_IW_SLC__1SDV_20180810T224749_20180810T224816_023190_02850D_0C43.SAFE')
    parser.add_argument('-d','--dir',type=str,default='.',help='Directory to download the resulting scenes to (default: current directory)')
    parser.add_argument('-p','--precise',action='store_true',help='Precise orbit file only. (default: either precise or restituted, whichever is most recent)')
    args = parser.parse_args()

    granule = args.granule
    dest_folder = args.dir

    start_time = f'{granule[17:21]}-{granule[21:23]}-{granule[23:25]}T{granule[26:28]}:{granule[28:30]}:{granule[30:32]}'
    end_time = f'{granule[33:37]}-{granule[37:39]}-{granule[39:41]}T{granule[42:44]}:{granule[44:46]}:{granule[46:48]}'
    sat_ab=granule[2:3]

    orbit = s1_func.get_latest_orbit_copernicus_api(sat_ab,start_time,end_time, 'AUX_POEORB')
    if not orbit:
        if args.precise:
            print("Error: option --precise was set, but no precise orbit file found. Not trying restituted orbit search")
            sys.exit(1)
        else:
            orbit = s1_func.get_latest_orbit_copernicus_api(sat_ab,start_time,end_time, 'AUX_RESORB')
    print('Found orbit: ',orbit['name'], ' at ', orbit['remote_url'])
    eof_filename = s1_func.download_copernicus_orbit_file(dest_folder, orbit['remote_url'])
    print(f'Downloaded file: {eof_filename}')
