import numpy as np

import geopandas as gpd
import geowrangler.area_zonal_stats as azs
from geowrangler.datasets.ookla import OoklaDataManager

from loguru import logger
from typing import Dict, Any

def add_ookla_features(
    aoi: gpd.GeoDataFrame,  # Area of interest
    type_: str,  # Ookla speed type: 'fixed` or `mobile`
    year: str,  # Year to aggregate (over 4 quarters)
    ookla_data_manager: OoklaDataManager,  # Ookla Data Manager Instance
    use_cache=True,  # Use cached data in cache dir as specified in ookla_data_manager
    metric_crs="epsg:3123",  # metric crs to use in calculating overlap
    inplace=False,  # Modify original aoi
    aggregations: Dict[  # Aggregation functions on ookla data (see https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.agg.html)
        str, Any
    ] = dict(
        mean_avg_d_kbps=("avg_d_kbps", "mean"),
        mean_avg_u_kbps=("avg_u_kbps", "mean"),
        mean_avg_lat_ms=("avg_lat_ms", "mean"),
        mean_num_tests=("tests", "mean"),
        mean_num_devices=("devices", "mean"),
    ),
):
    """Generates yearly aggregate features for the AOI based on Ookla data for a given type (fixed, mobile) and year."""

    # Create a copy of the AOI gdf if not inplace to avoid modifying the original gdf
    if not inplace:
        aoi = aoi.copy()

    ookla_yearly = ookla_data_manager.aggregate_ookla_features(
        aoi,
        type_,
        year,
        use_cache=use_cache,
        return_geometry=True,
        aggregations=aggregations,
    )
    # GeoWrangler: area zonal stats of features per AOI
    features = ookla_yearly.columns[
        ~ookla_yearly.columns.isin(["quadkey", "tile", "geometry"])
    ]
    agg_funcs = ["mean"]
    feature_aggregations = [
        dict(func=agg_funcs, column=feature) for feature in features
    ]
    logger.info(
        f"Creating ookla zonal stats for bounds {np.array2string(aoi.total_bounds, precision=6)} type {type_} year {year} "
    )
    aoi_orig_crs = aoi.crs
    aoi = azs.create_area_zonal_stats(
        aoi.to_crs(metric_crs),
        ookla_yearly.to_crs(metric_crs),
        feature_aggregations,
        include_intersect=False,
    ).to_crs(aoi_orig_crs)

    return aoi
