"""
Crypto Airdrop Tracker — Flask メインアプリケーション
"""

import json
import logging
import os
from datetime import datetime

from flask import Flask, jsonify, render_template, request

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
        now=datetime.now().strftime("%Y年%m月%d日 %H:%M"),
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


@app.route("/api/pending-email")
def pending_email():
    """Gmail MCPでの送信用: 未送信メール内容を返す"""
    import os
    from config import DATA_DIR
    pending_path = os.path.join(DATA_DIR, "pending_email.json")
    if not os.path.exists(pending_path):
        return jsonify({"status": "none", "message": "未送信メールなし"})
    try:
        with open(pending_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"status": "pending", **data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/pending-email/mark-sent", methods=["POST"])
def mark_email_sent():
    """Gmail MCPでの送信完了後に呼び出す"""
    from config import DATA_DIR
    pending_path = os.path.join(DATA_DIR, "pending_email.json")
    if os.path.exists(pending_path):
        os.remove(pending_path)
        updates = _load_json(UPDATES_FILE, [])
        if updates:
            updates[0]["email_sent"] = True
            os.makedirs(os.path.dirname(UPDATES_FILE), exist_ok=True)
            with open(UPDATES_FILE, "w", encoding="utf-8") as f:
                json.dump(updates, f, ensure_ascii=False, indent=2)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    os.makedirs(os.path.dirname(AIRDROPS_FILE), exist_ok=True)

    # 初回データが無い場合は即座に更新
    if not os.path.exists(AIRDROPS_FILE):
        logger.info("初回データ取得中...")
        run_daily_update()

    # 定期スケジューラ起動
    start_scheduler()

    app.run(debug=False, host="0.0.0.0", port=5000)
