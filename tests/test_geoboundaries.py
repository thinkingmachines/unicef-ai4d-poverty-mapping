from povertymapping.geoboundaries import get_geoboundaries

import pytest
import pandas as pd


@pytest.fixture
def mock_geobounds_req(mocker):
    mock_df = pd.DataFrame.from_records(
        [
            {
                "name": "Afghanistan",
                "alpha-3": "AFG",
            }
        ]
    )
    mocker.patch("pandas.read_csv", return_value=mock_df)
    mock_resp = mocker.MagicMock()
    return_value = [{"gjDownloadURL": "https://example.com/afghanistan.geojson"}]
    mock_resp.json = mocker.MagicMock(return_value=return_value)
    mocker.patch("requests.get", return_value=mock_resp)
    yield


def test_get_geoboundaries(tmpdir, mocker, mock_geobounds_req):
    mock_file = mocker.MagicMock()
    expected_return = (mock_file, None, None)
    mocker.patch(
        "povertymapping.geoboundaries.urlretrieve", return_value=expected_return
    )
    mock_cache_dir = str(tmpdir / "this-directory-does-not-exist")

    result = get_geoboundaries("afghanistan", cache_dir=mock_cache_dir)
    assert result is mock_file
