import geopandas as gpd
import pandas as pd
from geowrangler import dhs
from haversine import Direction, inverse_haversine
from shapely import wkt


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

    # Aggregate households according ot their cluster IDs
    household_df = dhs.load_dhs_file(dhs_household_dta_filepath)
    household_df = household_df.rename(columns=col_rename_config)
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
