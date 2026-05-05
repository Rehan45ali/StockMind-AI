from flask import Blueprint, jsonify, request, session

from models.demo import (
    DemoAccountError,
    demo_session_active,
    get_demo_overview,
    place_demo_order,
)
from models.upstox import UpstoxError, get_account_overview, place_order


account_bp = Blueprint("account", __name__)


@account_bp.get("/overview")
def overview():
    if demo_session_active(session):
        return jsonify({"ok": True, **get_demo_overview()})

    try:
        return jsonify({"ok": True, **get_account_overview()})
    except UpstoxError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 401


@account_bp.post("/order")
def order():
    payload = request.get_json(silent=True) or {}
    symbol = str(payload.get("symbol", "")).strip().upper()
    transaction_type = str(payload.get("transaction_type", "BUY")).strip().upper()
    product = str(payload.get("product", "D")).strip().upper()
    order_type = str(payload.get("order_type", "MARKET")).strip().upper()

    try:
        quantity = int(payload.get("quantity", 0))
    except (TypeError, ValueError):
        quantity = 0

    try:
        price = float(payload.get("price", 0) or 0)
    except (TypeError, ValueError):
        price = 0.0

    if not symbol:
        return jsonify({"ok": False, "error": "Symbol is required."}), 400
    if transaction_type not in {"BUY", "SELL"}:
        return jsonify({"ok": False, "error": "Transaction type must be BUY or SELL."}), 400
    if product not in {"D", "I", "MTF"}:
        return jsonify({"ok": False, "error": "Product must be D, I, or MTF."}), 400
    if order_type not in {"MARKET", "LIMIT"}:
        return jsonify({"ok": False, "error": "Order type must be MARKET or LIMIT."}), 400
    if quantity <= 0:
        return jsonify({"ok": False, "error": "Quantity must be greater than zero."}), 400

    if demo_session_active(session):
        try:
            result = place_demo_order(
                symbol=symbol,
                quantity=quantity,
                transaction_type=transaction_type,
                product=product,
                order_type=order_type,
                price=price,
            )
            return jsonify({"ok": True, **result})
        except DemoAccountError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    try:
        result = place_order(
            symbol=symbol,
            quantity=quantity,
            transaction_type=transaction_type,
            product=product,
            order_type=order_type,
            price=price,
        )
        return jsonify({"ok": True, **result})
    except UpstoxError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
