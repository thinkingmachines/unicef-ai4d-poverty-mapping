from povertymapping.geoboundaries import get_geoboundaries
from povertymapping.hdx import get_hdx_file
from geowrangler.grids import BingTileGridGenerator
import geowrangler.spatialjoin_highest_intersection as sjhi
import geowrangler.raster_zonal_stats as rzs
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
import os
from loguru import logger
import fastcore.all as fc

DEFAULT_ADMIN_LVL = 'ADM2'
DEFAULT_QUADKEY_LVL = 14
DEFAULT_CACHE_DIR = '~/.cache/geowrangler'

def parallel_zonal_stats(batch_item):
    batch, hdx_pop_file, aggregation, extra_args = batch_item
    result = rzs.create_raster_zonal_stats(batch, hdx_pop_file, aggregation=aggregation, extra_args=extra_args)
    return result

def compute_parallel_raster_zonal_stats(batch, hdx_pop_file, aggregation, extra_args, n_workers):
    batch_items = [(item.copy().reset_index(drop=True), hdx_pop_file, aggregation, extra_args) for item in np.array_split(batch, n_workers)]
    results = fc.parallel(parallel_zonal_stats, batch_items, n_workers=n_workers, threadpool=True, progress=True)
    logger.info(f'Completed parallel raster zonal stats for {len(results)} threads')
    result = pd.concat(results, ignore_index=True)
    logger.info(f'Concatenated parallel raster zonal stats for {len(results)} threads')
    result =  gpd.GeoDataFrame(result, geometry='geometry', crs=batch.crs)
    return result

def compute_raster_stats(admin_grids_gdf, 
                         hdx_pop_file,
                         aggregation=dict(column='population', output='pop_count', func='sum'),
                         extra_args=dict(nodata=np.nan),
                         max_batch_size=None,
                         n_workers=None):
    "Compute raster stats"
    fsize = hdx_pop_file.stat().st_size
    grid_count = len(admin_grids_gdf)
    if max_batch_size is None and n_workers is None:
        logger.info(f'Creating raster zonal stats for {grid_count} grids for file size {fsize}')
        return rzs.create_raster_zonal_stats(admin_grids_gdf, hdx_pop_file, aggregation=aggregation, extra_args=extra_args)
    logger.info(f'Batching call to create raster_zonal stats for {grid_count} grids for file size {fsize}')
    grid_count = len(admin_grids_gdf)
    n_splits = grid_count // max_batch_size if max_batch_size < grid_count else 1
    grid_batches = [item.copy().reset_index(drop=True) for item in np.array_split(admin_grids_gdf, n_splits)]
    logger.info(f'Created {len(grid_batches)} for {n_splits} splits of {max_batch_size}')
    grid_results = []
    for i, batch in enumerate(grid_batches):
        if n_workers is None:
            logger.info(f'Creating raster zonal stats for batch {i} with index ({batch.index.min()}/{batch.index.max()}')
            batch_result = rzs.create_raster_zonal_stats(batch, hdx_pop_file, aggregation=aggregation, extra_args=extra_args)
        else:
            logger.info(f'Creating raster zonal stats for batch {i} with index ({batch.index.min()}/{batch.index.max()} in {n_workers} parallel threads')
            batch_result = compute_parallel_raster_zonal_stats(batch, hdx_pop_file, aggregation=aggregation, extra_args=extra_args, n_workers=n_workers)
        grid_results.append(batch_result)
    logger.info(f'Completed raster zonal stats for {len(grid_batches)} batches')
    result_grid = pd.concat(grid_results, ignore_index=True)
    logger.info(f'Concatenated raster zonal stats for {len(grid_batches)} batches')
    result_grid = gpd.GeoDataFrame(result_grid, geometry='geometry', crs=admin_grids_gdf.crs)
    return result_grid


def get_region_filtered_bingtile_grids(region: str,
                              admin_lvl = DEFAULT_ADMIN_LVL ,
                              quadkey_lvl = DEFAULT_QUADKEY_LVL,
                              use_cache=True,
                              cache_dir=DEFAULT_CACHE_DIR,
                              filter_population=True,
                              assign_grid_admin_area=True,
                              metric_crs='epsg:3857',
                              extra_args=dict(nodata=np.nan),
                              max_batch_size=None,
                              n_workers=None

) -> gpd.GeoDataFrame:
    """
    Get a geodataframe consisting of bing tile grids for a region/country at a quadkey level.
    By default, the grids are filtered by population
    Arguments:
       region: (required) the country/region for which grids will be created
       admin_lvl: (default: ADM2) the administrative level boundaries used for assigning the grids
       quadkey_lvl: (default: 14) the bingtile grid size zoom level 
       use_cache: (default: True) whether to use a cached version or overwrite existing file
       cache_dir: (default: '~/.cache/geowrangler') directory where grids geojson will be created
       filter_population: (default: True) - whether to filter out grids with zero population counts
       assign_grid_admin_area: (default: True) whether to merge the admin level area data to the grids data
       metric_crs: (default: 'epsg:3857') - CRS to use for assigning for admin areas
       extra_args: (default: dict(nodata=np.nan)) - extra arguments passed to raster zonal stats computing
       max_batch_size: (default:None) - set batch size to limit memory used for raster zonal stats
       n_workers: (default:None) - set number of workers to parallelize raster zonal stats computation per batch
    """
    directory = Path(os.path.expanduser(cache_dir))/'quadkey_grids'
    directory.mkdir(parents=True,exist_ok=True)
    
    if filter_population:
        admin_grids_file = directory/f'{region}_{quadkey_lvl}_populated_admin_grids.geojson'
    else: 
        admin_grids_file = directory/f'{region}_{quadkey_lvl}_admin_grids.geojson'
    
    if admin_grids_file.exists() and use_cache:
        logger.info(f'Loading cached grids file {admin_grids_file}')
        admin_grids_gdf = gpd.read_file(admin_grids_file)
        return admin_grids_gdf
                    
    if not admin_grids_file.exists():
        logger.info(f'No cached grids file found. Generating grids file :{admin_grids_file}')
    else:
        logger.info(f'Regenerating grids file {admin_grids_file}')
        
    logger.debug(f'Loading boundaries for region {region} and admin level {admin_lvl}')
    admin_area_file = get_geoboundaries(region, adm=admin_lvl); 
    admin_gdf = gpd.read_file(admin_area_file)

    logger.info(f'Generating grids for region {region} and admin level {admin_lvl} at quadkey level {quadkey_lvl}')
    grid_gen = BingTileGridGenerator(quadkey_lvl)
    admin_grids_gdf = grid_gen.generate_grid_join(admin_gdf)
    grid_count = len(admin_grids_gdf)
    logger.info(f'Generated {grid_count} grids for region {region} and admin level {admin_lvl} at quadkey level {quadkey_lvl}')

    # use a metric crs (e.g. epsg:3857) for computing overlaps
    if assign_grid_admin_area:
        logger.info(f'Assigning grids to admin areas using metric crs {metric_crs}')
        admin_grids_gdf = sjhi.get_highest_intersection(admin_grids_gdf, admin_gdf,metric_crs)

    if filter_population:
        logger.info(f'Getting {region} population data for filtering grids')
        hdx_pop_file = get_hdx_file(region)
        logger.info('Computing population zonal stats per grid')
        admin_grids_gdf = compute_raster_stats(admin_grids_gdf, hdx_pop_file,
                                                 aggregation=dict(column='population',
                                                                   output='pop_count',
                                                                   func='sum'),
                                                 extra_args=extra_args,
                                                 max_batch_size=max_batch_size,
                                                 n_workers=n_workers)
        
        
        logger.info('Filtering unpopulated grids based on population data')
        admin_grids_gdf = admin_grids_gdf[admin_grids_gdf['pop_count'] > 0]
        filtered_grid_count = len(admin_grids_gdf)
        logger.info(f'Filtered admin grid count: {filtered_grid_count}')
        
    admin_grids_gdf.to_file(admin_grids_file, driver='GeoJSON')
    return admin_grids_gdf