import os

import geopandas as gpd
import pandas as pd
from povertymapping.utils.data_utils import (
    add_buffer_geom,
    compute_feat_by_adm,
    plot_feature_by_adm,
)


def process_ookla_data(config):

    # create output path directory if it doesn't exist
    save_path = config["save_path"]
    if not os.path.isdir(save_path):
        os.makedirs(save_path)

    # extract some config params
    boundary_file = config["boundary_file"]  # make this more generic
    year = config["year"]
    quarter = config["quarter"]
    crs = config["crs"]
    feature = config["ookla_feature"]


    repo_path = config["repo_path"]

    ookla_folder = config["ookla_folder"]
    ookla_data_path = os.path.join(repo_path, config["data_dir"], ookla_folder )

    if not os.path.exists(ookla_data_path):
        raise Exception(f"Ookla data folder {ookla_data_path} is missing")

    hdx_folder = config["hdx_folder"]
    hdx_data_path = os.path.join(repo_path, config["data_dir"], hdx_folder)

    if not os.path.exists(hdx_data_path):
        raise Exception(f"Boundary data file {hdx_data_path} is missing!")

    # save geojson file in data dir
    country = config["country"]
    merged_file_path = os.path.join(
        ookla_data_path, f"{country}_{year}_{quarter}_ookla.geojson"
    )
    if not os.path.exists(merged_file_path):
        raise Exception(f"Filtered ookla data file {merged_file_path} not found!")

    boundary_file_path = os.path.join(hdx_data_path, boundary_file)
    if not os.path.exists(boundary_file_path):
        raise Exception(f"Cannot continue, boundary shapes file {boundary_file_path} missing!")


    country_boundaries = gpd.read_file(boundary_file_path).to_crs(crs)


    # NOTE: the quarterly ookla speed data covers the whole globe (6.9M rows of geometries)
    #       when merged with country boundary shapes it may or may not yield
    #       more intersections with clusters (in the case of PH it does)
    #       possible reason for this would be that cluster buffers lie
    #       strategically close to several adm level regions which might be due
    #       to 4-10km change in centroid location

    # for now we will use the finest adm level merged data
    # to obtain internet speed aggregates with cluster buffers

    tiles_in_country = gpd.read_file(merged_file_path)

    # convert to Mbps for easier reading
    tiles_in_country["avg_d_mbps"] = tiles_in_country["avg_d_kbps"] / 1000
    tiles_in_country["avg_u_mbps"] = tiles_in_country["avg_u_kbps"] / 1000

    dhs_geo_zip_folder = config["dhs_geo_zip_folder"]
    cluster_coords_filename = f"{dhs_geo_zip_folder}_cluster_coords"
    cluster_centroids_df_path = os.path.join(config["save_path"], f"{cluster_coords_filename}.csv")
    cluster_centroid_df = pd.read_csv(cluster_centroids_df_path)

    # sample clusters
    if config["sample"]:
        no_samples = config["no_samples"]
        seed = config["random_seed"]
        if config["random_sample"]:
            cluster_centroid_df = cluster_centroid_df.sample(
                no_samples, random_state=seed
            )
        else:
            cluster_centroid_df = cluster_centroid_df.head(no_samples)

    # BUFFERS
    # read cluster centroids
    # generate buffer of area ~16km^2
    # create geopandas
    # add geometry column
    add_buffer_geom(cluster_centroid_df, r=config['clust_rad'])
    # convert to geodataframe
    cluster_centroid_df = gpd.GeoDataFrame(cluster_centroid_df, geometry="geometry")
    cluster_centroid_df.crs = f"EPSG:{crs}"
    

    # compute mean feature by cluster centroid as aoi, tiles_in_country as data
    # TODO: replace with geowrangler area zonal stats?
    buffer_aggregate_country = gpd.sjoin(
        cluster_centroid_df,
        tiles_in_country.drop(["index_right"], axis=1),
        how="inner",
        predicate="intersects",
    )
    mean_download_by_cluster = (
        buffer_aggregate_country[["DHSID", feature]]
        .groupby(["DHSID"])
        .mean()
        .reset_index()
    )

    # PLOT FEATURES
    if config["plot_ookla_features"]:
        # testing
        # although the following steps might seem circular
        # this is the best we've got to sort out feature geo spatial mapping.
        # merge mean_download with cluster_buffers
        geometry_and_mean = pd.merge(
            cluster_centroid_df, mean_download_by_cluster, on="DHSID", how="inner"
        )
        # how many rows will the dataframe above have? Hmmm
        # no aggregate by adm3 level, assuming there will be more than several
        # buffers intersecting adm shape regions
        # in order words, treat geometry_and_mean as ookla data
        # and repeat the spatial join inside the methods compute_ookla_stats

        # features_list = [feature]
        to_map_data_left = compute_feat_by_adm(
            country_boundaries, geometry_and_mean, config
        )

        plot_feature_by_adm(to_map_data_left, config, feature)

    result_file_path = os.path.join(
        save_path, f"{country}_{year}_{quarter}_{feature}.csv"
    )
    mean_download_by_cluster.to_csv(result_file_path)
    # unfortunately there is less than half unique clusters after merge (561 clusters :()
    # but there is more data in buffer_aggregate_country
