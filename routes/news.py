from flask import Blueprint, jsonify, request

from models.news import NewsError, get_economy_news


news_bp = Blueprint("news", __name__)


@news_bp.get("/economy")
def economy_news():
    force_refresh = request.args.get("refresh", "0") == "1"
    try:
        items = get_economy_news(force_refresh=force_refresh)
        return jsonify({"ok": True, "items": items})
    except NewsError as exc:
        return jsonify({"ok": False, "items": [], "error": str(exc)}), 503
