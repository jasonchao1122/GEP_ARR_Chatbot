#!/usr/bin/env python3
"""
Simple auto-refresh for monthly targets
Uses direct file reading since MCP may not work in cron
Falls back gracefully to manual refresh
"""

import json
from datetime import datetime
import sys

CACHE_FILE = "targets_cache.json"

# Targets by month
# Update this at the start of each month with values from Google Sheets:
# - Latest Forecast: https://docs.google.com/spreadsheets/d/1Mq6UMgxhJFdjct3NRg57kKRi7Y-orboFMrQlGrliSfw
# - FY26 Targets: https://docs.google.com/spreadsheets/d/19bUdcBUkatQUWPijtHC5pc0wv1hsJce-zLkXM37t5Uk
MONTHLY_TARGETS = {
    "2026-01": {"forecast": 933, "stretch": 1534, "low": 987},
    "2026-02": {"forecast": 948, "stretch": 1534, "low": 987},
    "2026-03": {"forecast": 948, "stretch": 1534, "low": 987},  # TODO: Fetch actual March targets
    "2026-04": {"forecast": 948, "stretch": 1534, "low": 987},  # TODO: Fetch actual April targets
    "2026-05": {"forecast": 948, "stretch": 1534, "low": 987},  # TODO: Fetch actual May targets
    "2026-06": {"forecast": 948, "stretch": 1534, "low": 987},  # TODO: Fetch actual June targets
}


def update_cache_for_current_month():
    """Update targets cache for the current month."""
    today = datetime.now()
    month_key = f"{today.year}-{today.month:02d}"
    month_full_key = f"{month_key}-01"
    month_name = today.strftime("%B %Y")
    
    print(f"🔄 Checking targets for {month_name}...")
    print(f"   Month key: {month_full_key}")
    
    # Check if we have targets for this month
    if month_key not in MONTHLY_TARGETS:
        print(f"⚠️  No targets defined for {month_name}")
        print(f"   Using previous month's targets as fallback")
        
        # Try previous month
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_year = today.year if today.month > 1 else today.year - 1
        prev_key = f"{prev_year}-{prev_month:02d}"
        
        if prev_key in MONTHLY_TARGETS:
            targets = MONTHLY_TARGETS[prev_key]
            print(f"   Using {prev_key} targets as fallback")
        else:
            print(f"   ERROR: No fallback available!")
            return False
    else:
        targets = MONTHLY_TARGETS[month_key]
    
    # Check current cache
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        
        # If cache is already up to date, skip
        if cache.get('month') == month_full_key:
            print(f"✅ Cache already up to date for {month_name}")
            print(f"   Forecast: {cache['forecast']}")
            print(f"   Stretch: {cache['stretch']}")
            print(f"   Low: {cache['low']}")
            return True
    except (FileNotFoundError, json.JSONDecodeError):
        cache = {}
    
    # Update cache
    cache_data = {
        "month": month_full_key,
        "forecast": targets["forecast"],
        "stretch": targets["stretch"],
        "low": targets["low"],
        "last_updated": datetime.now().isoformat(),
        "fetched_by": "Auto-refresh script (simple)",
        "source": "Monthly targets table"
    }
    
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    print(f"\n✅ Updated cache for {month_name}:")
    print(f"   Forecast: {targets['forecast']}")
    print(f"   Stretch: {targets['stretch']}")
    print(f"   Low: {targets['low']}")
    print(f"\n💾 Saved to {CACHE_FILE}")
    
    return True


if __name__ == "__main__":
    success = update_cache_for_current_month()
    if success:
        print("\n✅ Targets refresh complete!")
        sys.exit(0)
    else:
        print("\n⚠️  Targets refresh failed - using cached values")
        sys.exit(0)  # Don't fail the whole workflow
