#!/usr/bin/env -S bash -c 'source venv/bin/activate && exec "$0" "$@"'

# Daily Palette Rotation Script
# This script can be run daily via cron to update A/B palettes
#
# To set up daily rotation at 8 AM, add this line to your crontab:
# 0 8 * * * /path/to/your/project/daily_palette_rotation.sh
#
# To edit crontab, run: crontab -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

# Log the rotation attempt
echo "[$(date)] Starting daily palette rotation..." >> palette_rotation.log

# Run the A/B palette selector
if venv/bin/python ab_palette_selector.py >> palette_rotation.log 2>&1; then
    echo "[$(date)] Palette rotation completed successfully" >> palette_rotation.log
else
    echo "[$(date)] ERROR: Palette rotation failed" >> palette_rotation.log
    exit 1
fi

# Clean up old backup files (keep only last 30 days)
find . -name "palette_*_????????_??????.json" -mtime +30 -delete 2>/dev/null

echo "[$(date)] Daily palette rotation script completed" >> palette_rotation.log

