from povertymapping.rollout_grids import get_region_filtered_bingtile_grids
import pytest

@pytest.mark.slow
def test_get_region_filtered_bingtile_grids(mocker, tmpdir):
    cache_dir = str(tmpdir/'this-directory-does-not-exist')
    gdf = get_region_filtered_bingtile_grids('timor-leste', cache_dir=cache_dir)
    assert len(gdf) == 2024

@pytest.mark.slow
def test_get_region_filtered_bingtile_grids_with_parallel(tmpdir):
    cache_dir = str(tmpdir/'this-directory-does-not-exist')
    gdf = get_region_filtered_bingtile_grids('timor-leste', cache_dir=cache_dir, max_batch_size=50_000, n_workers=8)
    assert len(gdf) == 2024

@pytest.mark.slow
def test_get_region_filtered_bingtile_grids_batched(tmpdir):
    cache_dir = str(tmpdir/'this-directory-does-not-exist')
    gdf = get_region_filtered_bingtile_grids('timor-leste', cache_dir=cache_dir, max_batch_size=351)
    assert len(gdf) == 2024

@pytest.mark.slow
def test_get_region_filtered_bingtile_grids_with_batched_parallel(tmpdir):
    cache_dir = str(tmpdir/'this-directory-does-not-exist')
    gdf = get_region_filtered_bingtile_grids('timor-leste', cache_dir=cache_dir, max_batch_size=700, n_workers=4)
    assert len(gdf) == 2024

