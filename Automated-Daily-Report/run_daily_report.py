#!/usr/bin/env python3
"""
Main entry point for Gumloop automation
Runs both update and send scripts in sequence
"""

import sys
import subprocess
from datetime import datetime

def run_script(script_name, description):
    """Run a Python script and capture output"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}:")
        print(e.stdout)
        print(e.stderr)
        return False

def main():
    """Main execution flow"""
    print(f"\n{'='*60}")
    print(f"📊 GEP DAILY REPORT AUTOMATION")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"{'='*60}\n")
    
    # Step 0: Auto-refresh targets
    if not run_script('refresh_targets_simple.py', 'Checking/refreshing monthly targets'):
        print("\n⚠️  Warning: Failed to refresh targets. Using cached values.")
        # Don't exit - continue with cached targets
    
    # Step 1: Update GEP report (fetch data from Snowflake)
    if not run_script('update_gep_report.py', 'Fetching latest data from Snowflake'):
        print("\n❌ Failed to update GEP report. Aborting.")
        sys.exit(1)
    
    # Step 2: Send to Slack
    if not run_script('send_slack_update.py', 'Sending update to Slack'):
        print("\n❌ Failed to send Slack update.")
        sys.exit(1)
    
    # Success!
    print(f"\n{'='*60}")
    print(f"✅ DAILY REPORT COMPLETED SUCCESSFULLY")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
