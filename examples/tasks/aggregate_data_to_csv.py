#!/usr/bin/env python3
"""
This script aggregates all weather observation data from individual JSON files
into a single CSV file for easier analysis.
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime
from glob import glob
from typing import Dict, List, Any, Optional

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Aggregate weather observations into a CSV file")
    parser.add_argument("--output", default="weather_observations.csv", 
                        help="Output CSV filename (default: weather_observations.csv)")
    parser.add_argument("--days", type=int, default=0,
                        help="Only include observations from the past N days (0 for all)")
    
    # Parse known args only to handle the way Featherflow passes arguments
    args, _ = parser.parse_known_args()
    return args

def get_json_files() -> List[str]:
    """
    Get all JSON files from the tmp directory
    
    Returns:
        List of file paths to JSON files
    """
    # Use the TMP_DIR environment variable if available, otherwise fall back to ./tmp
    tmp_dir = os.environ.get('TMP_DIR', os.path.join(os.getcwd(), 'tmp'))
    
    # Check if the directory exists
    if not os.path.exists(tmp_dir):
        print(f"Temp directory not found: {tmp_dir}")
        return []
    
    # Get all JSON files in the directory
    json_files = glob(os.path.join(tmp_dir, "*.json"))
    
    print(f"Found {len(json_files)} JSON files in {tmp_dir}")
    return json_files

def extract_station_from_filename(filename: str) -> str:
    """
    Extract the station ID from the filename
    
    Args:
        filename: Path to the JSON file
        
    Returns:
        Station ID extracted from the filename
    """
    # Get just the filename without path
    basename = os.path.basename(filename)
    # Split by underscore and get the first part (station ID)
    return basename.split('_')[0]

def load_json_data(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load data from a JSON file
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Dictionary of data from the JSON file, or None if loading fails
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading JSON file {filepath}: {e}")
        return None

def process_json_files(files: List[str], max_days: int = 0) -> List[Dict[str, Any]]:
    """
    Process all JSON files and extract the relevant data
    
    Args:
        files: List of JSON file paths
        max_days: Only include files from the past N days (0 for all)
        
    Returns:
        List of dictionaries containing the processed data
    """
    processed_data = []
    
    for file_path in files:
        # Skip files older than max_days if specified
        if max_days > 0:
            try:
                # Extract date from filename (assuming format STATIONID_YYYYMMDD_HHMMSS.json)
                filename = os.path.basename(file_path)
                date_part = filename.split('_')[1]
                file_date = datetime.strptime(date_part, "%Y%m%d")
                
                # Calculate days difference
                days_diff = (datetime.now() - file_date).days
                if days_diff > max_days:
                    continue
            except (ValueError, IndexError):
                # If we can't parse the date, include the file anyway
                pass
        
        # Load the JSON data
        data = load_json_data(file_path)
        if not data:
            continue
        
        # Extract station ID from filename
        station_id = extract_station_from_filename(file_path)
        
        # Extract relevant observation data
        record = {
            "station_id": station_id,
            "timestamp": os.path.getmtime(file_path),  # Use file modification time as fallback
            "datetime": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Extract temperature (convert to Fahrenheit)
        if "temperature" in data and "value" in data["temperature"]:
            temp_c = data["temperature"]["value"]
            if temp_c is not None:
                temp_f = (temp_c * 9/5) + 32
                record["temperature_c"] = temp_c
                record["temperature_f"] = temp_f
        
        # Extract wind speed
        if "windSpeed" in data and "value" in data["windSpeed"]:
            wind_speed = data["windSpeed"]["value"]
            if wind_speed is not None:
                record["wind_speed_kmh"] = wind_speed
                # Convert to mph
                record["wind_speed_mph"] = wind_speed * 0.621371
        
        # Extract present weather if available
        if "presentWeather" in data and data["presentWeather"]:
            # Join multiple weather conditions with semicolons
            weather_descriptions = [w.get("weather", "") for w in data["presentWeather"] if "weather" in w]
            record["weather_conditions"] = "; ".join(weather_descriptions)
        else:
            record["weather_conditions"] = "Clear" # Default if no conditions specified
        
        processed_data.append(record)
    
    return processed_data

def write_csv(data: List[Dict[str, Any]], output_file: str) -> bool:
    """
    Write the processed data to a CSV file
    
    Args:
        data: List of dictionaries containing the processed data
        output_file: Path to the output CSV file
        
    Returns:
        True if successful, False otherwise
    """
    if not data:
        print("No data to write to CSV.")
        return False
    
    try:
        # Use the TMP_DIR environment variable if available, otherwise fall back to ./tmp
        tmp_dir = os.environ.get('TMP_DIR', os.path.join(os.getcwd(), 'tmp'))
        # Ensure directory exists
        os.makedirs(tmp_dir, exist_ok=True)
        
        # Create full output path
        output_path = os.path.join(tmp_dir, output_file)
        
        # Determine all fields that exist in any record
        fieldnames = set()
        for record in data:
            fieldnames.update(record.keys())
        
        # Sort fieldnames for consistent output
        fieldnames = sorted(fieldnames)
        
        # Write CSV with all fields
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"CSV file created successfully: {output_path}")
        return True
    
    except Exception as e:
        print(f"Error writing CSV file: {e}")
        return False

def main():
    args = parse_args()
    
    # Get all JSON files
    json_files = get_json_files()
    if not json_files:
        print("No observation data files found.")
        return 1
    
    print(f"Found {len(json_files)} observation data files.")
    
    # Process the JSON files
    processed_data = process_json_files(json_files, args.days)
    if not processed_data:
        print("No data to process.")
        return 1
    
    print(f"Processed {len(processed_data)} observations.")
    
    # Write the data to a CSV file
    if write_csv(processed_data, args.output):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
