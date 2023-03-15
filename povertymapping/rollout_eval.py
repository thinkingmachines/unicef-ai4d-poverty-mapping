from povertymapping.geoboundaries import get_geoboundaries
import geopandas as gpd
import geowrangler.vector_zonal_stats as vzs

DEFAULT_CACHE_DIR = "~/.cache/geowrangler"


def aggregate_grids_by_admin_bounds(
    grids,
    region,
    aggregations=[
        dict(column="Predicted Relative Wealth Index", output="Mean RWI", func="mean")
    ],
    adm="ADM0",
    dest=None,
    cache_dir=DEFAULT_CACHE_DIR,
    overwrite=False,
    show_progress=True,
    chunksize=8192,
):
    admin_bounds_file = get_geoboundaries(
        region=region,
        adm=adm,
        dest=dest,
        cache_dir=cache_dir,
        overwrite=overwrite,
        show_progress=show_progress,
        chunksize=chunksize,
    )

    admin_bounds_gdf = gpd.read_file(admin_bounds_file)
    admin_bounds_agg = vzs.create_zonal_stats(
        admin_bounds_gdf, grids, aggregations=aggregations
    )
    return admin_bounds_agg
