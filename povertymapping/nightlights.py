import geowrangler.raster_zonal_stats as rzs

from geowrangler.datasets.nightlights import (
    get_clipped_raster,
    EOG_VIIRS_DATA_TYPE,
    EOG_PRODUCT_VERSION,
    EOG_PRODUCT,
    EOG_COVERAGE,
    NIGHTLIGHTS_CACHE_DIR,
    get_eog_access_token, # forward access
)


def generate_nightlights_feature(
    aoi,
    year,
    viirs_data_type=EOG_VIIRS_DATA_TYPE.AVERAGE,
    version=EOG_PRODUCT_VERSION.VER21,
    product=EOG_PRODUCT.ANNUAL,
    coverage=EOG_COVERAGE.GLOBAL,
    cache_dir=NIGHTLIGHTS_CACHE_DIR,
    process_suffix="c202205302300",
    vcmcfg="vcmslcfg",
    extra_args=dict(band_num=1, nodata=-999),
    func=["min", "max", "mean", "median", "std"],
    column="avg_rad",
    copy=False,
):
    clipped_raster_file = get_clipped_raster(
        year,
        aoi.total_bounds,
        viirs_data_type=viirs_data_type,
        version=version,
        product=product,
        coverage=coverage,
        cache_dir=cache_dir,
        process_suffix=process_suffix,
        vcmcfg=vcmcfg,
    )
    if copy:
        aoi = aoi.copy()
    aoi = rzs.create_raster_zonal_stats(
        aoi,
        clipped_raster_file.as_posix(),
        aggregation=dict(
            func=func,
            column=column,
        ),
        extra_args=extra_args,
    )
    return aoi
