import os
import shutil
from pathlib import Path
from zipfile import ZipFile

import geopandas as gpd
from geowrangler import distance_zonal_stats as dzs
from geowrangler import vector_zonal_stats as vzs
from geowrangler.datasets import geofabrik
from loguru import logger

DEFAULT_POI_TYPES = ["restaurant", "school", "bank", "supermarket", "mall", "atm"]


def add_osm_features(
    aoi,
    country,
    cache_dir,
    poi_types=DEFAULT_POI_TYPES,
    metric_crs="epsg:3123",
    inplace=False,
    force_overwrite=False,
):
    """Generates features for the AOI based on OSM data (POIs, roads, etc)."""

    # Load-in the OSM POIs data
    osm_cache_dir = download_osm_country_data(
        country, cache_dir, force_overwrite=force_overwrite
    )
    osm_pois_filepath = os.path.join(osm_cache_dir, "gis_osm_pois_free_1.shp")
    osm = gpd.read_file(osm_pois_filepath)

    # Create a copy of the AOI gdf if not inplace to avoid modifying the original gdf
    if not inplace:
        aoi = aoi.copy()

    # GeoWrangler: Count number of all POIs per tile
    aoi = vzs.create_zonal_stats(
        aoi,
        osm,
        overlap_method="intersects",
        aggregations=[{"func": "count", "output": "poi_count", "fillna": True}],
    )

    # Count specific aoi types
    for poi_type in poi_types:
        # GeoWrangler: Count with vector zonal stats
        aoi = vzs.create_zonal_stats(
            aoi,
            osm[osm["fclass"] == poi_type],
            overlap_method="intersects",
            aggregations=[
                {"func": "count", "output": f"{poi_type}_count", "fillna": True}
            ],
        )

        # GeoWrangler: Distance with distance zonal stats
        col_name = f"{poi_type}_nearest"
        aoi = dzs.create_distance_zonal_stats(
            aoi.to_crs(metric_crs),
            osm[osm["fclass"] == poi_type].to_crs(metric_crs),
            max_distance=10_000,
            aggregations=[],
            distance_col=col_name,
        ).to_crs("epsg:4326")

        # If no POI was found within the distance limit, set the distance to a really high value
        aoi[col_name] = aoi[col_name].fillna(value=999999)

    return aoi


def download_osm_country_data(country, cache_dir, force_overwrite=False):

    osm_cache_dir = os.path.join(cache_dir, "osm/")
    # TODO consider incorporating year or quarter to automatically avoid using stale data
    country_cache_dir = os.path.join(osm_cache_dir, country)

    # Check if the cached data is valid. Otherwise, we have to re-download.
    # Temporary quick check now is to see if the country cache folder is non-empty.
    # TODO: Can improve this later if we need more specific validity checks.
    cached_data_available = (
        os.path.exists(country_cache_dir) and len(os.listdir(country_cache_dir)) > 0
    )

    logger.info(
        f"OSM Data: Cached data available for {country} at {country_cache_dir}? {cached_data_available}"
    )

    # Download if cache is invalid or user specified force_overwrite=True
    if not cached_data_available or force_overwrite:
        logger.info(
            f"OSM Data: Re-initializing OSM country cache dir at {country_cache_dir}..."
        )
        # Re-create the country cache dir and start over to fix any corrupted states
        shutil.rmtree(country_cache_dir, ignore_errors=True)
        Path(country_cache_dir).mkdir(parents=True, exist_ok=True)

        # This downloads a zip file to the country cache dir
        logger.info(f"OSM Data: Downloading Geofabrik zip file...")
        zipfile_path = geofabrik.download_geofabrik_region(country, country_cache_dir)

        # Unzip the zip file
        logger.info(f"OSM Data: Unzipping the zip file...")
        with ZipFile(zipfile_path, "r") as zip_object:
            zip_object.extractall(country_cache_dir)

        # Delete the zip file
        os.remove(zipfile_path)

        logger.info(
            f"OSM Data: Successfully downloaded and cached OSM data for {country} at {country_cache_dir}!"
        )

    return country_cache_dir
