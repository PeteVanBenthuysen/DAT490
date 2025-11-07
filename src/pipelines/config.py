from __future__ import annotations
import os
from pathlib import Path

# Navigate up from src/pipelines/config.py to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FINAL = PROJECT_ROOT / "data" / "final"
CACHE_DIR = PROJECT_ROOT / ".cache"
CACHE_DIR.mkdir(exist_ok=True, parents=True)

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY", None)

# Metro Area Configurations
# Format: "metro_key": {
#   "name": Full metro name,
#   "cbsa_code": CBSA code from Census,
#   "state_fips": Primary state FIPS code,
#   "county_fips_list": List of county FIPS codes in the metro,
#   "zip_prefixes": ZIP code prefixes for ZCTA queries,
#   "utm_zone": UTM zone EPSG code for accurate spatial calculations
# }
METRO_CONFIGS = {
    "phoenix": {
        "name": "Phoenix-Mesa-Chandler, AZ",
        "cbsa_code": "38060",
        "state_fips": "04",  # Arizona
        "county_fips_list": ["013", "021"],  # Maricopa, Pinal
        "zip_prefixes": ["85"],
        "utm_zone": 32612  # UTM Zone 12N
    },
    "memphis": {
        "name": "Memphis, TN-MS-AR",
        "cbsa_code": "32820",
        "state_fips": "47",  # Tennessee (primary)
        "county_fips_list": ["157", "047", "033"],  # Shelby TN, Fayette TN, Crittenden AR (28)
        "zip_prefixes": ["38", "72"],  # TN and AR prefixes
        "utm_zone": 32616  # UTM Zone 16N
    },
    "los_angeles": {
        "name": "Los Angeles-Long Beach-Anaheim, CA",
        "cbsa_code": "31080",
        "state_fips": "06",  # California
        "county_fips_list": ["037"],  # Los Angeles County
        "zip_prefixes": ["90", "91"],  # Primary LA area prefixes
        "utm_zone": 32611  # UTM Zone 11N
    },
    "dallas": {
        "name": "Dallas-Fort Worth-Arlington, TX",
        "cbsa_code": "19100",
        "state_fips": "48",  # Texas
        "county_fips_list": ["113", "121", "257", "439"],  # Dallas, Denton, Collin, Tarrant
        "zip_prefixes": ["75", "76"],  # Dallas and Fort Worth areas
        "utm_zone": 32614  # UTM Zone 14N
    }
}

# Select which metro to use (change this to switch metros)
SELECTED_METRO = os.getenv("METRO", "phoenix")  # Can be: phoenix, memphis, los_angeles, dallas

# Get the selected metro configuration
_metro_config = METRO_CONFIGS.get(SELECTED_METRO, METRO_CONFIGS["phoenix"])
CBSA_CODE = _metro_config["cbsa_code"]
STATE_FIPS = _metro_config["state_fips"]
COUNTY_FIPS_LIST = _metro_config["county_fips_list"]
ZIP_PREFIXES = _metro_config["zip_prefixes"]
UTM_ZONE = _metro_config["utm_zone"]
METRO_NAME = _metro_config["name"]

# Zillow Research CSV URL for ZORI by ZIP (official data file; no public API)
# Update if Zillow changes paths.
ZORI_ZIP_CSV_URL = "https://files.zillowstatic.com/research/public_csvs/zori/Zip_zori_uc_sfrcondomfr_sm_sa_month.csv"

# Overpass transit feature filters (OpenStreetMap)
OSM_TRANSIT_NODE_FILTER = '["public_transport"~"platform|stop|station"]'
OSM_TRANSIT_FALLBACK = '["highway"="bus_stop"]'

# Output filename (includes metro name)
FINAL_ZCTA_OUT = DATA_FINAL / f"final_zcta_dataset_{SELECTED_METRO}.csv"