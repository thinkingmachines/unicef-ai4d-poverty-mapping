
import pytest
import shutil

from fastcore.all import *
from pathlib import Path
from povertymapping.dhs_data_proc import process_dhs_data

@pytest.fixture()
def dhsconfig():
    yield dict(
        save_path="test_data/outputs/dhs",
        repo_path="test_data",
        data_dir="inputs",
        dhs_folder="ph",
        dhs_zip_folder="dhs_ph",
        dhs_file="ph.DTA",
        country="ph",
        dhs_geo_zip_folder="dhs_ph",
        dhs_geo_file="ph_gps.shp"

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
    assert (Path(save_path)/"dhs_ph_raw.csv").exists()
    assert (Path(save_path)/"dhs_ph_base.csv").exists()
    assert (Path(save_path)/"dhs_ph_cluster_coords.csv").exists()
    assert (Path(save_path)/"dhs_ph_dhs_ph_by_cluster.csv").exists()
    cap = capsys.readouterr()
    assert cap.out == expected_out
    
