#!/usr/bin/env python3
"""
Task: Generate trading signals based on technical indicators

This script generates buy/sell signals based on various trading strategies.
"""
import os
import sys
import csv
import json
import argparse
from datetime import datetime

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Generate trading signals from indicators")
    parser.add_argument("--indicators", required=True, help="Input CSV file with technical indicators")
    parser.add_argument("--output", required=True, help="Output CSV file for generated signals")
    parser.add_argument("--strategy", choices=["sma_crossover", "macd", "rsi", "bollinger"], 
                       default="sma_crossover", help="Trading strategy to use")
    return parser.parse_args()

def read_indicators_data(csv_file):
    """Read technical indicators from CSV file"""
    data = []
    with open(csv_file, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numerical values
            processed_row = {
                "date": row["date"],
                "symbol": row["symbol"],
                "close": float(row["close"]),
            }
            
            # Convert indicator values to float if not None
            for key, value in row.items():
                if key not in processed_row and value.strip():
                    try:
                        processed_row[key] = float(value)
                    except ValueError:
                        processed_row[key] = None
            
            data.append(processed_row)
    
    return data

def sma_crossover_strategy(data, fast_sma="ema_12", slow_sma="ema_26"):
    """
    Generate signals based on SMA/EMA crossover strategy
    Buy when fast SMA crosses above slow SMA, sell when it crosses below
    """
    signals = []
    for i, item in enumerate(data):
        signal = "HOLD"
        reason = ""
        
        # Skip if we don't have enough data
        if i >= len(data) - 1:
            signals.append({"signal": signal, "reason": reason})
            continue
            
        # Check if both SMAs exist
        current = item
        next_day = data[i+1]
        
        if (current[fast_sma] is not None and current[slow_sma] is not None and
            next_day[fast_sma] is not None and next_day[slow_sma] is not None):
            
            # Current day's relationship
            current_diff = current[fast_sma] - current[slow_sma]
            # Next day's relationship (actually previous day since data is in reverse order)
            next_diff = next_day[fast_sma] - next_day[slow_sma]
            
            # Buy signal: fast SMA crosses above slow SMA
            if current_diff > 0 and next_diff <= 0:
                signal = "BUY"
                reason = f"{fast_sma} crossed above {slow_sma}"
            
            # Sell signal: fast SMA crosses below slow SMA
            elif current_diff < 0 and next_diff >= 0:
                signal = "SELL"
                reason = f"{fast_sma} crossed below {slow_sma}"
        
        signals.append({"signal": signal, "reason": reason})
    
    return signals

def macd_strategy(data):
    """
    Generate signals based on MACD strategy
    Buy when MACD histogram turns positive, sell when it turns negative
    """
    signals = []
    for i, item in enumerate(data):
        signal = "HOLD"
        reason = ""
        
        # Skip if we don't have enough data
        if i >= len(data) - 1:
            signals.append({"signal": signal, "reason": reason})
            continue
            
        # Check if MACD values exist
        current = item
        next_day = data[i+1]
        
        if (current["macd_hist"] is not None and next_day["macd_hist"] is not None):
            # Buy signal: histogram turns positive
            if current["macd_hist"] > 0 and next_day["macd_hist"] <= 0:
                signal = "BUY"
                reason = "MACD histogram turned positive"
            
            # Sell signal: histogram turns negative
            elif current["macd_hist"] < 0 and next_day["macd_hist"] >= 0:
                signal = "SELL"
                reason = "MACD histogram turned negative"
        
        signals.append({"signal": signal, "reason": reason})
    
    return signals

def rsi_strategy(data, oversold=30, overbought=70):
    """
    Generate signals based on RSI strategy
    Buy when RSI crosses above oversold level, sell when RSI crosses below overbought level
    """
    signals = []
    for i, item in enumerate(data):
        signal = "HOLD"
        reason = ""
        
        # Skip if we don't have enough data
        if i >= len(data) - 1:
            signals.append({"signal": signal, "reason": reason})
            continue
            
        # Check if RSI values exist
        current = item
        next_day = data[i+1]
        
        if (current["rsi_14"] is not None and next_day["rsi_14"] is not None):
            # Buy signal: RSI crosses above oversold level
            if current["rsi_14"] > oversold and next_day["rsi_14"] <= oversold:
                signal = "BUY"
                reason = f"RSI crossed above {oversold} (oversold)"
            
            # Sell signal: RSI crosses below overbought level
            elif current["rsi_14"] < overbought and next_day["rsi_14"] >= overbought:
                signal = "SELL"
                reason = f"RSI crossed below {overbought} (overbought)"
        
        signals.append({"signal": signal, "reason": reason})
    
    return signals

def bollinger_bands_strategy(data):
    """
    Generate signals based on Bollinger Bands strategy
    Buy when price crosses above lower band, sell when price crosses below upper band
    """
    signals = []
    for i, item in enumerate(data):
        signal = "HOLD"
        reason = ""
        
        # Skip if we don't have enough data
        if i >= len(data) - 1:
            signals.append({"signal": signal, "reason": reason})
            continue
            
        # Check if Bollinger Bands values exist
        current = item
        next_day = data[i+1]
        
        if (current["bb_upper"] is not None and current["bb_lower"] is not None and
            next_day["bb_upper"] is not None and next_day["bb_lower"] is not None):
            
            # Buy signal: price crosses above lower band
            if current["close"] > current["bb_lower"] and next_day["close"] <= next_day["bb_lower"]:
                signal = "BUY"
                reason = "Price crossed above lower Bollinger Band"
            
            # Sell signal: price crosses below upper band
            elif current["close"] < current["bb_upper"] and next_day["close"] >= next_day["bb_upper"]:
                signal = "SELL"
                reason = "Price crossed below upper Bollinger Band"
        
        signals.append({"signal": signal, "reason": reason})
    
    return signals

def adjust_signals_by_risk(signals, risk_tolerance):
    """Adjust signals based on risk tolerance"""
    # This is a simplified version - in real scenarios, this would be more sophisticated
    if risk_tolerance == "low":
        # More conservative - fewer signals
        for i, signal_data in enumerate(signals):
            # Randomly reduce some buy signals to holds
            if signal_data["signal"] == "BUY" and i % 3 == 0:
                signals[i]["signal"] = "HOLD"
                signals[i]["reason"] = "Signal suppressed due to low risk tolerance"
    
    elif risk_tolerance == "high":
        # More aggressive - more signals
        for i in range(1, len(signals)-1):
            if (signals[i]["signal"] == "HOLD" and 
                (signals[i-1]["signal"] == "BUY" or signals[i+1]["signal"] == "BUY")):
                signals[i]["signal"] = "BUY"
                signals[i]["reason"] = "Signal enhanced due to high risk tolerance"
    
    return signals

def main():
    """Main function"""
    args = parse_args()
    
    # Get risk tolerance from environment (set in flow definition)
    risk_tolerance = os.environ.get("RISK_TOLERANCE", "medium").lower()
    print(f"Using {risk_tolerance} risk tolerance")
    
    print(f"Reading indicator data from {args.indicators}...")
    
    # Read indicators data
    try:
        indicators_data = read_indicators_data(args.indicators)
    except Exception as e:
        print(f"Error reading indicators data: {e}")
        return 1
    
    print(f"Generating signals using {args.strategy} strategy...")
    
    # Apply selected strategy
    if args.strategy == "sma_crossover":
        signals = sma_crossover_strategy(indicators_data)
    elif args.strategy == "macd":
        signals = macd_strategy(indicators_data)
    elif args.strategy == "rsi":
        signals = rsi_strategy(indicators_data)
    elif args.strategy == "bollinger":
        signals = bollinger_bands_strategy(indicators_data)
    else:
        print(f"Error: Unknown strategy {args.strategy}")
        return 1
    
    # Adjust signals based on risk tolerance
    signals = adjust_signals_by_risk(signals, risk_tolerance)
    
    # Combine original data with signals
    output_data = []
    for i, indicator_row in enumerate(indicators_data):
        row = {
            "date": indicator_row["date"],
            "symbol": indicator_row["symbol"],
            "close": indicator_row["close"],
            "signal": signals[i]["signal"],
            "reason": signals[i]["reason"]
        }
        output_data.append(row)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Write signals to CSV
    with open(args.output, "w", newline="") as f:
        fieldnames = ["date", "symbol", "close", "signal", "reason"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_data)
    
    # Count signals
    buy_count = sum(1 for row in output_data if row["signal"] == "BUY")
    sell_count = sum(1 for row in output_data if row["signal"] == "SELL")
    
    print(f"Generated signals: {buy_count} buy, {sell_count} sell")
    print(f"Signals saved to {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())