import os
import shutil
import uuid
from pathlib import Path
from zipfile import ZipFile

import geopandas as gpd
from geowrangler import distance_zonal_stats as dzs
from geowrangler import vector_zonal_stats as vzs
from geowrangler.datasets import geofabrik
from loguru import logger

DEFAULT_POI_TYPES = [
    "atm",
    "bank",
    "bus_station",
    "cafe",
    "charging_station",
    "courthouse",
    "dentist",
    "fast_food",
    "fire_station",
    "food_court",
    "fuel",
    "hospital",
    "library",
    "marketplace",
    "pharmacy",
    "police",
    "post_box",
    "post_office",
    "restaurant",
    "social_facility",
    "supermarket",
    "townhall",
]


def add_osm_poi_features(
    aoi,
    country,
    osm_data_manager,
    use_cache=True,
    poi_types=DEFAULT_POI_TYPES,
    metric_crs="epsg:3857",
    inplace=False,
    nearest_poi_max_distance=10000,
):
    """Generates features for the AOI based on OSM POI data (POIs, roads, etc)."""

    # Load-in the OSM POIs data
    osm = osm_data_manager.load_pois(country, use_cache=use_cache)

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
            max_distance=nearest_poi_max_distance,
            aggregations=[],
            distance_col=col_name,
        ).to_crs("epsg:4326")

        # If no POI was found within the distance limit, set the distance to the max distance
        aoi[col_name] = aoi[col_name].fillna(value=nearest_poi_max_distance)

    return aoi


def add_osm_road_features(
    aoi, country, osm_data_manager, use_cache=True, inplace=False
):
    """Generates features for the AOI based on OSM road data"""
    roads_gdf = osm_data_manager.load_roads(country, use_cache=use_cache)
    assert aoi.crs == roads_gdf.crs

    if not inplace:
        aoi = aoi.copy()

    # Create a temporary ID column to use for our processing
    # Assign simple integer values
    temp_id = str(uuid.uuid4())
    aoi[temp_id] = list(range(len(aoi)))

    # Get intersections between the AOIs and the roads
    joined = gpd.sjoin(aoi, roads_gdf, how="inner", predicate="intersects")

    # Count the number of roads that intersected
    road_stats_df = joined.groupby(temp_id)["index_right"].agg(road_count="count")
    # Join back to the original AOI gdf
    aoi = aoi.join(road_stats_df, how="left", on=temp_id)

    # There might be AOIs that did not intersect with any roads at all
    aoi["road_count"] = aoi["road_count"].fillna(0)

    # Remove the temporary ID column
    del aoi[temp_id]

    return aoi


class OsmDataManager:
    """An instance of this class provides convenience functions for loading and caching OSM data"""

    DEFAULT_CACHE_DIR = "~/.geowrangler/osm"

    def __init__(self, cache_dir=DEFAULT_CACHE_DIR):
        self.cache_dir = os.path.expanduser(cache_dir)
        self.pois_cache = {}
        self.roads_cache = {}

    def load_pois(self, country, use_cache=True):
        # Get from RAM cache if already available
        if country in self.pois_cache:
            logger.debug(f"OSM POIs for {country} found in cache.")
            return self.pois_cache[country]

        # Otherwise, load from file and add to cache
        country_cache_dir = download_osm_country_data(
            country,
            cache_dir=self.cache_dir,
            use_cache=use_cache,
        )
        osm_pois_filepath = os.path.join(country_cache_dir, "gis_osm_pois_free_1.shp")
        logger.debug(f"OSM POIs for {country} being loaded from {osm_pois_filepath}")
        gdf = gpd.read_file(osm_pois_filepath)
        self.pois_cache[country] = gdf

        return gdf

    def load_roads(self, country, use_cache=True):
        # Get from RAM cache if already available
        if country in self.roads_cache:
            logger.debug(f"OSM Roads for {country} found in cache.")
            return self.roads_cache[country]

        # Otherwise, load from file and add to cache
        country_cache_dir = download_osm_country_data(
            country,
            cache_dir=self.cache_dir,
            use_cache=use_cache,
        )
        osm_roads_filepath = os.path.join(country_cache_dir, "gis_osm_roads_free_1.shp")
        logger.debug(f"OSM Roads for {country} being loaded from {osm_roads_filepath}")
        gdf = gpd.read_file(osm_roads_filepath)
        self.roads_cache[country] = gdf

        return gdf


def download_osm_country_data(country, cache_dir, use_cache=True):

    # TODO consider incorporating year or quarter to automatically avoid using stale data
    country_cache_dir = os.path.join(cache_dir, country)

    # Check if the cached data is valid. Otherwise, we have to re-download.
    # Temporary quick check now is to see if the country cache folder is non-empty.
    # TODO: Can improve this later if we need more specific validity checks.
    cached_data_available = (
        os.path.exists(country_cache_dir) and len(os.listdir(country_cache_dir)) > 0
    )

    logger.info(
        f"OSM Data: Cached data available for {country} at {country_cache_dir}? {cached_data_available}"
    )

    # Download if cache is invalid or user specified use_cache = False
    if not cached_data_available or not use_cache:
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
