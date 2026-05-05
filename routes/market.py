from flask import Blueprint, jsonify, request

from config import DASHBOARD
from models.upstox import (
    UpstoxError,
    get_connection_status,
    get_index_quotes,
    get_market_status,
    get_symbol_detail,
    get_watchlist_quotes,
    search_symbols,
)


market_bp = Blueprint("market", __name__)


@market_bp.get("/snapshot")
def snapshot():
    raw_symbols = request.args.get("symbols", "")
    symbols = [item.strip().upper() for item in raw_symbols.split(",") if item.strip()]
    if not symbols:
        symbols = DASHBOARD["default_watchlist"]

    status = get_connection_status()
    try:
        return jsonify(
            {
                "ok": True,
                "connection": status,
                "market_status": get_market_status(),
                "watchlist": get_watchlist_quotes(symbols),
                "indices": get_index_quotes(),
            }
        )
    except UpstoxError as exc:
        return jsonify(
            {
                "ok": False,
                "connection": status,
                "market_status": get_market_status(),
                "watchlist": [],
                "indices": [],
                "error": str(exc),
            }
        )


@market_bp.get("/detail/<symbol>")
def detail(symbol: str):
    timeframe = request.args.get("tf", "1D").upper()
    if timeframe not in {"1D", "1W", "1M", "1Y"}:
        timeframe = "1D"
    try:
        return jsonify({"ok": True, **get_symbol_detail(symbol.upper(), timeframe)})
    except UpstoxError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@market_bp.get("/search")
def search():
    query = request.args.get("q", "")
    try:
        return jsonify({"ok": True, "results": search_symbols(query)})
    except UpstoxError as exc:
        return jsonify({"ok": False, "error": str(exc), "results": []}), 400
