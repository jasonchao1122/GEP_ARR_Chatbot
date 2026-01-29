#!/usr/bin/env python3
"""
GEP Daily Report Runner
Fetches data from Snowflake and posts to Slack.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file if present
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Import the data fetcher
from update_gep_report import get_report_data


# Slack Configuration
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', '#emb-auto-growth-updates')


def format_currency(value: float) -> str:
    """Format number as currency."""
    if value is None:
        return "N/A"
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:.2f}"


def format_percentage(value: float) -> str:
    """Format number as percentage."""
    if value is None:
        return "N/A"
    return f"{value:+.1f}%" if value != 0 else "0.0%"


def build_slack_message(report_data: dict) -> list:
    """
    Build Slack message blocks from report data.
    """
    today = datetime.now().strftime("%B %d, %Y")
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📊 GEP Daily Report - {today}",
                "emoji": True
            }
        },
        {
            "type": "divider"
        }
    ]
    
    # ARR Summary Section
    arr = report_data.get('arr_summary', {})
    if arr:
        arr_text = f"*Current ARR:* {format_currency(arr.get('current_arr', 0))}\n"
        arr_text += f"*MTD Growth:* {format_percentage(arr.get('arr_growth_mtd', 0))}\n"
        arr_text += f"*YTD Growth:* {format_percentage(arr.get('arr_growth_ytd', 0))}\n"
        arr_text += f"*EOM Forecast:* {format_currency(arr.get('arr_forecast_eom', 0))}\n"
        arr_text += f"*vs Forecast:* {format_percentage(arr.get('arr_vs_forecast_pct', 0))}"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*💰 ARR Summary*\n{arr_text}"
            }
        })
        blocks.append({"type": "divider"})
    
    # Channel Performance Section
    channel_df = report_data.get('channel_performance')
    if channel_df is not None and not channel_df.empty:
        channel_text = "*📈 Channel Performance*\n"
        for _, row in channel_df.head(5).iterrows():
            emoji = "🟢" if row.get('performance_vs_target_pct', 0) >= 0 else "🔴"
            channel_text += f"{emoji} *{row.get('channel_name', 'Unknown')}*: "
            channel_text += f"{format_currency(row.get('arr_contribution', 0))} ARR, "
            channel_text += f"{row.get('conversion_rate', 0):.1f}% CVR\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": channel_text
            }
        })
        blocks.append({"type": "divider"})
    
    # GEP Metrics Summary
    gep_df = report_data.get('gep_metrics')
    if gep_df is not None and not gep_df.empty:
        latest_date = gep_df['report_date'].max() if 'report_date' in gep_df.columns else None
        metrics_text = f"*📋 GEP Metrics* (Latest: {latest_date})\n"
        metrics_text += f"Total metrics tracked: {len(gep_df)}\n"
        
        # Summary by segment if available
        if 'segment' in gep_df.columns:
            segments = gep_df['segment'].nunique()
            metrics_text += f"Segments covered: {segments}\n"
        
        if 'channel' in gep_df.columns:
            channels = gep_df['channel'].nunique()
            metrics_text += f"Channels tracked: {channels}"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": metrics_text
            }
        })
    
    # Footer
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"🤖 _Auto-generated at {datetime.now().strftime('%H:%M:%S')} | Data source: Snowflake_"
            }
        ]
    })
    
    return blocks


def post_to_slack(blocks: list) -> bool:
    """
    Post the report to Slack.
    """
    if not SLACK_BOT_TOKEN:
        print("ERROR: SLACK_BOT_TOKEN environment variable not set!")
        print("Please set it with: export SLACK_BOT_TOKEN='your-token-here'")
        return False
    
    client = WebClient(token=SLACK_BOT_TOKEN)
    
    try:
        print(f"Posting to Slack channel: {SLACK_CHANNEL}")
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL,
            blocks=blocks,
            text="GEP Daily Report"  # Fallback text for notifications
        )
        print(f"Message posted successfully! Timestamp: {response['ts']}")
        return True
        
    except SlackApiError as e:
        print(f"Slack API Error: {e.response['error']}")
        if e.response['error'] == 'channel_not_found':
            print(f"Channel '{SLACK_CHANNEL}' not found. Make sure the bot is invited to the channel.")
        elif e.response['error'] == 'invalid_auth':
            print("Invalid Slack bot token. Please check your SLACK_BOT_TOKEN.")
        return False
    except Exception as e:
        print(f"Error posting to Slack: {e}")
        return False


def main():
    """
    Main function to run the daily GEP report.
    """
    print("=" * 60)
    print(f"GEP Daily Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Step 1: Fetch data from Snowflake
    print("\n[Step 1/3] Fetching data from Snowflake...")
    try:
        report_data = get_report_data()
        print("✅ Data fetched successfully!")
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        sys.exit(1)
    
    # Step 2: Build Slack message
    print("\n[Step 2/3] Building Slack message...")
    blocks = build_slack_message(report_data)
    print(f"✅ Message built with {len(blocks)} blocks")
    
    # Step 3: Post to Slack
    print("\n[Step 3/3] Posting to Slack...")
    success = post_to_slack(blocks)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ GEP Daily Report completed successfully!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ GEP Daily Report failed to post to Slack")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
