import os

import geopandas as gpd
# import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
# import yaml
from povertymapping.utils.data_utils import (
    add_buffer_geom,
    compute_feat_by_adm,
    # get_title_url,
    plot_feature_by_adm,
)


# def compute_ookla_stats(tiles_in_country, country_boundaries):
#     """Compute internat speed wt by number of tests"""
#     # average download speed by admin level
#     # weighted by the number of tests
#     wt_avg_by_adm = tiles_in_country.groupby(["ADM3_PCODE", "ADM3_EN"]).apply(
#         lambda x: pd.Series(
#             {"avg_d_mbps_wt": np.average(x["avg_d_mbps"], weights=x["tests"])}
#         )
#     )
#     # add test sum column
#     country_adm_stats = wt_avg_by_adm.merge(
#         tiles_in_country.groupby(["ADM3_PCODE", "ADM3_EN"])
#         .agg(tests=("tests", "sum"))
#         .reset_index(),
#         on=["ADM3_PCODE", "ADM3_EN"],
#     )

#     # extract adms with highest download speed with at least 50 tests
#     top_20_download_adm = (
#         country_adm_stats.loc[country_adm_stats["tests"] >= 50]
#         .nlargest(20, "avg_d_mbps_wt")
#         .sort_values("avg_d_mbps_wt", ascending=False)
#         .round(2)
#     )

#     # map the adm levels
#     admin_data = country_boundaries[["ADM3_PCODE", "geometry"]].merge(
#         country_adm_stats, on="ADM3_PCODE"
#     )

#     return admin_data, top_20_download_adm


# def plot_buffer_size(dataframe, buffer_df, point=False):
#     """Plot cluster locations on boundary shapes"""
#     # plot on boundary
#     fig, ax = plt.subplots()

#     # plot shapes in the background
#     dataframe.plot(facecolor="none", edgecolor="black", linewidth=0.1, ax=ax)

#     boundary_outline = f"output/{country}_boundary_shapes2.jpeg"

#     if point:
#         cluster_buffers = gpd.GeoDataFrame(
#             buffer_df,
#             geometry=gpd.points_from_xy(buffer_df.longitude, buffer_df.latitude),
#         )
#     else:
#         cluster_buffers = gpd.GeoDataFrame(buffer_df, geometry="geometry")

#     # merge/extract feature corresponding to clusters
#     cluster_result = mean_download_by_cluster.merge(
#         cluster_buffers, on="DHSID", how="left"
#     )
#     cluster_result.plot(column="avg_d_mbps", color="red", ax=ax)

#     fig.savefig(boundary_outline)


# if __name__ == "__main__":
def process_ookla_data(config):
    # read in config file
    # config = yaml.safe_load(open("config.yml"))

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

    # ookla_dvc_folder = config["ookla_target_folder_name"]
    ookla_folder = config["ookla_folder"]

    # def path_map(x, folder_name):
    #     return os.path.join(repo_path, config["data_dir"], x, folder_name)

    # ookla_reg_path, ookla_dvc_path = list(
    #     map(path_map, ["", ookla_dvc_folder], [ookla_folder, ookla_folder])
    # )
    # ookla_reg_path = path_map(ookla_folder,ookla_folder)
    ookla_reg_path = os.path.join(repo_path, config["data_dir"], ookla_folder )

    if os.path.exists(ookla_reg_path):
        ookla_data_path = ookla_reg_path  # or some function of reg_path
    # elif os.path.exists(ookla_dvc_path):
    #     ookla_data_path = ookla_dvc_path  # or some function of dvc_path
    else:
        raise Exception(f"Ookla data file {ookla_reg_path} is missing")

    hdx_folder = config["hdx_folder"]
    # hdx_dvc_folder = config["hdx_target_folder_name"]

    # hdx_reg_path, hdx_dvc_path = list(
    #     map(path_map, ["", hdx_dvc_folder], [hdx_folder, hdx_folder])
    # )
    hdx_reg_path = os.path.join(repo_path, config["data_dir"], hdx_folder)

    if os.path.exists(hdx_reg_path):
        hdx_data_path = hdx_reg_path  # or some function of reg_path
    # elif os.path.exists(hdx_dvc_path):
    #     hdx_data_path = hdx_dvc_path  # or some function of dvc_path
    else:
        raise Exception(f"Boundary data file {hdx_reg_path} is missing!")

    # save geojson file in data dir
    country = config["country"]
    merged_file_path = os.path.join(
        ookla_data_path, f"{country}_{year}_{quarter}_ookla.geojson"
    )

    # TODO: come up with naming conventions
    boundary_file_path = os.path.join(hdx_data_path, boundary_file)

    if not os.path.exists(boundary_file_path):
        raise Exception("Cannot continue, boundary shapes missing!")

    if not os.path.exists(merged_file_path):
        raise Exception("Filtered ookla data not found!")

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

    buffer_aggregate_country = gpd.sjoin(
        cluster_centroid_df,
        tiles_in_country.drop(["index_right"], axis=1),
        how="inner",
        predicate="intersects",
    )
    mean_download_by_cluster = (
        buffer_aggregate_country[["DHSID", "avg_d_mbps"]]
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
