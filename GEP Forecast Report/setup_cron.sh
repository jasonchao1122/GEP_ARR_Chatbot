#!/bin/bash
#
# GEP Forecast Report - Cron Job Setup Script
# This script sets up a cron job to run the GEP daily report at 8 AM.
#

set -e

echo "=================================================="
echo "GEP Forecast Report - Cron Job Setup"
echo "=================================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python3"

# Verify virtual environment exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo "Script directory: $SCRIPT_DIR"
echo "Python path: $PYTHON_PATH"
echo ""

# Prompt for Slack bot token if not set
if [ -z "$SLACK_BOT_TOKEN" ]; then
    echo "Please enter your Slack bot token:"
    read -r SLACK_TOKEN
    if [ -z "$SLACK_TOKEN" ]; then
        echo "ERROR: Slack bot token is required!"
        exit 1
    fi
else
    SLACK_TOKEN="$SLACK_BOT_TOKEN"
    echo "Using SLACK_BOT_TOKEN from environment."
fi

echo ""
echo "Setting up cron job for 8 AM daily..."

# Create the cron entry
# Format: minute hour day month weekday command
CRON_ENTRY="0 8 * * * export SLACK_BOT_TOKEN='$SLACK_TOKEN' && cd \"$SCRIPT_DIR\" && $PYTHON_PATH run_daily_report.py >> \"$SCRIPT_DIR/cron.log\" 2>&1"

# Check if cron entry already exists
EXISTING_CRON=$(crontab -l 2>/dev/null | grep -F "run_daily_report.py" || true)

if [ -n "$EXISTING_CRON" ]; then
    echo ""
    echo "WARNING: A GEP report cron job already exists:"
    echo "$EXISTING_CRON"
    echo ""
    echo "Do you want to replace it? (y/n)"
    read -r REPLACE
    if [ "$REPLACE" != "y" ] && [ "$REPLACE" != "Y" ]; then
        echo "Keeping existing cron job. Exiting."
        exit 0
    fi
    # Remove existing entry
    crontab -l 2>/dev/null | grep -v "run_daily_report.py" | crontab -
fi

# Add the new cron entry
(crontab -l 2>/dev/null || true; echo "$CRON_ENTRY") | crontab -

echo ""
echo "=================================================="
echo "✅ Cron job setup complete!"
echo "=================================================="
echo ""
echo "The following cron job has been added:"
echo ""
echo "$CRON_ENTRY"
echo ""
echo "To verify, run: crontab -l"
echo ""
echo "To view logs, check: $SCRIPT_DIR/cron.log"
echo ""
echo "IMPORTANT NOTES:"
echo "- Your computer needs to be on at 8 AM for the cron job to run"
echo "- The cron job will open a browser for Snowflake Okta authentication"
echo "- Make sure you're logged in before 8 AM or the job may fail"
echo ""
echo "To test manually, run:"
echo "  cd \"$SCRIPT_DIR\" && python3 run_daily_report.py"
echo ""
