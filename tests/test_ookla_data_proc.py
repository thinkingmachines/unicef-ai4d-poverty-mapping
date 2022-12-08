import pytest
import shutil

import pandas as pd
# import geopandas as gpd
import os
from pathlib import Path
from povertymapping.ookla_data_proc import process_ookla_data


@pytest.fixture()
def ooklaconfig():
    yield dict(
        save_path="test_data/outputs/ookla",
        repo_path="test_data/inputs",
        data_dir="tl",
        country="tl",
        ookla_folder="ookla_tl",
        hdx_folder="hdx_tl",
        dhs_geo_zip_folder="TLGE71FL",
        crs="4683",
        ookla_feature="avg_d_mbps",
        boundary_file="new_suco_map",
        year="2019",
        quarter="2",
        sample=False,
        random_sample=False,
        no_samples=60,
        random_seed=42,
        clust_rad=2000,
        plot_ookla_features=True,
        adm_level=3,
        use_pcode=False,
        shape_label='SUCO_NUMCD',
        bins=6,
        show_legend=False,
    )

def test_process_ookla_data(ooklaconfig, capsys):
    # clear out output data dir
    save_path = ooklaconfig["save_path"]
    shutil.rmtree(save_path, ignore_errors=True)
    # setup dhs data
    os.makedirs(Path(save_path))
    # copy dhs preproc data from output of tl process_dhs_data - TLGE71FL_cluster_coords.csv to save path
    shutil.copy("test_data/real_outputs/dhs_tl/TLGE71FL_cluster_coords.csv",(Path(save_path)/"TLGE71FL_cluster_coords.csv").as_posix())
    process_ookla_data(ooklaconfig)
    assert Path(save_path).exists()
    assert (Path(save_path)/"tl_2019_2_avg_d_mbps.csv").exists()
    assert (Path(save_path)/"new_suco_map_avg_d_mbps.jpeg").exists()
    ookla_by_cluster_df = pd.read_csv(Path(save_path)/"tl_2019_2_avg_d_mbps.csv")
    assert len(ookla_by_cluster_df) == 28
