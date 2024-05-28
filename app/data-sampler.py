import ctypes, time

# Set up the connection to the C++ math helper
lib = ctypes.CDLL("./app/math-helper.so")

# Set up `generate_regular`
lib.generate_regular.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_int)
lib.generate_regular.restype = ctypes.c_int

# Set up `generate_depending_fill`
lib.generate_depending_fill.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_int)
lib.generate_depending_fill.restype = ctypes.POINTER(ctypes.c_int * 2)

# Set up `free_memory`
lib.free_memory.argtypes = [ctypes.POINTER(ctypes.c_int * 2)]
lib.free_memory.restype = None
    
descending_levels = {
    "low": "valley",
    "normal": "low",
    "high": "normal",
    "peak": "high"
}

values = []

last_value = 175
min_value = 150
max_value = 200

def generate():
    new_value = lib.generate_regular(min_value, max_value, last_value)
    values.insert(0, new_value)
    
    length = len(values)
    if length > 205:
        values.pop(length - 1)
    
from algorithm import generate_test
import pandas as pd

data = pd.read_csv("./app/csv/seven.csv")["Close"]
data = list(data)

while True:
    generate_test(data)
    data.pop(0)
    
    