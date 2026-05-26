"""
毎日の更新処理コア。
- エアドロップデータを最新化
- 更新ログを記録
- Gmail通知を送信 (毎日必ず + 新ホット案件は即時アラート)
"""

import json
import logging
import os
from datetime import datetime, timezone, timedelta

from config import AIRDROPS_FILE, UPDATES_FILE, DATA_DIR
from fetchers.airdrop_fetcher import fetch_all_airdrops
from fetchers.coingecko import get_trending_coins
from notifier.gmail import send_daily_report, send_hot_alert

logger = logging.getLogger(__name__)


def _load_json(path: str, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def _save_json(path: str, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _detect_changes(old_airdrops: list[dict], new_airdrops: list[dict]) -> dict:
    old_ids = {a["id"]: a for a in old_airdrops}
    new_ids = {a["id"]: a for a in new_airdrops}

    added = [a for aid, a in new_ids.items() if aid not in old_ids]
    removed = [a["name"] for aid, a in old_ids.items() if aid not in new_ids]
    changed = []

    for aid, new_a in new_ids.items():
        if aid in old_ids:
            old_a = old_ids[aid]
            diffs = []
            if old_a.get("status") != new_a.get("status"):
                diffs.append(
                    f"ステータス変更: {old_a.get('status','?')} → {new_a.get('status','?')}"
                )
            if old_a.get("estimated_value_usd") != new_a.get("estimated_value_usd"):
                old_v = old_a.get("estimated_value_usd", 0)
                new_v = new_a.get("estimated_value_usd", 0)
                if old_v and new_v:
                    direction = "↑" if new_v > old_v else "↓"
                    diffs.append(
                        f"推定価値 {direction}: ${old_v:,} → ${new_v:,}"
                    )
            if not old_a.get("is_hot") and new_a.get("is_hot"):
                diffs.append("🔥 HOT案件に昇格！")
            if diffs:
                changed.append({"name": new_a["name"], "changes": diffs})

    return {"added": added, "removed": removed, "changed": changed}


def _was_email_sent_today(updates_log: list[dict]) -> bool:
    """本日すでに日次メールを送信済みかチェック"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for upd in updates_log[:5]:
        if upd.get("date") == today and upd.get("email_sent"):
            return True
    return False


def run_daily_update(force_email: bool = False) -> dict:
    """メイン更新処理。戻り値: 更新サマリーdict"""
    now = datetime.now(timezone.utc)
    # JSTに変換 (UTC+9)
    jst = now + timedelta(hours=9)
    logger.info(f"=== 日次更新開始 {jst.strftime('%Y-%m-%d %H:%M')} JST ===")

    old_airdrops = _load_json(AIRDROPS_FILE, [])
    updates_log = _load_json(UPDATES_FILE, [])

    # データ取得
    new_airdrops, scraped_new = fetch_all_airdrops()
    trending = get_trending_coins()

    # 変更検出
    diff = _detect_changes(old_airdrops, new_airdrops)

    # 新規ホット案件: 即時アラートメール
    newly_hot = [a for a in diff["added"] if a.get("is_hot")]
    for airdrop in newly_hot:
        try:
            send_hot_alert(airdrop)
        except Exception as e:
            logger.error(f"ホットアラート送信エラー: {e}")

    # データ保存
    _save_json(AIRDROPS_FILE, new_airdrops)

    # 更新ログ
    summary = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time_jst": jst.strftime("%Y年%m月%d日 %H:%M"),
        "total_airdrops": len(new_airdrops),
        "added_count": len(diff["added"]),
        "removed_count": len(diff["removed"]),
        "changed_count": len(diff["changed"]),
        "hot_count": sum(1 for a in new_airdrops if a.get("is_hot")),
        "added_names": [a["name"] for a in diff["added"]],
        "removed_names": diff["removed"],
        "changes": diff["changed"],
        "trending_coins": [t["name"] for t in trending[:5]],
        "newly_hot": [a["name"] for a in newly_hot],
        "email_sent": False,
    }

    updates_log.insert(0, summary)
    updates_log = updates_log[:30]
    _save_json(UPDATES_FILE, updates_log)

    # メール送信判断:
    #   - force_email=True の場合は強制送信
    #   - 新着・ホット案件変化があれば送信
    #   - 毎日1回は必ず送信（本日未送信の場合）
    already_sent_today = _was_email_sent_today(updates_log[1:])  # 直前の記録を確認
    should_email = (
        force_email
        or bool(diff["added"])
        or bool(newly_hot)
        or bool(diff["changed"])
        or not already_sent_today
    )

    if should_email:
        try:
            sent = send_daily_report(new_airdrops, scraped_new, trending, diff)
            summary["email_sent"] = sent
            updates_log[0]["email_sent"] = sent
            _save_json(UPDATES_FILE, updates_log)
            if sent:
                logger.info(f"日次メール送信成功")
        except Exception as e:
            logger.error(f"日次メール送信エラー: {e}")

    logger.info(
        f"=== 日次更新完了: 全{len(new_airdrops)}件 / "
        f"追加{len(diff['added'])}件 / 変更{len(diff['changed'])}件 / "
        f"メール={'送信済' if summary['email_sent'] else 'スキップ'} ==="
    )
    return summary
