# Stock Prediction Game

A static web game that uses real stock data from Alpha Vantage. Enter any valid stock ticker (e.g., `MSFT`), view the last 7 trading days up to a random start date (7–100 days before today), then predict if the price will go up or down on the next day. Your score increases by 1 for each correct prediction. The chart reveals each next day as you guess.

Data source: Alpha Vantage TIME_SERIES_DAILY_ADJUSTED (free tier).

## Local development

Open `index.html` in a browser. Because data is fetched directly from `alphavantage.co`, no local server is required.

## Environment

The demo uses the provided API key, embedded client-side:

- Alpha Vantage API key: set within `script.js` as `API_KEY`.
- Note: the free tier has strict rate limits (typically 5 requests/minute, 500/day). If you hit the limit, the app will display a friendly message. Wait a minute and try again.

## GitHub Pages deployment

1. Commit the files and push to GitHub.
2. Ensure your repository has these files at the repo root: `index.html`, `styles.css`, `script.js`.
3. In GitHub, go to Settings → Pages.
4. Under "Build and deployment":
   - Source: "Deploy from a branch"
   - Branch: select `main` (or your default branch), folder `/root`
5. Save. Your site will be available at the GitHub Pages URL shown.

Alternatively, use the `gh` CLI:

```bash
# From repo root
gh repo create your-user/stock-prediction-game --public --source=. --push
# Then enable Pages in Settings via the web UI or:
# gh api -X POST repos/your-user/stock-prediction-game/pages ... (requires extra JSON)
```

## How it works

- On load, you enter a ticker and click Load. The app fetches `TIME_SERIES_DAILY_ADJUSTED` and validates the response.
- It randomly selects a start date in the valid range and requires at least 7 prior trading days for charting.
- You guess Up/Down for the next trading day; the app reveals that day's close, updates the chart, date, and score, and repeats.

## Notes and limitations

- Market holidays and weekends are implicitly handled because Alpha Vantage only returns trading days; the app advances to the next available date in the series.
- If a symbol has insufficient history in the 100-day window (or data gaps), try another ticker.
- This is a purely static site; no server is used.