# GEP Forecast Report Automation

Automated daily reporting system that fetches GEP performance data from Snowflake and posts to Slack.

## Setup Instructions

### 1. Prerequisites

- Python 3.9+
- Snowflake access via Okta SSO
- Slack bot token with permissions to post to #emb-auto-growth-updates

### 2. Install Dependencies

The virtual environment is already set up. If you need to recreate it:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and update:
- `SLACK_BOT_TOKEN` - Your Slack bot token
- `SNOWFLAKE_USER` - Your Gusto email address

Or set them in your shell profile (`~/.bashrc` or `~/.zshrc`):

```bash
export SLACK_BOT_TOKEN='xoxb-your-token-here'
export SNOWFLAKE_USER='your.email@gusto.com'
```

### 4. Update Your Email

Edit `update_gep_report.py` and replace `YOUR_EMAIL@gusto.com` with your actual Gusto email address.

### 5. Test the Setup

```bash
source venv/bin/activate
python run_daily_report.py
```

This will:
- Open a browser for Snowflake Okta authentication
- Fetch GEP data from Snowflake
- Post the report to Slack #emb-auto-growth-updates

### 6. Set Up Cron Job (Optional)

To run automatically at 8 AM daily:

```bash
./setup_cron.sh
```

When prompted, enter your Slack bot token.

Verify the cron job:

```bash
crontab -l
```

## Files

- `run_daily_report.py` - Main script that orchestrates the daily report
- `update_gep_report.py` - Snowflake data fetcher module
- `setup_cron.sh` - Script to set up the daily cron job
- `requirements.txt` - Python dependencies
- `.env.example` - Template for environment variables
- `cron.log` - Log file for cron job output (created after first run)

## Troubleshooting

### Authentication Issues

The Snowflake connection uses Okta SSO (externalbrowser authenticator). Make sure:
- Your browser can open for authentication
- You're logged into Okta
- For cron jobs: you may need to be present for the first authentication

### Slack Posting Failures

- Verify `SLACK_BOT_TOKEN` is set correctly
- Ensure the bot is invited to #emb-auto-growth-updates
- Check the token has `chat:write` permission

### Cron Job Not Running

- Your computer must be on at 8 AM
- Check `cron.log` for errors
- Verify cron is installed: `crontab -l`

## Notes

- The cron job requires your computer to be running at 8 AM
- Snowflake Okta authentication may require browser interaction
- All paths in the cron job are absolute to avoid path issues
