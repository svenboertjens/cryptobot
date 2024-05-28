import sqlite3


# This script controls the user's settings


# Create connection to database
conn = sqlite3.connect("data.db")
c = conn.cursor()

# Set up tables
c.execute("""CREATE TABLE IF NOT EXISTS settings (
    name TEXT NOT NULL
    value TEXT NOT NULL
)""")
c.execute("""CREATE TABLE IF NOT EXISTS markets
    coin TEXT NOT NULL
""")

# Get active markets
c.execute("SELECT * FROM markets")
markets = c.fetchall()

# Check whether it's a first-time login
if len(markets) == 0:
    markets = ["BTC-EUR"]

settings = {
    "sma_margin": 7.5
}

def get_setting(setting: str):
    return settings[setting]