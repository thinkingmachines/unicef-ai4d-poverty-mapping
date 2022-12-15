import os

import geopandas as gp
import pandas as pd
# import yaml

from povertymapping.utils.data_utils import (
    add_buffer_geom,
    # compute_feat_by_adm,
    get_missing_data_dist,
)


def get_geoframe(hrsl_path):
    """Convert hrsl dataframe into a geo dataframe

    Args:
        hrsl_path (str): path to hrsl file

    Returns:
        GeoDataFrame: hrsl geodataframe
    """

    hrsl = pd.read_csv(hrsl_path)

    lons, lats = hrsl["longitude"], hrsl["latitude"]
    hrsl_geo = gp.GeoDataFrame(hrsl, geometry=gp.points_from_xy(lons, lats))
    return hrsl_geo


# if __name__ == "__main__":
def process_train_test(config):
    # read in config
    # config = yaml.safe_load(open("config.yml"))
    # country = config["osm_country"]
    # create output directory
    save_path = config["save_path"]
    if not os.path.isdir(save_path):
        os.makedirs(save_path)

    data_path = "data_labels.csv"
    data = pd.read_csv(os.path.join(save_path, data_path))

    # drop additional column from multiprocessing
    if config["multiprocess"]:
        data = data.drop("Unnamed: 0.1", errors="ignore", axis=1)

    dhs_geo_zip_folder = config["dhs_geo_zip_folder"]

    cluster_coords_filename = f"{dhs_geo_zip_folder}_cluster_coords"
    cluster_centroid_df = pd.read_csv(
        os.path.join(save_path, f"{cluster_coords_filename}.csv")
    )

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

    dhs_geo_zip_folder = config["dhs_geo_zip_folder"]
    osm_path = f"{dhs_geo_zip_folder}_cluster_coords_osm_agg.csv"
    # from guild run
    # osm_df = pd.read_csv(osm_path)
    # # from repo
    osm_df = pd.read_csv(os.path.join(save_path, osm_path))

    if config["use_ntl"]:
        if "ntl_path" in config:
            ntl_path = config["ntl_path"]
        else:
            ntl_path = f"{dhs_geo_zip_folder}_cluster_coords_gee_agg.csv"
        # from guild run
        # gee_df = pd.read_csv(ntl_path)
        # # from repo
        gee_df = pd.read_csv(os.path.join(save_path, ntl_path))

        _, complete_gee_feats = get_missing_data_dist(gee_df, null_val=None)

    # exclude rows with null wealth index labels
    data_wo_null = data[~data["Wealth Index"].isna()]

    # extract boundary data
    # repo_dir = config["repo_dir"]
    # data_dir = os.path.join(repo_dir, config["data_dir"], config["hdx_folder"])

    # boundary_file_path = os.path.join(data_dir, config["boundary_file"])

    # ph_boundaries = gp.read_file(boundary_file_path).to_crs(crs)

    # restrict to clusters used in 2017 paper
    if config["use_filt_clt"]:
        crs = config["crs"]

        hrsl_path = config["filt_filename"]
        hrsl_geo = get_geoframe(hrsl_path)

        # convert cluster df into geoframe using polygonal geoemtry
        add_buffer_geom(cluster_centroid_df, r=config["clust_rad"])
        cluster_centroid_df = gp.GeoDataFrame(cluster_centroid_df, geometry="geometry")
        cluster_centroid_df.crs = f"EPSG:{crs}"

        # perform spatial join with buffer cluster df
        geometry_and_mean = gp.sjoin(
            cluster_centroid_df, hrsl_geo, how="inner", predicate="intersects"
        )

        # extract population column names
        column_names = hrsl_geo.columns
        pop_col_names = [col for col in column_names if "population" in col]

        geometry_and_mean_cluster = (
            geometry_and_mean.groupby(["DHSID", "DHSCLUST"])
            .sum()
            .reset_index()[["DHSID", "DHSCLUST"] + pop_col_names]
        )

        # population min threshold
        thresh = config["pop_thresh"]
        DHSCLUST_to_exclude = geometry_and_mean_cluster[
            geometry_and_mean_cluster[pop_col_names[0]] < thresh
        ]["DHSCLUST"]
        # filtered_DHSCLUST = list(
        #     set(cluster_centroid_df.DHSCLUST) - set(DHSCLUST_to_exclude)
        # )

        # geometry_and_mean_cluster_geo = gp.GeoDataFrame(
        #     pd.merge(
        #         geometry_and_mean_cluster,
        #         geometry_and_mean[["DHSID", "geometry"]],
        #         how="inner",
        #     ),
        #     geometry="geometry",
        # )

        # for visualization
        # feature = "population_2015"
        # features_list = [feature]
        # to_map_data_left = compute_feat_by_adm(
        #     ph_boundaries, geometry_and_mean_cluster_geo, features_list, config
        # )

        data_wo_null = data_wo_null[~data_wo_null.DHSCLUST.isin(DHSCLUST_to_exclude)]

    # else:
    #     # the following csv only applies to ph
    #     if country == "ph":
    #         # osm_roads_path = "/home/butchtm/work/povmap/povmap-int/output/osm_roads.csv"  # 'osm_roads.csv'
    #         osm_roads_path = os.path.join(
    #             repo_dir, "output/osm_roads.csv"
    #         )  # 'osm_roads.csv'
    #         osm_roads = pd.read_csv(osm_roads_path)
    #         # check with clusters ids in osm_roads
    #         data_wo_null = data_wo_null[data_wo_null.DHSCLUST.isin(osm_roads.DHSCLUST)]
    #     else:
    #         # perform some operation on data_wo_null that doesn't require population estimate data
    #         # e.g. select a specific demographic or region
    #         data_wo_null = data_wo_null  # TODO: implement filtering by region

    # print("Filtered!")

    # restrict to subset of columns for train
    columns = []
    features = []
    # identifier
    columns.append("DHSID")
    # label
    columns.append("Wealth Index")
    # features
    if config["use_ntl"]:
        features.extend(complete_gee_feats)
    # # add binned radiance feature
    # features.extend(quartile_features)

    osm_features = osm_df.columns[3:-1]
    features.extend(osm_features)
    features.append("avg_d_mbps")
    columns.extend(features)
    # full data
    data_final = data_wo_null[columns]

    # replace nans in ookla column with 0
    # TODO: add a one hot encoding for ookla nan versus not nan
    replace_na_col = "avg_d_mbps"
    data_final[replace_na_col] = data_final[replace_na_col].fillna(0)

    # apparently there are nans in other columns
    # NOTE: just as a temporary solution we replace all nas with 0
    data_final = data_final.fillna(0)

    # train test split
    label_name = "Wealth Index"

    X = data_final[features]
    y = data_final[label_name]

    def path_map(x):
        return os.path.join(save_path, f"{dhs_geo_zip_folder}_{x}.pkl")

    features_path, labels_path = list(map(path_map, ["features", "labels"]))

    # pickle
    print("Saving pickled files...")
    X.to_pickle(features_path)
    y.to_pickle(labels_path)

    # also save DHSID and wealth index pair for visualization in evaluation script
    data_final.to_pickle(os.path.join(save_path, "data_final.pkl"))
