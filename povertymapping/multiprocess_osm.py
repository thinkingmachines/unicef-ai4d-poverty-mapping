import os
import pandas as pd
from povertymapping.osm_data_proc import process_osm_data

def compute_intervals(no_rows):
    no_cpu = os.cpu_count()
    interval_len = no_rows // no_cpu
    intervals = [[interval_len * i, interval_len * (i + 1)] for i in range(no_cpu)]

    # we might miss the last few rows if no_cpu doesn't divide into no_rows exactly
    # we fix this by changing the last interval to cover the tail
    intervals[-1] = [intervals[-1][0]]
    return intervals


def merge_osm_intervals(config, intervals):

    # we might miss the last few rows if no_cpu doesn't divide into no_rows exactly
    # we fix this by changing the last interval to cover the tail
    save_path = config["save_path"]

    dhs_geo_zip_folder = config["dhs_geo_zip_folder"]
    cluster_coords_filename = f"{dhs_geo_zip_folder}_cluster_coords"
  
    intervals_str = ["".join(f"{interval}".split(" ")) for interval in intervals]

    # read in list of generated dataframes
    dfs = [
        pd.read_csv(f"{save_path}/{cluster_coords_filename}_osm_agg_{interval}.csv")
        for interval in intervals_str
    ]
    # concat vertically
    result_df = pd.concat(dfs, axis=0)
    # result using mp matches original :)
    # NOTE: index and column 'Unnamed: 0' differ from original but all features match
    #       for now, we will ignore reindexing and/or modifying column 'Unnamed: 0'
    #       to match original

    # TODO: after concatenation is successful, delete partitioned dataframes
    #       to save save space :)

    # delete subframes
    for interval in intervals_str:
        file_path = f"{save_path}/{cluster_coords_filename}_osm_agg_{interval}.csv"
        if os.path.exists(file_path):
            os.remove(file_path)
    return result_df