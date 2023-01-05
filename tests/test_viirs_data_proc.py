import pytest
import shutil
# from types import SimpleNamespace
# import pandas as pd
# import geopandas as gpd
from pathlib import Path
from povertymapping.viirs_data_proc import process_viirs_data
import os

@pytest.fixture()
def viirsconfig():
    # args = SimpleNamespace(slice_interval="[0,100]")
    yield dict(
        # save_path="test_data/test_outputs/osm", # output directory
        # repo_path="test_data/inputs", # input directory root
        # data_dir="tl", # input dir folder (usually country)
        # country="tl", # country
        # dhs_folder="dhs_tl", # dhs folder
        # dhs_geo_zip_folder="TLGE71FL", # folder holding DHS shape files
        # use_pbf=False,
        # multiprocess=False,
        # args=args,
        # osm_country="tl",
        # osm_folder="osm_tl",
        # sample=False,
        # no_samples=60,
        # random_sample=False,
        # random_seed=42,
        # buffer_side_length=4.0,
        # crs="4683",
        # osm_shp_filename="east-timor-latest-free.shp",
        # osm_pbf_filename="east-timor-latest.osm.pbf",
        bbox_size=2000,
        save_path="test_data/test_outputs/viirs_tl",
        # repo_path="../data/SVII_PH_KH_MM_TL",
        viirs_tif_path="test_data/inputs/tl/viirs_tl/eog_viirs_tl_2016.tif",
        # data_dir="ph",
        country="tl",
        # viirs_folder="viirs_tl",
        # hdx_folder="hdx_tl",
        # dhs_folder="dhs_tl",
        dhs_geo_zip_folder="TLGE71FL",
        # dhs_zip_folder="TLHR71DT",
        crs="4683",
        viirs_feature="avg_rad",
        # boundary_file="new_suco_map",
        year="2016",
        # sample=False,
        # random_sample=False,
        # no_samples=60,
        # random_seed=42,
        # clust_rad=2000,
        # plot_viirs_features=True,
        # adm_level=3,
        # use_pcode=True,
        # shape_label='ADM3_PCODE',
        # bins=6,
        # show_legend=False,
    
    )



def test_process_dhs_data(viirsconfig):
    # clear out output data dir
    save_path = viirsconfig["save_path"]
    shutil.rmtree(save_path, ignore_errors=True)
    #
    os.makedirs(Path(save_path))
    # copy dhs preproc data from output of tl process_dhs_data - TLGE71FL_cluster_coords.csv to save path
    shutil.copy("data/outputs/dhs_tl/TLGE71FL_cluster_coords.csv",(Path(save_path)/"TLGE71FL_cluster_coords.csv").as_posix())

    process_viirs_data(viirsconfig)
    assert (Path(save_path)).exists()
    assert (Path(save_path)/'tl_2016_viirs_avg_rad_zonal_stats.csv').exists()
    assert (Path(save_path)/'tl_2016_viirs_avg_rad_zonal_stats.gpkg').exists()
    # assert (Path(save_path) / "PHHR71DT_raw.csv").exists()
    # assert (Path(save_path) / "PHHR71DT_base.csv").exists()
    # assert (Path(save_path) / "PHGE71FL_cluster_coords.csv").exists()
    # assert (Path(save_path) / "PHHR71DT_PHGE71FL_by_cluster.csv").exists()
    # assert (Path(save_path) / "PHHR71DT_PHGE71FL_by_cluster.geojson").exists()

    # raw = pd.read_csv(Path(save_path) / "PHHR71DT_raw.csv")
    # assert raw.shape == (1000, 15)
    # base = pd.read_csv(Path(save_path) / "PHHR71DT_base.csv")
    # assert base.shape == (1000, 15)
    # coords = pd.read_csv(Path(save_path) / "PHGE71FL_cluster_coords.csv")
    # assert coords.shape == (679, 8)
    # cluster = pd.read_csv(Path(save_path) / "PHHR71DT_PHGE71FL_by_cluster.csv")
    # assert cluster.shape == (679, 9)
    # gdf = gpd.read_file(Path(save_path) / "PHHR71DT_PHGE71FL_by_cluster.geojson")
    # assert gdf.shape == (679, 9)
    # assert gdf.crs == "EPSG:4326"
