"""
毎日の更新処理コア。
- エアドロップデータを最新化
- 更新ログを記録
- Gmail通知を送信 (SMTP or MCP)
"""

import json
import logging
import os
from datetime import datetime, timezone

import pytz

from config import AIRDROPS_FILE, UPDATES_FILE, DATA_DIR, GMAIL_RECIPIENT
from fetchers.airdrop_fetcher import fetch_all_airdrops
from fetchers.coingecko import get_trending_coins
from notifier.gmail import send_daily_report, send_hot_alert

logger = logging.getLogger(__name__)

JST = pytz.timezone("Asia/Tokyo")


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
    newly_hot = []

    for aid, new_a in new_ids.items():
        if aid in old_ids:
            old_a = old_ids[aid]
            diffs = []
            if old_a.get("status") != new_a.get("status"):
                diffs.append(f"ステータス: {old_a.get('status')} → {new_a.get('status')}")
            if old_a.get("estimated_value_usd") != new_a.get("estimated_value_usd"):
                diffs.append(
                    f"推定価値: ${old_a.get('estimated_value_usd', 0):,} → ${new_a.get('estimated_value_usd', 0):,}"
                )
            if old_a.get("difficulty") != new_a.get("difficulty"):
                diffs.append(f"難易度: {old_a.get('difficulty')} → {new_a.get('difficulty')}")
            if not old_a.get("is_hot") and new_a.get("is_hot"):
                newly_hot.append(new_a)
                diffs.append("🔥 ホット案件に追加")
            if diffs:
                changed.append({"name": new_a["name"], "changes": diffs})

    # 新規追加のホット案件も追加
    for a in added:
        if a.get("is_hot"):
            newly_hot.append(a)

    return {"added": added, "removed": removed, "changed": changed, "newly_hot": newly_hot}


def run_daily_update(force_email: bool = False) -> dict:
    """メイン更新処理。戻り値: 更新サマリーdict"""
    now = datetime.now(timezone.utc)
    now_jst = now.astimezone(JST)
    logger.info(f"=== 日次更新開始 {now_jst.strftime('%Y-%m-%d %H:%M JST')} ===")

    old_airdrops = _load_json(AIRDROPS_FILE, [])

    # データ取得
    logger.info("エアドロップデータを取得中...")
    new_airdrops, scraped_new = fetch_all_airdrops()

    logger.info("CoinGeckoトレンドを取得中...")
    try:
        trending = get_trending_coins()
    except Exception as e:
        logger.warning(f"CoinGeckoトレンド取得失敗: {e}")
        trending = []

    # 変更検出
    diff = _detect_changes(old_airdrops, new_airdrops)
    logger.info(
        f"変更検出: 追加{len(diff['added'])}件, 削除{len(diff['removed'])}件, "
        f"変更{len(diff['changed'])}件, 新規ホット{len(diff['newly_hot'])}件"
    )

    # 新規ホット案件アラートメール
    for airdrop in diff["newly_hot"]:
        logger.info(f"🚨 ホットアラート送信: {airdrop['name']}")
        send_hot_alert(airdrop)

    # データ保存
    _save_json(AIRDROPS_FILE, new_airdrops)
    logger.info(f"airdrops.jsonを更新 ({len(new_airdrops)}件)")

    # 更新ログ
    summary = {
        "timestamp": now.isoformat(),
        "date": now_jst.strftime("%Y-%m-%d"),
        "time_jst": now_jst.strftime("%Y年%m月%d日 %H:%M JST"),
        "total_airdrops": len(new_airdrops),
        "added_count": len(diff["added"]),
        "removed_count": len(diff["removed"]),
        "changed_count": len(diff["changed"]),
        "hot_count": sum(1 for a in new_airdrops if a.get("is_hot")),
        "newly_hot_count": len(diff["newly_hot"]),
        "added_names": [a["name"] for a in diff["added"]],
        "removed_names": diff["removed"],
        "changes": diff["changed"],
        "newly_hot_names": [a["name"] for a in diff["newly_hot"]],
        "trending_coins": [t["name"] for t in trending[:7]],
        "email_sent": False,
        "email_recipient": GMAIL_RECIPIENT,
    }

    updates_log = _load_json(UPDATES_FILE, [])
    updates_log.insert(0, summary)
    updates_log = updates_log[:30]  # 直近30件を保持
    _save_json(UPDATES_FILE, updates_log)

    # メール送信判定
    # 新着あり、またはホット案件変化、または強制送信
    should_email = force_email or diff["added"] or diff["newly_hot"] or diff["changed"]
    if should_email:
        logger.info(f"メール送信中... 宛先: {GMAIL_RECIPIENT}")
        sent = send_daily_report(
            new_airdrops, scraped_new, trending,
            changes=diff["changed"], removed=diff["removed"]
        )
        summary["email_sent"] = sent
        updates_log[0]["email_sent"] = sent
        _save_json(UPDATES_FILE, updates_log)

        if sent:
            logger.info(f"✅ メール送信成功: {GMAIL_RECIPIENT}")
        else:
            logger.warning("⚠️ メール送信失敗 (.envのGmail設定を確認してください)")
    else:
        logger.info("変更なし — メール送信スキップ")

    logger.info(
        f"=== 日次更新完了: 追加{len(diff['added'])}件, "
        f"変更{len(diff['changed'])}件, ホット{summary['hot_count']}件 ==="
    )
    return summary
