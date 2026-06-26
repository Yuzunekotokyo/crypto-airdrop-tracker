"""
Claude日次Web更新スクリプト。
このスクリプトはCronCreateによってClaudeが毎日呼び出す際に参照する。

使い方:
  python daily_web_update.py               # 通常更新
  python daily_web_update.py --force-email # メール強制送信
"""

import json
import os
import sys
import logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

from config import DATA_DIR, AIRDROPS_FILE, UPDATES_FILE
from updater import run_daily_update


def load_discovered():
    path = os.path.join(DATA_DIR, "discovered_airdrops.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_discovered(airdrops: list[dict]):
    path = os.path.join(DATA_DIR, "discovered_airdrops.json")
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(airdrops, f, ensure_ascii=False, indent=2)
    logger.info(f"discovered_airdrops.json を更新: {len(airdrops)} 件")


def main():
    force_email = "--force-email" in sys.argv
    logger.info("=== Claude日次Web更新開始 ===")

    # discovered_airdrops.json の鮮度チェック
    discovered = load_discovered()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    up_to_date = all(a.get("added_date") == today for a in discovered) if discovered else False

    if up_to_date:
        logger.info(f"discovered_airdrops.json は本日付け ({today}) — 追加スキップ")
    else:
        logger.info(f"discovered_airdrops.json の追加日: 更新必要 → Claudeがweb検索で更新済み")

    # メイン更新実行
    summary = run_daily_update(force_email=force_email, web_search_used=True)

    # 結果を表示
    print("\n" + "=" * 60)
    print(f"  日次更新完了 — {summary['time_jst']}")
    print("=" * 60)
    print(f"  総件数   : {summary['total_airdrops']} 件")
    print(f"  ホット   : {summary['hot_count']} 件")
    print(f"  新着追加 : {summary['added_count']} 件")
    print(f"  変更     : {summary['changed_count']} 件")
    if summary.get("top_hot_names"):
        print(f"  注目案件 : {', '.join(summary['top_hot_names'])}")
    if summary.get("trending_coins"):
        print(f"  トレンド : {', '.join(summary['trending_coins'])}")
    print(f"  メール   : {'送信済' if summary.get('email_sent') else '未送信'}")
    print("=" * 60)

    return summary


if __name__ == "__main__":
    main()
