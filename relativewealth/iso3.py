
from functools import lru_cache
import pandas as pd
import warnings
# ISO3166 source list
# see https://github.com/lukes//ISO-3166-Countries-with-Regional-Codes

ISO3_URL = "https://datahub.io/core/country-codes/r/country-codes.csv"

@lru_cache(maxsize=None)
def get_iso3_codes():
    iso3_df = pd.read_csv(ISO3_URL)
    iso3_df.columns = [col.lower().replace('_','-').replace(' ','-') for col in iso3_df.columns]
    iso3_lookup = iso3_df[['iso3166-1-alpha-3','cldr-display-name']].apply(lambda x: x.astype(str).str.lower())
    iso3_lookup['cldr-display-name'] = iso3_lookup['cldr-display-name'].str.replace(' ','-')
    iso3_lookup['iso-alpha-2'] = iso3_lookup['iso3166-1-alpha-3'].apply(lambda x: x[:-1])
    iso3_lookup.columns = ['iso-alpha-3','common-name','iso-alpha-2']
    
    return iso3_lookup

def is_valid_iso3_code(iso_country_code, code='alpha-2'):
    iso3_lookup = get_iso3_codes()
    return True if iso_country_code in iso3_lookup['iso-'+code].values else False

def is_valid_country_name(country_common_name):
    iso3_lookup = get_iso3_codes()
    return True if country_common_name in iso3_lookup['common-name'].values else False

def get_region_name(iso_country_code, code='alpha-2'):
    iso3_lookup = get_iso3_codes()
    if is_valid_iso3_code(iso_country_code, code):
        return iso3_lookup[iso3_lookup['iso-'+code]==iso_country_code]['common-name'].values[0]
    else:
        warnings.warn(f'Invalid iso3 code. Head to https://www.iso.org/iso-3166-country-codes.html to check the correct code.')
        return None

def get_iso3_code(country_common_name, code='alpha-2'):
    iso3_lookup = get_iso3_codes()
    if is_valid_country_name(country_common_name):
        return iso3_lookup[iso3_lookup['common-name']==country_common_name]['iso-'+code].values[0]
    else:
        warnings.warn(f'Country {country_common_name} not found. Head to https://www.iso.org/iso-3166-country-codes.html to check the correct country name.')
        return None

