"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してメール送信。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)


def _build_html_body(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    diff: dict | None = None,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    diff = diff or {}

    # ===== 新着セクション =====
    new_html = ""
    if new_items:
        items_html = "".join(f"<li>{n}</li>" for n in new_items)
        new_html = f"""
        <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>🆕 新着エアドロップ ({len(new_items)}件)</strong>
          <ul style="margin:8px 0 0 0;">{items_html}</ul>
        </div>"""

    # ===== 変更セクション =====
    changes_html = ""
    changed = diff.get("changed", [])
    if changed:
        changed_rows = "".join(
            f"<li><strong>{c['name']}</strong>: {' / '.join(c['changes'])}</li>"
            for c in changed
        )
        changes_html = f"""
        <div style="background:#cce5ff;border-left:4px solid #004085;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>✏️ ステータス・価値の変更 ({len(changed)}件)</strong>
          <ul style="margin:8px 0 0 0;">{changed_rows}</ul>
        </div>"""

    # ===== 終了・削除セクション =====
    removed_html = ""
    removed = diff.get("removed", [])
    if removed:
        removed_items = "".join(f"<li>{n}</li>" for n in removed)
        removed_html = f"""
        <div style="background:#f8d7da;border-left:4px solid #721c24;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>🗑️ 終了・削除 ({len(removed)}件)</strong>
          <ul style="margin:8px 0 0 0;">{removed_items}</ul>
        </div>"""

    # ===== ホット案件テーブル =====
    hot_rows = ""
    for a in hot[:5]:
        difficulty_color = {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}.get(
            a.get("difficulty", "easy"), "#6c757d"
        )
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "不明"
        hot_rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <strong>{a['name']}</strong><br>
            <span style="color:#6c757d;font-size:12px;">{a.get('category','')}</span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:bold;">{value}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <span style="background:{difficulty_color};color:white;padding:2px 8px;border-radius:12px;font-size:12px;">
              {a.get('difficulty','').upper()}
            </span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">{a.get('end_date','未定')}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <a href="{a.get('url','#')}" style="color:#0d6efd;">参加する</a>
          </td>
        </tr>"""

    # ===== トレンドコイン =====
    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li><strong>{t['name']}</strong> ({t['symbol']}) — スコア: {t.get('score', 0)}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#6f42c1;">📈 CoinGecko トレンドコイン</h3>
        <ul>{t_items}</ul>"""

    total = len(airdrops)
    hot_count = len(hot)

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;background:#f8f9fa;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:24px;border-radius:8px 8px 0 0;">
    <h1 style="margin:0;font-size:22px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:4px 0 0;opacity:0.8;">{today} 日次更新レポート</p>
  </div>
  <div style="background:white;padding:24px;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">

    <!-- サマリー -->
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px;">
      <div style="background:#e8f4fd;border-radius:8px;padding:12px 20px;text-align:center;">
        <div style="font-size:24px;font-weight:bold;color:#1e90ff;">{total}</div>
        <div style="font-size:12px;color:#666;">総案件数</div>
      </div>
      <div style="background:#fff0f0;border-radius:8px;padding:12px 20px;text-align:center;">
        <div style="font-size:24px;font-weight:bold;color:#dc3545;">{hot_count}</div>
        <div style="font-size:12px;color:#666;">🔥 ホット案件</div>
      </div>
      <div style="background:#f0fff4;border-radius:8px;padding:12px 20px;text-align:center;">
        <div style="font-size:24px;font-weight:bold;color:#28a745;">{len(new_items)}</div>
        <div style="font-size:12px;color:#666;">🆕 新着</div>
      </div>
      <div style="background:#fffbe6;border-radius:8px;padding:12px 20px;text-align:center;">
        <div style="font-size:24px;font-weight:bold;color:#fd7e14;">{len(changed)}</div>
        <div style="font-size:12px;color:#666;">✏️ 変更</div>
      </div>
    </div>

    {new_html}
    {changes_html}
    {removed_html}

    <h3 style="color:#dc3545;">🔥 注目のホットエアドロップ TOP5</h3>
    <table style="width:100%;border-collapse:collapse;margin-top:8px;">
      <thead>
        <tr style="background:#f8f9fa;">
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">プロジェクト</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">推定価値</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">難易度</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">期限</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">リンク</th>
        </tr>
      </thead>
      <tbody>{hot_rows}</tbody>
    </table>

    {trending_html}

    <hr style="margin:24px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:12px;margin:0;">
      ※ このメールはCrypto Airdrop Trackerから自動送信されています (毎日8:00 JST)。<br>
      投資は自己責任で行ってください。情報は参考目的のみです。
    </p>
  </div>
</body>
</html>"""


def send_daily_report(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    diff: dict | None = None,
) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    diff = diff or {}
    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    changed_count = len(diff.get("changed", []))
    removed_count = len(diff.get("removed", []))

    subject = f"[Airdrop日報] {today} — 🔥ホット{hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"
    if changed_count:
        subject += f" ✏️変更{changed_count}件"
    if removed_count:
        subject += f" 🗑️終了{removed_count}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, diff)
    plain_body = (
        f"{today} Airdrop日次レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"変更: {changed_count}件\n"
        f"終了: {removed_count}件\n"
        f"トレンド: {', '.join(t['name'] for t in trending[:5])}"
    )

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"日次レポート送信成功: {GMAIL_RECIPIENT}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗。アプリパスワードを確認してください。")
        return False
    except Exception as e:
        logger.error(f"メール送信失敗: {e}")
        return False


def send_hot_alert(airdrop: dict) -> bool:
    """注目案件出現時の即時アラート (ホット案件追加時に即送信)"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        return False

    name = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd", 0)
    subject = f"🚨 [HOT Airdrop速報] {name} — 推定${value:,}の新案件が登場！今すぐ確認を"

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#dc3545,#ff6b81);color:white;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;">🚨 ホットエアドロップ速報！</h2>
    <p style="margin:4px 0 0;opacity:0.9;">注目の高収益案件が新たに追加されました</p>
  </div>
  <div style="background:white;padding:20px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 8px 8px;">
    <div style="background:#fff3cd;border-radius:8px;padding:16px;margin-bottom:16px;">
      <h3 style="margin:0 0 8px;">{name}
        {f'<span style="font-size:14px;color:#666;">({airdrop.get("symbol","")})</span>' if airdrop.get("symbol") else ""}
      </h3>
      <p style="margin:0;font-size:22px;font-weight:bold;color:#28a745;">推定 ~${value:,}</p>
    </div>
    <table style="width:100%;border-collapse:collapse;">
      <tr><td style="padding:8px;border-bottom:1px solid #eee;color:#666;width:100px;">カテゴリ</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{airdrop.get('category','')}</td></tr>
      <tr><td style="padding:8px;border-bottom:1px solid #eee;color:#666;">難易度</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{airdrop.get('difficulty','').upper()}</td></tr>
      <tr><td style="padding:8px;border-bottom:1px solid #eee;color:#666;">期限</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{airdrop.get('end_date','未定')}</td></tr>
    </table>
    <p style="margin:16px 0 8px;"><strong>📋 概要:</strong> {airdrop.get('description','')}</p>
    <p style="margin:0 0 8px;"><strong>参加方法:</strong></p>
    <ul>{"".join(f"<li>{t}</li>" for t in airdrop.get('tasks', []))}</ul>
    <div style="text-align:center;margin-top:20px;">
      <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#ff6b81);color:white;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:16px;">
        🚀 今すぐ参加する
      </a>
    </div>
    <hr style="margin:20px 0;">
    <p style="color:#6c757d;font-size:12px;">投資は自己責任で行ってください。Crypto Airdrop Trackerより自動送信。</p>
  </div>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"ホットアラート送信: {name}")
        return True
    except Exception as e:
        logger.error(f"ホットアラート送信失敗: {e}")
        return False
