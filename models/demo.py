from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime
from threading import Lock

from config import DEMO, TOKENS
from models.timezone_utils import IST
from models.upstox import UpstoxError, get_quotes_map

WORKDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if os.getenv("VERCEL"):
    WORKDIR = tempfile.gettempdir()
DEMO_PATH = os.path.join(WORKDIR, TOKENS["demo_account_file"])
_LOCK = Lock()


class DemoAccountError(RuntimeError):
    pass


def _now_ist() -> datetime:
    return datetime.now(IST)


def _profile() -> dict:
    return {
        "user_id": "demo-user",
        "user_name": DEMO["display_name"],
        "email": DEMO["username"],
    }


def _default_state() -> dict:
    starting_balance = round(float(DEMO["starting_balance"]), 2)
    return {
        "wallet": {
            "starting_balance": starting_balance,
            "cash_balance": starting_balance,
            "realized_pnl": 0.0,
        },
        "positions": [],
        "orders": [],
    }


def _read_state() -> dict:
    if not os.path.exists(DEMO_PATH):
        return _default_state()
    try:
        with open(DEMO_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return _default_state()

    state = _default_state()
    wallet = data.get("wallet", {})
    state["wallet"]["starting_balance"] = round(float(wallet.get("starting_balance", state["wallet"]["starting_balance"]) or state["wallet"]["starting_balance"]), 2)
    state["wallet"]["cash_balance"] = round(float(wallet.get("cash_balance", state["wallet"]["cash_balance"]) or state["wallet"]["cash_balance"]), 2)
    state["wallet"]["realized_pnl"] = round(float(wallet.get("realized_pnl", 0) or 0), 2)
    state["positions"] = list(data.get("positions", []))
    state["orders"] = list(data.get("orders", []))
    return state


def _write_state(state: dict) -> None:
    with open(DEMO_PATH, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def demo_session_active(session) -> bool:
    return bool(session.get("demo_logged_in"))


def authenticate_demo(username: str, password: str) -> dict:
    if username.strip().lower() != DEMO["username"].strip().lower() or password != DEMO["password"]:
        raise DemoAccountError("Demo login failed. Check the demo username and password.")
    return _profile()


def _recent_activity(orders: list[dict]) -> list[dict]:
    activity = []
    for order in reversed(orders[-5:]):
        activity.append(
            {
                "title": f'{order.get("transaction_type", "TRADE")} {order.get("quantity", 0)} {order.get("symbol", "")}',
                "subtitle": f'{order.get("product", "")} at INR {order.get("average_price", 0):,.2f}',
                "timestamp": order.get("order_timestamp", ""),
            }
        )
    return activity


def get_demo_overview() -> dict:
    with _LOCK:
        state = _read_state()

    positions = [item for item in state["positions"] if int(item.get("quantity", 0) or 0) > 0]
    symbols = [item.get("symbol", "").upper() for item in positions if item.get("symbol")]
    quote_map = {}
    if symbols:
        try:
            quote_map = get_quotes_map(symbols)
        except UpstoxError:
            quote_map = {}

    holdings = []
    intraday_positions = []
    holdings_value = 0.0
    positions_value = 0.0
    holdings_pnl = 0.0
    positions_pnl = 0.0

    for item in positions:
        symbol = str(item.get("symbol", "")).upper()
        quantity = int(item.get("quantity", 0) or 0)
        average_price = round(float(item.get("average_price", 0) or 0), 2)
        product = str(item.get("product", "D")).upper()
        quote = quote_map.get(symbol, {})
        last_price = round(float(quote.get("last_price", item.get("last_trade_price", average_price)) or average_price), 2)
        current_value = round(quantity * last_price, 2)
        pnl = round((last_price - average_price) * quantity, 2)
        payload = {
            "symbol": symbol,
            "name": quote.get("display_name", symbol),
            "exchange": quote.get("exchange", item.get("exchange", "NSE")),
            "product": product,
            "quantity": quantity,
            "average_price": average_price,
            "last_price": last_price,
            "current_value": current_value,
            "pnl": pnl,
            "value": current_value,
            "instrument_key": quote.get("instrument_key", ""),
        }
        if product == "I":
            intraday_positions.append(payload)
            positions_value += current_value
            positions_pnl += pnl
        else:
            holdings.append(payload)
            holdings_value += current_value
            holdings_pnl += pnl

    orders = list(reversed(state["orders"][-12:]))
    today = _now_ist().date().isoformat()
    orders_today = sum(1 for order in state["orders"] if str(order.get("order_timestamp", "")).startswith(today))
    cash_balance = round(float(state["wallet"].get("cash_balance", 0) or 0), 2)
    realized_pnl = round(float(state["wallet"].get("realized_pnl", 0) or 0), 2)
    invested_value = round(holdings_value + positions_value, 2)
    total_equity = round(cash_balance + invested_value, 2)

    return {
        "mode": "demo",
        "profile": _profile(),
        "funds": {},
        "holdings": holdings,
        "positions": intraday_positions,
        "orders": orders,
        "wallet": {
            "cash_balance": cash_balance,
            "invested_value": invested_value,
            "total_equity": total_equity,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": round(holdings_pnl + positions_pnl, 2),
            "starting_balance": round(float(state["wallet"].get("starting_balance", DEMO["starting_balance"]) or DEMO["starting_balance"]), 2),
        },
        "recent_activity": _recent_activity(state["orders"]),
        "summary": {
            "available_margin": cash_balance,
            "used_margin": invested_value,
            "holdings_value": invested_value,
            "holdings_pnl": round(holdings_pnl + positions_pnl, 2),
            "positions_pnl": round(positions_pnl, 2),
            "orders_today": orders_today,
            "cash_balance": cash_balance,
            "invested_value": invested_value,
            "total_equity": total_equity,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": round(holdings_pnl + positions_pnl, 2),
        },
    }


def get_demo_status(logged_in: bool) -> dict:
    if not logged_in:
        return {
            "ok": True,
            "logged_in": False,
            "profile": None,
            "wallet": {
                "cash_balance": round(float(DEMO["starting_balance"]), 2),
                "invested_value": 0.0,
                "total_equity": round(float(DEMO["starting_balance"]), 2),
                "realized_pnl": 0.0,
                "unrealized_pnl": 0.0,
                "starting_balance": round(float(DEMO["starting_balance"]), 2),
            },
            "recent_activity": [],
            "message": "Demo account is offline. Log in to place paper trades and track the wallet.",
        }

    overview = get_demo_overview()
    return {
        "ok": True,
        "logged_in": True,
        "profile": overview["profile"],
        "wallet": overview["wallet"],
        "recent_activity": overview["recent_activity"],
        "message": "Demo account is active. Orders are paper-traded against the live market quote.",
    }


def place_demo_order(
    symbol: str,
    quantity: int,
    transaction_type: str,
    product: str = "D",
    order_type: str = "MARKET",
    price: float = 0.0,
) -> dict:
    symbol = symbol.strip().upper()
    if not symbol:
        raise DemoAccountError("Symbol is required for demo trading.")
    if quantity <= 0:
        raise DemoAccountError("Quantity must be greater than zero.")

    quote = {}
    try:
        quote = get_quotes_map([symbol]).get(symbol, {})
    except UpstoxError:
        quote = {}

    live_price = round(float(quote.get("last_price", 0) or 0), 2)
    if order_type == "LIMIT":
        if price <= 0:
            raise DemoAccountError("Limit orders need a positive limit price.")
        fill_price = round(float(price), 2)
        fill_note = "Filled at the requested demo limit price."
    else:
        if live_price <= 0:
            raise DemoAccountError("Live quote is unavailable. Connect the market feed or use a limit price for demo trading.")
        fill_price = live_price
        fill_note = "Filled at the latest live market quote."

    with _LOCK:
        state = _read_state()
        cash_balance = round(float(state["wallet"].get("cash_balance", 0) or 0), 2)
        realized_pnl = round(float(state["wallet"].get("realized_pnl", 0) or 0), 2)
        positions = list(state["positions"])

        position = None
        for item in positions:
            if str(item.get("symbol", "")).upper() == symbol and str(item.get("product", "D")).upper() == product:
                position = item
                break

        trade_value = round(fill_price * quantity, 2)

        if transaction_type == "BUY":
            if cash_balance < trade_value:
                raise DemoAccountError("Demo wallet balance is too low for this buy order.")
            cash_balance = round(cash_balance - trade_value, 2)
            if position:
                existing_qty = int(position.get("quantity", 0) or 0)
                existing_cost = round(existing_qty * float(position.get("average_price", 0) or 0), 2)
                new_qty = existing_qty + quantity
                position["quantity"] = new_qty
                position["average_price"] = round((existing_cost + trade_value) / new_qty, 2)
                position["last_trade_price"] = fill_price
            else:
                positions.append(
                    {
                        "symbol": symbol,
                        "exchange": quote.get("exchange", "NSE"),
                        "product": product,
                        "quantity": quantity,
                        "average_price": fill_price,
                        "last_trade_price": fill_price,
                    }
                )
        else:
            available_qty = int(position.get("quantity", 0) or 0) if position else 0
            if available_qty < quantity:
                raise DemoAccountError("Demo account does not have enough quantity to sell this symbol.")
            average_price = round(float(position.get("average_price", 0) or 0), 2)
            realized_pnl = round(realized_pnl + ((fill_price - average_price) * quantity), 2)
            cash_balance = round(cash_balance + trade_value, 2)
            remaining_qty = available_qty - quantity
            if remaining_qty == 0:
                positions = [item for item in positions if item is not position]
            else:
                position["quantity"] = remaining_qty
                position["last_trade_price"] = fill_price

        order = {
            "order_id": f"DEMO-{uuid.uuid4().hex[:10].upper()}",
            "symbol": symbol,
            "exchange": quote.get("exchange", "NSE"),
            "product": product,
            "transaction_type": transaction_type,
            "order_type": order_type,
            "status": "FILLED",
            "quantity": quantity,
            "average_price": fill_price,
            "order_timestamp": _now_ist().isoformat(timespec="seconds"),
            "status_message": fill_note,
        }

        state["wallet"]["cash_balance"] = cash_balance
        state["wallet"]["realized_pnl"] = realized_pnl
        state["positions"] = positions
        state["orders"] = (state["orders"] + [order])[-100:]
        _write_state(state)

    return {
        "mode": "demo",
        "order_id": order["order_id"],
        "symbol": symbol,
        "transaction_type": transaction_type,
        "quantity": quantity,
        "fill_price": fill_price,
        "message": f"Demo {transaction_type} order filled for {quantity} {symbol} at {fill_price:.2f}.",
    }
