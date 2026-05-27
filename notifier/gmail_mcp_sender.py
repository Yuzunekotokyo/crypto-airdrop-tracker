"""
Gmail MCP経由でメール下書きを作成するモジュール。
Claude Code環境で実行される際に使用。
Gmail MCPが使えない場合はSMTPフォールバック。
"""

import json
import logging
import subprocess
import sys
from datetime import datetime

logger = logging.getLogger(__name__)


def build_email_html(airdrops: list[dict], new_items: list[str], trending: list[dict],
                     changes: list[dict] = None, removed: list[str] = None) -> tuple[str, str]:
    """
    メール用HTMLとプレーンテキストを生成する。
    Returns: (subject, html_body)
    """
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    hot_count = len(hot)

    subject = f"🪂 [{today}] Airdrop更新レポート — 🔥ホット{hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"

    # 新着セクション
    new_html = ""
    if new_items:
        items_html = "".join(f"<li style='margin:4px 0;'>{n}</li>" for n in new_items[:10])
        new_html = f"""
        <div style="background:#1a3a1a;border-left:4px solid #2ed573;padding:14px 18px;margin:16px 0;border-radius:6px;">
          <div style="color:#2ed573;font-weight:700;font-size:15px;margin-bottom:8px;">🆕 新着エアドロップ {len(new_items)}件</div>
          <ul style="margin:0;padding-left:20px;color:#c8f7c5;">{items_html}</ul>
        </div>"""

    # 変更セクション
    changed_html = ""
    if changes:
        change_items = ""
        for c in changes[:5]:
            ch_list = "".join(f"<li style='color:#ffd700;font-size:12px;'>{ch}</li>" for ch in c.get("changes", []))
            change_items += f"<li style='margin:6px 0;'><strong>{c['name']}</strong><ul>{ch_list}</ul></li>"
        changed_html = f"""
        <div style="background:#2a2500;border-left:4px solid #ffa502;padding:14px 18px;margin:16px 0;border-radius:6px;">
          <div style="color:#ffa502;font-weight:700;font-size:15px;margin-bottom:8px;">✏️ 情報更新 {len(changes)}件</div>
          <ul style="margin:0;padding-left:20px;color:#e8e0b0;">{change_items}</ul>
        </div>"""

    # ホット案件テーブル
    hot_rows = ""
    for a in hot[:5]:
        diff_color = {"easy": "#2ed573", "medium": "#ff6348", "hard": "#ff4757"}.get(
            a.get("difficulty", "easy"), "#888"
        )
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        hot_rows += f"""
        <tr>
          <td style="padding:12px;border-bottom:1px solid #2e3460;vertical-align:top;">
            <div style="font-weight:700;color:#e8eaf6;">{a['name']}</div>
            <div style="color:#9fa8da;font-size:12px;margin-top:2px;">{a.get('category', '')}</div>
          </td>
          <td style="padding:12px;border-bottom:1px solid #2e3460;color:#2ed573;font-weight:800;font-size:16px;">{value}</td>
          <td style="padding:12px;border-bottom:1px solid #2e3460;">
            <span style="background:{diff_color}22;color:{diff_color};border:1px solid {diff_color};padding:3px 8px;border-radius:12px;font-size:11px;font-weight:700;">
              {a.get('difficulty', '').upper()}
            </span>
          </td>
          <td style="padding:12px;border-bottom:1px solid #2e3460;color:#9fa8da;font-size:13px;">{a.get('end_date', '未定')}</td>
          <td style="padding:12px;border-bottom:1px solid #2e3460;">
            <a href="{a.get('url', '#')}" style="background:linear-gradient(135deg,#7c4dff,#651fff);color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:700;">参加する</a>
          </td>
        </tr>"""

    # トレンドコイン
    trending_html = ""
    if trending:
        t_items = "".join(
            f"""<li style="margin:6px 0;color:#c0c8f0;">
              <strong style="color:#e8eaf6;">{t['name']}</strong>
              <span style="color:#9fa8da;"> ({t.get('symbol', '')})</span>
              <span style="color:#ffa502;"> — スコア: {t.get('score', 0)}</span>
            </li>"""
            for t in trending[:7]
        )
        trending_html = f"""
        <div style="margin-top:24px;">
          <h3 style="color:#7c4dff;font-size:16px;margin-bottom:12px;">📈 CoinGeckoトレンドコイン</h3>
          <ul style="padding-left:20px;">{t_items}</ul>
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;background:#0f0f1a;color:#e8eaf6;margin:0;padding:20px;">

  <div style="max-width:720px;margin:0 auto;">

    <!-- ヘッダー -->
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:28px;border-radius:12px 12px 0 0;border-bottom:2px solid #7c4dff;">
      <h1 style="margin:0;font-size:24px;background:linear-gradient(135deg,#fff,#7c4dff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
        🪂 Crypto Airdrop Tracker
      </h1>
      <p style="margin:6px 0 0;color:#9fa8da;font-size:14px;">{today} 自動更新レポート</p>
    </div>

    <!-- メインコンテンツ -->
    <div style="background:#16213e;padding:24px;border-radius:0 0 12px 12px;border:1px solid #2e3460;border-top:none;">

      <!-- 統計 -->
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px;">
        <div style="background:#1e2240;border:1px solid #2e3460;padding:12px 18px;border-radius:8px;text-align:center;">
          <div style="color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:1px;">合計</div>
          <div style="color:#1e90ff;font-size:22px;font-weight:800;">{len(airdrops)}</div>
          <div style="color:#9fa8da;font-size:11px;">件</div>
        </div>
        <div style="background:#1e2240;border:1px solid #ff475722;padding:12px 18px;border-radius:8px;text-align:center;">
          <div style="color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:1px;">🔥 HOT</div>
          <div style="color:#ff4757;font-size:22px;font-weight:800;">{hot_count}</div>
          <div style="color:#9fa8da;font-size:11px;">件</div>
        </div>
        <div style="background:#1e2240;border:1px solid #2ed57322;padding:12px 18px;border-radius:8px;text-align:center;">
          <div style="color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:1px;">🆕 新着</div>
          <div style="color:#2ed573;font-size:22px;font-weight:800;">{len(new_items)}</div>
          <div style="color:#9fa8da;font-size:11px;">件</div>
        </div>
        <div style="background:#1e2240;border:1px solid #ffa50222;padding:12px 18px;border-radius:8px;text-align:center;">
          <div style="color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:1px;">✏️ 変更</div>
          <div style="color:#ffa502;font-size:22px;font-weight:800;">{len(changes) if changes else 0}</div>
          <div style="color:#9fa8da;font-size:11px;">件</div>
        </div>
      </div>

      {new_html}
      {changed_html}

      <!-- ホット案件 -->
      <h3 style="color:#ff4757;font-size:17px;margin:20px 0 12px;">🔥 今狙うべき注目エアドロップ</h3>
      <table style="width:100%;border-collapse:collapse;background:#1e2240;border-radius:8px;overflow:hidden;">
        <thead>
          <tr style="background:#252b4a;">
            <th style="padding:12px;text-align:left;color:#9fa8da;font-size:12px;text-transform:uppercase;">プロジェクト</th>
            <th style="padding:12px;text-align:left;color:#9fa8da;font-size:12px;text-transform:uppercase;">推定価値</th>
            <th style="padding:12px;text-align:left;color:#9fa8da;font-size:12px;text-transform:uppercase;">難易度</th>
            <th style="padding:12px;text-align:left;color:#9fa8da;font-size:12px;text-transform:uppercase;">期限</th>
            <th style="padding:12px;text-align:left;color:#9fa8da;font-size:12px;text-transform:uppercase;">参加</th>
          </tr>
        </thead>
        <tbody>{hot_rows if hot_rows else '<tr><td colspan="5" style="padding:20px;text-align:center;color:#9fa8da;">現在ホット案件なし</td></tr>'}</tbody>
      </table>

      {trending_html}

      <hr style="border:none;border-top:1px solid #2e3460;margin:24px 0;">
      <p style="color:#6c757d;font-size:11px;text-align:center;margin:0;">
        🪂 Crypto Airdrop Tracker — 自動送信メール<br>
        投資は自己責任で行ってください。掲載情報は参考目的のみです。
      </p>
    </div>

  </div>
</body>
</html>"""

    return subject, html


def create_gmail_draft(airdrops: list[dict], new_items: list[str], trending: list[dict],
                       recipient: str, changes: list[dict] = None, removed: list[str] = None) -> bool:
    """
    Gmail MCPを使ってメール下書きを作成。
    Claude Code環境でのみ動作。
    Returns: True if draft created, False otherwise.
    """
    subject, html_body = build_email_html(airdrops, new_items, trending, changes, removed)

    # Gmail MCP呼び出し用のスクリプトを生成
    # このデータをファイルに保存して、Claude Codeが読み取れるようにする
    draft_data = {
        "to": recipient,
        "subject": subject,
        "html_body": html_body,
        "timestamp": datetime.now().isoformat(),
    }

    draft_file = "/tmp/gmail_draft_pending.json"
    try:
        with open(draft_file, "w", encoding="utf-8") as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Gmail下書きデータを保存: {draft_file}")
        return True
    except Exception as e:
        logger.error(f"Gmail下書きデータ保存失敗: {e}")
        return False
