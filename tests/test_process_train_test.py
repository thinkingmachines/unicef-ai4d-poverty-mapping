import pytest
import shutil
# from types import SimpleNamespace
# import pandas as pd
# import geopandas as gpd
from pathlib import Path
from povertymapping.process_train_test import process_train_test
import os

@pytest.fixture()
def process_train_test_config():
    yield dict(
        save_path="test_data/test_outputs/tl", # output directory
        dhs_geo_zip_folder="TLGE71FL", # folder holding DHS shape files
        use_ntl=True,
        use_filt_clt=False,
        multiprocess=False,
        ntl_path = "TLGE71FL_cluster_coords_gee_agg.csv",
        sample=False,
        no_samples=60,
        random_sample=False,
        random_seed=42,
        crs="4683",
        clust_rad=2000
    )

@pytest.fixture()
def process_train_test_config_ph():
    yield dict(
        save_path="test_data/test_outputs/ph", # output directory
        dhs_geo_zip_folder="PHGE71FL", # folder holding DHS shape files
        use_ntl=True,
        use_filt_clt=False,
        multiprocess=False,
        ntl_path = "ph_2017_viirs_avg_rad_zonal_stats.csv",
        sample=False,
        no_samples=60,
        random_sample=False,
        random_seed=42,
        crs="4683",
        clust_rad=2000
    )


def test_process_train_test(process_train_test_config):
    # clear out output data dir
    save_path = process_train_test_config["save_path"]
    shutil.rmtree(save_path, ignore_errors=True)
    #
    os.makedirs(Path(save_path))
    # copy dhs preproc data from output of tl process_dhs_data - TLGE71FL_cluster_coords.csv to save path
    shutil.copy("data/outputs/dhs_tl/TLGE71FL_cluster_coords.csv",(Path(save_path)/"TLGE71FL_cluster_coords.csv").as_posix())
    shutil.copy("data/outputs/osm_tl/TLGE71FL_cluster_coords_osm_agg.csv",(Path(save_path)/"TLGE71FL_cluster_coords_osm_agg.csv").as_posix())
    shutil.copy("data/outputs/ntl_tl/TLGE71FL_cluster_coords_gee_agg.csv",(Path(save_path)/"TLGE71FL_cluster_coords_gee_agg.csv").as_posix())
    shutil.copy("test_data/inputs/tl/prepare_train_tl/data_labels.csv",(Path(save_path)/"data_labels.csv").as_posix())

    process_train_test(process_train_test_config)
    assert (Path(save_path)).exists()

def test_process_train_test_ph(process_train_test_config_ph):
    # clear out output data dir
    save_path = process_train_test_config_ph["save_path"]
    shutil.rmtree(save_path, ignore_errors=True)
    #
    os.makedirs(Path(save_path))
    # copy dhs preproc data from output of tl process_dhs_data - TLGE71FL_cluster_coords.csv to save path
    shutil.copy("data/outputs/dhs_ph/PHGE71FL_cluster_coords.csv",(Path(save_path)/"PHGE71FL_cluster_coords.csv").as_posix())
    shutil.copy("data/outputs/osm_ph/PHGE71FL_cluster_coords_osm_agg.csv",(Path(save_path)/"PHGE71FL_cluster_coords_osm_agg.csv").as_posix())
    shutil.copy("data/outputs/viirs_ph/ph_2017_viirs_avg_rad_zonal_stats.csv",(Path(save_path)/"ph_2017_viirs_avg_rad_zonal_stats.csv").as_posix())
    shutil.copy("data/outputs/training_ph/data_labels.csv",(Path(save_path)/"data_labels.csv").as_posix())

    process_train_test(process_train_test_config_ph)
    assert (Path(save_path)).exists()
