#!/bin/bash

gen () {
    echo "Testing with args: $1, $2, $3, $4, $5, $6"
    python3 - "$1" "$2" "$3" "$4" "$5" "$6" <<PY
import sys
print(f"Python received {len(sys.argv)} args:")
for i, arg in enumerate(sys.argv):
    print(f"  argv[{i}]: {arg}")
PY
}

gen "Miami Edgewater sky-suite" "Cartier Love ring" "Spoil to Stay Close" "4:5" "mia_edge_cartier" "ig"

