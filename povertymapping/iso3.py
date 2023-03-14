
from functools import lru_cache
import pandas as pd
# ISO3166 source list
# see https://github.com/lukes//ISO-3166-Countries-with-Regional-Codes

ISO3_URL = 'https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.csv'


@lru_cache(maxsize=None)
def get_iso3_codes():
    iso3_df = pd.read_csv(ISO3_URL)
    iso3_lookup = {item['name'].lower(): item for item in iso3_df.to_dict('records')}
    return iso3_lookup

def get_iso3_code(region, code='alpha-3'):
    """
    Returns the country ISO-3166 code
    Args:
        region (str): Common short country name. Refer to https://data.worldbank.org/country for possible values
        code (str): The country code standard, either 'alpha-3' or 'alpha-2'
    """
    # TODO: Find more elegant solution to correct country common name to ISO standard spelling
    iso_standard_region_name_lookup = {"vietnam": "viet nam",
                            "laos": "lao people's democratic republic",
                            "lao pdr": "lao people's democratic republic",
                            "east-timor": "timor-leste"}
    iso3_lookup = get_iso3_codes()
    iso3_entry = iso3_lookup.get(iso_standard_region_name_lookup.get(region, region))
    return iso3_entry[code] if iso3_entry is not None else None
