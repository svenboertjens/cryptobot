#!/bin/bash

# Loop through all .so files with the specific naming pattern
for so_file in *.cpython-*.so; do
    # Extract the base name before the .cpython part
    base_name=$(echo "$so_file" | sed -E 's/(.+)\.cpython-.+\.so/\1/')

    # Check if there is a corresponding .py file
    if [ -f "${base_name}.py" ]; then
        # Remove the .py file
        rm "${base_name}.py"
    fi
done
