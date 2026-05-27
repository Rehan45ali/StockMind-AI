import os


APP = {
    "name": "STOCKMIND AI",
    "secret_key": os.getenv("FLASK_SECRET_KEY", "stockmind-upstox-local-secret"),
    "port": int(os.getenv("PORT", "5000")),
    "debug": os.getenv("FLASK_DEBUG", "0") == "1",
}

UPSTOX = {
    "client_id": os.getenv("UPSTOX_CLIENT_ID", ""),
    "client_secret": os.getenv("UPSTOX_CLIENT_SECRET", ""),
    "redirect_uri": os.getenv("UPSTOX_REDIRECT_URI", "http://localhost:5000/upstox/callback"),
    "analytics_token": os.getenv("UPSTOX_ANALYTICS_TOKEN", ""),
    "algo_name": os.getenv("UPSTOX_ALGO_NAME", ""),
    "request_timeout": int(os.getenv("UPSTOX_REQUEST_TIMEOUT", "15")),
}

TOKENS = {
    "full_token_file": ".upstox_token.json",
    "instrument_cache_file": ".upstox_instruments.json",
    "demo_account_file": ".stockmind_demo.json",
}

DASHBOARD = {
    "default_watchlist": [
        "RELIANCE",
        "TCS",
        "INFY",
        "HDFCBANK",
        "ICICIBANK",
        "SBIN",
        "ITC",
        "LT",
    ],
    "default_indices": [
        "Nifty 50",
        "Nifty Bank",
        "Nifty IT",
        "Sensex",
    ],
}

DEMO = {
    "username": os.getenv("DEMO_ACCOUNT_USERNAME", "demo@stockmind.ai"),
    "password": os.getenv("DEMO_ACCOUNT_PASSWORD", ""),
    "display_name": os.getenv("DEMO_ACCOUNT_NAME", "STOCKMIND AI Demo"),
    "starting_balance": float(os.getenv("DEMO_STARTING_BALANCE", "500000")),
}

NEWS = {
    "query": os.getenv(
        "ECONOMY_NEWS_QUERY",
        "Indian economy OR RBI OR inflation OR GDP OR rupee OR crude oil OR global economy",
    ),
    "feed_url": os.getenv("ECONOMY_NEWS_FEED", "").strip(),
    "cache_seconds": int(os.getenv("NEWS_CACHE_SECONDS", "300")),
    "max_items": int(os.getenv("NEWS_MAX_ITEMS", "8")),
}
