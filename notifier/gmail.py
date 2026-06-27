"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してメール送信。
Gmail MCP未対応の場合はdraftを作成。
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

    # 新着セクション
    new_html = ""
    if new_items:
        items_html = "".join(f"<li>{n}</li>" for n in new_items)
        new_html = f"""
        <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>🆕 新着エアドロップ ({len(new_items)}件)</strong>
          <ul style="margin:8px 0 0 0;">{items_html}</ul>
        </div>"""

    # HOT昇格セクション
    newly_hot_html = ""
    newly_hot_names = diff.get("newly_hot_names") or [
        a["name"] for a in diff.get("newly_hot", [])
    ]
    if newly_hot_names:
        hot_items_html = "".join(f"<li><strong>{n}</strong></li>" for n in newly_hot_names)
        newly_hot_html = f"""
        <div style="background:#ffe0e0;border-left:4px solid #dc3545;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>🚨 HOT昇格！ 新たな注目案件 ({len(newly_hot_names)}件)</strong>
          <ul style="margin:8px 0 0 0;">{hot_items_html}</ul>
        </div>"""

    # 変更検知セクション
    changes_html = ""
    changes = diff.get("changes", [])
    if changes:
        change_items = ""
        for c in changes[:5]:
            change_list = "".join(f"<li>{d}</li>" for d in c.get("changes", []))
            change_items += f"<li><strong>{c['name']}</strong><ul>{change_list}</ul></li>"
        changes_html = f"""
        <div style="background:#e8f4fd;border-left:4px solid #1e90ff;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>✏️ 変更検知 ({len(changes)}件)</strong>
          <ul style="margin:8px 0 0 0;">{change_items}</ul>
        </div>"""

    # HOT案件テーブル
    hot_rows = ""
    for a in hot[:6]:
        difficulty_color = {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}.get(
            a.get("difficulty", "easy"), "#6c757d"
        )
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        hot_flag = "🔥 " if a.get("is_hot") else ""
        hot_rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <strong>{hot_flag}{a['name']}</strong><br>
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

    # トレンドセクション
    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li><strong>{t['name']}</strong> ({t.get('symbol','')}) — スコア: {t.get('score', 0)}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#6f42c1;margin:20px 0 8px;">📈 CoinGecko トレンドコイン TOP5</h3>
        <ul style="padding-left:20px;">{t_items}</ul>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,'Hiragino Sans','Meiryo',sans-serif;max-width:700px;margin:0 auto;background:#f8f9fa;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:24px;border-radius:8px 8px 0 0;">
    <h1 style="margin:0;font-size:22px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:4px 0 0;opacity:0.8;">{today} 更新レポート</p>
  </div>
  <div style="background:white;padding:24px;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
    {newly_hot_html}
    {new_html}
    {changes_html}

    <h3 style="color:#dc3545;margin:20px 0 8px;">🔥 注目のホットエアドロップ TOP6</h3>
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
      ※ このメールはCrypto Airdrop Trackerから自動送信されています。<br>
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

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    subject = f"[Airdrop] {today} 更新 — ホット案件{hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"
    if diff and diff.get("newly_hot_names"):
        subject += f" 🚨HOT昇格{len(diff['newly_hot_names'])}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, diff)
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"変更: {len((diff or {}).get('changes', []))}件\n"
        f"トレンド: {', '.join(t['name'] for t in trending[:5])}"
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
    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,}の注目案件！"

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#dc3545,#7c4dff);color:white;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;">🚨 ホットエアドロップ出現！</h2>
    <p style="margin:4px 0 0;opacity:0.9;">今すぐチェックすべき注目案件です</p>
  </div>
  <div style="background:white;padding:20px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 8px 8px;">
    <h3>{name} ({airdrop.get('symbol','')})</h3>
    <table style="width:100%;border-collapse:collapse;">
      <tr><td style="padding:6px 0;color:#666;width:120px;">推定価値</td><td style="padding:6px 0;color:#28a745;font-weight:bold;font-size:18px;">~${value:,}</td></tr>
      <tr><td style="padding:6px 0;color:#666;">カテゴリ</td><td style="padding:6px 0;">{airdrop.get('category','')}</td></tr>
      <tr><td style="padding:6px 0;color:#666;">難易度</td><td style="padding:6px 0;">{airdrop.get('difficulty','').upper()}</td></tr>
      <tr><td style="padding:6px 0;color:#666;">期限</td><td style="padding:6px 0;">{airdrop.get('end_date','未定')}</td></tr>
    </table>
    <p style="margin:12px 0 6px;"><strong>概要:</strong> {airdrop.get('description','')}</p>
    <p style="margin:12px 0 6px;"><strong>参加方法:</strong></p>
    <ul style="padding-left:20px;">{"".join(f"<li>{t}</li>" for t in airdrop.get('tasks', []))}</ul>
    <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#7c4dff);color:white;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:bold;margin-top:12px;">今すぐ参加する →</a>
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
