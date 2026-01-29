# GEP Automated Daily Report

Automated system that fetches GEP performance data from Snowflake and posts daily updates to Slack.

## Features

- **Daily automated reports** at 8 AM via cron job
- **Snowflake integration** with Okta SSO authentication
- **Slack posting** to #emb-auto-growth-updates
- **Dynamic targets** from Google Sheets (Latest Forecast + FY26 Targets)
- **Partner breakdown** by pod (Accounting, HRIS, Banking, VSaaS)
- **YoY comparisons** and trending analysis
- **1-day data lag handling** (shows complete previous day data)

## Quick Setup

### 1. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Set Slack Bot Token
```bash
echo 'export SLACK_BOT_TOKEN="your-token-here"' >> ~/.zshrc
source ~/.zshrc
```

### 3. Update Your Email
Edit `update_gep_report.py` line 44:
```python
SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER', 'your.email@gusto.com')
```

### 4. Test Connection
```bash
python3 update_gep_report.py
```
This will open a browser for Snowflake Okta login and fetch data.

### 5. Set Up Cron Job (Optional)
```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

## Files

| File | Purpose |
|------|---------|
| `update_gep_report.py` | Fetches data from Snowflake, calculates metrics |
| `send_slack_update.py` | Formats and sends Slack messages |
| `run_daily_report.py` | Main entry point (runs both scripts) |
| `refresh_targets_simple.py` | Auto-updates monthly targets |
| `partner_pods.py` | Partner categorization (Accounting, HRIS, etc.) |
| `partner_tiers.py` | Partner tier classifications (Anchor, P1, P2) |
| `targets_cache.json` | Monthly forecast/stretch/low targets |
| `SNOWFLAKE_QUERY_PROMPT.md` | SQL query reference |
| `setup_cron.sh` | Automated cron job setup |

## Manual Run

```bash
python3 run_daily_report.py
```

⚠️ **Warning:** This posts to Slack! Only run for testing in off-hours.

## Output

**Main message includes:**
- MTD progress and daily average
- Run-rate projection vs goals (Forecast, Stretch, Low)
- Current attainment percentages
- Top performers
- Trending up/down partners
- Leads pipeline summary

**Thread reply includes:**
- Partner breakdown by pod and priority
- Per-partner MTD adds and leads
- MoM changes
- Partial data for current day

## Requirements

- Python 3.9+
- Snowflake access (Okta SSO)
- Slack bot token
- Google Sheets access (for targets)

## Troubleshooting

### "SLACK_BOT_TOKEN not set"
Make sure the token is in your shell config (`~/.zshrc` or `~/.bash_profile`) and reload: `source ~/.zshrc`

### "Can't connect to Snowflake"
- Check VPN connection
- Verify Okta SSO works in browser
- Confirm your email in `update_gep_report.py`

### Cron job not running
- Computer must be on at 8 AM
- Check logs: `tail -50 cron.log`
- Verify cron entry: `crontab -l`

## Maintenance

### Update Monthly Targets
Edit `refresh_targets_simple.py` to add new months:
```python
MONTHLY_TARGETS = {
    "2026-01": {"forecast": 933, "stretch": 1534, "low": 987},
    "2026-02": {"forecast": 948, "stretch": 1534, "low": 987},
    # Add new months here
}
```

### Add New Partners
Update `partner_pods.py` with pod and priority classifications.

## Notes

- Data has 1-day lag (shows complete data through yesterday)
- Runs at 8 AM daily (configurable in cron job)
- Posts to `#emb-auto-growth-updates` channel
- First day of month shows complete previous month results

## Contact

For questions or issues, contact the Data Analytics team.
