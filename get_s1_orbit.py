import requests,cgi,json,os,sys,argparse
from xml.etree import ElementTree

# auto-download of orbit files from ESA's Copernicus GNSS products API
# original credit to https://github.com/asjohnston-asf/s1qc-orbit-api/blob/master/src/main.py
# modified to work with new API by E. Lindsey, April 2021

def get_orbit_copernicus_api(granule, orbit_type):
    # use the new Copernicus GNSS data hub API to find an orbit file
    # Updated by E. Lindsey, April 2021
    
    # some hard-coded URLs to make the API work
    scihub_url='https://scihub.copernicus.eu/gnss/odata/v1/Products'
    # these are from the namespaces of the XML file returned in the query. Hopefully not subject to change?
    w3_url='{http://www.w3.org/2005/Atom}'
    m_url='{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}'
    d_url='{http://schemas.microsoft.com/ado/2007/08/dataservices}'

    start_time = f'{granule[17:21]}-{granule[21:23]}-{granule[23:25]}T{granule[26:28]}:{granule[28:30]}:{granule[30:32]}'
    end_time = f'{granule[33:37]}-{granule[37:39]}-{granule[39:41]}T{granule[42:44]}:{granule[44:46]}:{granule[46:48]}'
    platform = granule[0:3]

    filterstring = "startswith(Name,'%s') and substringof('%s',Name) and ContentDate/Start lt datetime'%s' and ContentDate/End gt datetime'%s'"%(platform,orbit_type,start_time,end_time)
    params = { '$top': 1, '$orderby': 'ContentDate/Start asc', '$filter': filterstring }
    search_response = requests.get(url=scihub_url, params=params, auth=('gnssguest','gnssguest'))
    search_response.raise_for_status()

    # parse XML tree from response
    tree = ElementTree.fromstring(search_response.content)
    
    #extract w3.org URL that gets inserted into all sub-element names for some reason
    w3url=tree.tag.split('feed')[0]
    
    # extract the product's hash-value ID
    product_ID=tree.findtext(f'.//{w3_url}entry/{m_url}properties/{d_url}Id')
    product_url = f"{scihub_url}('{product_ID}')/$value"
    product_name=tree.findtext(f'./{w3url}entry/{w3url}title')

    # return the orbit name, type, and download URL
    if product_ID is not None:
        orbit={'name':product_name, 'orbit_type':orbit_type, 'remote_url':product_url}
    else:
        orbit=None
    return orbit

def download_copernicus_orbit_file(dest_folder,remote_url):
    """
    Download orbit file returned by the Copernicus GNSS products API.  Inputs: destination folder (absolute or relative path) and the remote URL, with a format like: https://scihub.copernicus.eu/gnss/odata/v1/Products('3a773f7a-0602-44e4-b4c0-609b7f4291f0')/$value
    Returns the absolute path of the saved file.
    """
    # created by E. Lindsey, April 2021

    # check that the output folder exists
    os.makedirs(dest_folder, exist_ok = True)

    # download the orbit file
    dl_response = requests.get(url=remote_url, auth=('gnssguest','gnssguest'))

    # find the filename in the header
    header = dl_response.headers['content-disposition']
    header_value, header_params = cgi.parse_header(header)

    #compose the full filename
    eof_filename = os.path.abspath(os.path.join(dest_folder,header_params['filename']))

    # save the file with the correct filename
    open(eof_filename, 'wb').write(dl_response.content)

    return eof_filename

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Find and download a Sentinel-1 Orbit file (Precise or Restituted) matching an input Granule file (SAFE or zip format)')
    parser.add_argument('granule',type=str,help='supply name of granule for which to find a matching orbit. Required. Example: S1A_IW_SLC__1SDV_20180810T224749_20180810T224816_023190_02850D_0C43.SAFE')
    parser.add_argument('-d','--dir',type=str,default='.',help='Directory to download the resulting scenes to (default: current directory)')
    parser.add_argument('-p','--precise',action='store_true',help='Precise orbit file only. (default: either precise or restituted, whichever is most recent)')
    args = parser.parse_args()

    granule = args.granule
    dest_folder = args.dir
    orbit = get_orbit_copernicus_api(granule, 'AUX_POEORB')
    if not orbit:
        if args.precise:
            print("Error: option --precise was set, but no precise orbit file found. Not trying restituted orbit search")
            sys.exit(1)
        else:
            orbit = get_orbit_copernicus_api(granule, 'AUX_RESORB')
    print('Found orbit: ',orbit['name'], ' at ', orbit['remote_url'])
    eof_filename = download_copernicus_orbit_file(dest_folder, orbit['remote_url'])
    print(f'Downloaded file: {eof_filename}')
