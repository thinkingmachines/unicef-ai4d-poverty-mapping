import requests
import json
import os
from fastprogress.fastprogress import progress_bar
import gzip
import geowrangler.raster_process as rp
import geowrangler.raster_zonal_stats as rzs
from shapely.geometry import box
from pathlib import Path
import shutil
import json, contextlib
import hashlib
import numpy as np

from urllib.error import HTTPError, ContentTooShortError
from fastcore.net import urlopen, urldest

DEFAULT_EOG_CREDS_PATH = "~/.eog_creds/eog_access_token" 
EOG_ENV_VAR = "EOG_ACCESS_TOKEN"
NIGHTLIGHTS_CACHE_DIR = "~/.geowrangler/nightlights"
# Retrieve access token
def get_eog_access_token(
    username,
    password,
    save_token=False,
    save_path=DEFAULT_EOG_CREDS_PATH,
    set_env=True,
    env_token_var=EOG_ENV_VAR,
):
    params = {
        "client_id": "eogdata_oidc",
        "client_secret": "2677ad81-521b-4869-8480-6d05b9e57d48",
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    token_url = (
        "https://eogauth.mines.edu/auth/realms/master/protocol/openid-connect/token"
    )
    response = requests.post(token_url, data=params)
    access_token_dict = json.loads(response.text)
    access_token = access_token_dict.get("access_token")

    if save_token:
        save_path = Path(os.path.expanduser(save_path))
        if not save_path.parent.exists():
            save_path.parent.mkdir(mode=510, parents=True, exist_ok=True)
        with open(save_path, "w") as f:
            f.write(access_token)
    if set_env:
        os.environ[env_token_var] = access_token

    return access_token


def clear_eog_access_token(
    save_file=DEFAULT_EOG_CREDS_PATH,
    env_var=EOG_ENV_VAR,
    clear_file=True,
    clear_env=True,
):
    save_path = Path(os.path.expanduser(save_file))
    if clear_file:
        if save_path.exists():
            save_path.unlink()
    if clear_env:
        os.environ[env_var] = ""


# from https://github.com/fastai/fastcore/blob/86337bad16a65f23c5335286ab73cd4d6425c586/fastcore/net.py#L147
# add headers to urlwrap call (to allow auth)
def urlretrieve(
    url, filename, headers=None, reporthook=None, timeout=None, chunksize=8192
):
    "Same as `urllib.request.urlretrieve` but also works with `Request` objects"
    with contextlib.closing(
        urlopen(url, data=None, headers=headers, timeout=timeout)
    ) as fp:
        respheaders = fp.info()

        with open(filename, "wb") as tfp:
            size = -1
            read = 0
            blocknum = 0
            if "Content-length" in respheaders:
                size = int(respheaders["Content-Length"])
                if size < chunksize:
                    chunksize = size
            if reporthook:
                reporthook(blocknum, chunksize, size)
            while True:
                block = fp.read(chunksize)
                if not block:
                    break
                read += len(block)
                tfp.write(block)
                blocknum += 1
                if reporthook:
                    reporthook(blocknum, chunksize, size)

    if size >= 0 and read < size:
        raise ContentTooShortError(
            f"retrieval incomplete: got only {read} out of {size} bytes", respheaders
        )
    return filename, respheaders, fp


def download_url(
    url,
    dest=None,
    access_token=None,
    headers=None,
    timeout=None,
    show_progress=True,
    chunksize=1024*1024,
    env_var=EOG_ENV_VAR,
    creds_file=DEFAULT_EOG_CREDS_PATH,
):
    "Download `url` to `dest` and show progress"
    if show_progress:
        pbar = progress_bar([])

        def progress(count=1, bsize=1, tsize=None):
            pbar.total = tsize
            pbar.update(count * bsize)

        reporthook = progress
    else:
        reporthook = None

    if access_token is None:
        # try getting it from environ
        if (
            os.environ.get(env_var, None) is not None
            and len(os.environ.get(env_var)) > 0
        ):
            access_token = os.environ.get(env_var)
        else:
            save_path = Path(os.path.expanduser(creds_file))
            if save_path.exists():
                with open(save_path) as f:
                    access_token = f.read()

    if access_token:
        auth = "Bearer " + access_token
        if headers:
            headers.update(dict(Authorization=auth))
        else:
            headers = dict(Authorization=auth)

    dest = urldest(url, dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    nm, resp, fp = urlretrieve(
        url,
        filename=dest,
        headers=headers,
        reporthook=reporthook,
        timeout=timeout,
        chunksize=chunksize,
    )
    if "Cache-Control" in resp and "must-revalidate" in resp["Cache-Control"]:
        raise HTTPError(
            url,
            401,
            "No access token or invalid access token provided, please call `get_eog_access_token` to get one",
            resp,
            fp,
        )
    return nm

def unzip_eog_gzip(gz_file, dest=None, delete_src=False):
    
    if gz_file is None:
        raise ValueError('gz_file cannot be empty')
        
    if type(gz_file) == str:
        gz_file = Path(gz_file)
        
    if not gz_file.exists():
        raise ValueError(f'gzip file {gz_file} does not exist!')
        
    if gz_file.is_dir():
        raise ValueError(f'gzip file {gz_file} is a directory')
                         
    if dest is None:
        output_file = gz_file.parent/gz_file.stem
    else:
        if type(dest) == str:
            dest = Path(dest)
            
        if dest.is_dir():
            output_file = dest/gz_file.stem
        else:
            output_file = dest
        
    with gzip.open(gz_file,'rb') as f_in: 
        with open(output_file,'wb') as f_out:
            # TODO implement https://stackoverflow.com/questions/29967487/get-progress-back-from-shutil-file-copy-thread to add progress callback
            shutil.copyfileobj(f_in, f_out)

    if delete_src:
        if not output_file.exists():
            raise ValueError("Something went wrong with creating the output file, source file not deleted")
        gz_file.unlink()

    return output_file


def get_bounding_polygon(bounds, buffer=None):
    if buffer is None:
        return box(*bounds)
    return box(*bounds).buffer(buffer)
    
def clip_raster(input_raster_file,
                dest,
                bounds,
                buffer=None):
    bounds_poly = get_bounding_polygon(bounds,buffer=buffer)            
    rp.query_window_by_polygon(input_raster_file, dest,bounds_poly)
    return Path(dest)

def make_url(year, viirs_data_type = 'average', ntlights_base_url = 'https://eogdata.mines.edu/nighttime_light',version = 'v21', product = 'annual',coverage = 'global'):
    url_format = f'{ntlights_base_url}/{product}/{version}/{year}/VNL_{version}_npp_{year}_{coverage}_vcmslcfg_c202205302300.{viirs_data_type}.dat.tif.gz'
    return url_format

def make_clip_hash(year, bounds, viirs_data_type='average', version='v21', product='annual', coverage='global'):
    # Generate hash from aoi, type_, and year, which will act as a hash key for the cache     
    data_tuple = (
        np.array2string(bounds),
        str(year),
        viirs_data_type,
        version,
        product,
        coverage
    )
    m = hashlib.md5()
    for item in data_tuple:
        m.update(item.encode())
    data_key = m.hexdigest()
    return data_key

def generate_clipped_raster(year, bounds, dest, viirs_data_type='average', version='v21', product='annual', coverage='global', cache_dir=NIGHTLIGHTS_CACHE_DIR):
    viirs_cache_dir = Path(os.path.expanduser(cache_dir))/'global'
    viirs_url = make_url(year,viirs_data_type=viirs_data_type,version=version,product=product,coverage=coverage)
    viirs_zipped_filename = viirs_url.split('/')[-1]
    viirs_unzip_filename = ".".join(viirs_zipped_filename.split(".")[:-1])
    viirs_unzip_file = viirs_cache_dir/viirs_unzip_filename
    if not viirs_unzip_file.exists():
        # create viirs_cache if not exist
        viirs_cache_dir.parent.mkdir(parents=True,exist_ok=True)
        # download viirs file and unzip
        viirs_zip_file = download_url(viirs_url,dest=viirs_cache_dir)
        viirs_unzip_file = unzip_eog_gzip(viirs_zip_file,dest=viirs_cache_dir,delete_src=True)
    clipped_raster = clip_raster(viirs_unzip_file.as_posix(),dest.as_posix(), bounds, buffer=0.1)
    return clipped_raster
    

def get_clipped_raster(year, bounds, viirs_data_type='average', version='v21', product='annual', coverage='global', cache_dir=NIGHTLIGHTS_CACHE_DIR):
    key = make_clip_hash(year,bounds, viirs_data_type,version,product,coverage)
    clip_cache_dir = Path(os.path.expanduser(cache_dir))/'clip'
    clipped_file = clip_cache_dir/f'{key}.tif'
    if clipped_file.exists():
        return clipped_file
    # create clip cache dir if not exist
    clipped_file.parent.mkdir(parents=True,exist_ok=True)
    # generate clipped raster
    clipped_file = generate_clipped_raster(year,bounds,clipped_file, viirs_data_type=viirs_data_type,version=version,product=product,coverage=coverage)
    return clipped_file
    

def generate_nightlights_feature(aoi, year,viirs_data_type='average', version='v21', product='annual', coverage='global', cache_dir=NIGHTLIGHTS_CACHE_DIR):
    clipped_raster_file = get_clipped_raster(year, aoi.total_bounds, viirs_data_type=viirs_data_type,version=version,product=product,coverage=coverage, cache_dir=cache_dir) 
    aoi = rzs.create_raster_zonal_stats(
        aoi,
        clipped_raster_file.as_posix(),
        aggregation=dict(
            # func=["min", "max", "mean", "median", "kurtosis", "var"],
            func=["min", "max", "mean", "median", "std"],
            column="avg_rad",
        ),
        extra_args=dict(band_num=1, nodata=-999),
    )
    return aoi

