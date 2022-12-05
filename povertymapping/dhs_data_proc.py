import os

import geopandas as gpd
import pandas as pd
import yaml
from utils.data_utils import aggregate_dhs, get_base_dhs_df

if __name__ == "__main__":

    config = yaml.safe_load(open("config.yml"))
    # create output directory
    save_path = config["save_path"]
    if not os.path.isdir(save_path):
        os.makedirs(save_path)

    # setup upload paths
    folder_name = config["dhs_folder"]  # maybe avoid this???
    data_dir = os.path.join(config["data_dir"].split("/")[-1], folder_name)
    dhs_zip_folder = config["dhs_zip_folder"]

    dvc_folder_name = config["dhs_target_folder_name"]
    repo_path = config["repo_path"]

    # no lambda hook
    # path_map = lambda x: os.path.join(repo_path, config['data_dir'], x, folder_name)

    def path_map(x):
        return os.path.join(repo_path, config["data_dir"], x, folder_name)

    reg_path, dvc_path = list(map(path_map, ["", dvc_folder_name]))

    if os.path.exists(reg_path):
        data_path = reg_path  # or some function of reg_path
    elif os.path.exists(dvc_path):
        data_path = dvc_path  # or some function of dvc_path
    else:
        raise Exception("DHS survey data missing!")

    # get base dhs table
    dhs_file = os.path.join(data_path, dhs_zip_folder, config["dhs_file"])
    dhs_dict_file = os.path.join(data_path, dhs_zip_folder, config["dhs_dict_file"])
    dhs = get_base_dhs_df(dhs_file, dhs_dict_file)
    # check shape
    print("Data Dimensions: {}".format(dhs.shape))
    # save base dhs csv
    dhs.to_csv(os.path.join(save_path, f"{dhs_zip_folder}_base.csv"))
    # aggregate by cluster
    survey_data = aggregate_dhs(dhs)
    print("Data Dimensions: {}".format(survey_data.shape))

    # process geospatial
    dhs_geo_zip_folder = config["dhs_geo_zip_folder"]
    dhs_geo_file = config["dhs_geo_file"]
    shp_file_path = os.path.join(data_path, dhs_geo_zip_folder, dhs_geo_file)
    data = gpd.read_file(shp_file_path)

    # process gps coordinates per cluster
    cluster_coords = pd.DataFrame(
        {
            "DHSID": data["DHSID"],
            "DHSCLUST": data["DHSCLUST"],
            "longitude": data["LONGNUM"],
            "latitude": data["LATNUM"],
        }
    )
    cluster_coords.to_csv(
        os.path.join(save_path, f"{dhs_geo_zip_folder}_cluster_coords.csv")
    )

    # combine survey with geo data
    survey_geo = pd.merge(survey_data, cluster_coords, on="DHSCLUST")
    # NOTE: there are 36 clusters without geo location info
    # save combined base csv
    survey_geo.to_csv(
        os.path.join(save_path, f"{dhs_zip_folder}_{dhs_geo_zip_folder}_by_cluster.csv")
    )
