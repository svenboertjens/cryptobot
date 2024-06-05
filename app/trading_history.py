from datetime import datetime
from file_queue import queue
import logger
import json
import os


# This file acts as the trading history controller.


history_path = "./app/history.json"

def thread_wrapper(f):
    def wrapper(*args, **kwargs):
        finished = None
        try:
            finished = queue.attempt_entry(history_path)
            to_return = f(*args, **kwargs)
            finished()
            return to_return
        except Exception as e:
            logger.log(f"Something went wrong while updating the trading history. Error message: {str(e)}", "error")
            if finished:
                finished()
    return wrapper

class History:
    @thread_wrapper
    def add_value(self, market: str, price: float, balance: float, action: str = None):
        time = datetime.now()
        date = f"{time.day:02}-{time.month:02}-{time.year}:{time.hour}"
        
        with open(history_path, "r") as file:
            # Get data from json file
            data = json.load(file)
            print(data)
            balance_data = data[market + "/balance"]
            actions_data = data[market + "/actions"]
            if action == "buy":
                data[market + "/active"] -= price * amount
                data["EUR/active"] += price * amount
            elif action == "sell":
                data[market + "/active"] += price * amount
                data["EUR/active"] -= price * amount
            
        # Add data to the end of the list
        balance_data.append({ "date": date, "balance": balance })
        if action:
            actions_data.append({ "date": date, "balance": balance, "action": action })
            if len(actions_data) > 100:
                # Remove the 101th data entry if exists
                actions_data.pop(0)
                
            # Add changes
            data[market + "/actions"] = actions_data
        
        # If another entry of today exist, remove it
        length = len(balance_data)
        if length > 1 and balance_data[-2]["date"] == date:
            balance_data.pop(length - 2)
        elif length > 365:
            # Remove the 366th data entry if exists
            balance_data.pop(0)
            
        # Add changes to the data list
        data[market + "/balance"] = balance_data
        
        # Write changes to the file
        with open(history_path, "w") as file:
            print(data)
            json.dump(data, file, indent=4)

    # Function to get the active balance of a market
    @thread_wrapper
    def get_balance(self, market: str):
        with open(history_path, "r") as file:
            return json.load(file)[market + "/active"]
            
    # Function to correct the available balance amount
    @thread_wrapper
    def correct(self, market: str, amount: float):
        with open(history_path, "r") as file:
            data = json.load(file)
            data[market + "/active"] = amount
            
        with open(history_path, "w") as file:
            json.dump(data, file, indent=4)
            
    @thread_wrapper
    def get_values(self):
        with open(history_path, "r") as file:
            data = json.load(file)
            return data
        
    @thread_wrapper
    def add_market(self, market: str):
        with open(history_path, "r") as file:
            data = json.load(file)
            
        # Add values to the data
        if (market + "/active") not in data:
            data[market + "/balance"] = []
            data[market + "/actions"] = []
            data[market + "/active"] = 0
            
        with open(history_path, "w") as file:
            # Write changes
            json.dump(data, file, indent=4)
        
    @thread_wrapper
    def remove_market(self, market: str):
        with open(history_path, "r") as file:
            data = json.load(file)
            
        if (market + "/balance") in data:
            del data[market + "/balance"]
            del data[market + "/actions"]
            del data[market + "/active"]
            
        with open(history_path, "w") as file:
            # Write changes
            json.dump(data, file, indent=4)
            
