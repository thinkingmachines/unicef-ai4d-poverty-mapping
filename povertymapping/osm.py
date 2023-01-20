import os
import shutil
import uuid
from pathlib import Path
from zipfile import ZipFile
from urllib.request import HTTPError
import geopandas as gpd
from geowrangler import distance_zonal_stats as dzs
from geowrangler import vector_zonal_stats as vzs
from geowrangler.datasets.geofabrik import list_geofabrik_regions
from loguru import logger
from urllib.parse import urlparse
from povertymapping.nightlights import urlretrieve, make_report_hook
from typing import Union
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

DEFAULT_CACHE_DIR = "~/.geowrangler"


class OsmDataManager:
    """An instance of this class provides convenience functions for loading and caching OSM data"""


    def __init__(self, cache_dir=DEFAULT_CACHE_DIR):
        self.cache_dir = os.path.expanduser(cache_dir)
        self.pois_cache = {}
        self.roads_cache = {}

    def load_pois(self, country, year=None, use_cache=True, chunksize=1024*1024, show_progress=True):
        # Get from RAM cache if already available
        if year is None:
            if country in self.pois_cache:
                logger.debug(f"OSM POIs for {country} found in cache.")
                return self.pois_cache[country]
            else:
                short_year = str(year)[-2:]
                lookup = f'{country}_{short_year}'
                if lookup in self.pois_cache[lookup]:
                    logger.debug(f"OSM POIs for {country} and year {year} found in cache.")
                    return self.pois_cache[lookup]

        # Otherwise, load from file and add to cache
        country_cache_dir = download_osm_country_data(
            country,
            year=year,
            cache_dir=self.cache_dir,
            use_cache=use_cache,
            chunksize=chunksize,
            show_progress=show_progress,
        )
        if country_cache_dir is None:
            return None

        osm_pois_filepath = os.path.join(country_cache_dir, "gis_osm_pois_free_1.shp")
        if year is None:
            logger.debug(f"OSM POIs for {country} being loaded from {osm_pois_filepath}")
        else:
            logger.debug(f"OSM POIs for {country} and year {year} being loaded from {osm_pois_filepath}")
        gdf = gpd.read_file(osm_pois_filepath)

        if year is None:
            self.pois_cache[country] = gdf
        else:
            short_year = str(year)[-2:]
            lookup = f'{country}_{short_year}'
            self.pois_cache[lookup] = gdf

        return gdf

    def load_roads(self, country, year=None, use_cache=True, chunksize=1024*1024, show_progress=True):
        # Get from RAM cache if already available
        if year is None:
            if country in self.roads_cache:
                logger.debug(f"OSM POIs for {country} found in cache.")
                return self.roads_cache[country]
            else:
                short_year = str(year)[-2:]
                lookup = f'{country}_{short_year}'
                if lookup in self.roads_cache[lookup]:
                    logger.debug(f"OSM POIs for {country} and year {year} found in cache.")
                    return self.roads_cache[lookup]

        # Otherwise, load from file and add to cache
        country_cache_dir = download_osm_country_data(
            country,
            year=year,
            cache_dir=self.cache_dir,
            use_cache=use_cache,
            chunksize=chunksize,
            show_progress=show_progress
        )

        if country_cache_dir is None:
            return None

        osm_roads_filepath = os.path.join(country_cache_dir, "gis_osm_roads_free_1.shp")
        if year is None:
            logger.debug(f"OSM Roads for {country} being loaded from {osm_roads_filepath}")
        else:
            logger.debug(f"OSM Roads for {country} and year {year} being loaded from {osm_roads_filepath}")
        gdf = gpd.read_file(osm_roads_filepath)

        if year is None:
            self.roads_cache[country] = gdf
        else:
            short_year = str(year)[-2:]
            lookup = f'{country}_{short_year}'
            self.roads_cache[lookup] = gdf

        return gdf

# TODO: update geowrangler.download_geofabrik_region to add progress bar
def download_geofabrik_region(
    region: str, year=None, directory: str = "data/", overwrite=False,
    show_progress=True,
    chunksize=8192,
) -> Union[Path,None]:
    """Download geofabrik region to path"""
    if not os.path.isdir(directory):
        os.makedirs(directory)
    geofabrik_info = list_geofabrik_regions()
    if region not in geofabrik_info:
        raise ValueError(
            f"{region} not found in geofabrik. Run list_geofabrik_regions() to learn more about available areas"
        )
    url = geofabrik_info[region]
    if year is not None:
        short_year = str(year)[-2:] # take last 2 digits
        year_prefix = f'{short_year}0101'
        url = url.replace('latest',year_prefix)

    parsed_url = urlparse(url)
    filename = Path(os.path.basename(parsed_url.path))
    filepath = directory / filename
    if not filepath.exists() or overwrite:
        reporthook = make_report_hook(show_progress)

        try:
            filepath, _, _ = urlretrieve(url, filepath, reporthook=reporthook, chunksize=chunksize)
        except HTTPError as err:
            if err.code == 404:
                if year is not None:
                    logger.warning(f'No data found for year {year} in region {region} : {url}')
                else:
                    logger.warning(f'No url found for region {region} : {url} ')
                return None
            else:
                raise err

    return filepath.as_posix()


def download_osm_country_data(country, year=None, cache_dir=DEFAULT_CACHE_DIR, use_cache=True, chunksize=8192, show_progress=True):

    osm_cache_dir = os.path.join(cache_dir, "osm/")
    # TODO consider incorporating year or quarter to automatically avoid using stale data

    # Check if the cached data is valid. Otherwise, we have to re-download.
    # Temporary quick check now is to see if the country cache folder is non-empty.
    # TODO: Can improve this later if we need more specific validity checks.
    if year is None:
        country_cache_dir = os.path.join(osm_cache_dir, country)
        cached_data_available = (
            os.path.exists(country_cache_dir) and len(os.listdir(country_cache_dir)) > 0
        )
    else:
        short_year = str(year)[-2:] # take last 2 digits
        year_prefix = f'{short_year}0101'
        lookup = f'{country}-{year_prefix}'
        country_cache_dir = os.path.join(osm_cache_dir,lookup)
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
        zipfile_path = download_geofabrik_region(country, year=year, directory=country_cache_dir, show_progress=show_progress, chunksize=chunksize)
        if zipfile_path is None:
            return None
        # Unzip the zip file
        logger.info(f"OSM Data: Unzipping the zip file {zipfile_path}...")
        with ZipFile(zipfile_path, "r") as zip_object:
            zip_object.extractall(country_cache_dir)

        # Delete the zip file
        os.remove(zipfile_path)
        if year is None:
            logger.info(
                f"OSM Data: Successfully downloaded and cached OSM data for {country} at {country_cache_dir}!"
            )
        else:
            logger.info(
                f"OSM Data: Successfully downloaded and cached OSM data for {country} and {year} at {country_cache_dir}!"
            )

    return country_cache_dir

def add_osm_poi_features(
    aoi,
    country,
    osm_data_manager:OsmDataManager,
    year=None,
    use_cache=True,
    poi_types=DEFAULT_POI_TYPES,
    metric_crs="epsg:3857",
    inplace=False,
    nearest_poi_max_distance=10000,
):
    """Generates features for the AOI based on OSM POI data (POIs, roads, etc)."""

    # Load-in the OSM POIs data
    osm = osm_data_manager.load_pois(country, year=year, use_cache=use_cache)
        
    # Create a copy of the AOI gdf if not inplace to avoid modifying the original gdf
    if not inplace:
        aoi = aoi.copy()

    if osm is None:
        if year is None:
            logger.warning(f'No POI features added for {country}')
        else:
            logger.warning(f'No POI features added for {country} and year {year}')
        return aoi

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
    aoi, country, osm_data_manager, year=None, use_cache=True, inplace=False
):
    """Generates features for the AOI based on OSM road data"""
    roads_gdf = osm_data_manager.load_roads(country, year=year, use_cache=use_cache)

    if not inplace:
        aoi = aoi.copy()

    if roads_gdf is None:
        if year is None:
            logger.warning(f'No Road features added for {country}')
        else:
            logger.warning(f'No Road features added for {country} and year {year}')
        return aoi

    assert aoi.crs == roads_gdf.crs

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


