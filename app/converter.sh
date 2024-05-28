#!/bin/bash

# Create location to store shared objects
mkdir -p shared_objects

# Rename all .py files to .pyx
for file in *.py; do
    if [[ "$file" != "webpage.py" && "$file" != "setup.py" ]]; then
        mv "$file" "${file%.py}.pyx"
    fi
done

# Create a setup.py file
echo 'from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize(["*.pyx"])
)' > setup.py

# Run the setup script to build shared objects
python setup.py build_ext --inplace

# Move all shared objects to the dir
mv *.so shared_objects/

