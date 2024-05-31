from python_bitvavo_api.bitvavo import Bitvavo
import logger


# This is the Bitvavo Client file, acting as a handle for Bitvavo API operations.


class BitvavoClient:
    # Define the engine and socket up front
    engine = None
    socket = None
        
    def initiate_api(self, api_key, api_secret):
        self.engine = Bitvavo({"APIKEY": api_key, "APISECRET": api_secret})
        self.socket = self.engine.newWebsocket()
        self.socket.setErrorCallback(self.error_callback)
        
    # Function to print and log errors
    def error_callback(self, error_data):
        error_message = "Bitvavo error: " + str(error_data)
        logger.log(error_message, "error")
        
    # Function to safely execute calls
    def socket_call(self, f: any):
        try:
            return f()
        except Exception as e:
            logger.log(str(e), "error")
        
    # Function to get market values
    def get_prices(self, market: str | None):
        return self.socket_call(lambda: self.socket.tickerPrice({"market": market}))
    
    # Function to get information about markets
    def available_markets(self, market: str | None):
        return self.socket_call(lambda: self.socket.markets({"market": market}))
    
    # Function to get relevant data of markets
    def ticker_24h(self, market: str | None):
        return self.socket_call(lambda: self.socket.ticker24h({"market": market}))
    
    # Function to place a market order
    def place_order(self, market: str, side: str, order_type: str, body: dict):
        return self.socket_call(lambda: self.socket.placeOrder(market, side, order_type, body))
        
    # Function to update a market order
    def update_order(self, market: str, order_id: str, body: dict):
        return self.socket_call(lambda: self.socket.updateOrder(market, order_id, body))
    
    # Function to cancel a market order
    def cancel_order(self, market: str, order_id: str):
        return self.socket_call(lambda: self.socket.cancelOrder(market, order_id))
    
    # Function to cancel all orders in a market
    def cancel_orders(self, market: str | None):
        return self.socket_call(lambda: self.socket.cancelOrders({"market": market}))
        
    # Function to get open orders of a market or body
    def get_open_orders(self, market: str | None, body: str | None):
        return self.socket_call(lambda: self.socket.ordersOpen({"market": market, "body": body}))
    
    # Function to get orders of a market
    def get_orders(self, market: str):
        return self.socket_call(lambda: self.socket.getOrders(market))
    
    # Function to get information about an order
    def get_order(self, market: str, order_id: str):
        return self.socket_call(lambda: self.socket.getOrder(market, order_id))
    
    # Function to get history of trades of a market
    def get_trades(self, market: str):
        return self.socket_call(lambda: self.socket.trades(market))
    
    # Function to get the fees of a market
    def get_fees(self, market: str | None):
        return self.socket_call(lambda: self.socket.fees(market))
    
    # Function to get the order book of a market
    def get_book(self, market: str):
        return self.socket_call(lambda: self.socket.book(market))
    
    # Function to get the account balance
    def get_balance(self, symbol: str | None):
        return self.socket_call(lambda: self.socket.balance({ "symbol": symbol }))
    
    # Function to subscribe to ticker updates
    def subscribe_ticker(self, market: str, callback):
        self.socket_call(lambda: self.socket.subscriptionTicker(market, callback))
        
    # Function to subscribe to trade updates
    def subscribe_trade(self, market: str, callback):
        self.socket_call(lambda: self.socket.subscriptionTrades(market, callback))
        
    # Function to get the candles of a market
    def get_candles(self, market: str, interval: str = "1h", limit: int = 1440):
        return self.socket_call(lambda: self.socket.candles(market, interval, limit=limit))
    

# The client to import in scripts, to use it shared
bitvavo = BitvavoClient()

