
from povertymapping.iso3 import get_iso3_codes, get_iso3_code 
import pandas as pd
import pytest

@pytest.fixture
def mock_pd(mocker):
    mock_df = pd.DataFrame.from_records([{
        "name": "Afghanistan",
        "alpha-3": "AFG",
    }])
    mocker.patch('pandas.read_csv', return_value=mock_df)
    yield

def test_get_iso3_codes(mock_pd):
    iso3_codes = get_iso3_codes()
    assert "afghanistan" in iso3_codes


def test_get_iso3_code(mock_pd):
    assert get_iso3_code('afghanistan') == 'AFG'
