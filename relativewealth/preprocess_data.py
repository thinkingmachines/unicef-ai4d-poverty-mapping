import osmium
import yaml
import os

import geopandas as gpd
import pandas as pd

from relativewealth.utils.data_utils import get_title_url


# let's write a class that parses tags
# ref: https://oslandia.com/en/2017/07/10/osm-tag-genome-how-are-osm-objects-tagged/
class TagGenomeHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.taggenome = []

    def str_list_way_nodes(self, way):
        elem_nodes_refs = [x.ref for x in way.nodes]
        return " ".join(str(x) for x in elem_nodes_refs)

    def tag_inventory(self, elem, elem_type):
        lat, lon = -1, -1
        nodes_str = ""
        if elem_type == "node":
            lat, lon = elem.location.lat, elem.location.lon
        elif elem_type == "way":
            nodes_str = self.str_list_way_nodes(elem)

        for tag in elem.tags:
            self.taggenome.append(
                [
                    elem_type,
                    elem.id,
                    pd.Timestamp(elem.timestamp),
                    elem.version,
                    nodes_str,
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


def preprocess_osm_pbf(config, cluster_id):
    """Preprocess osm pbf file into dataframe"""
    # extract some osm config params
    country = config["osm_country"]

    taghandler = TagGenomeHandler()
    cluster_filename = f"{country}_{cluster_id}.osm.pbf"
    pbf_filepath = os.path.join(config["save_path"], cluster_filename)
    taghandler.apply_file(pbf_filepath)

    colnames = [
        "type",
        "id",
        "ts",
        "version",
        "nodes_str",
        "lat",
        "lon",
        "tagkey",
        "tagvalue",
    ]
    tag_genome = pd.DataFrame(taghandler.taggenome, columns=colnames)

    return tag_genome


def preprocess_ookla(config):

    repo_path = config["repo_path"]
    crs = config["crs"]
    country = config["country"]
    year = config["year"]  # TODO: change param year to ookla year
    quarter = config["quarter"]  # TODO: change param qurater to ookla quarter
    hdx_folder = config["hdx_folder"]
    hdx_data_path = os.path.join(repo_path, config["data_dir"], hdx_folder)
    boundary_file = config["boundary_file"]  # make this more generic

    print("Downloading from s3 bucket...")
    ookla_s3_download_url = get_title_url("fixed", year, quarter)
    tiles = gpd.read_file(ookla_s3_download_url).to_crs(
        crs
    )
    boundary_file_path = os.path.join(hdx_data_path, boundary_file)
    country_boundaries = gpd.read_file(boundary_file_path).to_crs(crs)
    tiles_in_country = gpd.sjoin(
        tiles, country_boundaries, how="inner", predicate="intersects"
    ).to_crs(crs)

    # save geojson file
    merged_file_path = os.path.join(
        config["data_dir"], f"{country}_{year}_{quarter}_ookla.geojson"
    )
    tiles_in_country.to_file(merged_file_path, driver="GeoJSON")


