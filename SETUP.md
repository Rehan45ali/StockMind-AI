# Setup Guide

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Create your Upstox app

In the Upstox developer console:

1. Create an app
2. Set the redirect URI to:

```text
http://localhost:5000/upstox/callback
```

3. Copy:

- `client_id`
- `client_secret`

## 3. Set environment variables

PowerShell example:

```powershell
$env:UPSTOX_CLIENT_ID="your_upstox_api_key"
$env:UPSTOX_CLIENT_SECRET="your_upstox_api_secret"
$env:UPSTOX_REDIRECT_URI="http://localhost:5000/upstox/callback"
```

Optional read-only mode:

```powershell
$env:UPSTOX_ANALYTICS_TOKEN="your_analytics_token"
```

## 4. Run

```bash
python app.py
```

Open:

```text
http://localhost:5000
```

## 5. Connect Upstox

- Click `Connect Upstox`
- Finish the Upstox login in the popup
- The app stores the access token locally in `.upstox_token.json`
- Once connected, holdings, positions, funds, and order placement become available

## Notes

- The Upstox full access token expires at `3:30 AM` IST the next day.
- If the market dashboard should work without the OAuth popup, use `UPSTOX_ANALYTICS_TOKEN`.
- `.upstox_token.json` and `.upstox_instruments.json` should stay local and should not be uploaded anywhere.
