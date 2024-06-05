import pandas as pd
import time


# This is the Bitvavo Test Client file, to simulate the bot.


class BitvavoTestClient:
    data = {
        "BTC": list(pd.read_csv("./app/csv/one.csv")["Close"]),
        "ETH": list(pd.read_csv("./app/csv/seven.csv")["Close"]),
        "USD": list(pd.read_csv("./app/csv/four.csv")["Close"]),
        "BTC-EUR": [0],
        "ETH-EUR": [0],
        "USD-EUR": [0]
    }
    balance = {
        "EUR": { "available": 1000, "inOrder": 0 },
        "BTC": { "available": 0, "inOrder": 0 },
        "BTC-EUR": 0,
        "ETH": { "available": 0, "inOrder": 0 },
        "ETH-EUR": 0,
        "USD": { "available": 0, "inOrder": 0 },
        "USD-EUR": 0
    }
    start_time = time.time()
    
    # Function to get market values
    def get_prices(self, market: str | None):
        return [[None, self.data[market][0]]]
    
    # Function to place a market order
    def place_order(self, market: str, side: str, order_type: str, body: dict):
        if order_type == "market":
            price = self.data[market][0]
            amount = body["amount"]
            total_price = price * amount
            if side == "buy" and self.balance["EUR"]["available"] >= total_price:
                self.balance["EUR"]["available"] -= total_price  * 1.002
                self.balance[market]["available"] += total_price / 1.002
            elif side == "sell" and self.balance[market]["available"] >= total_price:
                self.balance["EUR"]["available"] += total_price  / 1.002
                self.balance[market]["available"] -= total_price * 1.002
            else:
                if side == "buy":
                    print(f"Buy error:  got '{total_price}', limit was '{self.balance["EUR"]}'")
                else:
                    print(f"Sell error: got '{total_price}', limit was '{self.balance[market]}'")
                    
                return "error"
    
    # Function to get the account balance
    def get_balance(self, symbol: str = None):
        if symbol:
            return self.balance[symbol]
        else:
            return self.balance
        
    # Function to get the candles of a market
    def get_candles(self, market: str):
        return self.data[market]
    
    iterations = 0
    
    # Function to go to the next period
    def next_period(self):
        self.iterations += 1
        
        for market, candles in self.data.items():
            if "-EUR" in market:
                continue
            
            old_price = candles.pop(0)
            new_price = candles[0]
            
            self.balance[market]["available"] = self.balance[market]["available"] / old_price * new_price
            self.data[market + "-EUR"][0] = new_price
            
            if len(candles) <= 200:
                total_balance = 0
                for market, balance in self.balance.items():
                    if "-EUR" not in market:
                        total_balance += balance["available"]
                    
                print(f"Balance: {total_balance:.2f}")
                print(f"Time: {(time.time() - self.start_time):.2f}s")
                print(f"Years: {(self.iterations / 365):.2f}")
                exit(1)
                
    def initiate_api(self, *args, **kwargs):
        return args, kwargs
    

# The client to import in scripts, to use it shared
bitvavo = BitvavoTestClient()

