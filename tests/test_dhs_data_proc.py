import pytest
import shutil

import pandas as pd
import geopandas as gpd
from pathlib import Path
from povertymapping.dhs_data_proc import process_dhs_data


@pytest.fixture()
def dhsconfig():
    yield dict(
        save_path="test_data/outputs/dhs",
        repo_path="test_data/inputs",
        data_dir="ph",
        dhs_folder="dhs_ph",
        dhs_zip_folder="PHHR71DT",
        dhs_file="PHHR71DT.DTA",
        country="ph",
        dhs_geo_zip_folder="PHGE71FL",
        dhs_geo_file="PHGE71FL.shp",
    )


expected_out = """Data Dimensions: (1000, 15)
Data Dimensions: (679, 1)
"""


def test_process_dhs_data(dhsconfig, capsys):
    # clear out output data dir
    save_path = dhsconfig["save_path"]
    shutil.rmtree(save_path, ignore_errors=True)
    #
    process_dhs_data(dhsconfig)
    assert (Path(save_path)).exists()
    assert (Path(save_path) / "PHHR71DT_raw.csv").exists()
    assert (Path(save_path) / "PHHR71DT_base.csv").exists()
    assert (Path(save_path) / "PHGE71FL_cluster_coords.csv").exists()
    assert (Path(save_path) / "PHHR71DT_PHGE71FL_by_cluster.csv").exists()
    assert (Path(save_path) / "PHHR71DT_PHGE71FL_by_cluster.geojson").exists()

    raw = pd.read_csv(Path(save_path) / "PHHR71DT_raw.csv")
    assert raw.shape == (1000, 15)
    base = pd.read_csv(Path(save_path) / "PHHR71DT_base.csv")
    assert base.shape == (1000, 15)
    coords = pd.read_csv(Path(save_path) / "PHGE71FL_cluster_coords.csv")
    assert coords.shape == (679, 8)
    cluster = pd.read_csv(Path(save_path) / "PHHR71DT_PHGE71FL_by_cluster.csv")
    assert cluster.shape == (679, 9)
    gdf = gpd.read_file(Path(save_path) / "PHHR71DT_PHGE71FL_by_cluster.geojson")
    assert gdf.shape == (679, 9)
    assert gdf.crs == "EPSG:4326"
    cap = capsys.readouterr()
    assert cap.out == expected_out
