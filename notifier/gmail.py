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
    diff: dict = None,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]

    # 新着セクション
    new_html = ""
    if new_items:
        items_html = "".join(f"<li>{n}</li>" for n in new_items)
        new_html = f"""
        <div style="background:#e8f5e9;border-left:4px solid #4caf50;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>🆕 新着エアドロップ ({len(new_items)}件)</strong>
          <ul style="margin:8px 0 0 0;">{items_html}</ul>
        </div>"""

    # 変更セクション
    changes_html = ""
    if diff and diff.get("changed"):
        rows = ""
        for item in diff["changed"]:
            changes_str = " / ".join(item.get("changes", []))
            rows += f"""
            <tr>
              <td style="padding:8px 12px;border-bottom:1px solid #dee2e6;font-weight:bold;">{item['name']}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #dee2e6;color:#e65100;">{changes_str}</td>
            </tr>"""
        changes_html = f"""
        <div style="margin:16px 0;">
          <h4 style="color:#f57c00;margin:0 0 8px;">✏️ 更新内容 ({len(diff['changed'])}件)</h4>
          <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead>
              <tr style="background:#fff8e1;">
                <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #ffe0b2;">プロジェクト</th>
                <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #ffe0b2;">変更内容</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>"""

    # 削除セクション
    removed_html = ""
    if diff and diff.get("removed"):
        items_html = "".join(
            f'<span style="background:#ffebee;color:#c62828;padding:3px 10px;border-radius:12px;font-size:12px;margin:2px;">{n}</span>'
            for n in diff["removed"]
        )
        removed_html = f"""
        <div style="background:#ffebee;border-left:4px solid #ef5350;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>❌ 終了/削除 ({len(diff['removed'])}件):</strong>
          <div style="margin-top:6px;">{items_html}</div>
        </div>"""

    # ホットエアドロップ一覧
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

    # トレンドコイン
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
    <p style="margin:4px 0 0;opacity:0.8;">{today} 更新レポート</p>
    <div style="margin-top:12px;display:flex;gap:12px;flex-wrap:wrap;">
      <span style="background:rgba(255,255,255,0.15);padding:4px 12px;border-radius:20px;font-size:13px;">
        📋 総数: <strong>{total}件</strong>
      </span>
      <span style="background:rgba(255,71,87,0.3);padding:4px 12px;border-radius:20px;font-size:13px;">
        🔥 ホット: <strong>{hot_count}件</strong>
      </span>
      {f'<span style="background:rgba(76,175,80,0.3);padding:4px 12px;border-radius:20px;font-size:13px;">🆕 新着: <strong>{len(new_items)}件</strong></span>' if new_items else ''}
      {f'<span style="background:rgba(255,152,0,0.3);padding:4px 12px;border-radius:20px;font-size:13px;">✏️ 変更: <strong>{len(diff["changed"])}件</strong></span>' if diff and diff.get("changed") else ''}
    </div>
  </div>
  <div style="background:white;padding:24px;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
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
    diff: dict = None,
) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))

    parts = [f"[Airdrop] {today} 更新"]
    parts.append(f"🔥ホット{hot_count}件")
    if new_items:
        parts.append(f"🆕新着{len(new_items)}件")
    if diff and diff.get("changed"):
        parts.append(f"✏️変更{len(diff['changed'])}件")
    if diff and diff.get("removed"):
        parts.append(f"❌削除{len(diff['removed'])}件")
    subject = " — ".join(parts)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, diff=diff)
    changes_text = ""
    if diff and diff.get("changed"):
        changes_text = "\n変更: " + ", ".join(c["name"] for c in diff["changed"])
    if diff and diff.get("removed"):
        changes_text += "\n削除: " + ", ".join(diff["removed"])
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}"
        f"{changes_text}"
    )

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"メール送信成功: {GMAIL_RECIPIENT}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗。アプリパスワードを確認してください。")
        return False
    except Exception as e:
        logger.error(f"メール送信失敗: {e}")
        return False


def send_hot_alert(airdrop: dict) -> bool:
    """注目案件出現時の即時アラート"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        return False

    name = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd", 0)
    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,}の新案件が登場！"

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:#dc3545;color:white;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;">🚨 ホットエアドロップ出現！</h2>
    <p style="margin:6px 0 0;opacity:0.9;">新しい高価値案件が追加されました</p>
  </div>
  <div style="background:white;padding:20px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 8px 8px;">
    <h3>{name} ({airdrop.get('symbol','')})</h3>
    <p><strong>推定価値:</strong> <span style="color:#28a745;font-size:18px;font-weight:bold;">~${value:,}</span></p>
    <p><strong>カテゴリ:</strong> {airdrop.get('category','')}</p>
    <p><strong>難易度:</strong> {airdrop.get('difficulty','').upper()}</p>
    <p><strong>概要:</strong> {airdrop.get('description','')}</p>
    <p><strong>参加方法:</strong></p>
    <ul>{"".join(f"<li>{t}</li>" for t in airdrop.get('tasks', []))}</ul>
    <p><strong>期限:</strong> {airdrop.get('end_date','未定')}</p>
    <a href="{airdrop.get('url','#')}" style="display:inline-block;background:#dc3545;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold;margin-top:8px;">今すぐ参加する →</a>
    <hr style="margin:20px 0;">
    <p style="color:#6c757d;font-size:12px;">投資は自己責任で行ってください。</p>
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
