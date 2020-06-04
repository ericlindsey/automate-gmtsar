import requests
import json

# original credit to https://github.com/asjohnston-asf/s1qc-orbit-api/blob/master/src/main.py
# modified by E. Lindsey, May 2020

def get_orbit_esa_api(granule, orbit_type):
    platform = granule[0:3]
    start_time = f'{granule[17:21]}-{granule[21:23]}-{granule[23:25]}T{granule[26:28]}:{granule[28:30]}:{granule[30:32]}'
    end_time = f'{granule[33:37]}-{granule[37:39]}-{granule[39:41]}T{granule[42:44]}:{granule[44:46]}:{granule[46:48]}'

    params = {
        'product_type': orbit_type,
        'product_name__startswith': platform,
        'validity_start__lt': start_time,
        'validity_stop__gt': end_time,
        'ordering': '-creation_date',
        'page_size': '1',
    }

    response = requests.get(url='https://qc.sentinel1.eo.esa.int/api/v1/', params=params)
    response.raise_for_status()
    qc_data = response.json()

    orbit = None
    if qc_data['results']:
        orbit = qc_data['results'][0]
    return orbit

if __name__ == '__main__':
    granule = 'S1A_IW_SLC__1SDV_20180810T224749_20180810T224816_023190_02850D_0C43'
    orbit = get_orbit_esa_api(granule, 'AUX_POEORB')
    if not orbit:
        orbit = get_orbit_esa_api(granule, 'AUX_RESORB')
    print(orbit)
