import shutil
from types import SimpleNamespace
# import pandas as pd
# import geopandas as gpd
from pathlib import Path
from povertymapping.osm_data_proc import process_osm_data
import os


if __name__ == "__main__":  # noqa
    args = SimpleNamespace(slice_interval="[0,100]")
    osm_config = dict(
        save_path="data/outputs/osm_ph",
        repo_path="data/SVII_PH_KH_MM_TL",
        data_dir="ph", # input dir folder (usually country)
        country="ph", # country
        dhs_folder="osm_ph", # dhs folder
        dhs_geo_zip_folder="PHGE71FL", # folder holding DHS shape files
        use_pbf=False,
        multiprocess=False,
        args=args,
        osm_country="ph",
        osm_folder="osm_ph",
        sample=False,
        no_samples=60,
        random_sample=False,
        random_seed=42,
        buffer_side_length=4.0,
        crs="4683",
        osm_shp_filename="philippines-latest-free.shp",
        osm_pbf_filename="philippines-latest.osm.pbf",
        clust_rad=2000

    )

    args = SimpleNamespace(slice_interval="[0,100]")
    # clear out output data dir
    save_path = osm_config["save_path"]
    shutil.rmtree(save_path, ignore_errors=True)
    #
    os.makedirs(Path(save_path))
    # copy dhs preproc data from output of tl process_dhs_data - TLGE71FL_cluster_coords.csv to save path
    shutil.copy("data/outputs/dhs_ph/PHGE71FL_cluster_coords.csv",(Path(save_path)/"PHGE71FL_cluster_coords.csv").as_posix())

    process_osm_data(osm_config)

