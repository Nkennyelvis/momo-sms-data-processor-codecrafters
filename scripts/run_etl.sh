#!/bin/bash

# ETL Pipeline Runner Script
# Runs the complete MoMo SMS data processing pipeline

set -e  # Exit on any error

echo "Starting MoMo SMS ETL Pipeline..."
echo "=================================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Warning: No virtual environment detected. Consider activating venv first."
fi

# Set default values
XML_FILE=${1:-"data/raw/momo.xml"}
OUTPUT_FILE=${2:-"data/processed/dashboard.json"}

echo "Input file: $XML_FILE"
echo "Output file: $OUTPUT_FILE"

# Check if input file exists
if [ ! -f "$XML_FILE" ]; then
    echo "Error: Input XML file not found: $XML_FILE"
    echo "Please ensure the XML file exists or provide the correct path."
    exit 1
fi

# Create necessary directories
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/logs
mkdir -p data/logs/dead_letter

echo ""
echo "Running ETL pipeline..."
echo "----------------------"

# Run the ETL pipeline
python etl/run.py --xml "$XML_FILE" --output "$OUTPUT_FILE" --verbose

# Check if the pipeline succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ETL Pipeline completed successfully!"
    echo "✅ Output saved to: $OUTPUT_FILE"
    
    # Show basic statistics if output file exists
    if [ -f "$OUTPUT_FILE" ]; then
        echo ""
        echo "Quick Stats:"
        echo "------------"
        python -c "
import json
with open('$OUTPUT_FILE', 'r') as f:
    data = json.load(f)
    summary = data.get('summary', {})
    print(f'Total Transactions: {summary.get(\"totalTransactions\", 0):,}')
    print(f'Total Volume: \${summary.get(\"totalVolume\", 0):,.2f}')
    print(f'Average Transaction: \${summary.get(\"averageTransaction\", 0):.2f}')
    print(f'Active Users: {summary.get(\"activeUsers\", 0):,}')
" 2>/dev/null || echo "Could not parse output statistics"
    fi
    
else
    echo ""
    echo "❌ ETL Pipeline failed!"
    echo "Check the logs in data/logs/etl.log for more details."
    exit 1
fi

echo ""
echo "Pipeline execution completed."
echo "=============================="
