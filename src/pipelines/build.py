"""Main pipeline orchestration for building ZCTA-level housing dataset.

This module coordinates the entire data pipeline: fetching geographic boundaries,
retrieving census and rental data, computing spatial joins, and aggregating to
produce a final ZCTA-level dataset with housing, commute, and transit metrics.
"""
from __future__ import annotations

import geopandas as gpd
import pandas as pd

from .acs import compute_acs_features, fetch_acs_for_county
from .config import (
    CBSA_CODE,
    COUNTY_FIPS_LIST,
    FINAL_ZCTA_OUT,
    METRO_NAME,
    STATE_FIPS,
    ZIP_PREFIXES,
    ZORI_ZIP_CSV_URL,
)
from .demographics import (
    aggregate_demographics_to_zcta,
    compute_demographic_percentages,
    create_income_segments,
    fetch_demographics_for_county,
)
from .osm import zcta_transit_density
from .spatial import filter_zctas_in_cbsa, tract_to_zcta_centroid_map
from .tiger import get_cbsa_polygon, get_state_tracts, get_state_zctas
from .zori import fetch_zori_latest


def build_final_dataset() -> str:
    """Execute the full data pipeline to build ZCTA-level housing dataset.
    
    This function orchestrates a multi-step ETL pipeline that:
    1. Fetches CBSA (metro area) boundary for spatial filtering
    2. Retrieves ZCTA (ZIP code) and census tract geometries
    3. Fetches ACS demographic/commute data at tract level
    4. Maps tracts to ZCTAs via centroid-based spatial join
    5. Aggregates tract data to ZCTA level
    6. Fetches Zillow rent index (ZORI) by ZIP code
    7. Computes OpenStreetMap transit stop density by ZCTA
    8. Merges all data sources into final dataset
    
    Returns:
        String path to the output CSV file
        
    Raises:
        requests.HTTPError: If any API request fails
        ValueError: If no ZCTAs or tracts are found for the metro area
        
    Side Effects:
        - Creates output directory if it doesn't exist
        - Writes CSV file to path specified in FINAL_ZCTA_OUT config
        - Prints progress messages to console
        
    Output Schema:
        ZCTA5CE, rent_to_income, long45_share, long60_share, commute_min_proxy,
        ttw_total, total_pop, pct_hispanic, pct_white, pct_black, pct_asian, 
        pct_other, median_income, income_segment, period, zori, stops_per_km2
    """
    print(f"Building dataset for: {METRO_NAME}")
    
    # Step 1: Fetch CBSA (metro area) boundary polygon for spatial filtering
    cbsa_boundary = get_cbsa_polygon(CBSA_CODE)
    print("Fetched CBSA boundary")

    # Step 2: Fetch ZCTA and tract geometries for the region
    zctas_all = get_state_zctas(ZIP_PREFIXES)
    tracts_all = get_state_tracts(STATE_FIPS, COUNTY_FIPS_LIST)
    print(f"Fetched {len(zctas_all)} ZCTAs and {len(tracts_all)} tracts")

    # Filter ZCTAs to only those within the CBSA (centroid-based)
    zctas_in_metro = filter_zctas_in_cbsa(zctas_all, cbsa_boundary)
    tracts_in_counties = tracts_all

    # Step 3: Fetch ACS commute data for each county
    print(f"Fetching ACS commute data for {len(COUNTY_FIPS_LIST)} counties...")
    acs_data_by_county = [fetch_acs_for_county(STATE_FIPS, county_fips) for county_fips in COUNTY_FIPS_LIST]
    acs_raw = pd.concat(acs_data_by_county, ignore_index=True)
    acs_features = compute_acs_features(acs_raw)
    print(f"Processed ACS commute data for {len(acs_raw)} tracts")
    
    # Step 3b: Fetch ACS demographic data (race, ethnicity, income) for each county
    print(f"Fetching ACS demographic data for {len(COUNTY_FIPS_LIST)} counties...")
    demo_data_by_county = [fetch_demographics_for_county(STATE_FIPS, county_fips) for county_fips in COUNTY_FIPS_LIST]
    demo_raw = pd.concat(demo_data_by_county, ignore_index=True)
    demo_with_pct = compute_demographic_percentages(demo_raw)
    print(f"Processed demographic data for {len(demo_raw)} tracts")

    # Step 4: Map census tracts to ZCTAs using centroid-based spatial join
    print(f"Mapping {len(tracts_in_counties)} tracts to {len(zctas_in_metro)} ZCTAs...")
    tract_to_zcta_map = tract_to_zcta_centroid_map(tracts_in_counties, zctas_in_metro)

    # DEBUG: Check mapping results
    tract_to_zcta_map.to_csv("data/test/debug_tract_to_zcta_map.csv", index=False)

    # Join ACS commute features with tract-to-ZCTA mapping
    acs_with_zcta = acs_features.merge(tract_to_zcta_map, on="GEOID", how="inner")
    
    # Aggregate commute tract-level data to ZCTA level using appropriate statistics
    zcta_aggregated = acs_with_zcta.groupby("ZCTA5CE", as_index=False).agg({
        "rent_to_income": "mean",  # Average rent burden across tracts
        "commute_min_proxy": "mean",  # Average estimated commute time (minutes)
        "ttw_total": "sum",  # Total workers (summed across tracts)
        # Commute time distribution (percentage in each bin)
        "pct_commute_lt10": "mean",  # Average % with commute < 10 min
        "pct_commute_10_19": "mean",  # Average % with commute 10-19 min
        "pct_commute_20_29": "mean",  # Average % with commute 20-29 min
        "pct_commute_30_44": "mean",  # Average % with commute 30-44 min
        "pct_commute_45_59": "mean",  # Average % with commute 45-59 min
        "pct_commute_60_plus": "mean",  # Average % with commute 60+ min
        # Transportation mode share
        "pct_drive_alone": "mean",  # Average % driving alone
        "pct_carpool": "mean",  # Average % carpooling
        "pct_transit": "mean",  # Average % using transit
        "pct_walk": "mean",  # Average % walking
        "pct_wfh": "mean",  # Average % working from home
        "pct_car": "mean",  # Average % using car (alone + carpool)
        # Rent burden
        "pct_rent_burden_30": "mean",  # Average % rent burdened (30%+)
        "pct_rent_burden_50": "mean",  # Average % severely rent burdened (50%+)
        # Legacy variables (kept for backward compatibility)
        "long45_share": "mean",  # Deprecated: use pct_commute_45_59 + pct_commute_60_plus
        "long60_share": "mean"  # Deprecated: use pct_commute_60_plus
    })
    print(f"Aggregated commute data to {len(zcta_aggregated)} ZCTAs")
    
    # Aggregate demographic data to ZCTA level (population-weighted)
    zcta_demographics = aggregate_demographics_to_zcta(demo_with_pct, tract_to_zcta_map)
    print(f"Aggregated demographic data to {len(zcta_demographics)} ZCTAs")

    # Step 5: Fetch Zillow Observed Rent Index (ZORI) for rental prices
    print("Fetching Zillow rent data...")
    zori_data = fetch_zori_latest(ZORI_ZIP_CSV_URL)
    zori_data = zori_data.rename(columns={"zip": "ZCTA5CE"})
    zori_data["ZCTA5CE"] = zori_data["ZCTA5CE"].astype(str).str.zfill(5)
    print(f"Fetched ZORI data for {len(zori_data)} ZIP codes")

    # Step 6: Compute transit stop density from OpenStreetMap for each ZCTA
    # Note: transit_filter and fallback_filter parameters currently unused
    # Create a proper GeoDataFrame with only needed columns
    print(f"Computing transit density for {len(zctas_in_metro)} ZCTAs (may take several minutes)...")
    zctas_for_transit = gpd.GeoDataFrame(
        zctas_in_metro[["ZCTA5CE"]],
        geometry=zctas_in_metro.geometry,
        crs=zctas_in_metro.crs
    )
    transit_density = zcta_transit_density(
        zctas_for_transit,
        transit_filter="",
        fallback_filter=""
    )
    print(f"Computed transit density for {len(transit_density)} ZCTAs")

    # Step 7: Merge all data sources into final dataset
    final_dataset = (
        zcta_aggregated
        .merge(
            zcta_demographics,
            on="ZCTA5CE",
            how="left"  # Left join to keep all ZCTAs
        )
        .merge(
            zori_data[["ZCTA5CE", "period", "zori"]],
            on="ZCTA5CE",
            how="left"  # Left join to keep all ZCTAs even without ZORI data
        )
        .merge(
            transit_density,
            on="ZCTA5CE",
            how="left"  # Left join to keep all ZCTAs even without transit data
        )
    )
    
    # Step 8: Create income segments based on median income quartiles
    final_dataset = create_income_segments(final_dataset)
    print(f"Created income segments (Low/Medium/High) based on quartiles")

    # Write output CSV file
    FINAL_ZCTA_OUT.parent.mkdir(parents=True, exist_ok=True)
    final_dataset.to_csv(FINAL_ZCTA_OUT, index=False)
    
    print(f"\nSUCCESS: Wrote {len(final_dataset)} ZCTAs to {FINAL_ZCTA_OUT.name}")
    print(f"   Output: {FINAL_ZCTA_OUT}")
    
    return str(FINAL_ZCTA_OUT)