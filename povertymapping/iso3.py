
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

def get_iso3_code(region):
    iso3_lookup = get_iso3_codes()
    iso3_entry = iso3_lookup.get(region, None)
    return iso3_entry['alpha-3'] if iso3_entry is not None else None
