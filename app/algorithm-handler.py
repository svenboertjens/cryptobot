from settings import settings
from algorithm import generate
import logger
import time

# This script handles running the algorithm.


from bitvavo_test import bitvavo


while True:
    markets = settings.get_markets()
    
    # Run all markets on a thread
    try:
        for market in markets:
            generate(market)
    except Exception as e:
        logger.log(f"A critical error occurred at running the algorithm. Error message: {str(e)}", "critical")
        
    bitvavo.next_period()
    
    #time.sleep(settings.get_setting("iteration_delay"))