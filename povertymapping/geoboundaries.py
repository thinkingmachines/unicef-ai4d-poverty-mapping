

import os
import geopandas as gpd
from pathlib import Path
import requests

from loguru import logger
import warnings
from povertymapping.nightlights import urlretrieve
from fastprogress.fastprogress import progress_bar
from povertymapping.iso3 import is_valid_country_name, get_iso3_code


DEFAULT_CACHE_DIR = '~/.cache/geowrangler'
GEOBOUNDARIES_REQUEST_URL = "https://www.geoboundaries.org/gbRequest.html?ISO={}&ADM={}"
# TODO: cite acknowledgement: https://www.geoboundaries.org/index.html#citation
#   
def get_geoboundaries(region, adm='ADM0', dest=None, cache_dir=DEFAULT_CACHE_DIR, overwrite=False, show_progress=True, chunksize=8192):
    if type(cache_dir) == str:
        cache_dir = Path(os.path.expanduser(cache_dir))

    if is_valid_country_name(region):
        iso = get_iso3_code(region, code = 'alpha-3').upper()
    else:
        warnings.warn(f'Invalid country name. Head to https://www.iso.org/iso-3166-country-codes.html to check the correct country name.')
        return None
    adm = adm.upper()
    
    if dest is None:
        bounds_cache = cache_dir/'geoboundaries'
        bounds_cache.mkdir(parents=True,exist_ok=True)

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
    url = GEOBOUNDARIES_REQUEST_URL.format(iso, adm)
    logger.info(f"Downloading geoboundaries for {iso} at admin level {adm} at {url}")

    r = requests.get(url)
    respjson = r.json()
    if respjson is None or len(respjson) < 1 or 'gjDownloadURL' not in respjson[0]:
        raise ValueError(f'Invalid results returned from reqest {url} : response is {respjson}')

    dl_path = respjson[0]["gjDownloadURL"]

    logger.info(f"Download path for {iso} at admin level {adm} found at {dl_path}")

    reporthook = None
    if show_progress:
        pbar = progress_bar([])
        def progress(count=1, bsize=1, tsize=None):
            pbar.total = tsize
            pbar.update(count * bsize)

        reporthook = progress

    filename, _, _ = urlretrieve(dl_path, filename, reporthook=reporthook, chunksize=chunksize)
    return filename
