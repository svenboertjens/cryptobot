from bitvavo_client import BitvavoClient
import pandas as pd
from settings import get_setting

bv = BitvavoClient()

# Function to get closing prices of a market
def get_closing(candles):
    closing = []
    
    for candle in candles:
        closing.append(candle)
        
    return closing


# Calculate MACD
def calculate_macd(candles):
    # Use only the first 26 candles
    candles = candles[:26]
    # Get the closing prices
    closing = get_closing(candles)
    prices = pd.Series(closing)

    # Short-term EMA
    ema_short = prices.ewm(span=12, adjust=False).mean()

    # Long-term EMA
    ema_long = prices.ewm(span=26, adjust=False).mean()

    # MACD line
    macd_line = ema_short - ema_long
    # Signal line
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    # MACD Histogram
    macd_histogram = macd_line - signal_line
    macd_histogram = macd_histogram[len(macd_histogram)-1] # Get last
    
    # Calculate whether it's bullish
    bullish = macd_line > signal_line
    bullish = bullish[len(bullish)-1] # Get last
    
    # Weight algorithm
    if bullish:
        if macd_histogram < 0:
            return 0.6
        elif macd_histogram < 1.5:
            return 0.8
        else:
            return 1.0
    else:
        if macd_histogram > 0:
            return 0.4
        elif macd_histogram > -1.5:
            return 0.2
        else:
            return 0.0
        
def calculate_sma(candles):
    # Use only first 200 candles
    candles = candles[:200]
    # Get closing values from candles
    closing = get_closing(candles)
    # Use pandas to get a dataframe
    data = pd.DataFrame(closing, columns=["close"])
    
    # Calculate the 50 and 200 period's mean
    period_50 = data["close"].rolling(window=50).mean()
    period_50 = period_50[len(period_50)-1]
    period_200 = data["close"].rolling(window=200).mean()
    period_200 = period_200[len(period_200)-1]
    
    margin = get_setting("sma_margin")
    
    if period_50 < period_200:
        if period_50 + (2 * margin) < period_200:
            return 1.0
        elif period_50 + margin < period_200:
            return 0.8
        else:
            return 0.6
    else:
        if period_50 - (2 * margin) > period_200:
            return 0.0
        elif period_50 - margin > period_200:
            return 0.2
        else:
            return 0.4
        
def calculate_rsi(candles):
    candles = candles[:14]
    closing = get_closing(candles)
    prices = pd.Series(closing)

    # Calculate price changes
    changes = prices.diff().fillna(0)

    # Calculate gains and losses
    gains = changes.where(changes > 0, 0)
    losses = changes.where(changes < 0, 0).abs()

    # Calculate average gain and average loss over a specified period (e.g., 14 periods)
    average_gain = gains.rolling(window=14, min_periods=1).mean()
    average_loss = losses.rolling(window=14, min_periods=1).mean()

    # Calculate RS (Relative Strength)
    rs = average_gain / average_loss

    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    
    rsi_len = len(rsi)
    
    bullish, bearish = False, False
    
    # See if there's a bullish momentum
    if rsi[rsi_len - 1] > rsi[rsi_len - 2]:
        bullish = True
    elif rsi[rsi_len - 1] < rsi[rsi_len - 2]:
        bearish = True
        
    rsi_curr = rsi[rsi_len - 1] / 100
    
    if bullish and rsi_curr > 0.6:
        rsi_curr += 0.4
    elif bearish and rsi_curr < 0.4:
        rsi_curr = max(0, rsi_curr - 0.4)
        
    return rsi_curr
    
global bought, sold

bought = []
sold = []

def buy(price):
    if len(sold) >= len(bought) - 3:
        bought.append(price)
        
def sell(price):
    if len(bought) > len(sold) - 3:
        sold.append(price)
    
    
def generate_test(candles):
    if len(candles) < 200:
        
        bought_amt = 0
        for price in bought:
            bought_amt += price
        
        sold_amt = 0
        for price in sold:
            sold_amt += price
            
        bought_amt /= len(bought)
        sold_amt /= len(sold)
            
        print(f"Gain/loss: {(sold_amt / bought_amt) * 100}%")
        
        exit(1)
        
        
    total_strats = 3
        
    sma = calculate_sma(candles)
    macd = calculate_macd(candles)
    rsi = calculate_rsi(candles)

    weight = sma + macd + rsi
    weight /= total_strats
    
    extreme_low = sma == 0 or macd == 0 or rsi == 0
    extreme_high = sma == 1 or macd == 1 or rsi == 1
    
    if extreme_low and weight < 0.75:
        weight = 0
    elif extreme_high and weight > 0.25:
        weight = 1
    
    weight = int(weight * 10000) / 10000
    
    price = candles[0]

    if weight > 0.75:
        buy(price)
    elif weight < 0.3:
        sell(price)

