import argparse
import os
from collections import defaultdict

import geopandas as gp
import osmium
import pandas as pd
import tqdm
import yaml
from povertymapping.preprocess_data import preprocess_osm_pbf
from povertymapping.utils.data_utils import (
    generate_osm_bbox,
    get_bbox_str,
    get_building_no,
    get_building_no_shp,
    get_no_intersections,
    get_no_roads,
    get_no_roads_shp,
    get_pois,
    get_pois_shp,
)


# let's write a class that parses tags
# ref: https://oslandia.com/en/2017/07/10/osm-tag-genome-how-are-osm-objects-tagged/
class TagGenomeHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.taggenome = []

    def tag_inventory(self, elem, elem_type):
        lat, lon = -1, -1
        if elem_type == "node":
            lat, lon = elem.location.lat, elem.location.lon

        for tag in elem.tags:
            self.taggenome.append(
                [
                    elem_type,
                    elem.id,
                    pd.Timestamp(elem.timestamp),
                    elem.version,
                    lat,
                    lon,
                    tag.k,
                    tag.v,
                ]
            )

    def node(self, n):
        self.tag_inventory(n, "node")

    def way(self, w):
        self.tag_inventory(w, "way")

    def relation(self, r):
        self.tag_inventory(r, "relation")


# if __name__ == "__main__":  # noqa
def process_osm_data(config):
    # parse args for multiprocessing
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--slice_interval", help="wait", default="[0, 100]")
    # TODO: Find a solution to pass two arguments when pooling processes

    # args = parser.parse_args()
    args = config["args"]

    # read in config file
    # config = yaml.safe_load(open("config.yml"))

    if config["multiprocess"]:
        interval_str = args.slice_interval
        interval = eval(interval_str)


    # OSM path
    osm_filename = config[
        "osm_pbf_filename"
    ]
    data_dir = config["data_dir"]
    # filepath = os.path.join(data_dir, osm_filename)

    # create output path directory if it doesn't exist
    save_path = config["save_path"]
    if not os.path.isdir(save_path):
        os.makedirs(save_path)

    # extract some osm config params
    country = config["osm_country"]
    # year, month, day = config["osm_year"], config["osm_month"], config["osm_day"]

    repo_path = config["repo_path"]
    osm_folder = config["osm_folder"]

    # def path_map(x):
    #     return os.path.join(repo_path, config["data_dir"], x, osm_folder)

    # osm_dvc_folder = config["osm_target_folder_name"]

    # osm_reg_path, osm_dvc_path = list(map(path_map, ["", osm_dvc_folder]))
    osm_reg_path = os.path.join(repo_path, data_dir, osm_folder)


    if os.path.exists(osm_reg_path):
        osm_data_path = osm_reg_path  # or some function of reg_path
    # elif os.path.exists(osm_dvc_path):
    #     osm_data_path = osm_dvc_path  # or some function of dvc_path
    else:
        raise Exception(f"OSM data folder {osm_reg_path} is missing!")

    data_dir_osm = osm_data_path


    # read in househould cluster geo data
    # if config["use_sb_dhs"]:  
    #     sb_region = config["sb_region"]
    #     cluster_coords_filename = f"sustainbench_labels_{sb_region}"
    #     cluster_centroid_df = pd.read_csv(
    #         os.path.join(
    #             repo_path,
    #             data_dir,
    #             f"{cluster_coords_filename}.csv"
    #         )
    #     )
    # else:
    dhs_geo_zip_folder = config["dhs_geo_zip_folder"]

    cluster_coords_filename = f"{dhs_geo_zip_folder}_cluster_coords"
    cluster_centroid_df = pd.read_csv(
        os.path.join(save_path, f"{cluster_coords_filename}.csv")
    )

    # sample clusters
    if config["sample"]:
        no_samples = config["no_samples"]
        seed = config["random_seed"]
        if config["random_sample"]:
            cluster_centroid_df = cluster_centroid_df.sample(
                no_samples, random_state=seed
            )
        else:
            cluster_centroid_df = cluster_centroid_df.head(no_samples)

    if config["multiprocess"]:
        if len(interval) < 2:
            cluster_centroid_df = cluster_centroid_df.iloc[interval[0] :, :]
        else:
            cluster_centroid_df = cluster_centroid_df.iloc[interval[0] : interval[1], :]

    # we can perform a simple computation to count the number of buildings within a certain
    # distance_km using haversine distance
    lats = cluster_centroid_df["LATNUM"]
    lons = cluster_centroid_df["LONGNUM"]
    ids = cluster_centroid_df["DHSCLUST"]

    cluster_centroids = list(zip(lats, lons, ids))
    result_dict = defaultdict(list)

    distance_km = config["buffer_side_length"] #4.0  # units are in km

    # feature_names = ["no_roads", "no_buildings", "no_intersections"]

    if not config["use_pbf"]:
        print()
        print("Loading osm shape files by layer...")
        print("This might take a while...")
        print()

        osm_layers = [
            "gis_osm_roads_free",
            "gis_osm_pois_free",
            "gis_osm_buildings_a_free",
        ]

        def map_df(x):
            return os.path.join(data_dir_osm, "shape", config["osm_shp_filename"], x)

        paths = list(map(map_df, osm_layers))
        roads_df, pois_df, buildings_df = list(map(lambda x: gp.read_file(x), paths))

        crs = config["crs"]

        for layer_df in [roads_df, pois_df, buildings_df]:
            layer_df.crs = f"EPSG:{crs}"

    for cluster in tqdm.tqdm(cluster_centroids, total=cluster_centroid_df.shape[0]):

        # extract long lat
        centroid_lat = cluster[0]
        centroid_lon = cluster[1]
        cluster_id = cluster[2]

        result_dict["longitude"].append(centroid_lon)
        result_dict["latitude"].append(centroid_lat)

        # use pbf
        if config["use_pbf"]:
            extract_path = os.path.join(data_dir_osm, "pbf", osm_filename)
            # osmium bbox param
            centroid_bbox = generate_osm_bbox(centroid_lat, centroid_lon, distance_km)
            centroid_bbox_str = get_bbox_str(centroid_bbox)

            extract_cmd = f"osmium extract -b {centroid_bbox_str} {extract_path} -o {save_path}/{country}_{cluster_id}.osm.pbf"

            os.system(extract_cmd + " --overwrite" + " >/dev/null 2>&1")
            # now process the pbf extract
            try:
                features_df = preprocess_osm_pbf(config, cluster_id)
                # once data has been processed delete original generated pbf file
                os.system(f"rm {save_path}/{country}_{cluster_id}.osm.pbf")
            except Exception as e:  # TODO: find adequate error object
                raise RuntimeError("Error processing features from pbf file!") from e

            no_roads_dict = get_no_roads(features_df)
            no_buildings = get_building_no(features_df)
            no_pois = get_pois(features_df)

            # concatenate dict results
            features_dict = {**no_roads_dict, **no_buildings, **no_pois}

            # no of intersections
            result_dict["no_intersections"].append(get_no_intersections(features_df))

        else:

            no_roads_dict = get_no_roads_shp(roads_df, cluster, config)
            no_pois = get_pois_shp(pois_df, cluster, config)

            # concatenate dict results
            features_dict = {**no_roads_dict, **no_pois}

            no_of_buildings = get_building_no_shp(buildings_df, cluster, config)
            result_dict["building_ct"].append(no_of_buildings)

        for key in features_dict:
            result_dict[key].append(features_dict[key])

    # add cluster id column
    result_dict["DHSID"] = list(cluster_centroid_df["DHSID"])
    result_df = pd.DataFrame(result_dict)

    # save result
    print("Saving aggregate dataframe...")
    result_file_name = f"{cluster_coords_filename}_osm_agg.csv"
    if config["multiprocess"]:
        interval_str = "".join(f"{interval}".split(" "))
        result_file_name = f"{cluster_coords_filename}_osm_agg_{interval_str}.csv"
    result_save_path = os.path.join(save_path, result_file_name)

    result_df.to_csv(result_save_path)

# if __name__ == "__main__":  # noqa

#     # parse args for multiprocessing
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--slice_interval", help="wait", default="[0, 100]")
#     # TODO: Find a solution to pass two arguments when pooling processes

#     args = parser.parse_args()

#     # read in config file
#     config = yaml.safe_load(open("config.yml"))
#     config["args"] = args
#     process_osm_data(config)

