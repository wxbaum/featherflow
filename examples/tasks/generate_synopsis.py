#!/usr/bin/env python3
"""
This script reads the aggregated weather CSV file and prints a synopsis 
of weather conditions across all stations to the command line.
"""
import argparse
import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from statistics import mean, median

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Generate a weather synopsis from CSV data")
    parser.add_argument("--input", default="weather_observations.csv", 
                        help="Input CSV filename (default: weather_observations.csv)")
    parser.add_argument("--format", choices=["plain", "fancy"], default="fancy",
                        help="Output format (default: fancy)")
    
    # Parse known args only to handle the way Featherflow passes arguments
    args, _ = parser.parse_known_args()
    return args

def read_csv(input_file: str) -> List[Dict[str, Any]]:
    """
    Read weather data from the CSV file
    
    Args:
        input_file: Path to the CSV file
        
    Returns:
        List of dictionaries containing the weather data
    """
    # Use the TMP_DIR environment variable if available, otherwise fall back to ./tmp
    tmp_dir = os.environ.get('TMP_DIR', os.path.join(os.getcwd(), 'tmp'))
    input_path = os.path.join(tmp_dir, input_file)
    
    if not os.path.exists(input_path):
        print(f"Error: CSV file not found at {input_path}")
        return []
    
    try:
        weather_data = []
        with open(input_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert numeric values from strings
                processed_row = {}
                for key, value in row.items():
                    if key in ['temperature_c', 'temperature_f', 'wind_speed_kmh', 'wind_speed_mph', 'timestamp']:
                        try:
                            processed_row[key] = float(value) if value else None
                        except ValueError:
                            processed_row[key] = None
                    else:
                        processed_row[key] = value
                
                weather_data.append(processed_row)
        
        return weather_data
    
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

def get_temperature_summary(weather_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate temperature statistics across all stations
    
    Args:
        weather_data: List of weather data dictionaries
        
    Returns:
        Dictionary with temperature statistics
    """
    temps_f = [row.get('temperature_f') for row in weather_data if row.get('temperature_f') is not None]
    
    if not temps_f:
        return {
            'avg_temp_f': None,
            'median_temp_f': None,
            'min_temp_f': None,
            'max_temp_f': None,
            'temp_range_f': None
        }
    
    return {
        'avg_temp_f': round(mean(temps_f), 1),
        'median_temp_f': round(median(temps_f), 1),
        'min_temp_f': round(min(temps_f), 1),
        'max_temp_f': round(max(temps_f), 1),
        'temp_range_f': round(max(temps_f) - min(temps_f), 1)
    }

def get_wind_summary(weather_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate wind statistics across all stations
    
    Args:
        weather_data: List of weather data dictionaries
        
    Returns:
        Dictionary with wind statistics
    """
    wind_speeds = [row.get('wind_speed_mph') for row in weather_data if row.get('wind_speed_mph') is not None]
    
    if not wind_speeds:
        return {
            'avg_wind_mph': None,
            'max_wind_mph': None
        }
    
    return {
        'avg_wind_mph': round(mean(wind_speeds), 1),
        'max_wind_mph': round(max(wind_speeds), 1)
    }

def get_weather_conditions(weather_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count occurrences of different weather conditions
    
    Args:
        weather_data: List of weather data dictionaries
        
    Returns:
        Dictionary with condition counts
    """
    conditions = {}
    
    for row in weather_data:
        weather_cond = row.get('weather_conditions', '').strip()
        if weather_cond:
            # Split multiple conditions
            for condition in weather_cond.split(';'):
                condition = condition.strip()
                if condition:
                    conditions[condition] = conditions.get(condition, 0) + 1
    
    # Return sorted by count (descending)
    return dict(sorted(conditions.items(), key=lambda x: x[1], reverse=True))

def get_station_data(weather_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Organize data by station for easy lookup
    
    Args:
        weather_data: List of weather data dictionaries
        
    Returns:
        Dictionary with data organized by station ID
    """
    station_data = {}
    
    for row in weather_data:
        station_id = row.get('station_id')
        if not station_id:
            continue
            
        # Get the datetime as a Python datetime object
        try:
            timestamp = row.get('timestamp')
            if timestamp:
                dt = datetime.fromtimestamp(float(timestamp))
            else:
                dt = None
        except (ValueError, TypeError):
            dt = None
            
        station_data[station_id] = {
            'temperature_f': row.get('temperature_f'),
            'wind_speed_mph': row.get('wind_speed_mph'),
            'conditions': row.get('weather_conditions', ''),
            'datetime': dt
        }
    
    return station_data

def get_most_recent_observation(weather_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Find the most recent weather observation
    
    Args:
        weather_data: List of weather data dictionaries
        
    Returns:
        Dictionary containing the most recent observation
    """
    most_recent = None
    latest_time = 0
    
    for row in weather_data:
        timestamp = row.get('timestamp')
        if timestamp and float(timestamp) > latest_time:
            latest_time = float(timestamp)
            most_recent = row
    
    return most_recent

def print_plain_synopsis(weather_data: List[Dict[str, Any]]):
    """
    Print a plain text weather synopsis to the console
    
    Args:
        weather_data: List of weather data dictionaries
    """
    if not weather_data:
        print("No weather data available.")
        return
        
    # Get statistics
    temp_stats = get_temperature_summary(weather_data)
    wind_stats = get_wind_summary(weather_data)
    conditions = get_weather_conditions(weather_data)
    station_data = get_station_data(weather_data)
    most_recent = get_most_recent_observation(weather_data)
    
    # Print synopsis
    print("===== WEATHER SYNOPSIS =====")
    print(f"Data from {len(station_data)} weather stations")
    
    if most_recent:
        most_recent_time = datetime.fromtimestamp(float(most_recent.get('timestamp', 0)))
        print(f"Most recent observation: {most_recent_time.strftime('%Y-%m-%d %H:%M:%S')} from {most_recent.get('station_id', 'unknown')}")
    
    # Temperature summary
    print("\nTEMPERATURE SUMMARY:")
    print(f"Average temperature: {temp_stats['avg_temp_f']}°F")
    print(f"Temperature range: {temp_stats['min_temp_f']}°F to {temp_stats['max_temp_f']}°F")
    
    # Wind summary
    print("\nWIND SUMMARY:")
    print(f"Average wind speed: {wind_stats['avg_wind_mph']} mph")
    print(f"Maximum wind speed: {wind_stats['max_wind_mph']} mph")
    
    # Weather conditions
    print("\nWEATHER CONDITIONS:")
    for condition, count in conditions.items():
        if condition:
            print(f"- {condition}: {count} stations")
    
    # Station details
    print("\nSTATION DETAILS:")
    for station_id, data in station_data.items():
        print(f"{station_id}: {data['temperature_f']}°F, {data['wind_speed_mph']} mph, {data['conditions']}")

def print_fancy_synopsis(weather_data: List[Dict[str, Any]]):
    """
    Print a fancy formatted weather synopsis to the console
    
    Args:
        weather_data: List of weather data dictionaries
    """
    if not weather_data:
        print("No weather data available.")
        return
        
    # Get statistics
    temp_stats = get_temperature_summary(weather_data)
    wind_stats = get_wind_summary(weather_data)
    conditions = get_weather_conditions(weather_data)
    station_data = get_station_data(weather_data)
    most_recent = get_most_recent_observation(weather_data)
    
    # Terminal width
    term_width = 80
    
    # Print header
    print("╔" + "═" * (term_width - 2) + "╗")
    header = "WEATHER SYNOPSIS"
    padding = (term_width - len(header) - 4) // 2
    print("║" + " " * padding + header + " " * (term_width - len(header) - padding - 2) + "║")
    print("╠" + "═" * (term_width - 2) + "╣")
    
    # Overview
    print("║ OVERVIEW" + " " * (term_width - 11) + "║")
    print("║" + "─" * (term_width - 2) + "║")
    
    if most_recent:
        most_recent_time = datetime.fromtimestamp(float(most_recent.get('timestamp', 0)))
        last_update = f"Last updated: {most_recent_time.strftime('%Y-%m-%d %H:%M:%S')} ({most_recent.get('station_id', 'unknown')})"
        print("║ " + last_update + " " * (term_width - len(last_update) - 3) + "║")
    
    station_count = f"Data from {len(station_data)} weather stations"
    print("║ " + station_count + " " * (term_width - len(station_count) - 3) + "║")
    
    # Temperature
    print("╠" + "═" * (term_width - 2) + "╣")
    print("║ TEMPERATURE" + " " * (term_width - 13) + "║")
    print("║" + "─" * (term_width - 2) + "║")
    
    temp_avg = f"Average: {temp_stats['avg_temp_f']}°F"
    print("║ " + temp_avg + " " * (term_width - len(temp_avg) - 3) + "║")
    
    temp_range = f"Range: {temp_stats['min_temp_f']}°F to {temp_stats['max_temp_f']}°F (Δ {temp_stats['temp_range_f']}°F)"
    print("║ " + temp_range + " " * (term_width - len(temp_range) - 3) + "║")
    
    # Wind
    print("╠" + "═" * (term_width - 2) + "╣")
    print("║ WIND" + " " * (term_width - 7) + "║")
    print("║" + "─" * (term_width - 2) + "║")
    
    wind_avg = f"Average speed: {wind_stats['avg_wind_mph']} mph"
    print("║ " + wind_avg + " " * (term_width - len(wind_avg) - 3) + "║")
    
    wind_max = f"Maximum speed: {wind_stats['max_wind_mph']} mph"
    print("║ " + wind_max + " " * (term_width - len(wind_max) - 3) + "║")
    
    # Conditions
    print("╠" + "═" * (term_width - 2) + "╣")
    print("║ CONDITIONS" + " " * (term_width - 12) + "║")
    print("║" + "─" * (term_width - 2) + "║")
    
    for condition, count in conditions.items():
        if condition:
            cond_text = f"{condition}: {count} station{'s' if count > 1 else ''}"
            print("║ " + cond_text + " " * (term_width - len(cond_text) - 3) + "║")
    
    # Station details
    print("╠" + "═" * (term_width - 2) + "╣")
    print("║ STATION DETAILS" + " " * (term_width - 17) + "║")
    print("║" + "─" * (term_width - 2) + "║")
    
    for station_id, data in station_data.items():
        station_text = f"{station_id}: {data['temperature_f']}°F, {data['wind_speed_mph']} mph wind"
        # Truncate conditions if too long
        if data['conditions']:
            max_cond_len = term_width - len(station_text) - 5
            conditions_text = data['conditions']
            if len(conditions_text) > max_cond_len:
                conditions_text = conditions_text[:max_cond_len-3] + "..."
            station_text += f", {conditions_text}"
        
        # Ensure line doesn't exceed terminal width
        if len(station_text) > term_width - 4:
            station_text = station_text[:term_width - 7] + "..."
            
        print("║ " + station_text + " " * (term_width - len(station_text) - 3) + "║")
    
    # Footer
    print("╚" + "═" * (term_width - 2) + "╝")

def main():
    args = parse_args()
    
    # Read the CSV file
    weather_data = read_csv(args.input)
    if not weather_data:
        print("No weather data found.")
        return 1
    
    # Print synopsis based on format
    if args.format == "fancy":
        print_fancy_synopsis(weather_data)
    else:
        print_plain_synopsis(weather_data)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
