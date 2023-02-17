from povertymapping.geoboundaries import get_geoboundaries


def test_get_geoboundaries(tmpdir, mocker):
    mock_file = mocker.MagicMock()
    expected_return = (mock_file, None, None)
    mocker.patch('povertymapping.nightlights.urlretrieve', return_value=expected_return)
    mock_cache_dir = str(tmpdir/'this-directory-does-not-exist')
    result = get_geoboundaries('afghanistan', cache_dir=mock_cache_dir)
    assert result is not None