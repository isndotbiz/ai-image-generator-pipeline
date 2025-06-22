#!/bin/bash
# Benchmarking Runner Script
# This script demonstrates proper usage of local venv for benchmarking

set -e

echo "🔍 Fortuna Bound Model Benchmarking Suite"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "../venv" ]; then
    echo "❌ Virtual environment not found at ../venv"
    echo "Please create a virtual environment first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Method 1: Use venv executable directly (recommended for scripts)
echo "🚀 Running benchmarks using venv/bin/python..."
echo ""

# Run the main benchmark suite
../venv/bin/python model_benchmark.py

echo ""
echo "💡 Alternative usage methods:"
echo ""
echo "Method 2: Activate venv first, then run python:"
echo "  source venv/bin/activate"
echo "  python benchmarking/model_benchmark.py"
echo ""
echo "Method 3: From project root with venv prefix:"
echo "  venv/bin/python benchmarking/model_benchmark.py"
echo ""

echo "✅ Benchmarking complete!"
echo "📊 Results saved in benchmarking/results/"

