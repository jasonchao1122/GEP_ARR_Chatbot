#!/usr/bin/env python3
"""
Send GEP Performance Update to Slack
Uses LOCKED format (no emojis, clean text, absolute numbers only)
"""

import os
import json
import time
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Initialize Slack client
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
if not SLACK_BOT_TOKEN:
    print("❌ Error: SLACK_BOT_TOKEN not set!")
    print("Run: export SLACK_BOT_TOKEN='your-slack-bot-token-here'")
    exit(1)

CHANNEL = 'emb-auto-growth-updates'  # Can use channel name or ID

def load_latest_metrics():
    """Load the latest metrics from JSON file"""
    with open('latest_metrics.json', 'r') as f:
        return json.load(f)

def format_slack_message(data):
    """Format metrics into Slack message using LOCKED format"""
    metrics = data['metrics']
    
    current_month = datetime.now().strftime('%B %Y')
    current_day = metrics['days_elapsed']
    total_days = metrics['days_in_month']
    mtd_pct = int((current_day / total_days) * 100)
    
    total_adds = metrics['mtd_adds']
    daily_avg = round(metrics['daily_average'], 1)
    run_rate = metrics['run_rate']
    forecast = metrics['forecast']
    stretch = metrics['stretch']
    
    forecast_pct = metrics['run_rate_vs_forecast']
    stretch_pct = metrics['run_rate_vs_stretch']
    forecast_gap = run_rate - forecast
    stretch_gap = run_rate - stretch
    
    forecast_attain_pct = metrics['attainment_forecast']
    stretch_attain_pct = metrics['attainment_stretch']
    
    # YoY data if available
    yoy_change = metrics.get('yoy_change', 0)
    
    # LOCKED FORMAT: Clean headers, no emojis
    message = f"*GEP Performance Update - {datetime.now().strftime('%B %d, %Y')}*\n\n"
    message += f"*MTD Progress:* {current_day} of {total_days} days ({mtd_pct}%)\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    message += f"*{current_month.upper()} MTD ACTUALS*\n"
    message += f"• Total Adds: *{total_adds}*"
    if yoy_change:
        message += f" (+{yoy_change} vs Jan 2025)"
    message += f"\n• Daily Average: *{daily_avg} adds/day*\n\n"
    
    message += "*RUN-RATE PROJECTION*\n"
    message += f"• Projected EOM: *{run_rate} adds*\n"
    message += f"• vs Forecast ({forecast:,}): *{forecast_pct}%* ({forecast_gap:+,})\n"
    message += f"• vs Stretch ({stretch:,}): *{stretch_pct}%* ({stretch_gap:+,})\n\n"
    
    message += "*CURRENT ATTAINMENT*\n"
    message += f"• vs Forecast: *{forecast_attain_pct}%*\n"
    message += f"• vs Stretch: *{stretch_attain_pct}%*\n\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Top 5 performers
    message += "*TOP 5 PERFORMERS BY VOLUME (MTD)*\n"
    top_partners = metrics.get('top_partners', [])
    partial_data = metrics.get('today_partial', {}).get('by_partner', {})
    
    for i, (partner_name, partner_data) in enumerate(top_partners[:5], 1):
        adds = partner_data.get('current', 0)
        today_adds = partial_data.get(partner_name, 0)
        today_str = f" (+{today_adds} today)" if today_adds > 0 else ""
        message += f"{i}. {partner_name}: {adds} adds{today_str}\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Trending UP - absolute numbers only, no percentages
    message += "*TRENDING UP*\n"
    message += f"_MoM comparing same MTD period (Jan 1-{current_day} vs Dec 1-{current_day})_\n"
    leaders = metrics.get('leaders', [])
    for partner_name, partner_data in leaders[:3]:
        adds = partner_data.get('current', 0)
        change = partner_data.get('change', 0)
        prior = partner_data.get('prior', 0)
        message += f"• {partner_name}: {adds} adds ({change:+d} vs {prior} prior)\n"
    
    # Trending DOWN
    message += "\n*TRENDING DOWN*\n"
    message += "_MoM comparing same MTD period_\n"
    laggards = metrics.get('laggards', [])
    if laggards:
        for partner_name, partner_data in laggards[:3]:
            adds = partner_data.get('current', 0)
            change = partner_data.get('change', 0)
            prior = partner_data.get('prior', 0)
            message += f"• {partner_name}: {adds} adds ({change:+d} vs {prior} prior)\n"
    
    # Leads section
    leads_data = metrics.get('leads_data', {})
    if leads_data:
        total_leads = leads_data.get('total_leads', 0)
        leads_change = leads_data.get('total_change', 0)
        daily_leads = round(leads_data.get('daily_avg', 0), 1)
        leads_runrate = leads_data.get('run_rate', 0)
        
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += f"*LEADS PIPELINE ({current_month})*\n"
        message += f"• Total Leads: *{total_leads}* ({leads_change:+d} vs Dec)\n"
        message += f"• Daily Average: *{daily_leads} leads/day*\n"
        message += f"• Projected EOM: *{leads_runrate} leads*\n"
        
        message += "\n*LEADS TRENDING UP*\n"
        message += "_MoM comparing same MTD period_\n"
        leads_leaders = leads_data.get('leaders', [])
        for partner_name, partner_data in leads_leaders[:3]:
            leads = partner_data.get('current', 0)
            change = partner_data.get('change', 0)
            prior = partner_data.get('prior', 0)
            message += f"• {partner_name}: {leads} leads ({change:+d} vs {prior} prior)\n"
        
        message += "\n*LEADS TRENDING DOWN*\n"
        message += "_MoM comparing same MTD period_\n"
        leads_laggards = leads_data.get('laggards', [])
        for partner_name, partner_data in leads_laggards[:3]:
            leads = partner_data.get('current', 0)
            change = partner_data.get('change', 0)
            prior = partner_data.get('prior', 0)
            message += f"• {partner_name}: {leads} leads ({change:+d} vs {prior} prior)\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Footer with notes
    message += "_Note: Partner lists show Anchor & P1 partners only. All partners included in totals._\n"
    
    # Partial data note if available
    today_partial = metrics.get('today_partial', {})
    if today_partial and today_partial.get('adds', 0) > 0:
        partial_adds = today_partial['adds']
        partial_date = today_partial.get('date', 'today')
        message += f"_{partial_date}'s partial data ({partial_adds} adds so far) not included in MTD calculations due to 1-day data lag._\n"
    
    message += "_Data: Snowflake (bi.gep_companies) | Targets: Latest Forecast sheet_\n"
    message += "_📊 Daily Tracker: <https://go/embpartnertracker|go/embpartnertracker> | APDs Set/Leads List: <https://go/embpartnertracker-leadintent|go/embpartnertracker-leadintent>_\n"
    message += f"_Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} PST_"
    
    return message

def send_to_slack(message, max_retries=3, retry_delay=10):
    """
    Send message to Slack channel with retry logic.
    Returns timestamp on success, None on failure.
    """
    if not SLACK_BOT_TOKEN:
        print("❌ SLACK_BOT_TOKEN environment variable not set!")
        print("\n📋 Message to send:\n")
        print(message)
        return None
    
    client = WebClient(token=SLACK_BOT_TOKEN)
    
    for attempt in range(max_retries):
        try:
            response = client.chat_postMessage(
                channel=CHANNEL,
                text=message,
                mrkdwn=True
            )
            timestamp = response['ts']
            print(f"✅ Message sent to {CHANNEL} successfully!")
            print(f"   Timestamp: {timestamp}")
            return timestamp
            
        except SlackApiError as e:
            error_msg = str(e.response.get('error', str(e)))
            print(f"❌ Attempt {attempt + 1}/{max_retries} failed: {error_msg}")
            
            if attempt < max_retries - 1:
                print(f"   Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"\n❌ All {max_retries} attempts failed!")
                print("\n📋 Copy and paste the message below to Slack manually:\n")
                print(message)
                return None
    
    return None

def send_partner_breakdown(timestamp, max_retries=3, retry_delay=10):
    """Send partner breakdown as thread reply"""
    if not timestamp:
        print("⚠️  No timestamp provided, skipping partner breakdown")
        return False
    
    if not SLACK_BOT_TOKEN:
        print("❌ SLACK_BOT_TOKEN not set, skipping partner breakdown")
        return False
    
    # Load metrics
    with open('latest_metrics.json', 'r') as f:
        data = json.load(f)
    
    metrics = data.get('metrics', data)
    report_date = data.get('report_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Import pod mapping
    from partner_pods import get_partner_pod, get_partner_priority, get_priority_sort_key, POD_ORDER
    
    # Format breakdown message (LOCKED format: no emojis, organized by pod)
    message = f"*PARTNER BREAKDOWN BY CATEGORY* - {report_date}\n\n"
    message += "_Format: [Priority] Partner Name: MTD adds (change vs last month) (partial today) | MTD leads (change)_\n\n"
    
    partner_comparison = metrics.get('partner_comparison', {})
    today_partial = metrics.get('today_partial', {})
    partial_by_partner = today_partial.get('by_partner', {})
    
    # Group partners by pod
    pods = {}
    for partner_name, partner_data in partner_comparison.items():
        if partner_name.startswith('_'):  # Skip internal keys
            continue
        
        # Filter out test partners
        if 'TEST' in partner_name.upper() or 'GOLDFISH' in partner_name.upper():
            continue
        
        pod = get_partner_pod(partner_name)
        priority = get_partner_priority(partner_name)
        
        if pod not in pods:
            pods[pod] = []
        
        pods[pod].append({
            'name': partner_name,
            'data': partner_data,
            'priority': priority
        })
    
    # Sort partners within each pod by priority ascending (Anchor, P1, P2)
    for pod in pods:
        pods[pod].sort(key=lambda x: get_priority_sort_key(x['priority']))
    
    # Output by pod in defined order
    for pod in POD_ORDER:
        if pod not in pods:
            continue
        
        message += f"*{pod.upper()}*\n"
        
        for partner_info in pods[pod]:
            partner_name = partner_info['name']
            partner_data = partner_info['data']
            priority = partner_info['priority']
            
            current = partner_data.get('current', 0)
            prior = partner_data.get('prior', 0)
            change = current - prior
            
            leads_current = partner_data.get('leads_current', 0)
            leads_prior = partner_data.get('leads_prior', 0)
            leads_change = leads_current - leads_prior
            
            # Check if partner has partial adds today
            partial_adds = partial_by_partner.get(partner_name, 0)
            partial_note = f" (+{partial_adds} today)" if partial_adds > 0 else ""
            
            message += f"  • [{priority}] {partner_name}: {current} adds ({change:+d}){partial_note} | {leads_current} leads ({leads_change:+d})\n"
        
        message += "\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += f"_All comparisons vs same MTD period last month_\n"
    message += f"_Data as of {report_date}_"
    
    # Send with retry
    client = WebClient(token=SLACK_BOT_TOKEN)
    
    print(f"\n📤 Sending partner breakdown as thread reply...")
    print(f"   Waiting 5 seconds before sending...")
    time.sleep(5)  # Brief delay to avoid rate limits
    
    for attempt in range(max_retries):
        try:
            response = client.chat_postMessage(
                channel=CHANNEL,
                thread_ts=timestamp,
                text=message,
                mrkdwn=True
            )
            print(f"✅ Partner breakdown sent successfully!")
            print(f"   Thread timestamp: {response['ts']}")
            return True
            
        except SlackApiError as e:
            error_msg = str(e.response.get('error', str(e)))
            print(f"❌ Attempt {attempt + 1}/{max_retries} failed: {error_msg}")
            
            if attempt < max_retries - 1:
                print(f"   Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"\n❌ All {max_retries} attempts failed!")
                print(f"\n📋 Copy and paste as thread reply to timestamp {timestamp}:\n")
                print(message)
                return False
    
    return False

def main():
    print("🚀 Loading latest metrics...")
    metrics = load_latest_metrics()
    
    print("📝 Formatting Slack message...")
    message = format_slack_message(metrics)
    
    print("📤 Sending main message to Slack...")
    timestamp = send_to_slack(message)
    
    if timestamp:
        print("\n✅ Main message sent successfully!")
        print("\n📤 Sending partner breakdown...")
        breakdown_success = send_partner_breakdown(timestamp)
        
        if breakdown_success:
            print("\n✅ Complete! Both messages sent successfully! 🎉")
            return 0
        else:
            print("\n⚠️  Main message sent, but partner breakdown failed.")
            print(f"   Use thread timestamp: {timestamp}")
            return 1
    else:
        print("\n❌ Failed to send main message.")
        print("📋 Copy and paste the messages above to Slack manually.")
        return 1

if __name__ == '__main__':
    exit(main())

