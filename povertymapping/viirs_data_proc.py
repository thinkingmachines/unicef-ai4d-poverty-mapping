import pandas as pd
import geopandas as gpd
# from rasterio.plot import show
# import matplotlib.pyplot as plt
# import numpy as np
from tqdm import tqdm
from shapely.geometry import Polygon
# from matplotlib.colors import colorConverter
import geowrangler.raster_zonal_stats as rzs
from haversine import Direction, inverse_haversine, Unit
import os
# import sys


from pathlib import Path

def create_polygon_bbox(centroid_lat, centroid_lon, distance_m):
    """Return bbox edge locations using haversine distance function
    The output is specified as (west, south, east, north)
    distance_km specifies the distance of each edge from the centroid
    """
    centroid = (centroid_lat, centroid_lon)
    top_left = inverse_haversine(
        inverse_haversine(centroid, distance_m, Direction.WEST, Unit.METERS),
        distance_m,
        Direction.NORTH,
        Unit.METERS
    )
    bottom_right = inverse_haversine(
        inverse_haversine(centroid, distance_m, Direction.EAST, Unit.METERS),
        distance_m,
        Direction.SOUTH,
        Unit.METERS
    )

    north, west = top_left
    south, east = bottom_right

    # check inequalities
    assert west < east
    assert south < north

    # bbox_coord_list = [west, south, east, north]

    bbox = Polygon([[west, south], [east, south], [east, north], [west, north]])
    return bbox


def add_bbox_geom(cluster_centroids_gdf, distance_m, output_col='bbox'):
    """Add bbox geometry to dhs cluster data (i.e. 6th column)
    Args:
        cluster_centroid_gdf (gpd.GeoDataFrame): DHS data frame
        length (int): buffer radius in meters
    Returns:
        geopandas.GeoDataFrame
    """

    cluster_centroids_gdf = cluster_centroids_gdf.copy()

    centroids = list(
        zip(cluster_centroids_gdf["LATNUM"], cluster_centroids_gdf["LONGNUM"])
    )
    bbox_geometry = []
    print("Adding buffer geometry...")
    for centroid in tqdm(centroids):
        centroid_lat, centroid_lon = centroid
        bbox = create_polygon_bbox(centroid_lat, centroid_lon, distance_m)
        
        bbox_geometry.append(bbox)
    cluster_centroids_gdf[output_col] = bbox_geometry
    return cluster_centroids_gdf

def process_viirs_data(config): 
# config = dict(
#         save_path="../data/outputs/viirs_ph",
#         repo_path="../data/SVII_PH_KH_MM_TL",
#         viirs_tif_path="../data/outputs/viirs_ph/eog_PH_2017.tif",
#         data_dir="ph",
#         country="ph",
#         viirs_folder="viirs_ph",
#         hdx_folder="hdx_ph",
#         dhs_folder="dhs_ph",
#         dhs_geo_zip_folder="PHGE71FL",
#         dhs_zip_folder="PHHR71DT",
#         crs="4683",
#         viirs_feature="avg_rad",
#         boundary_file="phl_adminboundaries_candidate_adm3",
#         year="2017",
#         # sample=False,
#         # random_sample=False,
#         # no_samples=60,
#         # random_seed=42,
#         clust_rad=2000,
#         plot_viirs_features=True,
#         adm_level=3,
#         use_pcode=True,
#         shape_label='ADM3_PCODE',
#         bins=6,
#         show_legend=False,
#     )
    # read in househould cluster geo data
    # data_dir = config["data_dir"]
    country = config["country"]
    crs = config["crs"]
    save_path = config["save_path"]
    if not os.path.isdir(save_path):
        os.makedirs(save_path)

    dhs_geo_zip_folder = config["dhs_geo_zip_folder"]

    cluster_coords_filename = f"{dhs_geo_zip_folder}_cluster_coords"
    # cluster_centroid_df = pd.read_csv(
    #     os.path.join(save_path, f"{cluster_coords_filename}.csv")
    # )

    cluster_centroids_df = pd.read_csv(
        os.path.join(save_path, f"{cluster_coords_filename}.csv")
    )


    # cluster_coords_path = Path(config['save_path'])/'..'/config['dhs_folder']/f"{config['dhs_geo_zip_folder']}_cluster_coords.csv"
    # cluster_coords_path

    viirs_tif_path = config['viirs_tif_path']

    # with rio.open(viirs_tif_path) as dst:
    #     data = dst.read(1)

    # cluster_centroids_df = pd.read_csv(cluster_coords_path)

    # Remove clusters with latitude == 0 for PH
    if country.lower() == "ph": 
        cluster_centroids_df = cluster_centroids_df[cluster_centroids_df.LATNUM > 0.0]


    cluster_centroids_gdf = gpd.GeoDataFrame(
        cluster_centroids_df,
        geometry=gpd.GeoSeries.from_wkt(cluster_centroids_df["geometry"], crs=f'epsg:{crs}')
    )
    bbox_size = config['bbox_size'] # bbox size in meters (distance from box center to side) 
    cluster_bbox_gdf = add_bbox_geom(cluster_centroids_gdf, bbox_size)
    cluster_bbox_gdf['geometry'] = cluster_bbox_gdf['bbox']

    # cluster_bbox_gdf.plot()

    cluster_zonal_stats_gdf = rzs.create_raster_zonal_stats(
        cluster_bbox_gdf,
        viirs_tif_path,
        aggregation=dict(
            # func=["min", "max", "mean", "median", "kurtosis", "var"],
            func=["min", "max", "mean", "median", "std"],
            column="avg_rad",
        ),
        extra_args=dict(band_num=1, nodata=-999),
    )
    save_name = f'{config["country"]}_{config["year"]}_viirs_{config["viirs_feature"]}_zonal_stats'
    output_gpkg_path = Path(config['save_path'])/f'{save_name}.gpkg'
    output_csv_path = Path(config['save_path'])/f'{save_name}.csv'

    ## GPKG
    output_gdf = cluster_zonal_stats_gdf.copy()
    output_gdf['latitude'] = output_gdf['LATNUM']
    output_gdf['longitude'] = output_gdf['LONGNUM']
    usecols = [
        "DHSID",
        "longitude",
        "latitude",
        "avg_rad_min",
        "avg_rad_max",
        "avg_rad_mean",
        "avg_rad_std",
        "avg_rad_median",
        "geometry"
    ]

    output_gdf = output_gdf[usecols]
    output_gdf.to_file(output_gpkg_path, driver="GPKG")

    ## CSV
    usecols = [
        "DHSID",
        "longitude",
        "latitude",
        "avg_rad_min",
        "avg_rad_max",
        "avg_rad_mean",
        "avg_rad_std",
        "avg_rad_median",
    ]

    output_df = output_gdf[usecols]
    output_df.to_csv(output_csv_path, index=False)