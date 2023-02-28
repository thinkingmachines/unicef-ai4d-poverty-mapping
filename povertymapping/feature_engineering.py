from povertymapping import ookla, nightlights, osm
from povertymapping.osm import OsmDataManager
from povertymapping.ookla import OoklaDataManager
from typing import Any
from sklearn.preprocessing import StandardScaler
import pandas as pd

DEFAULT_CACHE_DIR = "~/.geowrangler"


def generate_features(
    aoi: pd.DataFrame,
    country_osm: str,
    ookla_year: int,
    nightlights_year: int,
    inplace: bool = False,
    cache_dir: str = DEFAULT_CACHE_DIR,
    fill_na: bool = True,
    fill_na_value: int = 0,
    scale: bool = True,
    sklearn_scaler: Any = StandardScaler,
    scaled_only: bool = False,
    features_only: bool = False,
) -> pd.DataFrame:
    """Generates the base features for an AOI based on
    DHS, OSM, Ookla, and VIIRS (nighttime lights) data

    Args:
        aoi (pd.DataFrame): The input AOI dataframe.
        country_osm (str): The name of country to load features from OSM. For more information about
            supported countries, refer to Geofabrik documentation: https://download.geofabrik.de/index.html
        ookla_year (int): The year of Ookla data to use. Earliest available is 2019.
        nightlights_year (int): The year of nighttime lights data to use. Earliest available is 2012.
        inplace (bool, optional): Whether to overwrite the original dataframe or not. Defaults to False.
        cache_dir (str, optional): The path to the data directory where downloaded data is cached. Defaults to ~/.geowrangler.
        fill_na (bool, optional): Whether to fill missing values with fill_na_value or not. Defaults to True.
        fill_na_value (int, optional): The value to fill missing values. Defaults to 0.
        scale (bool, optional): Whether to scale the generated features or not. Defaults to True.
        sklearn_scaler (Any, optional): The scikit-learn scaler to use. Only applied if scale_features = True. Defaults to StandardScaler.
        scaled_only (bool, optional): Whether to return only the scaled features or not. Defaults to False.
        features_only (bool, optional): Whether to return only the generated features or not. Defaults to False.

    Returns:
        aoi (pd.DataFrame): The AOI dataframe with its new features.
    """
    # Make a copy of the dataframe to avoid overwriting the input data
    if not inplace:
        aoi = aoi.copy()

    # Store list of input columns
    input_cols = aoi.columns

    # Instantiate data managers for Ookla and OSM
    # This auto-caches requested data in RAM, so next fetches of the data are faster.
    osm_data_manager = OsmDataManager(cache_dir=cache_dir)
    ookla_data_manager = OoklaDataManager(cache_dir=cache_dir)

    # Add in OSM features
    aoi = osm.add_osm_poi_features(aoi, country_osm, osm_data_manager)
    aoi = osm.add_osm_road_features(aoi, country_osm, osm_data_manager)

    # Add in Ookla features
    aoi = ookla.add_ookla_features(aoi, "fixed", ookla_year, ookla_data_manager)
    aoi = ookla.add_ookla_features(aoi, "mobile", ookla_year, ookla_data_manager)

    # Add in the nighttime lights features
    aoi = nightlights.generate_nightlights_feature(
        aoi, nightlights_year, cache_dir=f"{cache_dir}/nightlights"
    )

    # Get list of features generated
    feature_cols = [x for x in aoi.columns if x not in input_cols]

    # Scale the features using the provided scaler
    if scale:
        scaler = sklearn_scaler()
        for col in feature_cols:
            aoi[col + "_scaled"] = scaler.fit_transform(aoi[[col]])
        if scaled_only:
            aoi = aoi.drop(columns=feature_cols)

    if fill_na:
        aoi = aoi.fillna(fill_na_value)

    # Drop the input columns, leaving only the features
    if features_only:
        aoi = aoi.drop(columns=input_cols)

    return aoi


def generate_labels(
    aoi: pd.DataFrame,
    label_col: str,
    inplace: bool = False,
    fill_na: bool = True,
    fill_na_value: int = 0,
    scale: bool = True,
    sklearn_scaler: Any = StandardScaler,
    labels_only: bool = False,
) -> pd.DataFrame:
    """Generates labels for an AOI based on a specified column.

    Args:
        aoi (pd.DataFrame): The input AOI dataframe.
        label_col (str): The column to use as the label.
        inplace (bool, optional): Whether to overwrite the original dataframe or not. Defaults to False.
        data_dir (str, optional): The path to the data directory. Defaults to settings.DATA_DIR.
        fill_na (bool, optional): Whether to fill missing values with fill_na_value or not. Defaults to True.
        fill_na_value (int, optional): The value to fill missing values. Defaults to 0.
        scale (bool, optional): Whether to scale the generated label or not. Defaults to True.
        sklearn_scaler (Any, optional): The scikit-learn scaler to use. Only applied if scale = True. Defaults to StandardScaler.
        labels_only (bool, optional): Whether to return only the generated labels or not. Defaults to False.

    Returns:
        aoi (pd.DataFrame): The AOI dataframe with its new labels.
    """
    # Make a copy of the dataframe to avoid overwriting the input data
    if not inplace:
        aoi = aoi.copy()

    # Store list of input columns
    input_cols = aoi.columns

    # Assign label to input dataframe
    aoi["label"] = aoi[label_col]

    # Scale the features using the provided scaler
    if scale:
        scaler = sklearn_scaler()
        aoi["label"] = scaler.fit_transform(aoi[["label"]])

    if fill_na:
        aoi = aoi.fillna(fill_na_value)

    # Drop the input columns, leaving only the features
    if labels_only:
        aoi = aoi.drop(columns=input_cols)

    return aoi
