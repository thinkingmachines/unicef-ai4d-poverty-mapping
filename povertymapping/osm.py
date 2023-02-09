import uuid

import geopandas as gpd
from geowrangler import distance_zonal_stats as dzs
from geowrangler import vector_zonal_stats as vzs
from geowrangler.datasets.geofabrik import OsmDataManager

DEFAULT_POI_TYPES = [
    "atm",
    "bank",
    "bus_station",
    "cafe",
    "charging_station",
    "courthouse",
    "dentist",
    "fast_food",
    "fire_station",
    "food_court",
    "fuel",
    "hospital",
    "library",
    "marketplace",
    "pharmacy",
    "police",
    "post_box",
    "post_office",
    "restaurant",
    "social_facility",
    "supermarket",
    "townhall",
]


def add_osm_poi_features(
    aoi,
    country,
    osm_data_manager:OsmDataManager,
    use_cache=True,
    poi_types=DEFAULT_POI_TYPES,
    metric_crs="epsg:3857",
    inplace=False,
    nearest_poi_max_distance=10_000,
):
    """Generates features for the AOI based on OSM POI data (POIs, roads, etc)."""

    # Load-in the OSM POIs data
    osm = osm_data_manager.load_pois(country, use_cache=use_cache)

    # Create a copy of the AOI gdf if not inplace to avoid modifying the original gdf
    if not inplace:
        aoi = aoi.copy()

    # GeoWrangler: Count number of all POIs per tile
    aoi = vzs.create_zonal_stats(
        aoi,
        osm,
        overlap_method="intersects",
        aggregations=[{"func": "count", "output": "poi_count", "fillna": True}],
    )

    # Count specific aoi types
    for poi_type in poi_types:
        # GeoWrangler: Count with vector zonal stats
        aoi = vzs.create_zonal_stats(
            aoi,
            osm[osm["fclass"] == poi_type],
            overlap_method="intersects",
            aggregations=[
                {"func": "count", "output": f"{poi_type}_count", "fillna": True}
            ],
        )

        # GeoWrangler: Distance with distance zonal stats
        col_name = f"{poi_type}_nearest"
        aoi = dzs.create_distance_zonal_stats(
            aoi.to_crs(metric_crs),
            osm[osm["fclass"] == poi_type].to_crs(metric_crs),
            max_distance=nearest_poi_max_distance,
            aggregations=[],
            distance_col=col_name,
        ).to_crs("epsg:4326")

        # If no POI was found within the distance limit, set the distance to the max distance
        aoi[col_name] = aoi[col_name].fillna(value=nearest_poi_max_distance)

    return aoi


def add_osm_road_features(
    aoi, country, osm_data_manager, use_cache=True, inplace=False
):
    """Generates features for the AOI based on OSM road data"""
    roads_gdf = osm_data_manager.load_roads(country, use_cache=use_cache)
    assert aoi.crs == roads_gdf.crs

    if not inplace:
        aoi = aoi.copy()

    # Create a temporary ID column to use for our processing
    # Assign simple integer values
    temp_id = str(uuid.uuid4())
    aoi[temp_id] = list(range(len(aoi)))

    # Get intersections between the AOIs and the roads
    joined = gpd.sjoin(aoi, roads_gdf, how="inner", predicate="intersects")

    # Count the number of roads that intersected
    road_stats_df = joined.groupby(temp_id)["index_right"].agg(road_count="count")
    # Join back to the original AOI gdf
    aoi = aoi.join(road_stats_df, how="left", on=temp_id)

    # There might be AOIs that did not intersect with any roads at all
    aoi["road_count"] = aoi["road_count"].fillna(0)

    # Remove the temporary ID column
    del aoi[temp_id]

    return aoi


