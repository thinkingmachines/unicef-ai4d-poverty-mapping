import geopandas as gpd
import pandas as pd
from geowrangler import dhs
from haversine import Direction, inverse_haversine
from shapely import wkt
from typing import Union

DEFAULT_AVAILABLE_COUNTRIES = ["ph", "kh", "mm", "tl"]
DEFAULT_DHS_HOUSEHOLD_COLS = [
    "case identification",
    "country code and phase",
    "DHSCLUST",
    "household number",
    "respondent's line number (answering household questionnaire)",
    "ultimate area unit",
    "household sample weight (6 decimals)",
    "month of interview",
    "year of interview",
    "date of interview (cmc)",
    "date of interview century day code (cdc)",
    "Wealth Index",
]
DEFAULT_DHS_CLUSTER_COLS = [
    "DHSCLUST",
    "Wealth Index",
    "DHSID",
    "DHSCC",
    "DHSYEAR",
    "CCFIPS",
    "ADM1FIPS",
    "ADM1FIPSNA",
    "ADM1SALBNA",
    "ADM1SALBCO",
    "ADM1DHS",
    "ADM1NAME",
    "DHSREGCO",
    "DHSREGNA",
    "SOURCE",
    "URBAN_RURA",
    "LATNUM",
    "LONGNUM",
    "ALT_GPS",
    "ALT_DEM",
    "DATUM",
    "geometry",
]
DEFAULT_INDEX_FEATURES = [
    "rooms",
    "electric",
    "mobile telephone",
    "radio",
    "television",
    "car/truck",
    "refrigerator",
    "motorcycle",
    "floor",
    "toilet",
    "drinking water",
]


class DHSDataManager:
    """
    An instance of this class manages loaded househould and cluster DHS data and handles
    cross-country operations (ex. concatenation, wealth-index recalculation)
    """

    def __init__(
        self,
        available_countries: list = DEFAULT_AVAILABLE_COUNTRIES,
        dhs_household_cols=DEFAULT_DHS_HOUSEHOLD_COLS,
        dhs_cluster_cols=DEFAULT_DHS_CLUSTER_COLS,
    ):
        # Initialize storage for processed country datasets
        # separated into household and cluster level
        self.available_countries = available_countries
        self.dhs_household_cols = dhs_household_cols
        self.dhs_cluster_cols = dhs_cluster_cols
        self.household_data = {}
        self.cluster_data = {}

    def cache_data(
        self,
        cache: dict,
        country_index: str,
        data: Union[pd.DataFrame, gpd.GeoDataFrame],
        overwrite_cache=False,
    ):
        "Place data in cache, throwing an exception if there is an existing entry with the same country index"
        if country_index in cache.keys() and not overwrite_cache:
            raise ValueError(
                "country_index is already in the specified cache. Double check the value or refresh the cache"
            )

        if overwrite_cache:
            print(f"Overwriting {country_index} in cache")

        cache[country_index] = data
        return

    def view_cache_keys(self, cache_type: str = None):

        if cache_type is None:
            print(
                "Household: ",
                list(self.household_data.keys()),
                "Cluster: ",
                list(self.cluster_data.keys()),
            )
        elif cache_type == "household":
            print(self.household_data.keys())
        elif cache_type == "cluster":
            print(self.cluster_data.keys())
        else:
            raise ValueError(
                'Invalid value for cache_type. Use "household", "cluster", or leave blank/none to view both'
            )

        return

    def generate_dhs_household_level_data(
        self,
        country_index: str,
        dhs_household_dta_filepath: str,
        col_rename_config: dict,
        drop_duplicate_cols: bool = True,
        overwrite_cache=False,
        return_data: bool = True,
    ):
        if (
            isinstance(col_rename_config, str)
            and col_rename_config.lower() in self.available_countries
        ):
            col_rename_config = dhs.load_column_config(col_rename_config)

        # If overwrite_cache = false, return cached data if it already exists
        if country_index in self.household_data and not overwrite_cache:
            print(f"Getting {country_index} data from cache.")
            household_df = self.household_data[country_index]
            if return_data:
                return household_df

        else:
            # Aggregate households according to their cluster IDs
            household_df = dhs.load_dhs_file(dhs_household_dta_filepath)
            household_df = household_df.rename(columns=col_rename_config)

            # Drop duplicated column names (keeps first occurence)
            if drop_duplicate_cols:
                household_df = household_df.loc[:, ~household_df.columns.duplicated()]

            # Add country_index as a column for future indexing
            household_df["country_index"] = country_index

            # Store it in cache
            self.cache_data(
                self.household_data,
                country_index,
                household_df,
                overwrite_cache=overwrite_cache,
            )

            if return_data:
                return household_df

    def generate_dhs_cluster_level_data(
        self,
        country_index: str,
        dhs_household_dta_filepath: str,
        dhs_geo_shp_filepath,
        col_rename_config={},
        wealth_col_name="Wealth Index",
        cluster_col_name="DHSCLUST",
        lat_col="LATNUM",
        lon_col="LONGNUM",
        filter_invalid=True,
        convert_geoms_to_bbox=True,
        bbox_size_km=2,
        drop_duplicate_cols=True,
        overwrite_cache=False,
        return_data=True,
    ):

        if (
            isinstance(col_rename_config, str)
            and col_rename_config.lower() in self.available_countries
        ):
            col_rename_config = dhs.load_column_config(col_rename_config)

        # If overwrite_cache = false, get cached data if it already exists
        if country_index in self.cluster_data and not overwrite_cache:
            print(f"Getting {country_index} data from cache.")
            cluster_gdf = self.cluster_data[country_index]
            if return_data:
                return cluster_gdf

        else:
            # Get the household level data
            household_df = self.generate_dhs_household_level_data(
                country_index,
                dhs_household_dta_filepath,
                col_rename_config,
                drop_duplicate_cols,
                overwrite_cache,
                return_data,
            )

            # Aggregate households according ot their cluster IDs
            cluster_df = (
                household_df[[wealth_col_name, cluster_col_name]]
                .groupby(cluster_col_name)
                .mean()
            )
            cluster_df.reset_index(inplace=True)

            # Read-in the cluster geo coordinates and merge with the cluster data
            dhs_geo_gdf = gpd.read_file(dhs_geo_shp_filepath)
            cluster_df = pd.merge(cluster_df, dhs_geo_gdf, on=cluster_col_name)

            # Some of the clusters in the data might have 0,0 coordinates.
            if filter_invalid:
                cluster_df = cluster_df[
                    (cluster_df[lat_col] != 0) | (cluster_df[lon_col] != 0)
                ]

            # Convert geoms to bbox if specified
            if convert_geoms_to_bbox:
                cluster_gdf = generate_bboxes(cluster_df, bbox_size_km)
            else:
                cluster_gdf = gpd.GeoDataFrame(cluster_df)

            # Add country_index as a column for future indexing
            cluster_gdf["country_index"] = country_index

            # Store it in cache
            self.cache_data(
                self.cluster_data,
                country_index,
                cluster_gdf,
                overwrite_cache=overwrite_cache,
            )
            if return_data:
                return cluster_gdf

    def get_household_level_data_by_country(
        self, country_index_list: list = None, drop_extra_cols=False
    ):
        "Concatenate all household level dataframes for each specified country_index in list"

        if country_index_list is None:
            country_index_list = list(self.household_data.keys())

        print(f"Combining household data for the ff. countries: {country_index_list}")

        country_household_data_list = [
            self.household_data[x].copy() for x in country_index_list
        ]
        countries_household_data = pd.concat(
            country_household_data_list, ignore_index=True
        )

        # If drop_extra_cols, we keep only the indicated dhs columns
        # and columns common to all country dataframes
        if drop_extra_cols:
            country_cols = [df.columns for df in country_household_data_list]
            common_cols = list(set.intersection(*map(set, country_cols)))
            keep_cols = self.dhs_household_cols + [
                x for x in common_cols if x not in self.dhs_household_cols
            ]
            countries_household_data = countries_household_data[keep_cols]

        return countries_household_data

    def get_cluster_level_data_by_country(
        self, country_index_list: list = None, drop_extra_cols=False
    ):
        "Concatenate all household level dataframes for each specified country_index in list"

        if country_index_list is None:
            country_index_list = list(self.household_data.keys())

        print(f"Combining cluster data for the ff. countries: {country_index_list}")

        country_cluster_data_list = [
            self.cluster_data[x].copy() for x in country_index_list
        ]
        countries_cluster_data = gpd.GeoDataFrame(
            pd.concat(country_cluster_data_list, ignore_index=True),
            crs=country_cluster_data_list[0].crs,
        )

        # If drop_extra_cols, we keep only the indicated dhs columns
        # and columns common to all country dataframes
        if drop_extra_cols:
            country_cols = [df.columns for df in country_cluster_data_list]
            common_cols = list(set.intersection(*map(set, country_cols)))
            keep_cols = self.dhs_cluster_cols + [
                x for x in common_cols if x not in self.dhs_cluster_cols
            ]
            countries_cluster_data = countries_cluster_data[keep_cols]

        return countries_cluster_data

    def recompute_index_household_level(
        self,
        country_index_list: list = None,
        index_features: list = DEFAULT_INDEX_FEATURES,
        output_col: str = "Recomputed Wealth Index",
    ):
        if country_index_list is None:
            country_index_list = list(self.household_data.keys())

        households_df = self.get_household_level_data_by_country(country_index_list)
        
        households_df[output_col] = dhs.assign_wealth_index(
            households_df[index_features].fillna(0)
        )

        return households_df

    def recompute_index_cluster_level(
        self,
        country_index_list: list = None,
        index_features: list = DEFAULT_INDEX_FEATURES,
        output_col: str = "Recomputed Wealth Index",
    ):

        if country_index_list is None:
            country_index_list = list(self.cluster_data.keys())

        # Recompute on household level first
        recomputed_household_df = self.recompute_index_household_level(
            country_index_list, index_features, output_col
        )

        # Aggregate household level data by country and cluster id
        # Note: cluster id is given as an integer and not unique across countries
        recomputed_cluster_df = (
            recomputed_household_df[["country_index", "DHSCLUST", output_col]]
            .groupby(["country_index", "DHSCLUST"])
            .mean()
        ).reset_index()

        # Load geographic cluster data for each country
        cluster_gdf = self.get_cluster_level_data_by_country(
            country_index_list, drop_extra_cols=True
        )

        # Merge the recalculated values into cluster_gdf
        merged_df = cluster_gdf.merge(
            recomputed_cluster_df, on=["country_index", "DHSCLUST"], how="left"
        )
        gdf = gpd.GeoDataFrame(merged_df)

        return gdf


def generate_dhs_household_level_data(
    dhs_household_dta_filepath, col_rename_config={}, drop_duplicate_cols=True
):
    AVAILABLE_COUNTRIES = ["ph", "kh", "mm", "tl"]
    if (
        isinstance(col_rename_config, str)
        and col_rename_config.lower() in AVAILABLE_COUNTRIES
    ):
        col_rename_config = dhs.load_column_config(col_rename_config)

    # Aggregate households according ot their cluster IDs
    household_df = dhs.load_dhs_file(dhs_household_dta_filepath)
    household_df = household_df.rename(columns=col_rename_config)

    # Drop duplicated column names (keeps first occurence)
    if drop_duplicate_cols:
        household_df = household_df.loc[:, ~household_df.columns.duplicated()]

    return household_df


def generate_dhs_cluster_level_data(
    dhs_household_dta_filepath,
    dhs_geo_shp_filepath,
    col_rename_config={},
    wealth_col_name="Wealth Index",
    cluster_col_name="DHSCLUST",
    lat_col="LATNUM",
    lon_col="LONGNUM",
    filter_invalid=True,
    convert_geoms_to_bbox=True,
    bbox_size_km=2,
):

    AVAILABLE_COUNTRIES = ["ph", "kh", "mm", "tl"]
    if (
        isinstance(col_rename_config, str)
        and col_rename_config.lower() in AVAILABLE_COUNTRIES
    ):
        col_rename_config = dhs.load_column_config(col_rename_config)

    # Get the household level data
    household_df = generate_dhs_household_level_data(
        dhs_household_dta_filepath, col_rename_config=col_rename_config
    )

    # Aggregate households according ot their cluster IDs
    cluster_df = (
        household_df[[wealth_col_name, cluster_col_name]]
        .groupby(cluster_col_name)
        .mean()
    )
    cluster_df.reset_index(inplace=True)

    # Read-in the cluster geo coordinates and merge with the cluster data
    dhs_geo_gdf = gpd.read_file(dhs_geo_shp_filepath)
    cluster_df = pd.merge(cluster_df, dhs_geo_gdf, on=cluster_col_name)

    # Some of the clusters in the data might have 0,0 coordinates.
    if filter_invalid:
        cluster_df = cluster_df[(cluster_df[lat_col] != 0) | (cluster_df[lon_col] != 0)]

    # Convert geoms to bbox if specified
    if convert_geoms_to_bbox:
        cluster_gdf = generate_bboxes(cluster_df, bbox_size_km)
    else:
        cluster_gdf = gpd.GeoDataFrame(cluster_df)

    return cluster_gdf


def generate_bboxes(
    locations_df,
    bbox_size_km,
    lat_col="LATNUM",
    lon_col="LONGNUM",
    geometry_col="geometry",
):
    """Creates a bounding box geometry for a DF of lat/lon coordinates."""
    locations_df = locations_df.copy()
    locations_df[geometry_col] = locations_df.apply(
        lambda row: generate_bbox_wkt(
            row[lat_col], row[lon_col], distance_km=bbox_size_km
        ),
        axis=1,
    )
    locations_gdf = gpd.GeoDataFrame(
        locations_df,
        geometry=locations_df[geometry_col].apply(wkt.loads),
        crs="epsg:4326",
    )

    return locations_gdf


def generate_bbox_wkt(centroid_lat, centroid_lon, distance_km):
    """Generates WKT string representing the bounding box for a given lat/lon coordinate"""
    centroid = (centroid_lat, centroid_lon)
    top_left = inverse_haversine(
        inverse_haversine(centroid, distance_km / 2, Direction.WEST),
        distance_km / 2,
        Direction.NORTH,
    )
    bottom_right = inverse_haversine(
        inverse_haversine(centroid, distance_km / 2, Direction.EAST),
        distance_km / 2,
        Direction.SOUTH,
    )

    tl_lat, tl_lon = top_left
    br_lat, br_lon = bottom_right

    tl_str = f"{tl_lon} {tl_lat}"
    tr_str = f"{br_lon} {tl_lat}"
    br_str = f"{br_lon} {br_lat}"
    bl_str = f"{tl_lon} {br_lat}"

    wkt_string = f"POLYGON(({tl_str}, {tr_str}, {br_str}, {bl_str}, {tl_str}))"

    return wkt_string
