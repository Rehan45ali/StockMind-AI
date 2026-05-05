from flask import Blueprint, jsonify, request, session

from models.demo import (
    DemoAccountError,
    authenticate_demo,
    demo_session_active,
    get_demo_status,
)


demo_bp = Blueprint("demo", __name__)


@demo_bp.get("/status")
def status():
    return jsonify(get_demo_status(demo_session_active(session)))


@demo_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    try:
        authenticate_demo(username, password)
        session["demo_logged_in"] = True
        return jsonify(get_demo_status(True))
    except DemoAccountError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 401


@demo_bp.post("/logout")
def logout():
    session.pop("demo_logged_in", None)
    return jsonify(get_demo_status(False))
