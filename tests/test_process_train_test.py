import pytest
import pandas as pd
import shutil
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
        ntl_path = "TLGE71FL_cluster_coords_gee_agg",
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
    assert (Path(save_path)/'data_final.pkl').exists()
    assert (Path(save_path)/'TLGE71FL_features.pkl').exists()
    assert (Path(save_path)/'TLGE71FL_labels.pkl').exists()
    df = pd.read_pickle(Path(save_path)/'data_final.pkl')
    assert len(df) == 455
    assert len(list(df.columns.values)) == 60
    features = pd.read_pickle(Path(save_path)/'TLGE71FL_features.pkl')
    assert len(features) == 455
    assert len(list(features.columns.values)) == 58
    labels = pd.read_pickle(Path(save_path)/'TLGE71FL_labels.pkl')
    assert len(labels) == 455




