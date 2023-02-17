

import os
import geopandas as gpd
from pathlib import Path
import requests

from loguru import logger
from povertymapping.nightlights import urlretrieve
from povertymapping.iso3 import get_iso3_code
from fastprogress.fastprogress import progress_bar

DEFAULT_CACHE_DIR = '~/.cache/geowrangler'
GEOBOUNDARIES_REQUEST_URL = "https://www.geoboundaries.org/gbRequest.html?ISO={}&ADM={}"
# TODO: cite acknowledgement: https://www.geoboundaries.org/index.html#citation
#   
def get_geoboundaries(region, adm='ADM0', dest=None, cache_dir=DEFAULT_CACHE_DIR, use_cache=True, show_progress=True, chunksize=8192):
    if type(cache_dir) == str:
        cache_dir = Path(os.path.expanduser(cache_dir))

    iso = get_iso3_code(region.lower())
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
    
    if filename.exists() and use_cache:
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
