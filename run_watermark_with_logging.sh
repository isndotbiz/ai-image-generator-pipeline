#!/bin/bash

# Comprehensive Watermark Workflow with Logging
# This script demonstrates the complete logging and progress tracking setup

echo "=== Fortuna Bound Watermark Workflow with Comprehensive Logging ==="
echo "Starting workflow at: $(date)"
echo ""

# Set log level to DEBUG for maximum verbosity
export LOG_LEVEL=DEBUG

# Create timestamped log filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/watermark_${TIMESTAMP}.log"

echo "Log file: $LOG_FILE"
echo "Log level: $LOG_LEVEL"
echo ""

# Run the workflow with comprehensive logging
echo "Running watermark workflow..."
python3 auto_watermark_workflow.py --mode full > "$LOG_FILE" 2>&1

# Check if workflow completed successfully
if [ $? -eq 0 ]; then
    echo "✓ Workflow completed successfully!"
else
    echo "✗ Workflow failed with errors"
    exit 1
fi

echo ""
echo "=== LOG ANALYSIS ==="

# Extract key metrics from the log
echo "Extracting metrics from log file..."

# Total images found
TOTAL_FOUND=$(grep "Total images found:" "$LOG_FILE" | grep -o '[0-9]\+')
echo "• Total images found: $TOTAL_FOUND"

# Total processed
TOTAL_PROCESSED=$(grep "Total images processed:" "$LOG_FILE" | grep -o '[0-9]\+')
echo "• Total images processed: $TOTAL_PROCESSED"

# Watermarked files
WATERMARKED=$(grep "Number of watermarked files:" "$LOG_FILE" | grep -o '[0-9]\+')
echo "• Number of watermarked files: $WATERMARKED"

# Originals deleted
DELETED=$(grep "Number of originals deleted:" "$LOG_FILE" | grep -o '[0-9]\+')
echo "• Number of originals deleted: $DELETED"

# Double-text removed
DOUBLE_TEXT=$(grep "Number of double-text images removed:" "$LOG_FILE" | grep -o '[0-9]\+')
echo "• Number of double-text images removed: $DOUBLE_TEXT"

# Processing time
PROCESSING_TIME=$(grep "Processing time:" "$LOG_FILE" | grep -o '[0-9.]\+ seconds')
echo "• Processing time: $PROCESSING_TIME"

echo ""
echo "=== ERROR AND WARNING CHECK ==="

# Check for errors and warnings
ERRORS=$(grep -i "error\|warning\|failed" "$LOG_FILE" | wc -l | tr -d ' ')
if [ "$ERRORS" -eq 0 ]; then
    echo "✓ No errors or warnings found in log"
else
    echo "⚠ Found $ERRORS potential issues:"
    grep -i "error\|warning\|failed" "$LOG_FILE"
fi

echo ""
echo "=== SUMMARY ==="
echo "Log file saved to: $LOG_FILE"
echo "Workflow completed at: $(date)"
echo ""
echo "For detailed analysis, view the full log:"
echo "  cat $LOG_FILE"
echo ""
echo "To search for specific events:"
echo "  grep 'WATERMARKING' $LOG_FILE"
echo "  grep 'STEP' $LOG_FILE"
echo "  grep 'METRICS' $LOG_FILE"

