import pandas as pd
import pytest

from povertymapping.iso3 import get_iso3_code, get_iso3_codes


def test_get_iso3_codes():
    iso3_codes = get_iso3_codes()
    assert "common-name" in iso3_codes
    assert "iso-alpha-2" in iso3_codes
    assert "iso-alpha-3" in iso3_codes


def test_get_iso3_code():
    assert get_iso3_code("afghanistan", code="alpha-2") == "af"
