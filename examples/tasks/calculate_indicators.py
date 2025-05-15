#!/usr/bin/env python3
"""
Task: Calculate technical indicators from stock price data

This script calculates various technical indicators based on input stock price data.
"""
import os
import sys
import csv
import argparse
import math
from datetime import datetime

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Calculate technical indicators from stock data")
    parser.add_argument("--input", required=True, help="Input CSV file with stock price data")
    parser.add_argument("--output", required=True, help="Output CSV file for calculated indicators")
    return parser.parse_args()

def read_stock_data(csv_file):
    """Read stock price data from CSV file"""
    data = []
    with open(csv_file, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                "date": row["date"],
                "symbol": row["symbol"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"])
            })
    return data

def calculate_sma(data, period):
    """Calculate Simple Moving Average"""
    result = []
    for i in range(len(data)):
        if i < period - 1:
            result.append(None)  # Not enough data yet
        else:
            # Sum the last 'period' closes and divide by period
            sum_close = sum(item["close"] for item in data[i-(period-1):i+1])
            result.append(round(sum_close / period, 2))
    return result

def calculate_ema(data, period, smoothing=2):
    """Calculate Exponential Moving Average"""
    ema_values = []
    # Start with SMA for first EMA value
    sma = sum(item["close"] for item in data[:period]) / period
    ema_values.append(sma)
    
    # EMA = Closing price x multiplier + EMA (previous day) x (1 - multiplier)
    multiplier = smoothing / (period + 1)
    
    for i in range(period, len(data)):
        ema = (data[i]["close"] * multiplier) + (ema_values[-1] * (1 - multiplier))
        ema_values.append(round(ema, 2))
    
    # Pad with None for days before we have an EMA value
    return [None] * (period - 1) + ema_values

def calculate_rsi(data, period=14):
    """Calculate Relative Strength Index"""
    deltas = []
    # Calculate price changes
    for i in range(1, len(data)):
        deltas.append(data[i-1]["close"] - data[i]["close"])  # Note: data is in reverse chronological order
    
    gains = []
    losses = []
    for delta in deltas:
        if delta > 0:
            gains.append(delta)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(delta))
    
    # Not enough data for RSI calculation
    if len(gains) < period:
        return [None] * len(data)
    
    # First average gain and loss
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # Calculate RSI values
    rsi_values = []
    rsi_values.extend([None] * (period + 1))  # First 'period+1' days don't have RSI
    
    for i in range(period, len(deltas)):
        # Update average gain and loss using smoothing formula
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
        
        if avg_loss == 0:
            rs = 100  # Avoid division by zero
        else:
            rs = avg_gain / avg_loss
        
        rsi = 100 - (100 / (1 + rs))
        rsi_values.append(round(rsi, 2))
    
    return rsi_values

def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    # Calculate EMAs
    ema_fast = calculate_ema(data, fast_period)
    ema_slow = calculate_ema(data, slow_period)
    
    # Calculate MACD line
    macd_line = []
    for i in range(len(data)):
        if ema_fast[i] is None or ema_slow[i] is None:
            macd_line.append(None)
        else:
            macd_line.append(round(ema_fast[i] - ema_slow[i], 2))
    
    # Calculate signal line (EMA of MACD line)
    # First, find the index where MACD line starts having values
    start_idx = 0
    while start_idx < len(macd_line) and macd_line[start_idx] is None:
        start_idx += 1
    
    macd_for_signal = [x for x in macd_line[start_idx:] if x is not None]
    if len(macd_for_signal) < signal_period:
        # Not enough data for signal line
        signal_line = [None] * len(data)
    else:
        # Calculate signal line (EMA of MACD)
        signal_ema = [None] * start_idx
        
        # Start with SMA of MACD
        sma = sum(macd_for_signal[:signal_period]) / signal_period
        signal_ema.append(sma)
        
        # Calculate EMA
        multiplier = 2 / (signal_period + 1)
        for i in range(1, len(macd_for_signal) - signal_period + 1):
            ema = (macd_for_signal[i+signal_period-1] * multiplier) + (signal_ema[-1] * (1 - multiplier))
            signal_ema.append(round(ema, 2))
        
        # Pad with None for first slow_period + signal_period days
        signal_line = signal_ema + [None] * (len(data) - len(signal_ema) - start_idx)
    
    # Calculate histogram (MACD line - signal line)
    histogram = []
    for i in range(len(data)):
        if macd_line[i] is None or signal_line[i] is None:
            histogram.append(None)
        else:
            histogram.append(round(macd_line[i] - signal_line[i], 2))
    
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(data, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma_values = calculate_sma(data, period)
    
    upper_band = []
    lower_band = []
    
    for i in range(len(data)):
        if sma_values[i] is None:
            upper_band.append(None)
            lower_band.append(None)
        else:
            # Calculate standard deviation of closing prices
            prices = [item["close"] for item in data[i-(period-1):i+1]]
            mean = sum(prices) / period
            variance = sum((price - mean) ** 2 for price in prices) / period
            std = math.sqrt(variance)
            
            # Calculate upper and lower bands
            upper_band.append(round(sma_values[i] + (std_dev * std), 2))
            lower_band.append(round(sma_values[i] - (std_dev * std), 2))
    
    return sma_values, upper_band, lower_band

def main():
    """Main function"""
    args = parse_args()
    
    print(f"Reading stock data from {args.input}...")
    
    # Read stock price data
    try:
        stock_data = read_stock_data(args.input)
    except Exception as e:
        print(f"Error reading stock data: {e}")
        return 1
    
    print(f"Calculating technical indicators for {len(stock_data)} data points...")
    
    # Calculate indicators
    sma_20 = calculate_sma(stock_data, 20)
    sma_50 = calculate_sma(stock_data, 50)
    ema_12 = calculate_ema(stock_data, 12)
    ema_26 = calculate_ema(stock_data, 26)
    rsi_14 = calculate_rsi(stock_data, 14)
    macd_line, signal_line, macd_histogram = calculate_macd(stock_data)
    bb_sma, bb_upper, bb_lower = calculate_bollinger_bands(stock_data)
    
    # Combine data with indicators
    output_data = []
    for i, price_data in enumerate(stock_data):
        output_data.append({
            "date": price_data["date"],
            "symbol": price_data["symbol"],
            "close": price_data["close"],
            "sma_20": sma_20[i],
            "sma_50": sma_50[i],
            "ema_12": ema_12[i],
            "ema_26": ema_26[i],
            "rsi_14": rsi_14[i],
            "macd": macd_line[i],
            "macd_signal": signal_line[i],
            "macd_hist": macd_histogram[i],
            "bb_middle": bb_sma[i],
            "bb_upper": bb_upper[i],
            "bb_lower": bb_lower[i]
        })
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Write indicators to CSV
    with open(args.output, "w", newline="") as f:
        fieldnames = [
            "date", "symbol", "close", 
            "sma_20", "sma_50", "ema_12", "ema_26", 
            "rsi_14", "macd", "macd_signal", "macd_hist",
            "bb_middle", "bb_upper", "bb_lower"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_data)
    
    print(f"Technical indicators calculated and saved to {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())