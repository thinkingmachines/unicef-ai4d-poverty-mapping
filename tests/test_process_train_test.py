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
    # args = SimpleNamespace(slice_interval="[0,100]")
    yield dict(
        save_path="test_data/test_outputs/tl", # output directory
        repo_path="test_data/inputs", # input directory root
        data_dir="tl", # input dir folder (usually country)
        country="tl", # country
        dhs_folder="dhs_tl", # dhs folder
        dhs_geo_zip_folder="TLGE71FL", # folder holding DHS shape files
        use_ntl=True,
        use_pbf=False,
        use_filt_clt=False,
        multiprocess=False,
        ntl_path = "TLGE71FL_cluster_coords_gee_agg.csv",
        # args=args,
        osm_country="tl",
        osm_folder="osm_tl",
        sample=False,
        no_samples=60,
        random_sample=False,
        random_seed=42,
        buffer_side_length=4.0,
        crs="4683",
        osm_shp_filename="east-timor-latest-free.shp",
        osm_pbf_filename="east-timor-latest.osm.pbf",
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
