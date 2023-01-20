import os
import geopandas as gpd
from pathlib import Path
import requests

from loguru import logger
from povertymapping.nightlights import make_report_hook, urlretrieve
from fastprogress.fastprogress import progress_bar
from urllib.parse import urlparse
GEOBOUNDARIES_REQUEST_URL = "https://www.geoboundaries.org/gbRequest.html?ISO={}&ADM={}"
# acknowledgement: https://www.geoboundaries.org/index.html#citation  
def get_geoboundaries(iso, adm='ADM0', dest=None, cache_dir='~/.geowrangler', overwrite=False,show_progress=True, chunksize=1024*1024):
    if type(cache_dir) == str:
        cache_dir = Path(os.path.expanduser(cache_dir))
    iso = iso.upper()
    adm = adm.upper()
    bounds_cache = cache_dir/'geoboundaries'
    bounds_cache.mkdir(parents=True,exist_ok=True)
    
    if dest is None:
        filename = bounds_cache / f'{iso}_{adm}.geojson'
    else:
        if type(dest) == str:
            dest = Path(dest)
            if dest.is_dir():
                filename = dest/f'{iso}_{adm}.geojson'
            else:
                dest.parent.mkdir(parents=True,exist_ok=True)
                filename = dest
    
    if filename.exists() and not overwrite:
        return filename
        # logger.info(f"Loading cached boundaries file {filename}") 
        # admin_bounds_gdf = gpd.read_file(filename)
        # return admin_bounds_gdf
    url = GEOBOUNDARIES_REQUEST_URL.format(iso, adm)
    logger.info(f"Downloading geoboundaries for {iso} at admin level {adm} at {url}")

    r = requests.get(url)
    respjson = r.json()
    if respjson is None or len(respjson) < 1 or 'gjDownloadURL' not in respjson[0]:
        raise ValueError(f'Invalid results returned from reqest {url} : response is {respjson}')

    dl_path = r.json()[0]["gjDownloadURL"]

    logger.info(f"Download path for {iso} at admin level {adm} found at {dl_path}")
    # Save the result as a GeoJSON
    # filename = "../data/geoboundary.geojson"
  
    reporthook = make_report_hook(show_progress)
    filename, _, _ = urlretrieve(dl_path, filename, reporthook=reporthook, chunksize=chunksize)
    return filename
    # admin_bounds_gdf = gpd.read_file(filename)
    # return admin_bounds_gdf

    # admin_bounds = requests.get(dl_path).json()
    # with open(filename, "w") as file:
    #     logger.info(f"Saving downloaded file to {filename}")
    #     json.dump(admin_bounds, file)

    # # Read data using GeoPandas
    # admin_bounds_gdf = gpd.read_file(filename)
    # return admin_bounds_gdf

from countryinfo import CountryInfo

COUNTRYINFO = CountryInfo()

def get_iso3(country):
    if str(country).lower() in COUNTRYINFO._CountryInfo__countries:
        country = COUNTRYINFO._CountryInfo__countries[country.lower()]
        if 'ISO' in country:
            iso = country['ISO']
            if 'alpha3' in iso:
                return iso['alpha3']
            else:
                raise ValueError(f'Incomplete data for {country}, no ISO3 code found')
        else:
            raise ValueError(f'Incomplete data for {country}, no ISO entries found')
    else:
        raise ValueError(f'No country data found for {country}')
