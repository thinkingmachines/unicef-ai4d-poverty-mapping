import os
import warnings
import geopandas as gpd
import pandas as pd
# import yaml
from utils.data_utils import aggregate_dhs, get_base_dhs_df
import geowrangler.dhs as gdhs
class MissingDataException(Exception):
    pass

wealth_col_name = "Wealth Index"
cluster_col_name = "DHSCLUST"

def dhs_data_proc(config):

    save_path = config["save_path"]
    if not os.path.isdir(save_path):
        os.makedirs(save_path)

    folder_name = config["dhs_folder"]  
    dhs_zip_folder = config["dhs_zip_folder"]

    repo_path = config["repo_path"]

    reg_path = os.path.join(repo_path,config["data_dir"],folder_name )

    if os.path.exists(reg_path):
        data_path = reg_path  # or some function of reg_path
    else:
        raise MissingDataException("DHS survey data missing!")

    # get base dhs table
    dhs_file = os.path.join(data_path, dhs_zip_folder, config["dhs_file"])
    dhs_df = gdhs.load_dhs_file(dhs_file)
    # check shape
    print("Data Dimensions: {}".format(dhs_df.shape))
    # save raw dhs csv
    dhs_raw_output_file =  f"{dhs_zip_folder}_raw.csv"
    dhs_df.to_csv(os.path.join(save_path,dhs_raw_output_file))

    # rename columns
    country = config["country"]
    column_config = gdhs.load_column_config(country)
    dhs_df.rename(columns=column_config, inplace=True)
    dhs_base_output_file =  f"{dhs_zip_folder}_base.csv"
    dhs_df.to_csv(os.path.join(save_path, dhs_base_output_file))

    # aggregate by cluster
    survey_data = dhs_df[[wealth_col_name, cluster_col_name]].groupby(cluster_col_name).mean()
    print("Data Dimensions: {}".format(survey_data.shape))

    # process geospatial
    dhs_geo_zip_folder = config["dhs_geo_zip_folder"]
    dhs_geo_file = config["dhs_geo_file"]
    shp_file_path = os.path.join(data_path, dhs_geo_zip_folder, dhs_geo_file)
    dhs_shp = gpd.read_file(shp_file_path)
    dhs_cluster_coords_output_file =  f"{dhs_geo_zip_folder}_cluster_coords.csv"
    dhs_shp.to_csv(
        os.path.join(save_path,dhs_cluster_coords_output_file)
    )

    # combine survey with geo data
    survey_geo = pd.merge(survey_data, dhs_shp, on="DHSCLUST")
    survey_geo_output_file = "{dhs_zip_folder}_{dhs_geo_zip_folder}_by_cluster.csv"
    survey_geo.to_csv(
        os.path.join(save_path, survey_geo_output_file)
    )
