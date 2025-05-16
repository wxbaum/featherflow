#!/usr/bin/env python3
"""
This script retrieves weather data for a given station using the NWS free API.
"""
import argparse
import json
import os
import sys
from typing import Dict
import urllib.request
import urllib.error
from datetime import datetime

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Get weather observations for a station")
    parser.add_argument("--station", required=True, help="Weather station ID e.g. KSFO")
    
    # Parse known args only to handle the way Featherflow passes arguments
    args, _ = parser.parse_known_args()
    return args

def get_data(station: str) -> Dict:
    """Gets weather observation data for the station passed as param."""
    request_url = f"https://api.weather.gov/stations/{station}/observations/latest"
    try:
        with urllib.request.urlopen(request_url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            # Get subset of returned data
            keep_keys = [
                "station",
                "presentWeather",
                "temperature",
                "windSpeed"
            ]
            return {k: v for k, v in data["properties"].items() if k in keep_keys}
    except urllib.error.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except urllib.error.URLError as url_err:
        if isinstance(url_err.reason, TimeoutError):
            print("Error: The request to the NWS API timed out.")
        else:
            print(f"Error: Unable to connect to the NWS API. {url_err.reason}")
    except json.JSONDecodeError:
        print("Error: Failed to parse response as JSON.")
    except Exception as err:
        print(f"An unexpected error occurred: {err}")
    return {}  # Return empty dict on error

def save_data(station: str, data: Dict) -> None:
    """
    Save observation data to a file in the tmp directory
    
    Args:
        station: Weather station ID
        data: Observation data dictionary
    """
    # Use the TMP_DIR environment variable if available, otherwise fall back to ./tmp
    tmp_dir = os.environ.get('TMP_DIR', os.path.join(os.getcwd(), 'tmp'))
    
    # Create the directory if it doesn't exist
    os.makedirs(tmp_dir, exist_ok=True)
    
    # Create a timestamp for filename uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create the output filename
    filename = f"{station}_{timestamp}.json"
    filepath = os.path.join(tmp_dir, filename)
    
    # Write the data to the file
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Observation data saved to: {filepath}")

def main():
    args = parse_args()
    print(f"Getting observation data for {args.station}")
    obs = get_data(args.station)
    print(obs)
    
    # Save the data if we received any
    if obs:
        save_data(args.station, obs)
        return 0
    else:
        print(f"Failed to get data for station {args.station}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
