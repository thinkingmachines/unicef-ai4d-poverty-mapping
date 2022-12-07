import pytest
import shutil

# import pandas as pd
# import geopandas as gpd
import os
from pathlib import Path
from povertymapping.ookla_data_proc import process_ookla_data


@pytest.fixture()
def ooklaconfig():
    yield dict(
        save_path="test_data/outputs/ookla",
        year="2019",
        quarter="2",
        repo_path="test_data",
        boundary_file="new_suco_map",
        data_dir="inputs",
        crs="4683",
        ookla_feature="avg_d_mbps",
        ookla_folder="ookla_tl",
        hdx_folder="hdx_tl",
        country="tl",
        dhs_geo_zip_folder="TLGE71FL",
    )

def test_process_ookla_data(ooklaconfig, capsys):
    # clear out output data dir
    save_path = ooklaconfig["save_path"]
    shutil.rmtree(save_path, ignore_errors=True)
    # setup dhs data
    os.makedirs(Path(save_path))
    # copy dhs preproc data from tl process_dhs_data - TLGE71FL_cluster_coords.csv
    shutil.copy("test_data/real_outputs/dhs_tl/TLGE71FL_cluster_coords.csv",Path(save_path)/"TLGE71FL_cluster_coords.csv")
    # to save_path
    process_ookla_data(ooklaconfig)
    assert Path(save_path/"tl_2019_2_avg_d_mbps.csv").exists()
    # assert (Path(save_path)).exists()
    # assert (Path(save_path) / "dhs_ph_raw.csv").exists()
    # assert (Path(save_path) / "dhs_ph_base.csv").exists()
    # assert (Path(save_path) / "dhs_ph_cluster_coords.csv").exists()
    # assert (Path(save_path) / "dhs_ph_dhs_ph_by_cluster.csv").exists()
    # assert (Path(save_path) / "dhs_ph_dhs_ph_by_cluster.geojson").exists()

    # raw = pd.read_csv(Path(save_path) / "dhs_ph_raw.csv")
    # assert raw.shape == (1000, 15)
    # base = pd.read_csv(Path(save_path) / "dhs_ph_base.csv")
    # assert base.shape == (1000, 15)
    # coords = pd.read_csv(Path(save_path) / "dhs_ph_cluster_coords.csv")
    # assert coords.shape == (679, 8)
    # cluster = pd.read_csv(Path(save_path) / "dhs_ph_dhs_ph_by_cluster.csv")
    # assert cluster.shape == (679, 9)
    # gdf = gpd.read_file(Path(save_path) / "dhs_ph_dhs_ph_by_cluster.geojson")
    # assert gdf.shape == (679, 9)
    # assert gdf.crs == "EPSG:4326"
    # cap = capsys.readouterr()
    # assert cap.out == expected_out
