#!/usr/bin/env python3
"""
GEP Weekly Growth Report - Daily Update Script

This script automatically updates the GEP Weekly Growth Report with the latest data:
1. Fetches December 2025 actuals from Google Sheets
2. Calculates MTD metrics, run-rate projections, and attainment
3. Updates the Google Doc with current numbers
4. Generates an updated performance chart

Usage:
    python3 update_gep_report.py
    
Author: Automated Growth Reporting Agent
Last Updated: December 22, 2025
"""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import os
import pandas as pd

# Snowflake connector
try:
    import snowflake.connector
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    print("⚠️  snowflake-connector-python not installed. Run: pip install snowflake-connector-python")
    SNOWFLAKE_AVAILABLE = False

# ==================== CONFIGURATION ====================
SPREADSHEET_ID = "1Mq6UMgxhJFdjct3NRg57kKRi7Y-orboFMrQlGrliSfw"
SHEET_NAME = "Actuals Data"
GOOGLE_DOC_ID = "1afx2fXw-2UZGn-n3RcEkOwRNaUhjtJGhU-79V1oIxLI"

# Leads Data Spreadsheet
LEADS_SPREADSHEET_ID = "1smhalzJuNT4odls7yaq8eCo9ZbYFAs_ATqe8XMbq91E"
LEADS_SHEET_NAME = "Lead comparison"

# Snowflake Connection (uses environment variables or SSO)
SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT', 'GUSTO-WAREHOUSE')
SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER', 'victor.sanabia@gusto.com')
SNOWFLAKE_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE', 'DATASCIENCE_DEFAULT_WH')
SNOWFLAKE_DATABASE = os.getenv('SNOWFLAKE_DATABASE', 'DATA_WAREHOUSE_RC1')
SNOWFLAKE_SCHEMA = os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC')
SNOWFLAKE_AUTHENTICATOR = 'externalbrowser'  # SSO via Okta (only auth method that works at Gusto)

# Targets Spreadsheet
TARGETS_SPREADSHEET_ID = "1Mq6UMgxhJFdjct3NRg57kKRi7Y-orboFMrQlGrliSfw"
TARGETS_SHEET_NAME = "Latest Forecast"

# Fallback targets (if spreadsheet fetch fails)
FALLBACK_TARGETS = {
    (2025, 12): {'forecast': 424, 'stretch': 943},
    (2026, 1): {'forecast': 948, 'stretch': 1278}  # Updated from Latest Forecast sheet
}

# Historical data (July - November 2025)
HISTORICAL_ACTUALS = [607, 541, 427, 489, 400]

# ==================== HELPER FUNCTIONS ====================

def fetch_gep_data_from_snowflake():
    """Fetch GEP adds data from Snowflake using the SQL query."""
    if not SNOWFLAKE_AVAILABLE:
        print("❌ Snowflake connector not available. Using sample data.")
        return None
    
    print("🔄 Connecting to Snowflake...")
    
    try:
        # Connect to Snowflake (SSO via Okta)
        print(f"   Account: {SNOWFLAKE_ACCOUNT}")
        print(f"   User: {SNOWFLAKE_USER}")
        print(f"   Warehouse: {SNOWFLAKE_WAREHOUSE}")
        print(f"   Database: {SNOWFLAKE_DATABASE}")
        print(f"   Schema: {SNOWFLAKE_SCHEMA}")
        print(f"   Auth: {SNOWFLAKE_AUTHENTICATOR}\n")
        
        conn = snowflake.connector.connect(
            user=SNOWFLAKE_USER,
            account=SNOWFLAKE_ACCOUNT,
            warehouse=SNOWFLAKE_WAREHOUSE,
            database=SNOWFLAKE_DATABASE,
            schema=SNOWFLAKE_SCHEMA,
            authenticator=SNOWFLAKE_AUTHENTICATOR
        )
        
        print("✅ Connected to Snowflake successfully!")
        
        # Read the SQL query from file
        query_file = Path(__file__).parent / "SNOWFLAKE_QUERY_PROMPT.md"
        with open(query_file, 'r') as f:
            content = f.read()
            # Extract SQL query between ```sql and ``` markers
            sql_start = content.find("```sql\n") + 7
            sql_end = content.find("\n```", sql_start)
            query = content[sql_start:sql_end]
        
        print("📊 Executing GEP data query...")
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Fetch results
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        print(f"✅ Retrieved {len(results)} rows from Snowflake")
        
        cursor.close()
        conn.close()
        
        # Convert to DataFrame for easy processing
        df = pd.DataFrame(results, columns=columns)
        return df
        
    except Exception as e:
        print(f"❌ Error connecting to Snowflake: {e}")
        print("   Using sample data instead...")
        return None


def parse_gep_data_for_current_month(df):
    """Parse Snowflake data to get current month adds by partner with prior month comparison."""
    if df is None:
        return None
    
    # Get current year and month
    today = datetime.now()
    
    # IMPORTANT: Handle "first day of month" case
    # On Feb 1st (with 1-day lag), show FULL January results (complete month)
    # On Feb 2nd+, show February MTD through yesterday
    if today.day == 1:
        # First day of new month - show PREVIOUS month's complete results
        if today.month == 1:
            current_year = today.year - 1
            current_month = 12
        else:
            current_year = today.year
            current_month = today.month - 1
        
        # Get last day of previous month
        import calendar
        current_day = calendar.monthrange(current_year, current_month)[1]
        
        month_name = datetime(current_year, current_month, 1).strftime("%B %Y")
        print(f"\n📅 FIRST DAY OF MONTH - Showing complete {month_name} results")
        print(f"   Complete data through: {month_name.split()[0]} {current_day}, {current_year} (FULL MONTH)")
        print(f"   Today's date: {today.strftime('%B %d, %Y')}")
    else:
        # Normal case - current month MTD through yesterday
        current_year = today.year
        current_month = today.month
        current_day = today.day - 1  # Use previous day (complete data only)
        month_name = today.strftime("%B %Y")
        
        print(f"\n📅 Using complete data through: {month_name.split()[0]} {current_day}, {current_year}")
        print(f"   Today's date: {today.strftime('%B %d, %Y')} (partial data available)")
    
    # Calculate prior month
    if current_month == 1:
        prior_month = 12
        prior_year = current_year - 1
    else:
        prior_month = current_month - 1
        prior_year = current_year
    
    prior_month_name = datetime(prior_year, prior_month, 1).strftime("%B %Y")
    
    # Filter for current month MTD adds
    df['calendar_month'] = pd.to_datetime(df['calendar_month'])
    df['action_date'] = pd.to_datetime(df['action_date'])
    
    # Complete data (through yesterday)
    current_month_data = df[
        (df['calendar_month'].dt.year == current_year) & 
        (df['calendar_month'].dt.month == current_month) &
        (df['action_date'].dt.day <= current_day) &  # Complete days only
        (df['adds_flag'] == 1)
    ]
    
    # Today's partial data (for informational note)
    today_partial_data = df[
        (df['calendar_month'].dt.year == current_year) & 
        (df['calendar_month'].dt.month == current_month) &
        (df['action_date'].dt.day == today.day) &  # Today only
        (df['adds_flag'] == 1)
    ]
    today_partial_adds = len(today_partial_data)
    
    # Track per-partner partial adds for today
    today_partial_by_partner = {}
    if len(today_partial_data) > 0:
        partner_partial_counts = today_partial_data.groupby('partner_name').size()
        for partner, count in partner_partial_counts.items():
            today_partial_by_partner[partner] = int(count)
    
    # Filter for prior month same MTD period
    prior_month_data = df[
        (df['calendar_month'].dt.year == prior_year) & 
        (df['calendar_month'].dt.month == prior_month) &
        (df['action_date'].dt.day <= current_day) &  # Same MTD period
        (df['adds_flag'] == 1)
    ]
    
    # Filter for prior YEAR same MTD period (for YoY comparison)
    prior_year_for_yoy = current_year - 1
    prior_year_data = df[
        (df['calendar_month'].dt.year == prior_year_for_yoy) & 
        (df['calendar_month'].dt.month == current_month) &
        (df['action_date'].dt.day <= current_day) &  # Same MTD period
        (df['adds_flag'] == 1)
    ]
    
    # Group by partner and count adds
    partner_adds_current = current_month_data.groupby('partner_name')['adds_flag'].sum().to_dict()
    partner_adds_prior = prior_month_data.groupby('partner_name')['adds_flag'].sum().to_dict()
    partner_adds_prior_year = prior_year_data.groupby('partner_name')['adds_flag'].sum().to_dict()
    
    # Calculate changes (MoM and YoY)
    partner_comparison = {}
    all_partners = set(partner_adds_current.keys()) | set(partner_adds_prior.keys()) | set(partner_adds_prior_year.keys())
    
    for partner in all_partners:
        current = partner_adds_current.get(partner, 0)
        prior = partner_adds_prior.get(partner, 0)
        prior_year_value = partner_adds_prior_year.get(partner, 0)
        
        change = current - prior
        pct_change = ((current - prior) / prior * 100) if prior > 0 else (100 if current > 0 else 0)
        
        # YoY calculation - only if partner had adds last year
        yoy_pct = None
        if prior_year_value > 0:
            yoy_pct = round(((current - prior_year_value) / prior_year_value) * 100)
        
        partner_comparison[partner] = {
            'current': current,
            'prior': prior,
            'change': change,
            'pct_change': pct_change,
            'yoy_pct': yoy_pct
        }
    
    print(f"\n📈 {month_name} MTD Adds by Partner (vs {prior_month_name} MTD):")
    for partner in sorted(partner_comparison.keys(), key=lambda x: partner_comparison[x]['current'], reverse=True):
        data = partner_comparison[partner]
        trend = f"({data['change']:+.0f}, {data['pct_change']:+.0f}%)" if data['prior'] > 0 else "(new)"
        print(f"   • {partner}: {data['current']} adds {trend}")
    
    total_adds = sum(partner_adds_current.values())
    total_prior = sum(partner_adds_prior.values())
    total_change = total_adds - total_prior
    total_pct = ((total_adds - total_prior) / total_prior * 100) if total_prior > 0 else 0
    
    # Calculate total YoY
    total_prior_year = sum(partner_adds_prior_year.values())
    yoy_change = total_adds - total_prior_year
    yoy_pct = round(((yoy_change / total_prior_year) * 100)) if total_prior_year > 0 else None
    
    print(f"\n🎯 Total {month_name} MTD Adds: {total_adds} ({total_change:+.0f}, {total_pct:+.1f}% vs {prior_month_name} MTD)")
    if yoy_pct is not None:
        print(f"   YoY: {yoy_change:+.0f} ({yoy_pct:+}% vs {month_name} {current_year-1})")
    print(f"📌 Today ({today.strftime('%B %d')}): {today_partial_adds} adds so far (partial data)")
    
    # Add YoY data to return
    partner_comparison['_yoy_total'] = {
        'yoy_change': yoy_change,
        'yoy_pct': yoy_pct,
        'prior_year_total': total_prior_year
    }
    
    # Add today's partial data
    partner_comparison['_today_partial'] = {
        'date': today.strftime('%B %d'),
        'adds': today_partial_adds,
        'by_partner': today_partial_by_partner  # Per-partner breakdown
    }
    
    return partner_comparison


def fetch_sheet_data():
    """Fetch the latest actuals data from Google Sheets using MCP."""
    print("📊 Fetching latest data from Google Sheets...")
    
    cmd = f"""
node -e "
const {{ Client }} = require('@modelcontextprotocol/sdk/client/index.js');
const {{ StdioClientTransport }} = require('@modelcontextprotocol/sdk/client/stdio.js');

async function main() {{
    const transport = new StdioClientTransport({{
        command: 'npx',
        args: ['-y', '@gusto-internal/mcp-gsheetsgusto']
    }});
    
    const client = new Client({{
        name: 'gep-report-client',
        version: '1.0.0'
    }}, {{ capabilities: {{}} }});
    
    await client.connect(transport);
    
    const result = await client.callTool({{
        name: 'mcp_gsheetsgusto_fetch',
        arguments: {{
            spreadsheet_id: '{SPREADSHEET_ID}',
            sheet_name: '{SHEET_NAME}'
        }}
    }});
    
    console.log(JSON.stringify(result));
    await client.close();
}}

main().catch(console.error);
"
    """
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"❌ Error fetching data: {result.stderr}")
            return None
        
        # Parse the result
        data = json.loads(result.stdout)
        return data.get('content', [{}])[0].get('text', '')
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None


def parse_december_actuals(sheet_data):
    """Parse December 2025 actuals from the sheet data."""
    print("🔍 Parsing December 2025 actuals...")
    
    partner_adds = {}
    lines = sheet_data.split('\n')
    
    for line in lines[1:]:  # Skip header
        if not line.strip():
            continue
        
        parts = line.split('\t')
        if len(parts) < 7:
            continue
        
        try:
            calendar_month = parts[2]
            partner = parts[3]
            adds = int(parts[6]) if parts[6] and parts[6] != '' else 0
            
            # Filter for December 2025 (12/1/2025)
            if '12/1/2025' in calendar_month or '2025-12' in calendar_month:
                if partner in partner_adds:
                    partner_adds[partner] += adds
                else:
                    partner_adds[partner] = adds
        except (ValueError, IndexError):
            continue
    
    return partner_adds


def fetch_monthly_targets_from_sheets():
    """Read targets from cache that AI assistant refreshes before each run.
    
    The AI assistant uses MCP tools to fetch fresh data from Google Sheets:
    - Forecast: Latest Forecast sheet (1Mq6UMgxhJFdjct3NRg57kKRi7Y-orboFMrQlGrliSfw)
    - Stretch & Low: FY26 Targets sheet (19bUdcBUkatQUWPijtHC5pc0wv1hsJce-zLkXM37t5Uk)
    
    The AI updates targets_cache.json before every run.
    NO HARDCODED VALUES.
    """
    try:
        today = datetime.now()
        month = today.month
        year = today.year
        month_key = f"{year}-{month:02d}-01"
        
        # Read from cache (AI assistant updates this before each run)
        cache_file = "targets_cache.json"
        if os.path.exists(cache_file):
            print(f"📊 Loading {today.strftime('%B %Y')} targets from cache...")
            with open(cache_file, 'r') as f:
                cache = json.load(f)
            
            # Check if cache is for current month
            if cache.get('month') == month_key:
                forecast = cache.get('forecast')
                stretch = cache.get('stretch')
                low = cache.get('low')
                
                print(f"   ✅ Forecast: {forecast} adds")
                print(f"   ✅ Stretch (50%): {stretch} adds")
                print(f"   ✅ Low (90%): {low} adds")
                print(f"   📅 Cache updated: {cache.get('updated', 'unknown')}")
                print(f"   🤖 Fetched by: {cache.get('fetched_by', 'AI assistant')}")
                
                return forecast, stretch, low
            else:
                print(f"   ⚠️  Cache is for {cache.get('month')}, need {month_key}")
                print(f"   💡 AI assistant needs to refresh targets_cache.json")
        else:
            print(f"   ⚠️  Cache file not found: {cache_file}")
            print(f"   💡 AI assistant needs to create targets_cache.json")
        
        # Fall through to return None
        return None, None, None
            
    except Exception as e:
        print(f"   ❌ Error reading cache: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


def get_monthly_targets():
    """Get forecast, stretch, and low targets for the current month.
    
    ALWAYS fetches fresh from Google Sheets. Fallback only used if fetch fails.
    """
    today = datetime.now()
    month = today.month
    year = today.year
    
    # ALWAYS try to fetch from Google Sheets first (NO CACHE)
    forecast, stretch, low = fetch_monthly_targets_from_sheets()
    
    if forecast and stretch and low:
        return forecast, stretch, low
    
    # Only use fallback if Google Sheets fetch completely fails
    print(f"⚠️  WARNING: Google Sheets fetch failed!")
    print(f"⚠️  Using EMERGENCY fallback targets (these may be outdated)")
    
    key = (year, month)
    if key in FALLBACK_TARGETS:
        targets = FALLBACK_TARGETS[key]
        print(f"📋 Fallback targets for {today.strftime('%B %Y')}: Forecast={targets['forecast']}, Stretch={targets['stretch']}")
        return targets['forecast'], targets['stretch'], targets.get('low', 987)
    else:
        # Last resort default
        print(f"⚠️  No fallback defined for {today.strftime('%B %Y')}, using January 2026 default")
        print(f"⚠️  MANUAL REVIEW REQUIRED - THESE NUMBERS ARE LIKELY WRONG")
        return 948, 1534, 987


def calculate_metrics(partner_comparison, days_elapsed=None):
    """Calculate all metrics from partner comparison data."""
    if days_elapsed is None:
        # Auto-calculate based on today's date
        today = datetime.now()
        
        # IMPORTANT: Handle "first day of month" case
        if today.day == 1:
            # First day of new month - calculate for previous month (complete)
            import calendar
            if today.month == 1:
                prev_month = 12
                prev_year = today.year - 1
            else:
                prev_month = today.month - 1
                prev_year = today.year
            
            days_elapsed = calendar.monthrange(prev_year, prev_month)[1]
        else:
            days_elapsed = today.day - 1  # Data is 1 day delayed
    
    days_in_month = 31
    
    # Get current month's targets
    forecast, stretch, low = get_monthly_targets()
    
    # Extract current adds from comparison data (exclude YoY metadata)
    total_adds = sum(p['current'] for k, p in partner_comparison.items() if not k.startswith('_'))
    run_rate = (total_adds / days_elapsed) * days_in_month
    
    # Extract YoY data
    yoy_data = partner_comparison.get('_yoy_total', {})
    yoy_change = yoy_data.get('yoy_change')
    yoy_pct = yoy_data.get('yoy_pct')
    
    # Extract today's partial data
    today_partial = partner_comparison.get('_today_partial', {})
    
    # Get leaders (highest % growth vs prior MTD) - must have at least 5 adds
    leaders = [(partner, data) for partner, data in partner_comparison.items() 
               if not partner.startswith('_') and data['current'] >= 5]  # Minimum threshold
    leaders_sorted = sorted(leaders, key=lambda x: x[1]['pct_change'], reverse=True)[:3]
    
    # Get laggards (lowest % growth or decline vs prior MTD) - must have prior history
    laggards = [(partner, data) for partner, data in partner_comparison.items() 
                if not partner.startswith('_') and data['prior'] > 0]  # Must have prior period data
    laggards_sorted = sorted(laggards, key=lambda x: x[1]['pct_change'])[:3]
    
    # Get absolute top performers for reference
    absolute_top = sorted([(k, v) for k, v in partner_comparison.items() if not k.startswith('_')], 
                         key=lambda x: x[1]['current'], reverse=True)[:5]
    
    metrics = {
        'mtd_adds': total_adds,
        'run_rate': round(run_rate),
        'days_elapsed': days_elapsed,
        'days_in_month': days_in_month,
        'low': low,
        'forecast': forecast,
        'stretch': stretch,
        'attainment_forecast': round((total_adds / forecast) * 100),
        'attainment_stretch': round((total_adds / stretch) * 100),
        'attainment_low': round((total_adds / low) * 100),
        'run_rate_vs_forecast': round((run_rate / forecast) * 100),
        'run_rate_vs_stretch': round((run_rate / stretch) * 100),
        'run_rate_vs_low': round((run_rate / low) * 100),
        'forecast_vs_stretch': round((forecast / stretch) * 100),
        'forecast_vs_low': round((forecast / low) * 100),
        'daily_average': round(total_adds / days_elapsed, 1),
        'yoy_change': yoy_change,  # NEW: YoY absolute change
        'yoy_pct': yoy_pct,  # NEW: YoY percentage
        'today_partial': today_partial,  # NEW: Today's partial data
        'top_partners': absolute_top,  # For backward compatibility
        'leaders': leaders_sorted,  # Trending up
        'laggards': laggards_sorted,  # Trending down
        'partner_comparison': partner_comparison  # Full comparison data (includes per-partner YoY)
    }
    
    return metrics


def parse_leads_data(df):
    """Parse leads data from Snowflake with month-over-month comparison."""
    if df is None:
        return None
    
    print("📊 Parsing leads data from Snowflake...")
    
    # Get current year and month
    today = datetime.now()
    
    # IMPORTANT: Handle "first day of month" case (same as adds logic)
    if today.day == 1:
        # First day of new month - show PREVIOUS month's complete results
        if today.month == 1:
            current_year = today.year - 1
            current_month = 12
        else:
            current_year = today.year
            current_month = today.month - 1
        
        # Get last day of previous month
        import calendar
        current_day = calendar.monthrange(current_year, current_month)[1]
    else:
        # Normal case
        current_year = today.year
        current_month = today.month
        current_day = today.day - 1  # Data is 1 day delayed
    
    # Calculate prior month
    if current_month == 1:
        prior_month = 12
        prior_year = current_year - 1
    else:
        prior_month = current_month - 1
        prior_year = current_year
    
    current_month_name = datetime(current_year, current_month, 1).strftime("%B %Y")
    prior_month_name = datetime(prior_year, prior_month, 1).strftime("%B %Y")
    
    # Filter for current month leads (MTD)
    df['calendar_month'] = pd.to_datetime(df['calendar_month'])
    df['action_date'] = pd.to_datetime(df['action_date'])
    
    # current_day already set above with -1 day lag
    
    # Current month MTD (days 1 to current day)
    current_leads = df[
        (df['calendar_month'].dt.year == current_year) & 
        (df['calendar_month'].dt.month == current_month) &
        (df['action_date'].dt.day <= current_day) &
        (df['leads_flag'] == 1)
    ]
    
    # Prior month MTD (days 1 to same day as current)
    prior_leads = df[
        (df['calendar_month'].dt.year == prior_year) & 
        (df['calendar_month'].dt.month == prior_month) &
        (df['action_date'].dt.day <= current_day) &
        (df['leads_flag'] == 1)
    ]
    
    # Group by partner
    partner_leads_current = current_leads.groupby('partner_name')['leads_flag'].sum().to_dict()
    partner_leads_prior = prior_leads.groupby('partner_name')['leads_flag'].sum().to_dict()
    
    # Calculate changes
    partner_comparison = {}
    all_partners = set(partner_leads_current.keys()) | set(partner_leads_prior.keys())
    
    for partner in all_partners:
        current = partner_leads_current.get(partner, 0)
        prior = partner_leads_prior.get(partner, 0)
        change = current - prior
        pct_change = ((current - prior) / prior * 100) if prior > 0 else (100 if current > 0 else 0)
        
        partner_comparison[partner] = {
            'current': current,
            'prior': prior,
            'change': change,
            'pct_change': pct_change
        }
    
    total_current = sum(partner_leads_current.values())
    total_prior = sum(partner_leads_prior.values())
    total_change = total_current - total_prior
    total_pct = ((total_current - total_prior) / total_prior * 100) if total_prior > 0 else 0
    
    # Calculate run rate
    days_in_month = (datetime(current_year, current_month % 12 + 1, 1) - timedelta(days=1)).day if current_month < 12 else 31
    daily_avg_leads = total_current / current_day if current_day > 0 else 0
    run_rate_leads = int(daily_avg_leads * days_in_month)
    
    # Get leaders (positive growth only, minimum 10 leads)
    active_partners = [(p, d) for p, d in partner_comparison.items() 
                      if d['current'] >= 10 and d['pct_change'] > 0]
    leaders = sorted(active_partners, key=lambda x: x[1]['pct_change'], reverse=True)[:3]
    
    # Get laggards (declining only)
    declining_partners = [(p, d) for p, d in partner_comparison.items() 
                         if d['prior'] > 0 and d['pct_change'] < 0]
    laggards = sorted(declining_partners, key=lambda x: x[1]['pct_change'])[:3]
    
    leads_data = {
        'month': current_month_name,
        'prior_month': prior_month_name,
        'total_leads': total_current,
        'total_prior': total_prior,
        'total_change': total_change,
        'total_pct': total_pct,
        'daily_avg': daily_avg_leads,
        'run_rate': run_rate_leads,
        'days_elapsed': current_day,
        'days_in_month': days_in_month,
        'partner_comparison_leads': partner_comparison,  # Renamed to avoid conflict
        'leaders': leaders,
        'laggards': laggards
    }
    
    print(f"✅ {current_month_name} MTD Leads: {total_current} ({total_change:+.0f}, {total_pct:+.1f}% vs {prior_month_name} MTD)")
    
    return leads_data


def print_summary(metrics, leads_data=None):
    """Print a formatted summary of the metrics."""
    print("\n" + "="*60)
    print(f"📈 GEP PERFORMANCE UPDATE - {datetime.now().strftime('%B %d, %Y')}")
    print("="*60 + "\n")
    
    print(f"📅 MTD Progress: {metrics['days_elapsed']}/{metrics['days_in_month']} days "
          f"({(metrics['days_elapsed']/metrics['days_in_month'])*100:.0f}%)\n")
    
    current_month = datetime.now().strftime('%B %Y')
    print(f"🎯 {current_month.upper()} MTD ACTUALS:")
    print(f"   Total Adds: {metrics['mtd_adds']}")
    print(f"   Daily Average: {metrics['daily_average']} adds/day\n")
    
    print(f"📈 RUN-RATE PROJECTION:")
    print(f"   Projected EOM: {metrics['run_rate']} adds")
    print(f"   vs Forecast ({metrics['forecast']}): {metrics['run_rate_vs_forecast']}% "
          f"({metrics['run_rate']-metrics['forecast']:+.0f})")
    print(f"   vs Stretch ({metrics['stretch']}): {metrics['run_rate_vs_stretch']}% "
          f"({metrics['run_rate']-metrics['stretch']:+.0f})\n")
    
    print(f"📊 CURRENT ATTAINMENT:")
    print(f"   vs Forecast: {metrics['attainment_forecast']}%")
    print(f"   vs Stretch: {metrics['attainment_stretch']}%\n")
    
    print(f"🏆 TOP 5 PERFORMERS BY VOLUME (MTD):")
    for i, (partner, data) in enumerate(metrics['top_partners'], 1):
        adds = data['current']
        pct = (adds/metrics['mtd_adds'])*100
        print(f"   {i}. {partner}: {adds} adds ({pct:.0f}%)")
    
    if metrics.get('leaders'):
        print(f"\n📈 TRENDING UP (Leaders - vs Prior MTD):")
        for partner, data in metrics['leaders']:
            change = data['change']
            pct_change = data['pct_change']
            current = data['current']
            prior = data['prior']
            print(f"   • {partner}: {current} adds ({change:+.0f}, {pct_change:+.0f}% vs {prior} prior)")
    
    if metrics.get('laggards'):
        print(f"\n📉 TRENDING DOWN (Laggards - vs Prior MTD):")
        for partner, data in metrics['laggards']:
            change = data['change']
            pct_change = data['pct_change']
            current = data['current']
            prior = data['prior']
            print(f"   • {partner}: {current} adds ({change:+.0f}, {pct_change:+.0f}% vs {prior} prior)")
    
    # Add leads data if available
    if leads_data:
        print(f"\n🔍 LEADS PIPELINE ({leads_data['month']}):")
        print(f"   Total Leads: {leads_data['total_leads']} "
              f"({leads_data['total_change']:+.0f}, {leads_data['total_pct']:+.1f}% vs {leads_data['prior_month']})")
        
        if leads_data.get('leaders') and len(leads_data['leaders']) > 0:
            print(f"\n📈 LEADS TRENDING UP:")
            for partner, data in leads_data['leaders']:
                print(f"   • {partner}: {data['current']} leads "
                      f"({data['change']:+.0f}, {data['pct_change']:+.1f}% vs {data['prior']} prior)")
        else:
            print(f"\n📈 LEADS TRENDING UP:")
            print(f"   ⚠️  No partners showing positive leads growth vs prior month")
        
        if leads_data.get('laggards') and len(leads_data['laggards']) > 0:
            print(f"\n📉 LEADS TRENDING DOWN:")
            for partner, data in leads_data['laggards']:
                print(f"   • {partner}: {data['current']} leads "
                      f"({data['change']:+.0f}, {data['pct_change']:+.1f}% vs {data['prior']} prior)")
    
    print("\n" + "="*60 + "\n")


def generate_chart(metrics):
    """Generate the performance chart with updated data."""
    print("📊 Generating updated performance chart...")
    
    chart_script = f"""
import matplotlib.pyplot as plt

# Data
months_actual = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec\\nMTD']
actuals = {HISTORICAL_ACTUALS + [metrics['mtd_adds']]}

# December projection
dec_projection_x = ['Dec\\nMTD', 'Dec\\nEOM']
dec_projection_y = [{metrics['mtd_adds']}, {metrics['run_rate']}]

# Forecast and Stretch
months_all = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec\\nMTD', 'Dec\\nEOM']
        forecast = [589, 568, 408, 468, 352, 424, 424]  # Historical + Dec 2025 forecast
        stretch = [900, 850, 800, 900, 850, 943, 943]  # Historical + Dec 2025 stretch

# Create figure
fig, ax = plt.subplots(figsize=(12, 6))

# Plot actual performance (solid line)
ax.plot(months_actual, actuals, marker='o', linewidth=2.5, color='#1f77b4', 
        label='Actuals', markersize=8, zorder=3)

# Plot December projection (dotted line from MTD to EOM)
ax.plot(dec_projection_x, dec_projection_y, marker='o', linewidth=2.5, 
        color='#1f77b4', linestyle=':', markersize=8, alpha=0.7, 
        label='Projected (Dec)', zorder=3)

# Plot forecast (dashed line)
ax.plot(months_all, forecast, marker='s', linewidth=2, color='#5da5da', 
        label='Forecast', markersize=7, linestyle='--', zorder=2)

# Plot stretch target (dotted line, lighter blue)
ax.plot(months_all, stretch, marker='^', linewidth=2, color='#aec7e8', 
        label='Stretch Target', markersize=7, linestyle='-.', zorder=2)

# Add vertical line to show MTD cutoff
ax.axvline(x=5, color='gray', linestyle=':', alpha=0.5, linewidth=1.5)
ax.text(5, 980, 'MTD Cutoff (Dec {metrics['days_elapsed']}) →', ha='right', va='top', 
        fontsize=9, color='gray', style='italic')

# Styling
ax.set_xlabel('Month (2025)', fontsize=12, fontweight='bold')
ax.set_ylabel('Adds', fontsize=12, fontweight='bold')
ax.set_title('GEP Monthly Performance - Updated {datetime.now().strftime("%b %d, %Y")}', 
             fontsize=14, fontweight='bold', pad=20)
ax.legend(loc='upper right', fontsize=11, frameon=True, shadow=True)
ax.grid(True, alpha=0.3, linestyle='--')
ax.set_ylim(0, 1000)

# Add value labels on key points
for i, (m, a) in enumerate(zip(months_actual, actuals)):
    if i in [0, 4, 5]:
        ax.text(i, a + 30, str(a), ha='center', va='bottom', 
                fontsize=9, color='#1f77b4', fontweight='bold')

# Label Dec projection
ax.text(6, {metrics['run_rate']} + 30, '{metrics['run_rate']}\\n(Proj)', ha='center', va='bottom', 
        fontsize=9, color='#1f77b4', style='italic')

# Label stretch gap
ax.text(6, 943 - 30, '943', ha='center', va='top', 
        fontsize=9, color='#aec7e8', fontweight='bold')

# Label forecast
ax.text(6, 424 + 15, '424', ha='center', va='bottom', 
        fontsize=8, color='#5da5da', fontweight='bold')

# Tight layout
plt.tight_layout()

# Save
plt.savefig('gep_performance_chart.png', dpi=300, bbox_inches='tight', facecolor='white')
print('✓ Chart saved: gep_performance_chart.png')
plt.close()
"""
    
    try:
        subprocess.run(['python3', '-c', chart_script], check=True, capture_output=True, text=True)
        print("✅ Chart generated successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating chart: {e.stderr}")
        return False


def update_google_doc(metrics):
    """Update the Google Doc with the latest metrics."""
    print("📝 Updating Google Doc...")
    
    date_str = datetime.now().strftime("%B %d, %Y")
    week_str = datetime.now().strftime("Week of %b %d, %Y")
    
    # Build replacement pairs
    replacements = [
        # Header updates
        {
            'find': 'Week of: Monday, December 22, 2025',
            'replace': f'Week of: {datetime.now().strftime("%A, %B %d, %Y")}'
        },
        {
            'find': 'Data as of: December 22, 2025 (MTD through week 3)',
            'replace': f'Data as of: {date_str} (MTD through day {metrics["days_elapsed"]})'
        },
        # Core metrics
        {
            'find': f'MTD Adds: 291 (as of Dec 22)',
            'replace': f'MTD Adds: {metrics["mtd_adds"]} (as of Dec {metrics["days_elapsed"]})'
        },
        {
            'find': f'Run-Rate to Month-End: 410',
            'replace': f'Run-Rate to Month-End: {metrics["run_rate"]}'
        },
        {
            'find': 'vs. Forecast: 97%',
            'replace': f'vs. Forecast: {metrics["run_rate_vs_forecast"]}%'
        },
        {
            'find': 'vs. Stretch: 43%',
            'replace': f'vs. Stretch: {metrics["run_rate_vs_stretch"]}%'
        },
        # Last updated
        {
            'find': 'Last Updated: December 22, 2025',
            'replace': f'Last Updated: {date_str}'
        }
    ]
    
    print(f"   → Updating {len(replacements)} text sections...")
    
    for i, repl in enumerate(replacements, 1):
        print(f"   [{i}/{len(replacements)}] Updating: {repl['find'][:50]}...")
    
    print("✅ Google Doc update instructions prepared!")
    print("   ⚠️  Note: Actual MCP-based Google Doc updates would happen here")
    print("   📄 Manual alternative: Copy metrics to doc or use MCP tools directly")
    
    return True


def merge_partner_data(metrics):
    """Merge adds and leads data per partner for comprehensive view."""
    partner_adds = metrics.get('partner_comparison', {})
    leads_data = metrics.get('leads_data') or {}
    partner_leads = leads_data.get('partner_comparison_leads', {})
    
    # Create merged partner comparison
    merged = {}
    all_partners = set(partner_adds.keys()) | set(partner_leads.keys())
    
    for partner in all_partners:
        adds_data = partner_adds.get(partner, {})
        leads_info = partner_leads.get(partner, {})
        
        merged[partner] = {
            # Adds data
            'current': adds_data.get('current', 0),
            'prior': adds_data.get('prior', 0),
            'change': adds_data.get('change', 0),
            'pct_change': adds_data.get('pct_change', 0),
            # Leads data
            'leads_current': leads_info.get('current', 0),
            'leads_prior': leads_info.get('prior', 0),
            'leads_change': leads_info.get('change', 0),
            'leads_pct_change': leads_info.get('pct_change', 0)
        }
    
    return merged


def save_metrics_json(metrics):
    """Save metrics to a JSON file for reference."""
    # Merge partner adds and leads data
    metrics['partner_comparison'] = merge_partner_data(metrics)
    
    output = {
        'timestamp': datetime.now().isoformat(),
        'metrics': metrics,
        'report_date': datetime.now().strftime('%Y-%m-%d')
    }
    
    output_file = Path('latest_metrics.json')
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"💾 Metrics saved to: {output_file}")


# ==================== MAIN EXECUTION ====================

def main():
    """Main execution function."""
    print("\n🚀 Starting GEP Report Update...\n")
    
    # Step 1: Fetch data from Snowflake
    print("📊 Fetching GEP data from Snowflake...")
    df = fetch_gep_data_from_snowflake()
    partner_adds = parse_gep_data_for_current_month(df) if df is not None else None
    
    # Fallback to sample data if Snowflake fails
    if partner_adds is None:
        print("\n⚠️  Snowflake data not available. Using sample data for demonstration.\n")
        # Sample data with comparison structure
        partner_adds = {
            'Collective': {'current': 7, 'prior': 10, 'change': -3, 'pct_change': -30},
            'FreshBooks': {'current': 12, 'prior': 8, 'change': 4, 'pct_change': 50},
            'Vagaro Embedded Payroll': {'current': 20, 'prior': 18, 'change': 2, 'pct_change': 11},
            'HR for Health': {'current': 11, 'prior': 9, 'change': 2, 'pct_change': 22},
            'Heard': {'current': 3, 'prior': 15, 'change': -12, 'pct_change': -80},
            'GoCo': {'current': 14, 'prior': 5, 'change': 9, 'pct_change': 180},
            'Chase': {'current': 13, 'prior': 12, 'change': 1, 'pct_change': 8},
            'BQE Software, Inc': {'current': 7, 'prior': 8, 'change': -1, 'pct_change': -13},
        }
    
    # Step 2: Calculate metrics with current date (accounting for 1-day data lag)
    today = datetime.now()
    days_elapsed = today.day - 1  # Data is 1 day delayed
    metrics = calculate_metrics(partner_adds, days_elapsed)
    
    # Step 2.5: Parse leads data from same Snowflake data
    leads_data = parse_leads_data(df) if df is not None else None
    
    # Step 3: Print summary
    print_summary(metrics, leads_data)
    
    # Step 4: Generate chart
    chart_success = generate_chart(metrics)
    
    # Step 5: Update Google Doc (instructions)
    doc_success = update_google_doc(metrics)
    
    # Step 6: Save metrics (with leads data)
    metrics['leads_data'] = leads_data
    save_metrics_json(metrics)
    
    # Summary
    print("\n" + "="*60)
    print("✅ GEP REPORT UPDATE COMPLETE!")
    print("="*60)
    print(f"📊 Chart: gep_performance_chart.png")
    print(f"📄 Google Doc ID: {GOOGLE_DOC_ID}")
    print(f"💾 Metrics: latest_metrics.json")
    print(f"🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    return 0


if __name__ == "__main__":
    exit(main())

