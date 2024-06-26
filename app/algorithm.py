from trading_history import History
from bitvavo_test import bitvavo
from settings import settings
import pandas as pd
import logger


# This script contains the trading algorithm.


history = History()

# Function to get closing prices of a market
def get_closing(candles):
    closing = []
    
    for items in candles:
        closing.append(items[4])
        
    return closing


# Calculate MACD
def calculate_macd(closing, price):
    # Shrink the list size to only what's necessary
    closing = closing[:26]
    
    # Turn closing prices into pandas dataframe
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
    
    # Get threshold
    threshold = price * settings.get_setting("macd_percentage") / 100
    
    # Weight algorithm
    if bullish:
        if macd_histogram < 0:
            return 0.6
        elif macd_histogram < threshold:
            return 0.8
        else:
            return 1.0
    else:
        if macd_histogram > 0:
            return 0.4
        elif macd_histogram > -threshold:
            return 0.2
        else:
            return 0.0
        
def calculate_sma(closing, price):
    # Shrink the list size to only what's necessary
    closing = closing[:200]
    
    # Use pandas to get a dataframe
    data = pd.DataFrame(closing, columns=["close"])
    
    # Calculate the 50 and 200 period's mean
    period_50 = data["close"].rolling(window=50).mean()
    period_50 = period_50[len(period_50)-1]
    period_200 = data["close"].rolling(window=200).mean()
    period_200 = period_200[len(period_200)-1]
    
    margin = price * settings.get_setting("sma_percentage") / 100
    
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
        
def calculate_rsi(closing):
    # Shrink the list size to only what's necessary
    closing = closing[:14]
    
    # Generate pandas dataframe
    prices = pd.Series(closing)

    # Calculate price changes
    changes = prices.diff().fillna(0)

    # Calculate gains and losses
    gains = changes.where(changes > 0, 0)
    losses = changes.where(changes < 0, 0).abs()

    # Calculate average gain and average loss over a specified period
    average_gain = gains.rolling(window=14, min_periods=1).mean()
    average_loss = losses.rolling(window=14, min_periods=1).mean()

    # Calculate RS (Relative Strength)
    rs = average_gain / average_loss

    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    rsi_len = len(rsi)
    rsi_curr = rsi[rsi_len - 1] / 100
    
    # See if there's a bullish momentum
    if settings.get_setting("rsi_signal_boost"):
        bullish, bearish = False, False
        
        if rsi[rsi_len - 1] > rsi[rsi_len - 2]:
            bullish = True
        elif rsi[rsi_len - 1] < rsi[rsi_len - 2]:
            bearish = True
    
        if bullish and rsi_curr > 0.6:
            rsi_curr += 0.4
        elif bearish and rsi_curr < 0.4:
            rsi_curr = max(0, rsi_curr - 0.4)
            
    return rsi_curr


def buy(market, price):
    balance = settings.get_balance(market, "buy")
    if balance > 0.0001:
        amount = balance / price - 0.0001
        response = bitvavo.place_order(market, "buy", "market", { "amount": amount })
        settings.purchased(market)
        history.add_value(market, price, amount, "buy")
        logger.log(f"Bought '{amount}' of market '{market}' for '{price}'. API response: {response}")
        return balance
    
def sell(market, price):
    balance = settings.get_balance(market, "sell")
    if balance > 0.0001:
        amount = balance / price - 0.0001
        response = bitvavo.place_order(market, "sell", "market", { "amount": amount })
        settings.sold(market)
        history.add_value(market, price, amount, "sell")
        logger.log(f"Sold '{amount}' of market '{market}' for '{price}'. API response: {response}")
        return balance
    
    
def generate(market):
    # Get the market candles and closing prices
    candles = bitvavo.get_candles(market)
    closing = candles #get_closing(candles)
    
    # The amount of strategies are used
    total_strats = 3
    
    # Get the price of the market in euros
    price = bitvavo.get_prices(market + "-EUR")[0][1]
    
    # Generate strategy weights
    sma = calculate_sma(closing, price)
    macd = calculate_macd(closing, price)
    rsi = calculate_rsi(closing)
    
    # Normalize the weight to 0-1 range
    weight = sma + macd + rsi
    weight /= total_strats
    
    # Boost potential strong signals from a single strategy
    if settings.get_setting("weight_signal_boost"):
        extreme_low = sma == 0 or macd == 0 or rsi == 0
        extreme_high = sma == 1 or macd == 1 or rsi == 1
        
        if extreme_low and weight < 0.5:
            weight = 0
        elif extreme_high and weight > 0.5:
            weight = 1
    
    # Remove potential float-type decimal errors
    weight = int(weight * 1000) / 1000
    
    # Buy or sell if respective threshold is reached, or if price triggers risk management
    try:
        risk_signal = settings.get_setting("risk_management") and price < settings.get_last_price(market)
        if weight > settings.get_setting("buy_threshold"):
            balance = buy(market, price)
            settings.set_last_price(market, price)
            return balance
        elif weight < settings.get_setting("sell_threshold") or risk_signal:
            balance = sell(market, price)
            settings.set_last_price(market, price)
            return balance
    except Exception as e:
        logger.log(f"An error occurred at buying/selling at a market. Error message: {str(e)}", "error")
            
            