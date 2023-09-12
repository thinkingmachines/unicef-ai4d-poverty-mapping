import uuid

from relativewealth.geoboundaries import get_geoboundaries


def test_get_geoboundaries(tmpdir, mocker):
    mock_file = mocker.MagicMock()
    expected_return = (mock_file, None, None)
    mocker.patch(
        "relativewealth.geoboundaries.urlretrieve", return_value=expected_return
    )
    mock_cache_dir = str(tmpdir / str(uuid.uuid4()))

    result = get_geoboundaries("afghanistan", cache_dir=mock_cache_dir)
    assert result is mock_file
