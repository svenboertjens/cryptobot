import pandas as pd
import time


# This is the Bitvavo Test Client file, to simulate the bot.


class BitvavoTestClient:
    data = {
        "BTC-EUR": list(pd.read_csv("./app/csv/three.csv")["Close"]),
        "ETH-EUR": list(pd.read_csv("./app/csv/eight.csv")["Close"]),
        "USD-EUR": list(pd.read_csv("./app/csv/nine.csv")["Close"])
    }
    balance = {
        "EUR": 1000,
        "BTC-EUR": 0,
        "ETH-EUR": 0,
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
            if side == "buy" and self.balance["EUR"] >= total_price:
                self.balance["EUR"] -= total_price  * 1.002
                self.balance[market] += total_price / 1.002
            elif side == "sell" and self.balance[market] >= total_price:
                self.balance["EUR"] += total_price  / 1.002
                self.balance[market] -= total_price * 1.002
            else:
                if side == "buy":
                    print(f"Buy error:  got '{total_price}', limit was '{self.balance["EUR"]}'")
                else:
                    print(f"Sell error: got '{total_price}', limit was '{self.balance[market]}'")
                    
                return "error"
    
    # Function to get the account balance
    def get_balance(self, symbol: str | None):
        return self.balance[symbol]
        
    # Function to get the candles of a market
    def get_candles(self, market: str):
        return self.data[market]
    
    iterations = 0
    
    # Function to go to the next period
    def next_period(self):
        self.iterations += 1
        
        for market, candles in self.data.items():
            old_price = candles[0]
            new_price = candles[1]
            
            self.balance[market] = self.balance[market] / old_price * new_price
            
            candles.pop(0)
            
            if len(candles) <= 200:
                print(f"Balance: {sum(self.balance.values()):.2f}")
                print(f"Time: {(time.time() - self.start_time):.2f}s")
                print(f"Years: {(self.iterations / 365):.2f}")
                exit(1)
    

# The client to import in scripts, to use it shared
bitvavo = BitvavoTestClient()

