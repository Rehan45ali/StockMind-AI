from flask import Flask, render_template

from config import APP
from routes.account import account_bp
from routes.demo import demo_bp
from routes.market import market_bp
from routes.news import news_bp
from routes.upstox import handle_callback, upstox_bp


app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = APP["secret_key"]
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.register_blueprint(market_bp, url_prefix="/api/market")
app.register_blueprint(account_bp, url_prefix="/api/account")
app.register_blueprint(demo_bp, url_prefix="/api/demo")
app.register_blueprint(news_bp, url_prefix="/api/news")
app.register_blueprint(upstox_bp, url_prefix="/api/upstox")


@app.route("/")
def index():
    return render_template("index.html", app_name=APP["name"])


@app.route("/upstox/callback")
def upstox_callback():
    return handle_callback()


@app.get("/health")
def health():
    return {"ok": True, "app": APP["name"]}


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=APP["port"],
        debug=APP["debug"],
    )
