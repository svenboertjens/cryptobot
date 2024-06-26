from trading_history import History
from bitvavo_test import bitvavo
import sqlite3
import logger


# This script controls the user's settings.


def handle_errors(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.log(f"An error occurred with the settings class. Error message: {str(e)}", "error")
            
    return wrapper

class Settings:
    # Create connection to database
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    
    @handle_errors
    def __init__(self):
        # Set up tables
        self.c.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )""")
        self.c.execute("""CREATE TABLE IF NOT EXISTS markets (
            market TEXT NOT NULL
        )""")
        self.c.execute("""CREATE TABLE IF NOT EXISTS market_data (
            market TEXT NOT NULL,
            counter INTEGER DEFAULT 0,
            price REAL DEFAULT -1
        )""")
        
        # Get active markets
        self.c.execute("SELECT * FROM markets")
        markets = self.c.fetchall()
        
        # Get history class
        self.history = History()

        # Check whether it's a first-time login
        if len(markets) == 0:
            # Set up markets table and update history
            markets = ["BTC", "ETH", "USD"]
            for market in markets:
                self.add_market(market)
                self.history.add_market(market)
                
            # Manually set up the bot's EUR market
            self.history.add_market("EUR")
            self.history.correct("EUR", 1000)
            
            # List of the default values
            default_settings = {
                "sma_percentage": 25,
                "macd_percentage": 8,
                "rsi_signal_boost": True,
                "weight_signal_boost": False,
                "buy_threshold": 0.7,
                "sell_threshold": 0.3,
                "stop_percentage": 92.5,
                "risk_management": True,
                "iteration_delay": 60,
                "spread": 2,
                "max_balance": -1
            }
            
            # Insert the default values
            for key, value in default_settings.items():
                self.set_setting(key, value)
                
            # Save changes
            self.conn.commit()
                
            logger.log("Created storage tables")


    # Function to convert string values to their respective types
    @handle_errors
    def convert_value(self, value):
        # Check for boolean values
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # Check for number values
        try:
            float_value = float(value)
            return float_value
        except ValueError:
            pass
        
        # Return as string if no other type matched
        return value
    
    @handle_errors
    def api_name(self, string: str):
        return string.replace("_", "-")

    # Function to update settings
    @handle_errors
    def set_setting(self, key: str, value: str):
        # Assign the new value
        self.c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        # Save changes
        self.conn.commit()
        
    # Function to retrieve settings
    @handle_errors
    def get_setting(self, key: str):
        # Get the value of the key
        self.c.execute("SELECT value FROM settings WHERE key=?", (key,))
        # Fetch and return the value
        value = self.c.fetchone()
        return self.convert_value(value[0])

    # Function to add a market
    @handle_errors
    def add_market(self, market: str):
        # Assign the new market
        self.c.execute("INSERT OR REPLACE INTO markets (market) VALUES (?)", (market,))
        # Create buy counter
        self.c.execute("INSERT INTO market_data (market, counter, price) VALUES (?, ?, ?)", (market, 0, -1))
        # Save changes
        self.conn.commit()
        
    # Function to remove a market
    @handle_errors
    def remove_market(self, market: str):
        # Remove the market from the tables
        self.c.execute("DELETE FROM markets WHERE market=?", (market,))
        self.c.execute("DELETE FROM market_data WHERE market=?", (market,))
        # Save changes
        self.conn.commit() 

    # Function get all markets
    @handle_errors
    def get_markets(self):
        # Get the markets
        self.c.execute("SELECT market FROM markets")
        # Fetch the markets
        markets = self.c.fetchall()
        # Normalize the market names
        for i, market in enumerate(markets):
            markets[i] = market[0]
        
        return markets

    # Function to get the balance for buy/sell markets
    @handle_errors
    def get_balance(self, market: str, side: str):
        # Get the market's buy counter
        self.c.execute("SELECT counter FROM market_data WHERE market=?", (market,))
        counter = self.c.fetchall()[0][0]
        
        # Check the side
        if side == "buy":
            # Calculate how many times can be bought
            share = self.get_setting("spread") - counter
            # Check whether the market can be bought from
            if share > 0:
                # Get the total balance available
                total_balance = self.history.get_balance("EUR")
                # Correct balance anomalies
                max_balance = bitvavo.get_balance("EUR")["available"]
                if total_balance > max_balance:
                    total_balance = max_balance
                    self.history.correct("EUR", max_balance)
                
                if total_balance < 0.0001:
                    return 0
                
                max_balance = self.get_setting("max_balance")
                
                # Scale down the balance if necessary
                if max_balance > 0:
                    total_balance = min(total_balance, max_balance)
                    
                # Get the shares of all markets
                self.c.execute("SELECT counter FROM market_data")
                all_shares_list = self.c.fetchall()
                
                # Normalize the received shares list
                for i, values in enumerate(all_shares_list):
                    all_shares_list[i] = values[0]
                    
                # Calculate the shares that the budget is divided into
                all_shares = (len(all_shares_list) * self.get_setting("spread")) - sum(all_shares_list)
                # Return the
                if all_shares > 0.0001:
                    return total_balance / all_shares
                else:
                    return 0
            else:
                return 0
        elif side == "sell":
            # How many times can be sold to
            share = counter
            # Check whether the market can be sold
            if share > 0:
                # Calculate the available balance of the market
                market_balance = self.history.get_balance(market)
                # Correct anomalities in the available balance
                max_balance = bitvavo.get_balance(market)["available"]
                if market_balance > max_balance:
                    market_balance = max_balance
                    self.history.correct(market, max_balance)
                market_amount = market_balance * market_price
                if market_balance < 0.0001:
                    return 0
                # Return the balance of how much can be sold
                return market_balance / share
            else:
                return 0
        else:
            markets = self.get_markets()
            balances = bitvavo.get_balance()
            total_balance = 0
            
            for balance in balances:
                if balance["symbol"] in markets:
                    total_balance += balance["available"] + balance["inOrder"]
                    
            return total_balance
            
    # Function to add 1 to buy counter of a market
    @handle_errors
    def purchased(self, market: str):
        # Update the counter and save changes
        self.c.execute("UPDATE market_data SET counter = counter + 1 WHERE market=?", (market,))
        self.conn.commit()
        
    # Function to remove 1 to buy counter of a market
    @handle_errors
    def sold(self, market: str):
        # Update the counter and save changes
        self.c.execute("UPDATE market_data SET counter = counter - 1 WHERE market=? AND counter > 0", (market,))
        self.conn.commit()
        
    # Function to get the last price of a market
    @handle_errors
    def get_last_price(self, market: str):
        self.c.execute("SELECT price FROM market_data WHERE market=?", (market,))
        return self.c.fetchone()[0]
    
    # Function to set the last price of a market
    @handle_errors
    def set_last_price(self, market: str, price: float):
        price *= (self.get_setting("stop_percentage") / 100)
        last_price = self.get_last_price(market)
        # Only update if smaller than current risk price
        if price < last_price or last_price < 0:
            self.c.execute("UPDATE market_data SET price=? WHERE market=?", (price, market))
            self.conn.commit()


# Use a variable to define the settings to make it shared
settings = Settings()
