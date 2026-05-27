# StockMind Upstox

Fresh Flask rebuild for live Indian market data through Upstox.

This version removes the old Zerodha flow, removes simulated prices, and replaces the interface with a cleaner Upstox-first dashboard.

## What it does

- Pulls live equity watchlist quotes and major index quotes from Upstox
- Uses real historical candles from Upstox for charts and signal calculations
- Supports two modes:
  - analytics token: read-only live market data
  - full OAuth account connect: live market data plus holdings, positions, funds, and order placement
- Provides a fresh single-screen interface for watchlist, chart, signal view, holdings, positions, and today's orders

## Stack

- Python
- Flask
- HTML, CSS, vanilla JavaScript
- Chart.js
- Upstox REST APIs

## Quick start

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Set environment variables

```powershell
$env:UPSTOX_CLIENT_ID="your_upstox_api_key"
$env:UPSTOX_CLIENT_SECRET="your_upstox_api_secret"
$env:UPSTOX_REDIRECT_URI="http://localhost:5000/upstox/callback"
```

Optional read-only market feed without OAuth popup:

```powershell
$env:UPSTOX_ANALYTICS_TOKEN="your_read_only_token"
```

3. Run the app

```bash
python app.py
```

4. Open

```text
http://localhost:5000
```

## Vercel deploy

This repo is configured for Vercel with the Python function entrypoint in `api/index.py` and routes in `vercel.json`.

Set these environment variables in Vercel before using full Upstox login:

- `UPSTOX_CLIENT_ID`
- `UPSTOX_CLIENT_SECRET`
- `UPSTOX_ANALYTICS_TOKEN` if you want read-only live market data without OAuth

Register this callback URL in the Upstox app settings for the deployed site:

`https://<your-vercel-domain>/upstox/callback`

The app uses a writable temp directory on Vercel for token and demo-state files, so it can run in the serverless runtime.

## Key routes

- `GET /api/market/snapshot`
- `GET /api/market/detail/<symbol>?tf=1D|1W|1M|1Y`
- `GET /api/market/search?q=RELIANCE`
- `GET /api/account/overview`
- `POST /api/account/order`
- `GET /api/upstox/status`
- `GET /api/upstox/login-url`
- `POST /api/upstox/disconnect`

## Notes

- Upstox access tokens expire at `3:30 AM` IST the next day, so reconnecting is normal.
- Holdings, positions, funds, and trading require a full Upstox account connection.
- If you only set `UPSTOX_ANALYTICS_TOKEN`, the market dashboard still works on real data, but account data and order placement stay disabled.
