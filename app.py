"""
Crypto Airdrop Tracker — Flask メインアプリケーション
"""

import json
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, render_template, request

JST = ZoneInfo("Asia/Tokyo")

from config import AIRDROPS_FILE, UPDATES_FILE
from scheduler import start_scheduler
from updater import run_daily_update

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)


def _load_json(path: str, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


@app.route("/")
def index():
    airdrops = _load_json(AIRDROPS_FILE, [])
    updates = _load_json(UPDATES_FILE, [])
    latest_update = updates[0] if updates else None
    return render_template(
        "index.html",
        airdrops=airdrops,
        latest_update=latest_update,
        updates=updates[:5],
        now=datetime.now(JST).strftime("%Y年%m月%d日 %H:%M"),
    )


@app.route("/api/airdrops")
def api_airdrops():
    airdrops = _load_json(AIRDROPS_FILE, [])
    status = request.args.get("status")
    category = request.args.get("category")
    hot = request.args.get("hot")
    if status:
        airdrops = [a for a in airdrops if a.get("status") == status]
    if category:
        airdrops = [a for a in airdrops if a.get("category") == category]
    if hot == "1":
        airdrops = [a for a in airdrops if a.get("is_hot")]
    return jsonify(airdrops)


@app.route("/api/updates")
def api_updates():
    updates = _load_json(UPDATES_FILE, [])
    return jsonify(updates[:10])


@app.route("/api/trigger-update", methods=["POST"])
def trigger_update():
    """手動で更新をトリガー (開発・管理用)"""
    force_email = request.json.get("force_email", False) if request.is_json else False
    summary = run_daily_update(force_email=force_email)
    return jsonify({"status": "ok", "summary": summary})


if __name__ == "__main__":
    os.makedirs(os.path.dirname(AIRDROPS_FILE), exist_ok=True)

    # 初回データが無い場合は即座に更新
    if not os.path.exists(AIRDROPS_FILE):
        logger.info("初回データ取得中...")
        run_daily_update()

    # 定期スケジューラ起動
    start_scheduler()

    app.run(debug=False, host="0.0.0.0", port=5000)
