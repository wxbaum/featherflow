#!/usr/bin/env python3
"""
Task: Download historical stock price data

This script downloads historical stock price data for a given symbol
and saves it to a CSV file. It simulates the download process since we
don't have external dependencies in this example.
"""
import os
import sys
import csv
import json
import argparse
import random
from datetime import datetime, timedelta
import time

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Download historical stock price data")
    parser.add_argument("--symbol", required=True, help="Stock symbol (e.g., AAPL)")
    parser.add_argument("--days", type=int, default=90, help="Number of days of history to download")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    return parser.parse_args()

def generate_mock_stock_data(symbol, days):
    """
    Generate mock stock data for demonstration purposes
    
    Args:
        symbol: Stock ticker symbol
        days: Number of days of history
        
    Returns:
        List of dictionaries with stock data
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Set initial price based on symbol (hash of symbol)
    hash_value = sum(ord(c) for c in symbol)
    base_price = 50 + (hash_value % 200)  # Generate price between $50 and $250
    volatility = 0.02  # 2% daily volatility
    
    data = []
    current_price = base_price
    current_date = start_date
    
    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() >= 5:  # 5 is Saturday, 6 is Sunday
            current_date += timedelta(days=1)
            continue
            
        # Random price change with slight upward bias
        price_change = random.normalvariate(0.0005, volatility)
        current_price *= (1 + price_change)
        
        # Calculate high, low, open
        daily_high = current_price * (1 + random.uniform(0, 0.015))
        daily_low = current_price * (1 - random.uniform(0, 0.015))
        daily_open = current_price * (1 + random.uniform(-0.01, 0.01))
        
        # Calculate volume (proportional to volatility)
        volume = int(random.normalvariate(1000000, 300000) * (1 + abs(price_change) * 10))
        
        data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "symbol": symbol,
            "open": round(daily_open, 2),
            "high": round(daily_high, 2),
            "low": round(daily_low, 2),
            "close": round(current_price, 2),
            "volume": volume
        })
        
        current_date += timedelta(days=1)
    
    # Sort by date in descending order (most recent first)
    return sorted(data, key=lambda x: x["date"], reverse=True)

def main():
    """Main function"""
    args = parse_args()
    
    # Get flow parameters if available
    params_json = os.environ.get("MINIFLOW_PARAMS", "{}")
    flow_params = json.loads(params_json)
    
    # Override symbol from flow parameters if available
    symbol = flow_params.get("symbol", args.symbol)
    
    print(f"Downloading historical data for {symbol} (last {args.days} days)...")
    
    # Simulate network delay
    time.sleep(2)
    
    # Generate mock data
    stock_data = generate_mock_stock_data(symbol, args.days)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Write data to CSV
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "symbol", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(stock_data)
    
    print(f"Successfully downloaded {len(stock_data)} days of data for {symbol}")
    print(f"Data saved to {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())