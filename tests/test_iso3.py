
from povertymapping.iso3 import get_iso3_codes, get_iso3_code 

def test_get_iso3_codes():
    iso3_codes = get_iso3_codes()
    assert iso3_codes is not None
    assert len(iso3_codes.keys()) == 249

def test_get_iso3_code():
    assert get_iso3_code('afghanistan') == 'AFG'
