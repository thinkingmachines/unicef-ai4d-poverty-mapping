import shutil
from types import SimpleNamespace
# import pandas as pd
# import geopandas as gpd
from pathlib import Path
from povertymapping.osm_data_proc import process_osm_data
import os


if __name__ == "__main__":  # noqa

    args = SimpleNamespace(slice_interval="[0,100]")
    osmconfig = dict(
        save_path="test_data/test_outputs/osm", # output directory
        repo_path="test_data/inputs", # input directory root
        data_dir="tl", # input dir folder (usually country)
        country="tl", # country
        dhs_folder="dhs_tl", # dhs folder
        dhs_geo_zip_folder="TLGE71FL", # folder holding DHS shape files
        use_pbf=False,
        multiprocess=False,
        args=args,
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
    # clear out output data dir
    save_path = osmconfig["save_path"]
    shutil.rmtree(save_path, ignore_errors=True)
    #
    os.makedirs(Path(save_path))
    # copy dhs preproc data from output of tl process_dhs_data - TLGE71FL_cluster_coords.csv to save path
    shutil.copy("data/outputs/dhs_tl/TLGE71FL_cluster_coords.csv",(Path(save_path)/"TLGE71FL_cluster_coords.csv").as_posix())

    process_osm_data(osmconfig)

