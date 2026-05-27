from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, time, timedelta
from threading import Lock
from urllib.parse import urlencode

import requests

from config import DASHBOARD, TOKENS, UPSTOX
from models.analytics import analyze_price_action
from models.timezone_utils import IST

API_BASE_V2 = "https://api.upstox.com/v2"
API_BASE_V3 = "https://api-hft.upstox.com/v3"
WORKDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOKEN_PATH = os.path.join(WORKDIR, TOKENS["full_token_file"])
INSTRUMENT_CACHE_PATH = os.path.join(WORKDIR, TOKENS["instrument_cache_file"])

_session = requests.Session()
_token_lock = Lock()
_instrument_lock = Lock()


class UpstoxError(RuntimeError):
    pass


def _now_ist() -> datetime:
    return datetime.now(IST)


def _read_json(path: str, fallback):
    if not os.path.exists(path):
        return fallback
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return fallback


def _write_json(path: str, payload) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _delete_file(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)


def _full_token_expired(payload: dict | None) -> bool:
    if not payload or not payload.get("issued_at"):
        return False
    try:
        issued_at = datetime.fromisoformat(payload["issued_at"]).astimezone(IST)
    except ValueError:
        return False
    expiry = datetime.combine(issued_at.date() + timedelta(days=1), time(3, 30), tzinfo=IST)
    return _now_ist() >= expiry


def _load_full_token() -> dict | None:
    with _token_lock:
        payload = _read_json(TOKEN_PATH, None)
        if payload and _full_token_expired(payload):
            _delete_file(TOKEN_PATH)
            return None
        return payload


def _save_full_token(payload: dict) -> None:
    token_payload = {
        "access_token": payload.get("access_token", ""),
        "user_id": payload.get("user_id", ""),
        "user_name": payload.get("user_name", ""),
        "email": payload.get("email", ""),
        "broker": payload.get("broker", "UPSTOX"),
        "issued_at": _now_ist().isoformat(),
    }
    with _token_lock:
        _write_json(TOKEN_PATH, token_payload)


def _load_instrument_cache() -> dict:
    with _instrument_lock:
        return _read_json(INSTRUMENT_CACHE_PATH, {})


def _save_instrument_cache(cache: dict) -> None:
    with _instrument_lock:
        _write_json(INSTRUMENT_CACHE_PATH, cache)


def _require_json(response: requests.Response) -> dict | list:
    try:
        return response.json()
    except ValueError as exc:
        raise UpstoxError(f"Unexpected Upstox response: {response.text[:200]}") from exc


def _request(method: str, url: str, token: str, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.setdefault("Accept", "application/json")
    if kwargs.get("json") is not None:
        headers.setdefault("Content-Type", "application/json")
    headers["Authorization"] = f"Bearer {token}"

    response = _session.request(
        method=method,
        url=url,
        headers=headers,
        timeout=UPSTOX["request_timeout"],
        **kwargs,
    )
    payload = _require_json(response)

    if response.status_code == 401:
        with _token_lock:
            _delete_file(TOKEN_PATH)
        raise UpstoxError("Upstox session expired. Please reconnect your account.")

    if response.status_code >= 400:
        message = ""
        if isinstance(payload, dict):
            errors = payload.get("errors") or []
            if errors and isinstance(errors, list):
                message = errors[0].get("message", "")
            message = message or payload.get("message", "")
        raise UpstoxError(message or f"Upstox request failed with HTTP {response.status_code}.")

    return payload


def _any_access_token(prefer_full: bool = True) -> str | None:
    full = _load_full_token()
    analytics = UPSTOX["analytics_token"].strip()
    if prefer_full and full and full.get("access_token"):
        return full["access_token"]
    if analytics:
        return analytics
    if full and full.get("access_token"):
        return full["access_token"]
    return None


def _full_access_token() -> str | None:
    full = _load_full_token()
    return full.get("access_token") if full else None


def configured_for_login() -> bool:
    return bool(UPSTOX["client_id"].strip() and UPSTOX["client_secret"].strip() and UPSTOX["redirect_uri"].strip())


def get_connection_status() -> dict:
    full = _load_full_token()
    analytics = UPSTOX["analytics_token"].strip()
    has_full = bool(full and full.get("access_token"))
    has_any = has_full or bool(analytics)

    if has_full:
        mode = "full"
        message = "Upstox account connected for live market data, holdings, positions, and orders."
    elif analytics:
        mode = "analytics"
        message = "Read-only Upstox analytics token active for live market data."
    else:
        mode = "none"
        message = "Add an analytics token or connect your Upstox account to start the live feed."

    return {
        "configured": configured_for_login(),
        "full_connected": has_full,
        "read_only_connected": bool(analytics) and not has_full,
        "any_connected": has_any,
        "auth_mode": mode,
        "redirect_uri": UPSTOX["redirect_uri"],
        "user": {
            "user_id": full.get("user_id", ""),
            "user_name": full.get("user_name", ""),
            "email": full.get("email", ""),
        } if has_full else None,
        "message": message,
    }


def build_login_url(state: str) -> str:
    if not configured_for_login():
        raise UpstoxError("Fill UPSTOX_CLIENT_ID, UPSTOX_CLIENT_SECRET, and UPSTOX_REDIRECT_URI first.")
    query = urlencode(
        {
            "client_id": UPSTOX["client_id"].strip(),
            "redirect_uri": UPSTOX["redirect_uri"].strip(),
            "response_type": "code",
            "state": state,
        }
    )
    return f"https://api.upstox.com/v2/login/authorization/dialog?{query}"


def new_oauth_state() -> str:
    return secrets.token_urlsafe(24)


def exchange_code_for_token(code: str) -> dict:
    if not configured_for_login():
        raise UpstoxError("Upstox OAuth is not configured yet.")
    response = _session.post(
        f"{API_BASE_V2}/login/authorization/token",
        headers={
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "code": code,
            "client_id": UPSTOX["client_id"].strip(),
            "client_secret": UPSTOX["client_secret"].strip(),
            "redirect_uri": UPSTOX["redirect_uri"].strip(),
            "grant_type": "authorization_code",
        },
        timeout=UPSTOX["request_timeout"],
    )
    payload = _require_json(response)
    if response.status_code >= 400:
        message = payload.get("errors", [{}])[0].get("message") if isinstance(payload, dict) else ""
        raise UpstoxError(message or "Could not exchange the authorization code.")
    _save_full_token(payload)
    return payload


def disconnect() -> None:
    with _token_lock:
        _delete_file(TOKEN_PATH)


def _search_instruments(query: str, exchanges: str, segments: str, records: int = 10) -> list[dict]:
    token = _any_access_token(prefer_full=False)
    if not token:
        raise UpstoxError("No Upstox token is available yet. Add an analytics token or connect your account.")
    payload = _request(
        "GET",
        f"{API_BASE_V2}/instruments/search",
        token,
        params={
            "query": query,
            "exchanges": exchanges,
            "segments": segments,
            "page_number": 1,
            "records": records,
        },
    )
    return payload.get("data", []) if isinstance(payload, dict) else []


def search_symbols(query: str, limit: int = 8) -> list[dict]:
    if not query.strip():
        return []
    results = _search_instruments(query.strip(), "NSE,BSE", "EQ", min(limit, 10))
    final = []
    for item in results[:limit]:
        final.append(
            {
                "symbol": item.get("trading_symbol", ""),
                "name": item.get("short_name") or item.get("name", ""),
                "exchange": item.get("exchange", ""),
                "segment": item.get("segment", ""),
                "instrument_key": item.get("instrument_key", ""),
            }
        )
    return final


def _instrument_cache_key(query: str, exchanges: str, segments: str) -> str:
    return f"{exchanges}|{segments}|{query.strip().upper()}"


def _resolve_instrument(query: str, exchanges: str, segments: str) -> dict:
    cache = _load_instrument_cache()
    key = _instrument_cache_key(query, exchanges, segments)
    if key in cache:
        return cache[key]

    results = _search_instruments(query=query, exchanges=exchanges, segments=segments, records=10)
    if not results:
        raise UpstoxError(f"Could not resolve instrument for {query}.")

    normalized = query.strip().upper()
    choice = None
    for item in results:
        if item.get("trading_symbol", "").upper() == normalized:
            choice = item
            break
    if choice is None:
        for item in results:
            short_name = str(item.get("short_name", "")).upper()
            name = str(item.get("name", "")).upper()
            if normalized in {short_name, name}:
                choice = item
                break
    if choice is None:
        choice = results[0]

    cache[key] = choice
    _save_instrument_cache(cache)
    return choice


def _normalize_quote(item: dict, resolved: dict, label: str | None = None) -> dict:
    ohlc = item.get("ohlc", {})
    prev_close = float(ohlc.get("close", 0) or 0)
    last_price = float(item.get("last_price", 0) or 0)
    net_change = float(item.get("net_change", 0) or 0)
    pct_change = round((net_change / prev_close) * 100, 2) if prev_close else 0.0
    return {
        "symbol": item.get("symbol") or resolved.get("trading_symbol", ""),
        "display_name": label or resolved.get("short_name") or resolved.get("name") or resolved.get("trading_symbol", ""),
        "instrument_key": resolved.get("instrument_key", ""),
        "exchange": resolved.get("exchange", ""),
        "segment": resolved.get("segment", ""),
        "last_price": last_price,
        "open": float(ohlc.get("open", 0) or 0),
        "high": float(ohlc.get("high", 0) or 0),
        "low": float(ohlc.get("low", 0) or 0),
        "prev_close": prev_close,
        "net_change": round(net_change, 2),
        "pct_change": pct_change,
        "volume": int(item.get("volume", 0) or 0),
        "last_updated": item.get("timestamp", ""),
    }


def _get_quotes_for_resolved(resolved_items: list[tuple[str, dict]]) -> list[dict]:
    if not resolved_items:
        return []
    token = _any_access_token(prefer_full=False)
    if not token:
        raise UpstoxError("No Upstox token is available yet.")

    instrument_keys = [item[1]["instrument_key"] for item in resolved_items]
    payload = _request(
        "GET",
        f"{API_BASE_V2}/market-quote/quotes",
        token,
        params={"instrument_key": ",".join(instrument_keys)},
    )
    data = payload.get("data", {}) if isinstance(payload, dict) else {}

    quotes_by_token = {}
    for quote in data.values():
        token_key = quote.get("instrument_token") or quote.get("instrument_key")
        if token_key:
            quotes_by_token[token_key] = quote

    final = []
    for label, resolved in resolved_items:
        quote = quotes_by_token.get(resolved["instrument_key"])
        if quote:
            final.append(_normalize_quote(quote, resolved, label=label))
    return final


def get_watchlist_quotes(symbols: list[str] | None = None) -> list[dict]:
    symbols = symbols or DASHBOARD["default_watchlist"]
    resolved_items = []
    for symbol in symbols:
        try:
            resolved = _resolve_instrument(symbol, "NSE,BSE", "EQ")
            resolved_items.append((symbol.upper(), resolved))
        except UpstoxError:
            continue
    return _get_quotes_for_resolved(resolved_items)


def get_quotes_map(symbols: list[str] | None = None) -> dict[str, dict]:
    quotes = get_watchlist_quotes(symbols or [])
    return {item["symbol"].upper(): item for item in quotes}


def get_index_quotes() -> list[dict]:
    resolved_items = []
    for name in DASHBOARD["default_indices"]:
        try:
            resolved = _resolve_instrument(name, "NSE,BSE", "INDEX")
            resolved_items.append((name, resolved))
        except UpstoxError:
            continue
    return _get_quotes_for_resolved(resolved_items)


def get_market_status() -> dict | None:
    token = _any_access_token(prefer_full=False)
    if not token:
        return None
    try:
        payload = _request("GET", f"{API_BASE_V2}/market/status/NSE", token)
        return payload.get("data", {}) if isinstance(payload, dict) else None
    except UpstoxError:
        return None


def _parse_candles(payload: dict) -> list[dict]:
    raw_candles = payload.get("data", {}).get("candles", []) if isinstance(payload, dict) else []
    candles = []
    for row in reversed(raw_candles):
        candles.append(
            {
                "ts": row[0],
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]) if len(row) > 5 else 0.0,
                "oi": float(row[6]) if len(row) > 6 else 0.0,
            }
        )
    return candles


def _history_path(instrument_key: str, timeframe: str) -> str:
    today = _now_ist().date()
    if timeframe == "1D":
        return f"{API_BASE_V2}/historical-candle/intraday/{instrument_key}/30minute"
    if timeframe == "1W":
        from_date = today - timedelta(days=7)
        return f"{API_BASE_V2}/historical-candle/{instrument_key}/day/{today.isoformat()}/{from_date.isoformat()}"
    if timeframe == "1M":
        from_date = today - timedelta(days=30)
        return f"{API_BASE_V2}/historical-candle/{instrument_key}/day/{today.isoformat()}/{from_date.isoformat()}"
    from_date = today - timedelta(days=365)
    return f"{API_BASE_V2}/historical-candle/{instrument_key}/week/{today.isoformat()}/{from_date.isoformat()}"


def _daily_signal_history(instrument_key: str) -> list[dict]:
    token = _any_access_token(prefer_full=False)
    if not token:
        return []
    today = _now_ist().date()
    from_date = today - timedelta(days=180)
    payload = _request(
        "GET",
        f"{API_BASE_V2}/historical-candle/{instrument_key}/day/{today.isoformat()}/{from_date.isoformat()}",
        token,
    )
    return _parse_candles(payload)


def get_symbol_detail(symbol: str, timeframe: str = "1D") -> dict:
    resolved = _resolve_instrument(symbol, "NSE,BSE", "EQ")
    quote = _get_quotes_for_resolved([(symbol.upper(), resolved)])
    if not quote:
        raise UpstoxError(f"Live quote is not available for {symbol}.")

    token = _any_access_token(prefer_full=False)
    if not token:
        raise UpstoxError("No Upstox token is available yet.")

    history_payload = _request("GET", _history_path(resolved["instrument_key"], timeframe), token)
    history = _parse_candles(history_payload)
    signal_history = _daily_signal_history(resolved["instrument_key"])
    signal = analyze_price_action(signal_history)

    return {
        "symbol": symbol.upper(),
        "display_name": resolved.get("short_name") or resolved.get("name") or symbol.upper(),
        "instrument_key": resolved["instrument_key"],
        "quote": quote[0],
        "history": history,
        "signal": signal,
        "timeframe": timeframe,
    }


def get_account_overview() -> dict:
    token = _full_access_token()
    if not token:
        raise UpstoxError("Connect your Upstox account to load holdings, positions, and order data.")

    profile_payload = _request("GET", f"{API_BASE_V2}/user/profile", token)
    funds_payload = _request("GET", f"{API_BASE_V2}/user/get-funds-and-margin", token)
    holdings_payload = _request("GET", f"{API_BASE_V2}/portfolio/long-term-holdings", token)
    positions_payload = _request("GET", f"{API_BASE_V2}/portfolio/short-term-positions", token)
    orders_payload = _request("GET", f"{API_BASE_V2}/order/retrieve-all", token)

    profile = profile_payload.get("data", {}) if isinstance(profile_payload, dict) else {}
    funds = funds_payload.get("data", {}) if isinstance(funds_payload, dict) else {}
    holdings = holdings_payload.get("data", []) if isinstance(holdings_payload, dict) else holdings_payload
    positions = positions_payload.get("data", []) if isinstance(positions_payload, dict) else positions_payload
    orders = orders_payload if isinstance(orders_payload, list) else orders_payload.get("data", [])

    holdings_value = 0.0
    holdings_pnl = 0.0
    parsed_holdings = []
    for item in holdings:
        quantity = int(item.get("quantity", 0) or 0)
        last_price = float(item.get("last_price", 0) or 0)
        current_value = round(quantity * last_price, 2)
        pnl = float(item.get("pnl", 0) or 0)
        holdings_value += current_value
        holdings_pnl += pnl
        parsed_holdings.append(
            {
                "symbol": item.get("trading_symbol") or item.get("tradingsymbol", ""),
                "name": item.get("company_name", ""),
                "exchange": item.get("exchange", ""),
                "quantity": quantity,
                "average_price": float(item.get("average_price", 0) or 0),
                "last_price": last_price,
                "current_value": current_value,
                "pnl": round(pnl, 2),
                "day_change_pct": round(float(item.get("day_change_percentage", 0) or 0), 2),
                "instrument_key": item.get("instrument_token", ""),
            }
        )

    positions_pnl = 0.0
    parsed_positions = []
    for item in positions:
        pnl = float(item.get("pnl", 0) or 0)
        positions_pnl += pnl
        parsed_positions.append(
            {
                "symbol": item.get("trading_symbol") or item.get("tradingsymbol", ""),
                "exchange": item.get("exchange", ""),
                "product": item.get("product", ""),
                "quantity": int(item.get("quantity", 0) or 0),
                "average_price": float(item.get("average_price", 0) or 0),
                "last_price": float(item.get("last_price", 0) or 0),
                "pnl": round(pnl, 2),
                "value": round(float(item.get("value", 0) or 0), 2),
                "instrument_key": item.get("instrument_token", ""),
            }
        )

    parsed_orders = []
    for item in orders[:12]:
        parsed_orders.append(
            {
                "order_id": item.get("order_id", ""),
                "symbol": item.get("trading_symbol") or item.get("tradingsymbol", ""),
                "exchange": item.get("exchange", ""),
                "product": item.get("product", ""),
                "transaction_type": item.get("transaction_type", ""),
                "order_type": item.get("order_type", ""),
                "status": item.get("status", ""),
                "quantity": int(item.get("quantity", 0) or 0),
                "average_price": float(item.get("average_price", 0) or 0),
                "order_timestamp": item.get("order_timestamp", ""),
                "status_message": item.get("status_message", ""),
            }
        )

    equity = funds.get("equity", {}) if isinstance(funds, dict) else {}

    return {
        "profile": profile,
        "funds": funds,
        "holdings": parsed_holdings,
        "positions": parsed_positions,
        "orders": parsed_orders,
        "summary": {
            "available_margin": round(float(equity.get("available_margin", 0) or 0), 2),
            "used_margin": round(float(equity.get("used_margin", 0) or 0), 2),
            "holdings_value": round(holdings_value, 2),
            "holdings_pnl": round(holdings_pnl, 2),
            "positions_pnl": round(positions_pnl, 2),
            "orders_today": len(parsed_orders),
        },
    }


def place_order(
    symbol: str,
    quantity: int,
    transaction_type: str,
    product: str = "D",
    order_type: str = "MARKET",
    price: float = 0.0,
) -> dict:
    token = _full_access_token()
    if not token:
        raise UpstoxError(
            "No active full Upstox trading token found. If you changed the static IP, Upstox invalidates old tokens, "
            "so generate a fresh token before placing an order."
        )

    resolved = _resolve_instrument(symbol, "NSE,BSE", "EQ")
    order_type = order_type.upper()
    transaction_type = transaction_type.upper()
    product = product.upper()

    if order_type == "LIMIT" and price <= 0:
        raise UpstoxError("Limit orders need a positive limit price.")

    payload = {
        "quantity": int(quantity),
        "product": product,
        "validity": "DAY",
        "price": round(float(price), 2) if order_type == "LIMIT" else 0,
        "tag": "stockmind-upstox",
        "instrument_token": resolved["instrument_key"],
        "order_type": order_type,
        "transaction_type": transaction_type,
        "disclosed_quantity": 0,
        "trigger_price": 0,
        "is_amo": False,
        "slice": False,
        "market_protection": 0,
    }

    order_headers = {}
    if UPSTOX["algo_name"].strip():
        order_headers["X-Algo-Name"] = UPSTOX["algo_name"].strip()

    try:
        response = _request(
            "POST",
            f"{API_BASE_V3}/order/place",
            token,
            headers=order_headers,
            json=payload,
        )
    except UpstoxError as exc:
        if "static ip" in str(exc).lower():
            raise UpstoxError(
                "Upstox blocked the order because the request is not coming from your registered static IP. "
                "Update the static IP in My Apps or via /v2/user/ip, then generate a fresh token and retry."
            ) from exc
        if "x-algo-name" in str(exc).lower() or "algo name" in str(exc).lower():
            raise UpstoxError(
                "Upstox expects the configured Algo Name header for this app. Set UPSTOX_ALGO_NAME to the exact "
                "Algo Name configured in My Apps and retry."
            ) from exc
        raise
    data = response.get("data", {}) if isinstance(response, dict) else {}
    order_ids = data.get("order_ids", [])
    order_id = order_ids[0] if order_ids else data.get("order_id", "")
    return {
        "order_id": order_id,
        "symbol": symbol.upper(),
        "transaction_type": transaction_type,
        "quantity": int(quantity),
        "message": f"{transaction_type} order submitted for {quantity} {symbol.upper()} shares.",
    }
