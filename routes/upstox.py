from flask import Blueprint, jsonify, render_template, request, session

from models.upstox import (
    UpstoxError,
    build_login_url,
    disconnect,
    exchange_code_for_token,
    get_connection_status,
    new_oauth_state,
)


upstox_bp = Blueprint("upstox", __name__)


def _callback_redirect_uri() -> str:
    return request.url_root.rstrip("/") + "/upstox/callback"


def handle_callback():
    returned_state = request.args.get("state", "")
    expected_state = session.pop("upstox_oauth_state", "")
    code = request.args.get("code", "")

    if not code:
        return render_template(
            "upstox_callback.html",
            success=False,
            message="Upstox did not return an authorization code.",
        )
    if expected_state and returned_state != expected_state:
        return render_template(
            "upstox_callback.html",
            success=False,
            message="OAuth state check failed. Please try connecting again.",
        )

    try:
        payload = exchange_code_for_token(code, redirect_uri=_callback_redirect_uri())
        user_name = payload.get("user_name") or payload.get("user_id") or "your account"
        return render_template(
            "upstox_callback.html",
            success=True,
            message=f"Connected to {user_name}.",
        )
    except UpstoxError as exc:
        return render_template(
            "upstox_callback.html",
            success=False,
            message=str(exc),
        )


@upstox_bp.get("/status")
def status():
    return jsonify({"ok": True, **get_connection_status(redirect_uri=_callback_redirect_uri())})


@upstox_bp.get("/login-url")
def login_url():
    state = new_oauth_state()
    session["upstox_oauth_state"] = state
    try:
        return jsonify({"ok": True, "url": build_login_url(state, redirect_uri=_callback_redirect_uri())})
    except UpstoxError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@upstox_bp.get("/callback")
def callback():
    return handle_callback()


@upstox_bp.post("/disconnect")
def disconnect_route():
    disconnect()
    session.pop("upstox_oauth_state", None)
    return jsonify({"ok": True})
