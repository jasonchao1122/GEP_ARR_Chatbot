#!/bin/bash
# Setup script for local cron job automation

echo "🔧 GEP Report - Local Cron Job Setup"
echo "======================================"
echo ""

# Get the current directory
SCRIPT_DIR="/Users/victor.sanabia/GEP Forecast Report"
PYTHON_PATH=$(which python3)
LOG_FILE="$SCRIPT_DIR/cron.log"

echo "📁 Script directory: $SCRIPT_DIR"
echo "🐍 Python path: $PYTHON_PATH"
echo "📝 Log file: $LOG_FILE"
echo ""

# Set Slack token
SLACK_BOT_TOKEN=""  # Add your Slack bot token here
echo "✅ Using Slack bot token: xoxb-****${SLACK_BOT_TOKEN: -10}"

echo ""
echo "📅 Current crontab entries:"
crontab -l 2>/dev/null || echo "(no existing crontab)"
echo ""

# Create the cron job entry
CRON_ENTRY="0 9 * * * export SLACK_BOT_TOKEN='$SLACK_BOT_TOKEN' && cd \"$SCRIPT_DIR\" && $PYTHON_PATH run_daily_report.py >> \"$LOG_FILE\" 2>&1"

echo "🔧 Proposed cron job:"
echo "$CRON_ENTRY"
echo ""
echo "This will run daily at 9:00 AM"
echo ""

read -p "Add this to your crontab? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Backup existing crontab
    crontab -l 2>/dev/null > crontab_backup_$(date +%Y%m%d_%H%M%S).txt
    
    # Add new entry
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    
    echo "✅ Cron job added!"
    echo ""
    echo "📋 Current crontab:"
    crontab -l
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "📝 Notes:"
    echo "   - Your laptop must be awake at 10 AM for this to run"
    echo "   - Logs will be saved to: $LOG_FILE"
    echo "   - To remove: crontab -e (then delete the line)"
    echo "   - To test now: python3 run_daily_report.py"
else
    echo "❌ Setup cancelled"
    echo ""
    echo "To add manually, run:"
    echo "crontab -e"
    echo ""
    echo "Then add this line:"
    echo "$CRON_ENTRY"
fi
