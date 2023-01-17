import os
import shutil
from pathlib import Path
import hashlib
import numpy as np

import pandas as pd
import geopandas as gpd
from geowrangler import grids
import geowrangler.area_zonal_stats as azs
from geowrangler.datasets.ookla import download_ookla_file, OoklaFile, list_ookla_files

from loguru import logger

from povertymapping import settings


def get_OoklaFile(filename):
    """Get the corresponding OoklaFile tuple given the filename
    See: https://stackoverflow.com/questions/8023306/get-key-by-value-in-dictionary
    """

    available_ookla_files = list_ookla_files()
    for ooklafile_tuple, ooklafile_item in available_ookla_files.items():
        if ooklafile_item == filename:
            return ooklafile_tuple


class OoklaDataManager:
    """An instance of this class provides convenience functoins for loading and caching Ookla data"""

    DEFAULT_CACHE_DIR = "~/.geowrangler"

    def __init__(self, cache_dir=DEFAULT_CACHE_DIR):
        self.data_cache = {}
        self.cache_dir = os.path.expanduser(cache_dir)
        self.processed_cache_dir = os.path.join(self.cache_dir, "ookla/processed/")
        Path(self.processed_cache_dir).mkdir(parents=True, exist_ok=True)

    def reinitialize_processed_cache(self):
        "Reinitialize processed_cache_dir to start over from scratch."
        shutil.rmtree(self.processed_cache_dir, ignore_errors=True)
        response = Path(self.processed_cache_dir).mkdir(parents=True, exist_ok=True)
        logger.info(
            f"{self.processed_cache_dir} reintialized. All cached processed data in this folder has been deleted."
        )
        return response

    def load_type_year_data(
        self, aoi, type_, year, use_cache=True, return_geometry=False
    ):
        "Load Ookla data across all quarters for a specified aoi, type (fixed, mobile) and year"

        # Generate hash from aoi, type_, and year, which will act as a hash key for the cache
        aoi_bounds = aoi.total_bounds
        data_tuple = (
            np.array2string(aoi_bounds),
            str(type_),
            str(year),
            str(return_geometry),
        )
        m = hashlib.md5()
        for item in data_tuple:
            m.update(item.encode())
        data_key = m.hexdigest()

        # Get from RAM cache if already available
        logger.debug(f"Contents of data cache: {list(self.data_cache.keys())}")
        if data_key in self.data_cache:
            logger.debug(
                f"Ookla data for aoi, {type_} {year} (key: {data_key}) found in cache."
            )
            return self.data_cache[data_key]

        ## Get cached data from filesystem if saved
        cached_file_path = (
            os.path.join(self.processed_cache_dir, f"{data_key}.geojson")
            if return_geometry
            else os.path.join(self.processed_cache_dir, f"{data_key}.csv")
        )

        cached_data_available = os.path.exists(cached_file_path)
        logger.info(
            f"Cached data available at {cached_file_path}? {cached_data_available}"
        )

        if cached_data_available:
            logger.debug(
                f"Processed Ookla data for aoi, {type_} {year} (key: {data_key}) found in filesystem. Loading in cache."
            )
            if not return_geometry:
                df = pd.read_csv(cached_file_path)
                self.data_cache[data_key] = df
                return df
            else:
                gdf = gpd.read_file(cached_file_path, driver="GeoJSON")
                self.data_cache[data_key] = gdf
                return gdf

        logger.debug("No cached data found. Processing Ookla data from scratch.")

        # Otherwise, load from raw file and add to RAM cache
        type_year_cache_dir = download_ookla_year_data(
            type_,
            year,
            cache_dir=self.cache_dir,
            use_cache=use_cache,
        )

        # Generate the bing tile quadkeys that intersect with the input aoi
        bing_tile_grid_generator_no_geom = grids.BingTileGridGenerator(
            16, return_geometry=False
        )
        aoi_quadkeys = bing_tile_grid_generator_no_geom.generate_grid(aoi)[
            "quadkey"
        ].tolist()

        # Combine quarterly data for the specified year, filtered to the aoi using quadkey
        # Quarter is inferred from the Ookla filename
        quarter_df_list = []
        for ookla_filename in sorted(os.listdir(type_year_cache_dir)):
            quarter = int(getattr(get_OoklaFile(ookla_filename), "quarter"))
            ookla_quarter_filepath = os.path.join(type_year_cache_dir, ookla_filename)
            logger.debug(
                f"Ookla data for aoi, {type_} {year} {quarter} being loaded from {ookla_quarter_filepath}"
            )
            quarter_df = pd.read_parquet(ookla_quarter_filepath)
            quarter_df = quarter_df[quarter_df["quadkey"].isin(aoi_quadkeys)]
            quarter_df["quarter"] = quarter
            quarter_df_list.append(quarter_df)

            # Free memory after processing
            del quarter_df

        logger.debug(
            f"Concatenating quarterly Ookla data for {type_} and {year} into one dataframe"
        )
        df = pd.concat(quarter_df_list, ignore_index=True)

        # NOTE: Since there will be groupby operations in processing, we don't return
        #       a geodataframe by default since it does not work well with aggregations
        #       by quadkey.
        if not return_geometry:
            self.data_cache[data_key] = df
            df.to_csv(cached_file_path, index=False)
            return df
        else:
            logger.debug(f"Converting Ookla data into geodataframe")
            gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkt(df["tile"]))
            self.data_cache[data_key] = gdf
            gdf.to_file(cached_file_path, driver="GeoJSON")
            return gdf


def download_ookla_year_data(type_, year, cache_dir, use_cache=True):

    "Download ookla data for a specifed type (fixed or mobile) and year. Data for all 4 quarters will be downloaded."

    # Determine number of expected data for type_ and year, specified by OoklaFile(type, year, quarter)
    available_ookla_files = list_ookla_files()
    expected_ookla_files = {}
    for quarter in [1, 2, 3, 4]:
        quarter_ookla_file = OoklaFile(str(type_), str(year), str(quarter))
        if quarter_ookla_file in available_ookla_files.keys():
            expected_ookla_files[quarter_ookla_file] = available_ookla_files[
                quarter_ookla_file
            ]
    num_expected_ookla_files = len(expected_ookla_files)

    if num_expected_ookla_files == 0:
        logger.warning(f"Ookla data: No data available for {type_} and {year}")
    else:
        logger.info(
            f"Ookla Data: Number of available files for {type_} and {year}: {num_expected_ookla_files}"
        )

    ookla_cache_dir = os.path.join(cache_dir, "ookla/")
    type_year_cache_dir = os.path.join(ookla_cache_dir, type_, str(year))

    # Check if the cached data is valid. Otherwise, we have to re-download.
    # For Ookla, we need to check if we've downloaded all expected files for that year.
    cached_data_available = (
        os.path.exists(type_year_cache_dir)
        and len(os.listdir(type_year_cache_dir)) == num_expected_ookla_files
    )

    logger.info(
        f"Ookla Data: Cached data available for {type_} and {year} at {type_year_cache_dir}? {cached_data_available}"
    )

    # Download if cache is invalid or user specified use_cache = False
    if not cached_data_available or not use_cache:
        logger.info(
            f"Ookla Data: Re-initializing Ookla type/year cache dir at {type_year_cache_dir}..."
        )
        # Re-create the country cache dir and start over to fix any corrupted states
        shutil.rmtree(type_year_cache_dir, ignore_errors=True)
        Path(type_year_cache_dir).mkdir(parents=True, exist_ok=True)

        # This downloads a parquet file to the type_year_dir for each quarter
        for quarter in range(1, num_expected_ookla_files + 1, 1):
            logger.info(
                f"Ookla Data: Downloading Ookla parquet file for quarter {quarter}..."
            )
            download_path = download_ookla_file(
                type_=type_,
                year=year,
                quarter=str(quarter),
                directory=type_year_cache_dir,
            )

        logger.info(
            f"Ookla Data: Successfully downloaded and cached Ookla data for {type_} and {year} at {type_year_cache_dir}!"
        )

    return type_year_cache_dir


def add_ookla_features(
    aoi,
    type_,
    year,
    ookla_data_manager,
    use_cache=True,
    metric_crs="epsg:3123",
    inplace=False,
):
    """Generates yearly aggregate features for the AOI based on Ookla data for a given type (fixed, mobile) and year."""

    ookla = ookla_data_manager.load_type_year_data(
        aoi, type_, year, use_cache=use_cache
    )

    # Create a copy of the AOI gdf if not inplace to avoid modifying the original gdf
    if not inplace:
        aoi = aoi.copy()

    # Combine quarterly data from Ookla into yearly aggregate data
    # Geometries are stored separately and rejoined after aggregation by quadkey
    # TODO: incorporate parametrized aggregations, take inspiration from GeoWrangler agg spec
    ookla_geoms = ookla[["quadkey", "tile"]].drop_duplicates().reset_index(drop=True)
    ookla_yearly = (
        ookla.groupby("quadkey")
        .agg(
            mean_avg_d_kbps=("avg_d_kbps", "mean"),
            mean_avg_u_kbps=("avg_u_kbps", "mean"),
            mean_avg_lat_ms=("avg_lat_ms", "mean"),
            mean_num_tests=("tests", "mean"),
            mean_num_devices=("devices", "mean"),
        )
        .reset_index()
    )
    # Add type_year prefix to feature names
    ookla_yearly = ookla_yearly.rename(
        {
            col: f"{type_}_{year}_" + col
            for col in ookla_yearly.columns[~ookla_yearly.columns.isin(["quadkey"])]
        },
        axis=1,
    )
    ookla_yearly = ookla_yearly.merge(ookla_geoms, on="quadkey", how="left")
    ookla_yearly = gpd.GeoDataFrame(
        ookla_yearly,
        geometry=gpd.GeoSeries.from_wkt(ookla_yearly["tile"], crs="epsg:4326"),
    )

    # GeoWrangler: area zonal stats of features per AOI
    features = ookla_yearly.columns[
        ~ookla_yearly.columns.isin(["quadkey", "tile", "geometry"])
    ]
    agg_funcs = ["mean"]
    feature_aggregrations = [
        dict(func=agg_funcs, column=feature) for feature in features
    ]
    aoi = azs.create_area_zonal_stats(
        aoi.to_crs(metric_crs), ookla_yearly.to_crs(metric_crs), feature_aggregrations
    ).to_crs("epsg:4326")

    # Clean up columns
    drop_cols = ["intersect_area_sum"]
    aoi = aoi.drop(drop_cols, axis=1)

    return aoi
