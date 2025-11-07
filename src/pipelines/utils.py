"""Utility functions for HTTP requests and geospatial data parsing.

This module provides helpers for fetching CSV data and converting ESRI REST API
responses to GeoDataFrames for use with TIGER/Line geographic data.
"""
from __future__ import annotations
import io

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import shape


def http_csv_to_df(url: str) -> pd.DataFrame:
    """Fetch a CSV file from a URL and return as a DataFrame.
    
    Args:
        url: Full URL to the CSV file
        
    Returns:
        DataFrame containing the parsed CSV data
        
    Raises:
        requests.HTTPError: If the HTTP request fails
        pandas.errors.ParserError: If CSV parsing fails
    """
    response = requests.get(url, timeout=180)
    response.raise_for_status()
    return pd.read_csv(io.BytesIO(response.content))


def http_json_to_dict(url: str, params: dict | None = None) -> dict | list:
    """Fetch JSON data from a URL and return as Python dict or list.
    
    Args:
        url: Full URL to the JSON API endpoint
        params: Optional query parameters dictionary
        
    Returns:
        Parsed JSON response (dict or list depending on API)
        
    Raises:
        requests.HTTPError: If the HTTP request fails
        ValueError: If response is not valid JSON
    """
    response = requests.get(url, params=params, timeout=180)
    response.raise_for_status()
    return response.json()


def esri_geojson_to_gdf(url: str, params: dict) -> gpd.GeoDataFrame:
    """Fetch geospatial data from ESRI REST API and convert to GeoDataFrame.
    
    This function handles both ESRI JSON format (with 'attributes' field) and
    standard GeoJSON format (with 'properties' field), making it compatible
    with various Census TIGER/Line services.
    
    Args:
        url: ESRI REST API endpoint URL (typically ends with /query)
        params: Query parameters dict (where clause, outFields, f=geojson, etc.)
        
    Returns:
        GeoDataFrame in EPSG:4326 (WGS84) coordinate system. Returns empty
        GeoDataFrame with geometry column if no features found.
        
    Raises:
        requests.HTTPError: If the API request fails
        ValueError: If response JSON is malformed
    """
    response = requests.get(url, params=params, timeout=180)
    response.raise_for_status()
    
    data = response.json()
    features = data.get("features", [])
    
    # Return empty GeoDataFrame if no features returned
    if not features:
        return gpd.GeoDataFrame(
            columns=["geometry"], 
            geometry="geometry", 
            crs="EPSG:4326"
        )
    
    # Parse features into geometries and attributes
    geometries = []
    attributes = []
    for feature in features:
        # Handle both ESRI JSON (attributes) and GeoJSON (properties) formats
        attr = feature.get("attributes") or feature.get("properties", {})
        attributes.append(attr)
        
        # Convert geometry to Shapely object
        geom = feature.get("geometry")
        geometries.append(shape(geom) if geom else None)
    
    # Create GeoDataFrame with WGS84 coordinate system
    gdf = gpd.GeoDataFrame(attributes, geometry=geometries, crs="EPSG:4326")
    return gdf