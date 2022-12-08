import os
from datetime import datetime
from functools import partial

import geopandas as gp
import matplotlib
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyproj
import seaborn as sns
import tqdm
from haversine import Direction, inverse_haversine
from shapely.geometry import Point
from shapely.ops import transform
from sklearn.decomposition import PCA


def process_asset_features(
    dhs,
    features=[
        "rooms",
        "electric",
        "mobile telephone",
        "radio",
        "television",
        "car/truck",
        "refrigerator",
        "motorcycle",
        "floor",
        "toilet",
        "drinking water",
    ],
):
    """Extract sustainbench asset features

    Args:
        dhs (pd.DataFrame): dataframe with unaggregated features and wealth index
        features (list): feature kwds list to extract
    Returns:
        pd.DataFrame: dataframe with corresp. features
    """

    # we will take the unaggregated dhs survey data
    # and process asset features
    # not all columns will be the same across diff countries
    # so we first extract the relevant columns using kwds
    # in fact, the same kwds found in sustainbench

    extract_feature_label = lambda feature: [x for x in dhs.columns if feature in x]

    feature_labels = list(map(extract_feature_label, features))

    if any([len(l) == 0 for l in feature_labels]):
        print(feature_labels)
        raise Exception("Asset feature label(s) couldn't be found!")

    result_df = dhs[[label_list[0] for label_list in feature_labels]]
    # we rename the columns for consistency across diff surveys
    result_df.columns = features

    return result_df


def normalize_array(array):
    """Normalize array to 0 and 1
    Args:
        array (np.array): array to be normalized to 0 and 1
    Returns:
        np.array: array scaled with range 0 to 1.
    """
    return (array - np.min(array)) / (np.max(array) - np.min(array))


def extract_recode():
    """Return recode dictionary

    Args:
        None

    Returns:
        dict: dictionary of recode csv files corresp. to "floor", "toilet", and "water"
    """

    # since recode csvs are small
    # we will store them as pairs of lists

    # floor recode
    floor_code = [
        11,
        12,
        13,
        21,
        22,
        23,
        31,
        32,
        33,
        34,
        35,
        36,
        37,
        38,
        41,
        96,
        99,
        24,
        39,
    ]
    floor_qual = [1, 1, 3, 4, 4, 3, 5, 4, 5, 4, 3, 4, 4, 3, 2, 1, 1, 5, 5]
    floor_recode = pd.DataFrame({"floor_code": floor_code, "floor_qual": floor_qual})

    # toilet recode
    toilet_code = [
        11,
        12,
        13,
        14,
        15,
        17,
        18,
        19,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        31,
        32,
        41,
        42,
        43,
        44,
        45,
        51,
        61,
        71,
        91,
        92,
        96,
        99,
        30,
        16,
    ]
    toilet_qual = [
        5,
        5,
        4,
        5,
        5,
        5,
        5,
        1,
        4,
        3,
        2,
        3,
        2,
        2,
        3,
        3,
        1,
        1,
        1,
        4,
        2,
        3,
        4,
        3,
        1,
        1,
        1,
        4,
        2,
        1,
        1,
        1,
        4,
    ]
    toilet_recode = pd.DataFrame(
        {"toilet_code": toilet_code, "toilet_qual": toilet_qual}
    )

    # water recode
    water_code = [
        11,
        12,
        13,
        14,
        21,
        22,
        23,
        24,
        25,
        26,
        31,
        32,
        33,
        34,
        35,
        36,
        41,
        42,
        43,
        44,
        45,
        46,
        51,
        52,
        53,
        54,
        55,
        61,
        62,
        63,
        64,
        71,
        72,
        73,
        81,
        82,
        91,
        92,
        96,
        99,
        37,
        38,
        15,
    ]
    water_qual = [
        5,
        5,
        5,
        4,
        3,
        3,
        3,
        2,
        2,
        1,
        4,
        4,
        4,
        4,
        3,
        2,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        2,
        3,
        4,
        4,
        2,
        3,
        5,
        5,
        3,
        1,
        2,
        4,
        3,
        1,
        1,
        2,
        2,
        4,
    ]
    water_recode = pd.DataFrame({"water_code": water_code, "water_qual": water_qual})

    feats = ["floor", "toilet", "water"]
    recode_dfs = [floor_recode, toilet_recode, water_recode]
    recode_dict = dict(zip(feats, recode_dfs))

    return recode_dict


def assign_index(
    df,
    features=[
        "rooms",
        "electric",
        "mobile telephone",
        "radio",
        "television",
        "car/truck",
        "refrigerator",
        "motorcycle",
        "floor",
        "toilet",
        "drinking water",
    ],
    file_suff="",
    use_pca=True,
    threshold=False,
    normalize=False,
    config=None,
):
    """Compute and assign new wealth index on a subset of features
    Args:
        df (pd.DataFrame): survey data with asset features
    Returns:
        None
    """

    # TODO: drop na rows and save corresp indices
    asset_df = process_asset_features(df, features)

    # apply individual threshold (as in sustainbench)
    asset_df.loc[:, "rooms"] = asset_df["rooms"].apply(lambda x: 25 if x > 25 else x)

    # apply recode (as in sustainbench)
    recode_dict = extract_recode()
    for col in ["drinking water", "toilet", "floor"]:

        col_abb = col.split()[-1]
        asset_df.loc[:, col] = asset_df[col].replace(recode_dict[col_abb])

    if normalize:
        asset_df = asset_df.apply(normalize_array, axis=1)

    # TODO: Check floating number issue
    if use_pca:
        pca = PCA(1)
        pca.fit(asset_df.values)

        first_comp_vec_scaled = np.matmul(asset_df, pca.components_.T).squeeze()

    else:
        asset_df = asset_df.apply(lambda x: x - x.mean(), axis=1)
        u, s, _ = np.linalg.svd(asset_df.values.T, full_matrices=False)
        orthog_pc1_proj = np.matmul(asset_df, u[0])
        first_comp_vec_scaled = s[0] * orthog_pc1_proj

    df.loc[:, f"Recomputed Wealth Index{file_suff}"] = first_comp_vec_scaled


def quarter_start(year: int, q: int):
    """Return quarter datetime object"""
    if not 1 <= q <= 4:
        raise ValueError("Quarter must be within [1, 2, 3, 4]")

    month = [1, 4, 7, 10]
    return datetime(year, month[q - 1], 1)


def get_title_url(service_type: str, year: int, q: int):
    """Get url to s3 bucket"""
    dt = quarter_start(year, q)

    base_url = (
        "https://ookla-open-data.s3-us-west-2.amazonaws.com/shapefiles/performance"
    )
    url = f"{base_url}/type%3D{service_type}/year%3D{dt:%Y}/quarter%3D{q}/{dt:%Y-%m-%d}_performance_fixed_tiles.zip"
    return url


def create_polygon_buffer(lon, lat, r):
    """Return circular shapely 64-sided polygon object with radius r"""

    # NOTE: ~71m radius -> 16km square area
    local_azimuthal_projection = (
        f"+proj=aeqd +R=6371000 +units=m +lat_0={lat} +lon_0={lon}"
    )

    wgs84_to_aeqd = partial(
        pyproj.transform,
        pyproj.Proj("+proj=longlat +datum=WGS84 +no_defs"),
        pyproj.Proj(local_azimuthal_projection),
    )
    aeqd_to_wgs84 = partial(
        pyproj.transform,
        pyproj.Proj(local_azimuthal_projection),
        pyproj.Proj("+proj=longlat +datum=WGS84 +no_defs"),
    )

    center = Point(float(lon), float(lat))
    point_transformed = transform(wgs84_to_aeqd, center)
    point_buffer = point_transformed.buffer(r)

    # Get the polygon with lat lon coordinates
    circle_poly = transform(aeqd_to_wgs84, point_buffer)
    return circle_poly


def add_buffer_geom(cluster_centroid_df, r=4000):
    """Add buffer geometry to dhs cluster data (i.e. 6th column)
    Args:
        cluster_centroid_df (pd.DataFrame): DHS data frame
        config (dict): config yaml file
        r (int): buffer radius in meters
    Returns:
        geopandas.GeoDataFrame
    """

    centroids = list(
        zip(cluster_centroid_df["LATNUM"], cluster_centroid_df["LONGNUM"])
    )
    buffer_geometry = []
    print("Adding buffer geometry...")
    for cluster in tqdm.tqdm(centroids, total=cluster_centroid_df.shape[0]):
        lon, lat = cluster[1], cluster[0]

        # Q: Should we use empty geometry objects (i.e. Polygon([]))?
        polygon_buffer = None
        if lon != 0 and lat != 0:
            polygon_buffer = create_polygon_buffer(lon, lat, r)
        buffer_geometry.append(polygon_buffer)

    cluster_centroid_df["geometry"] = buffer_geometry


# def compute_feat_by_adm(boundaries_df, features_by_cluster, features_list, config):
def compute_feat_by_adm(boundaries_df, features_by_cluster, config):
    """Return feature mean, grouping by adm level
    Args:
        boundaries_df (geopandas.GeoDataFrame): geo dataframe containing adm level boundary shapes
        features_by_cluster (geopandas.GeoDataFrame): geo dataframe containing cluster buffer shapes and features
        features_list (list): list of features to aggregate by adm level
    """
    crs = config["crs"]

    # TODO: save boundary shape by adm level and save as json before uploading to GCS
    #       then name using adm level subscripts

    adm_level = config["adm_level"]
    geometry_and_cluster_features = gp.sjoin(
        features_by_cluster, boundaries_df, how="inner", predicate="intersects"
    ).to_crs(crs)

    use_pcode = config["use_pcode"]
    if use_pcode:
        group_indices = [f"ADM{adm_level}_PCODE", f"ADM{adm_level}_EN"]
    else:
        group_indices = [config["shape_label"]]

    geometry_and_mean_by_adm = (
        geometry_and_cluster_features.groupby(group_indices).mean().reset_index()
    )

    # perform left outer join
    geom_label = group_indices[0]
    to_map_data_left = pd.merge(
        boundaries_df[[geom_label, "geometry"]],
        geometry_and_mean_by_adm,
        on=geom_label,
        how="left",
    )

    return to_map_data_left

    # group_indices = [f"ADM{adm_level}_PCODE", f"ADM{adm_level}_EN"]
    # geometry_and_mean_by_adm = geometry_and_cluster_features.groupby(group_indices).mean().reset_index()

    # # perform left outer join
    # to_map_data_left = pd.merge(boundaries_df[[f"ADM{adm_level}_PCODE", "geometry"]], geometry_and_mean_by_adm, on=f"ADM{adm_level}_PCODE", how='left')

    # return to_map_data_left


def save_cmap(
    geo_df,
    title,
    column,
    save_file_path,
    remove_white=True,
    feature_series=None,
    plot_title="Ground Truth",
    config=None,
):
    """Save color map plot"""

    # plot
    fig, ax = plt.subplots(figsize=(12, 10))

    if remove_white:
        # remove white/light color from cmap
        min_val, max_val = 0.3, 1.0
        n = 10
        orig_cmap = plt.cm.Blues
        colors = orig_cmap(np.linspace(min_val, max_val, n))
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list("mycmap", colors)
    else:
        cmap = "Blues"

    plt.title(plot_title, x=0.5, y=0.95)
    # plt.rcParams["legend.loc"] = 'upper left'  # apparently does not work
    if feature_series is not None:
        # Normalizer
        col_series = feature_series
        vmin, vmax = col_series.min(), col_series.max()
        norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

        # custom cmap removing white
        # min_val, max_val = 0.3, 1.0
        # TODO: rewrite method signature to include param config so bins can be extracted!
        bins = config["bins"]
        min_val, max_val = 1.0 / bins, 1.0
        # min_val, max_val = vmin, vmax
        n = 10
        orig_cmap = plt.cm.Blues
        colors = orig_cmap(np.linspace(min_val, max_val, n))
        mycmap = matplotlib.colors.LinearSegmentedColormap.from_list("mycmap", colors)

        # creating ScalarMappable
        sm = plt.cm.ScalarMappable(cmap=mycmap, norm=norm)
        sm.set_array([])
        plt.colorbar(
            sm, orientation="horizontal", fraction=0.046, pad=0.04, shrink=0.70
        )
        # cbar = plt.colorbar(sm, orientation='horizontal', fraction=0.046, pad=0.04, shrink=0.70)

        # cbar.ax.set_xticklabels(['Low', 'Medium', 'High'])

    geo_df.plot(
        column=column, cmap=cmap, linewidth=0.1, ax=ax, edgecolor="0.1", legend=True
    )
    ax.axis("off")  # eliminates grid

    if config["show_legend"]:
        # place legend on the upper left corner
        leg = ax.get_legend()
        # leg.set_bbox_to_anchor(loc='upper right')
        # leg.set_bbox_to_anchor((0.37, 0.8))
        leg.set_title(title)
    else:
        ax.get_legend().remove()

    # plt.legend(loc="upper left")

    # save figure
    # make sure save_file_path
    # has not white space
    # plot_title_stripped = "_".join(plot_title.lower().split())
    # path_comps = save_file_path.split("/")
    # file_name = (
    #     "_".join(["_".join(path_comps[1:-1]), "".join(path_comps[-1].split())])[:-5]
    #     + "_" + plot_title_stripped
    #     + ".jpeg"
    # )
    # dir_path = path_comps[
    #     0
    # ]  # TODO: can you do this by passing **args to os.path.join method ???
    # save_file_path = os.path.join(dir_path, file_name)

    fig.savefig(save_file_path)

    plt.clf()


def plot_feature_by_adm(
    admin_data,
    config,
    col="avg_d_mbps_wt",
    leg_title="Mean download speed",
    unit="Mbps",
    display_cmap=False,
    plot_title="Ground Truth",
):
    """Plot features grouping by adm level"""
    # calculate range
    feature_series = admin_data[col]
    left = feature_series.min()
    right = feature_series.max()

    bins = config["bins"]
    d = (right - left) / bins
    cuts = tuple([left + d * i for i in range(-1, bins)])
    # d = (right - left) / 5
    # cuts = tuple([left + d*i for i in range(-1,6)])
    labels = []
    labels.append("NA")
    # construct labels
    upper_cuts = cuts[1:]  # lol
    for i, _ in enumerate(upper_cuts):
        if i == bins - 1:
            break
        le = round(upper_cuts[i], 2)
        re = round(upper_cuts[i + 1], 2)
        label = f"{le} to {re}"
        labels.append(label)
    # TODO: fix label duplicates error

    # replace NAs with the first bin value so we see empty boundaries
    null_val_rep = left - d
    feature_series = feature_series.fillna(null_val_rep)

    # labels = ["NA", "0 to 10 Mbps", "10 to 20 Mbps", "20 to 30 Mbps", "30 to 40 Mbps", "40 to 50 Mbps"]
    admin_data["group"] = pd.cut(feature_series, cuts, right=False, labels=labels)

    output_filename = config["boundary_file"]
    save_path = config["save_path"]
    save_file_path = os.path.join(save_path, f"{output_filename}_{col}.jpeg")
    column = "group"

    adm_level = config["adm_level"]
    # title = "Mean download speed (Mbps)\nin PH admin level 3"
    # TODO: find a more generic elegant formatting for legend title
    country = config["country"].upper()
    title = f"{leg_title}\n({unit})\n{country} admin level {adm_level}"

    if not display_cmap:
        feature_series = None

    save_cmap(
        admin_data,
        title,
        column,
        save_file_path,
        False,
        feature_series=feature_series,
        plot_title=plot_title,
        config=config,
    )


def generate_osm_bbox(centroid_lat, centroid_lon, distance_km):
    """Return bbox ee geometry object using haversine distance function"""
    centroid = (centroid_lat, centroid_lon)
    top_left = inverse_haversine(
        inverse_haversine(centroid, distance_km / 2, Direction.WEST),
        distance_km / 2,
        Direction.NORTH,
    )
    bottom_right = inverse_haversine(
        inverse_haversine(centroid, distance_km / 2, Direction.EAST),
        distance_km / 2,
        Direction.SOUTH,
    )

    north, west = top_left
    south, east = bottom_right

    # check inequalities
    assert west < east
    assert south < north

    bbox_coord_list = [west, south, east, north]

    return bbox_coord_list


def get_bbox_str(bbox_list):
    "Convert bbox list into string"
    return ",".join([str(round(x, 3)) for x in bbox_list])


def get_no_roads(df):
    """Sum up the number of roads (motorway, trunk, primary, secondary,
    tertiary, unclassified, and residential)
    """
    roads = get_roads(df)

    # no labmda hook
    # get_road_type = lambda x: roads[roads.tagvalue == x]

    def get_road_type(x):
        return roads[roads.tagvalue == x]

    primary_roads, trunk_roads = [get_road_type(x) for x in ["primary", "trunk"]]

    road_cts = {
        "no_roads": roads.shape[0],
        "no_primary_roads": primary_roads.shape[0],
        "no_trunk_roads": trunk_roads.shape[0],
    }

    return road_cts


def generate_cluster_buffer_df(cluster, config):
    """Return spatial intersection with cluster buffer
    Args:
        cluster (tuple): tuple of the form (lat, lon, cluster_id)
        config (dict): config params read from yml file
    Returns:
        geopandas.GeoDataFrame: merge resuts after performing spatial intersection
    """
    lon, lat = cluster[1], cluster[0]
    r = config["clust_rad"]
    polygon = create_polygon_buffer(lon, lat, r)
    polygon_df = pd.DataFrame(
        {"longitude": [lon], "latitude": [lat], "geometry": [polygon]}
    )
    crs = config["crs"]
    polygon_df_geo = gp.GeoDataFrame(polygon_df, geometry="geometry")
    polygon_df_geo.crs = f"EPSG:{crs}"
    return polygon_df_geo


# TODO: include radius inside config
#       so the polygon rad should correspond to sqrt(2) x 1/2 x distance_km (generate_bbox param)
def get_no_roads_shp(df, cluster, config):
    """Process road stats from geo pandas dataframe
    Args:
        df (pd.DataFrame): geopandas dataframe
        cluster (tuple): tuple of the form (lat, lon, cluster_id)
        config (dict): config params read from yml file
    Returns:
        dict: road count by type
    """

    # perform spatial join to restrict to a specific cluster

    # create 1-row dataframe with geometry being polygon above
    # lon, lat = cluster[1], cluster[0]
    # polygon = create_polygon_buffer(lon, lat, r)
    # polygon_df = pd.DataFrame({'longitude': [lon], 'latitude': [lat], 'geometry': [polygon]})
    # crs = config['crs']
    # polygon_df_geo = gp.GeoDataFrame(polygon_df, geometry='geometry')
    # polygon_df_geo.crs = f"EPSG:{crs}"

    polygon_df_geo = generate_cluster_buffer_df(cluster, config)
    crs = config["crs"]
    # # perform spatial join
    cluster_roads = gp.sjoin(
        df, polygon_df_geo, how="inner", predicate="intersects"
    ).to_crs(crs)
    primary_roads = cluster_roads[cluster_roads.fclass == "primary"]
    trunk_roads = cluster_roads[cluster_roads.fclass == "trunk"]

    # group by feature
    road_cts = {
        "no_roads": cluster_roads.shape[0],
        "no_primary_roads": primary_roads.shape[0],
        "no_trunk_roads": trunk_roads.shape[0],
    }

    return road_cts


def get_roads(df):
    """Extract highway rows from dataframe"""
    ways = df[df.type == "way"]
    highways = ways[ways.tagkey == "highway"]

    # what osm docs call roads
    road_tag_vals = [
        "tertiary",
        "residential",
        "primary",
        "trunk",
        "unclassified",
        "secondary",
        "service",
        "track",
        "pedestrian",
        "footway",
        "trunk_link",
    ]

    return highways[highways.tagvalue.isin(road_tag_vals)]


def get_no_intersections(df):
    """We simply find nodes that appear in more than one road"""

    # get highways that are considered roads according to osm docs
    roads = get_roads(df)

    # filter all nodes
    nodes = df[df.type == "node"]
    # get reference ids of all nodes
    node_ids = nodes.id

    # iterate through nodes and compute in how many
    # roads they appear
    no_intersections = 0
    for node in node_ids:

        # get the ref nodes list column for roads
        nodes_str = roads.nodes_str
        # find how many roads the given node appears
        node_freq = nodes_str.apply(lambda x: str(node) in x).sum()

        # TODO: fix null problem
        #       should we worry about nulls?

        if node_freq > 1:
            no_intersections += 1

    return no_intersections


def get_building_no(df, tags=["commercial", "school", "residential", "retail"]):
    """Compute count of different building types"""

    # we will focus on ways to count number of buildings
    # TODO: read up on relations and nodes tagged as buildings
    ways = df[df.type == "way"]

    buildings = ways[ways.tagkey == "building"]

    # no lambda hook
    # count_rows_by_type = lambda x: buildings[buildings.tagvalue == x].shape[0]

    def count_rows_by_type(x):
        return buildings[buildings.tagvalue == x].shape[0]

    result_dict = {}
    for tag in tags:
        result_dict[tag] = count_rows_by_type(tag)

    return result_dict


def get_building_no_shp(df, cluster, config):
    """Return number of buildings in cluster
    Args:
        df (pd.DataFrame): geopandas dataframe
        cluster (tuple): tuple of the form (lat, lon, cluster_id)
        config (dict): config params read from yml file
    Returns:
        int: buiding count

    """
    polygon_df_geo = generate_cluster_buffer_df(cluster, config)
    crs = config["crs"]
    # # perform spatial join
    cluster_buildings = gp.sjoin(
        df, polygon_df_geo, how="inner", predicate="intersects"
    ).to_crs(crs)

    return cluster_buildings.shape[0]


def get_pois(df):
    """Count points of interest appearing as nodes, ways, and relations"""

    tagkeys = [
        "amenity",
        "aeroway",
        "railway",
        "tourism",
        "place",
        "shop",
        "leisure",
        "historic",
    ]

    # no lambda hook
    # extract_tag = lambda tag: df[df.tagkey == tag]

    def extract_tag(tag):
        return df[df.tagkey == tag]

    tagged_dfs = {tag: extract_tag(tag) for tag in tagkeys}

    tagvals = [
        [
            "marketplace",
            "charging_station",
            "post_box",
            "post_office",
            "pharmacy",
            "hospital",
            "dentist",
            "restaurant",
            "food_court",
            "cafe",
            "fast_food",
            "police",
            "townhall",
            "fire_station",
            "social_facility",
            "courthouse",
            "fuel",
            "bus_station",
            "bank",
            "atm",
            "library",
        ],
        ["helipad", "aerodrome"],
        ["subway_entrance"],
        ["hotel", "camp_site"],
        ["city"],
        ["convenience", "supermarket", "car_repair", "department_store", "computer"],
        ["playground"],
        ["monument"],
    ]

    tag_key_val_dict = dict(zip(tagkeys, tagvals))

    result_dict = {}
    for key in tag_key_val_dict:

        tagged_df = tagged_dfs[key]
        # access corresp. tag values
        tag_vals = tag_key_val_dict[key]
        for tag_val in tag_vals:
            result_dict[f"{tag_val}_count"] = tagged_df[
                tagged_df.tagvalue == tag_val
            ].shape[0]

    return result_dict


def get_pois_shp(df, cluster, config):
    """Count points of interest appearing as nodes, ways, and relations
    Args:
        df (pd.DataFrame): geopandas dataframe
        cluster (tuple): tuple of the form (lat, lon, cluster_id)
        config (dict): config params read from yml file
    Returns:
        dict: poi count by category
    """

    polygon_df_geo = generate_cluster_buffer_df(cluster, config)

    crs = config["crs"]
    # # perform spatial join
    pois = gp.sjoin(df, polygon_df_geo, how="inner", predicate="intersects").to_crs(crs)

    poi_labels = [
        "marketplace",
        "charging_station",
        "post_box",
        "post_office",
        "pharmacy",
        "hospital",
        "dentist",
        "restaurant",
        "food_court",
        "cafe",
        "fast_food",
        "police",
        "townhall",
        "fire_station",
        "social_facility",
        "courthouse",
        "fuel",
        "bus_station",
        "bank",
        "atm",
        "library",
        "helipad",
        "aerodrome",
        "subway_entrance",
        "hotel",
        "camp_site",
        "city",
        "convenience",
        "supermarket",
        "car_repair",
        "department_store",
        "computer",
        "playground",
        "monument",
    ]

    result_dict = {}
    for poi_label in poi_labels:
        result_dict[f"{poi_label}_count"] = pois[pois.fclass == poi_label].shape[0]

    return result_dict


def plot_feature_distribution(
    df,
    col="avg_rad_median",
    xlabel="radiance(nanoWatts/cm2/sr)",
    output_path="output",
    save=False,
):
    """Save feature distribution plot"""

    df[col].plot.hist(bins=50)
    plt.xlabel("radiance(nanoWatts/cm2/sr)")
    plt.xlabel(xlabel)
    # plt.show()
    plt.tight_layout()
    if save:
        filepath = os.path.join(output_path, f"{col}.jpeg")
        plt.savefig(filepath)

    plt.clf()


def get_missing_data_dist(df, null_val=0, start_idx=3, end_idx=-1):
    """Find distribution of features with null or missing values"""
    missing_data = {}
    complete_cols = []
    for col_name in df.columns[start_idx:end_idx]:
        if null_val == 0:
            null_count = (df[col_name] == null_val).sum()
        elif null_val is None:
            null_count = df[col_name].isna().sum()
        missing_data[col_name] = null_count
        if null_count == 0:
            complete_cols.append(col_name)

    return missing_data, complete_cols


def plot_null_dist(df, data_type, null_val, save=False, save_path="output"):
    """Save feature null distribution plot"""
    missing_data, _ = get_missing_data_dist(df, null_val)
    series_result = pd.Series(missing_data)
    plt.title("Missing data histogram")
    plt.xlabel("No. of missing entries")

    series_result.plot.hist(bins=25, label=data_type)
    plt.legend()
    plt.tight_layout()

    if save:
        plt.savefig(os.path.join(save_path, f"{data_type}_missing_data_hist_.jpeg"))

    plt.clf()


def plot_corr_matrix(
    df, gee=True, stats="median", filename="corr", save=False, output_path="output"
):
    """Plot correlation matrix"""
    # TODO: fix slicing in case non-feature columns are accidentally included
    columns_subset = df.columns[3:-1]
    if gee:
        columns = list(
            set(["_".join(col.split("_")[:-1]) + f"_{stats}" for col in columns_subset])
        )
    else:
        columns = columns_subset

    plt.figure(figsize=(16, 10))
    sns.heatmap(df[columns].corr(), annot=True, fmt=".2g")
    plt.title("Correlation between Variables", fontsize=12)
    plt.tight_layout()

    if save:
        filepath = os.path.join(output_path, f"{filename}.jpeg")
        plt.savefig(filepath)

    plt.clf()


def run_osm_script(interval):
    os.system(f"python3 process/osm_data_proc.py --slice_interval {interval}")
