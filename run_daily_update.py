#!/usr/bin/env python3
"""
毎日の更新スクリプト。
GitHub ActionsまたはCronジョブから直接呼び出せる。

使い方:
  python run_daily_update.py              # 通常更新
  python run_daily_update.py --force      # メール強制送信
  python run_daily_update.py --test-email # テストメール送信
"""

import argparse
import json
import logging
import os
import sys

# パスをプロジェクトルートに設定
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Crypto Airdrop Tracker 日次更新")
    parser.add_argument("--force", action="store_true", help="変更なしでもメールを強制送信")
    parser.add_argument("--test-email", action="store_true", help="テストメールを送信して設定確認")
    parser.add_argument("--no-email", action="store_true", help="メール送信をスキップ")
    args = parser.parse_args()

    # 環境変数から force_email を読み取る (GitHub Actions用)
    force_email = args.force or os.getenv("FORCE_EMAIL", "false").lower() == "true"

    if args.test_email:
        logger.info("=== テストメール送信モード ===")
        from notifier.gmail import _send_email
        sent = _send_email(
            subject="🧪 [テスト] Crypto Airdrop Tracker 設定確認",
            html_body="""
            <div style="font-family:Arial,sans-serif;padding:20px;">
              <h2 style="color:#7c4dff;">✅ メール設定が正常に動作しています</h2>
              <p>Crypto Airdrop Trackerからのテストメールです。</p>
              <p>このメールが届いていれば、Gmail SMTP設定は正常です。</p>
              <hr>
              <p style="color:#999;font-size:12px;">毎日 08:00 JST に自動でアップデートレポートが送信されます。</p>
            </div>""",
            plain_body="テストメール: Crypto Airdrop Tracker の設定が正常です。",
        )
        if sent:
            logger.info("✅ テストメール送信成功！")
            sys.exit(0)
        else:
            logger.error("❌ テストメール送信失敗。.envのGmail設定を確認してください。")
            sys.exit(1)

    logger.info("=" * 50)
    logger.info("🪂 Crypto Airdrop Tracker 日次更新開始")
    logger.info("=" * 50)

    try:
        from updater import run_daily_update

        # no-emailオプションの場合、GMAIL_APP_PASSWORDを無効化
        if args.no_email:
            os.environ["GMAIL_APP_PASSWORD"] = ""
            logger.info("メール送信スキップモード")

        summary = run_daily_update(force_email=force_email)

        # 結果サマリー表示
        print("\n" + "=" * 50)
        print("📊 更新結果サマリー")
        print("=" * 50)
        print(f"  更新時刻: {summary['time_jst']}")
        print(f"  合計件数: {summary['total_airdrops']} 件")
        print(f"  🔥 ホット: {summary['hot_count']} 件")
        print(f"  🆕 新着: {summary['added_count']} 件")
        print(f"  ✏️  変更: {summary['changed_count']} 件")
        print(f"  🗑️  削除: {summary['removed_count']} 件")
        print(f"  📧 メール: {'✅ 送信済 → ' + summary.get('email_recipient', '') if summary['email_sent'] else '⏭️  スキップ'}")

        if summary["added_names"]:
            print(f"  新着案件: {', '.join(summary['added_names'][:5])}")
        if summary.get("newly_hot_names"):
            print(f"  🚨 新HOT: {', '.join(summary['newly_hot_names'])}")
        if summary["trending_coins"]:
            print(f"  📈 トレンド: {', '.join(summary['trending_coins'][:5])}")
        print("=" * 50)

        # GitHub ActionsのSTEP_SUMMARYに出力
        summary_file = os.getenv("GITHUB_STEP_SUMMARY")
        if summary_file:
            with open(summary_file, "a", encoding="utf-8") as f:
                f.write(f"\n### 更新完了: {summary['time_jst']}\n")
                f.write(f"- 合計 **{summary['total_airdrops']}件** / ホット **{summary['hot_count']}件**\n")
                if summary["added_names"]:
                    f.write(f"- 新着: {', '.join(summary['added_names'])}\n")

        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ 更新エラー: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
