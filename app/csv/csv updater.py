import pandas as pd

items = ["five", "six", "seven", "eight", "nine", "ten"]

for item in items:
    url = f"./app/csv/{item}.csv"
    data = pd.read_csv(url)["Close"]
    
    # Reverse the data directly within pandas DataFrame
    data = data[::-1]
    
    # Write the reversed 'Close' data back to the CSV file
    data.to_csv(url, index=False)
