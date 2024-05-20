from hdx.api.configuration import Configuration
from hdx.data.dataset import Dataset
from fastcore.all import L
from fastprogress.fastprogress import progress_bar
from urllib.parse import urlparse
from urllib.error import HTTPError

from typing import Union
from pathlib import Path

from loguru import logger
import geowrangler.raster_zonal_stats as rzs
import numpy as np
import pandas as pd
from povertymapping.nightlights import urlretrieve
from povertymapping.iso3 import get_iso3_code

import os
import re
import warnings
from zipfile import ZipFile

HDX_CONFIG = []


def init_hdx_config():
    if len(HDX_CONFIG) == 0:
        HDX_CONFIG.append(
            Configuration.create(
                hdx_site="prod", user_agent="Geowrangler", hdx_read_only=True
            )
        )


init_hdx_config()


def convert_dset(dset):
    return {k: v for k, v in dset.items()}


def get_hrsl_dataset(region):
    cname = region.lower().replace(" ", "-")  # For countries with space in name
    dataset_name = (
        f"{cname.lower()}-high-resolution-population-density-maps-demographic-estimates"
    )
    dataset = Dataset.read_from_hdx(dataset_name)
    return dataset


def get_hrsl_resources(region):
    dset = get_hrsl_dataset(region)
    if dset is None:
        return None
    resources = dset.get_resources()
    return resources


def convert_resources(resources):
    return L([convert_dset(res) for res in resources])


def search_dsets(search_term):
    dsets = Dataset.search_in_hdx(search_term)
    return L([convert_dset(dset) for dset in dsets]) if len(dsets) > 0 else L()


def make_hrsl_pattern(iso3, year, filetype, demographic):
    if year is None:
        year = "\d{4}"
    pat = f"{iso3}_{demographic}_{year}_{filetype}.zip"
    return pat


def is_hrsl_available(region, year=None, filetype="geotiff", demographic="general"):
    resources = get_hrsl_resources(region)
    if resources is None or len(resources) == 0:
        return False
    iso3 = get_iso3_code(region, code="alpha-3")
    if iso3 is None:
        warnings.warn(f"No iso3 code found for {region}")
        return False
    pattern = make_hrsl_pattern(iso3.lower(), year, filetype, demographic)
    reslist = convert_resources(resources)
    argwhere = reslist.argfirst(lambda o: re.search(pattern, o["name"]) is not None)
    return argwhere is not None


def get_hrsl_url(region, year=None, filetype="geotiff", demographic="general"):
    resources = get_hrsl_resources(region)
    if resources is None or len(resources) == 0:
        warnings.warn(f"Non resources found for {region}")
        return None
    iso3 = get_iso3_code(region, code="alpha-3")
    if iso3 is None:
        warnings.warn(f"No iso3 code found for {region}")
        return None
    pattern = make_hrsl_pattern(iso3.lower(), year, filetype, demographic)
    reslist = convert_resources(resources)
    argwhere = reslist.argfirst(lambda o: re.search(pattern, o["name"]) is not None)
    if argwhere is None:
        warnings.warn(f"No hrsl resource found for {pattern}")
        return None
    res = reslist[argwhere]
    if "download_url" in res:
        return res["download_url"]
    elif "url" in res:
        return res["url"]
    else:
        resname = res["name"]
        warnings.warn(f"No url attribute in resource for {resname}")
        return None


DEFAULT_CACHE_DIR = "~/.cache/geowrangler"


def download_hrsl(
    region,
    year=None,
    filetype="geotiff",
    demographic="general",
    cache_dir=DEFAULT_CACHE_DIR,
    use_cache=True,
    show_progress=True,
    chunksize=1024 * 1024,
) -> Union[Path, None]:
    """Download hrsl file to path"""
    directory = Path(os.path.expanduser(cache_dir)) / "hrsl"
    directory.mkdir(parents=True, exist_ok=True)

    url = get_hrsl_url(region, year=year, filetype=filetype, demographic=demographic)

    if url is None:
        raise ValueError(
            f"hrsl url not found for {region} {year} {demographic} {filetype}."
        )

    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    filepath = directory / filename
    if filepath.exists() and use_cache:
        return filepath

    reporthook = None
    if show_progress:
        pbar = progress_bar([])

        def progress(count=1, bsize=1, tsize=None):
            pbar.total = tsize
            pbar.update(count * bsize)

        reporthook = progress

    try:
        filepath, _, _ = urlretrieve(
            url, filepath, reporthook=reporthook, chunksize=chunksize
        )
    except HTTPError as err:
        if err.code == 404:
            if year is not None:
                logger.warning(
                    f"No data found for year {year} in region {region} : {url}"
                )
            else:
                logger.warning(f"No url found for region {region} : {url} ")
            return None
        else:
            raise err

    return filepath


def get_unzipped_hrslfile(
    region,
    year=None,
    filetype="geotiff",
    demographic="general",
    cache_dir=DEFAULT_CACHE_DIR,
):
    url = get_hrsl_url(region, year=year, filetype=filetype, demographic=demographic)
    if type(cache_dir) == str:
        cache_dir = Path(os.path.expanduser(cache_dir)) / "hrsl"
    zipfile_path = Path(url)
    ext = ".tif" if filetype == "geotiff" else ".csv"
    unzipped_name = zipfile_path.stem.replace("_" + filetype, "") + ext
    unzipfile = cache_dir / unzipped_name
    return unzipfile


def get_hrsl_file(
    region,
    year=None,
    filetype="geotiff",
    demographic="general",
    cache_dir=DEFAULT_CACHE_DIR,
    use_cache=True,
    show_progress=True,
    chunksize=1024 * 1024,
):
    unzipped_hrslfile = get_unzipped_hrslfile(
        region,
        year=year,
        filetype=filetype,
        demographic=demographic,
        cache_dir=cache_dir,
    )

    if unzipped_hrslfile.exists() and use_cache:
        return unzipped_hrslfile

    zipfile_path = download_hrsl(
        region,
        year=year,
        filetype=filetype,
        demographic=demographic,
        cache_dir=cache_dir,
        use_cache=use_cache,
        show_progress=show_progress,
        chunksize=chunksize,
    )

    if zipfile_path is None:
        return None
        # Unzip the zip file
    logger.info(f"HRSL Data: Unzipping the zip file {zipfile_path}...")
    with ZipFile(zipfile_path, "r") as zip_object:
        unzipped_hrslfile.parent.mkdir(parents=True, exist_ok=True)
        zip_object.extractall(unzipped_hrslfile.parent)

    if not unzipped_hrslfile.exists():
        raise ValueError(
            f"Something went wrong in unzipping {zipfile_path}, {unzipped_hrslfile} not created"
        )

    zipfile_path.unlink()

    logger.info(
        f"HRSL Data: Successfully downloaded and cached for {region} at {zipfile_path}!"
    )

    return unzipped_hrslfile


def generate_hrsl_features(
    aoi: pd.DataFrame,
    region: str,
    extra_args: dict = None,
) -> pd.DataFrame:
    """
    Append HRSL population from HDX to existing DataFrame

    Args:
        aoi (pandas DataFrame): The input AOI dataframe.
        region (str): Country/territory ISO3 region name (see iso3.get_region_name()).
        extra_args (dict, optional): Additional arguments to raster zonal stats (see geowrangler.raster_zonal_stats). Defaults to dict(nodata=np.nan).

    Returns:
        aoi (pd.DataFrame): The AOI dataframe with its new features.
    """
    if extra_args is None:
        extra_args = dict(nodata=np.nan)

    hrsl_pop_file = get_hrsl_file(region)

    aoi = rzs.create_raster_zonal_stats(
        aoi,
        hrsl_pop_file,
        aggregation=dict(output="population_density", func="mean"),
        extra_args=extra_args,
    )

    return aoi