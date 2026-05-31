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
    changes: list[dict] | None = None,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]

    # 新着セクション
    new_html = ""
    if new_items:
        items_html = "".join(f"<li>{n}</li>" for n in new_items)
        new_html = f"""
        <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>🆕 新着エアドロップ ({len(new_items)}件)</strong>
          <ul style="margin:8px 0 0 0;">{items_html}</ul>
        </div>"""

    # 変更セクション
    changes_html = ""
    if changes:
        change_rows = ""
        for c in changes[:10]:
            change_list = "".join(f"<li style='font-size:12px;color:#555'>{d}</li>" for d in c["changes"])
            change_rows += f"""
            <div style="background:#f8f9fa;border-left:3px solid #fd7e14;padding:8px 12px;margin:6px 0;border-radius:3px;">
              <strong style="font-size:13px;">{c['name']}</strong>
              <ul style="margin:4px 0 0 0;">{change_list}</ul>
            </div>"""
        changes_html = f"""
        <div style="background:#fff8f0;border-left:4px solid #fd7e14;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>✏️ 変更された案件 ({len(changes)}件)</strong>
          {change_rows}
        </div>"""

    # ホット案件テーブル
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

    # トレンドセクション
    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li><strong>{t['name']}</strong> ({t['symbol']}) — スコア: {t.get('score', 0)}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#6f42c1;">📈 CoinGecko トレンドコイン</h3>
        <ul>{t_items}</ul>"""

    # 全案件サマリー (ホット以外の上位)
    other_hot = [a for a in airdrops if not a.get("is_hot") and a.get("estimated_value_usd", 0) >= 300][:5]
    other_rows = ""
    for a in other_hot:
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        other_rows += f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #dee2e6;"><strong>{a['name']}</strong></td>
          <td style="padding:8px;border-bottom:1px solid #dee2e6;">{a.get('category','')}</td>
          <td style="padding:8px;border-bottom:1px solid #dee2e6;color:#28a745;">{value}</td>
          <td style="padding:8px;border-bottom:1px solid #dee2e6;">
            <a href="{a.get('url','#')}" style="color:#0d6efd;">参加</a>
          </td>
        </tr>"""

    other_html = ""
    if other_rows:
        other_html = f"""
        <h3 style="color:#495057;margin-top:24px;">📋 その他の注目案件 (推定$300以上)</h3>
        <table style="width:100%;border-collapse:collapse;margin-top:8px;font-size:13px;">
          <thead>
            <tr style="background:#f8f9fa;">
              <th style="padding:8px;text-align:left;border-bottom:2px solid #dee2e6;">プロジェクト</th>
              <th style="padding:8px;text-align:left;border-bottom:2px solid #dee2e6;">カテゴリ</th>
              <th style="padding:8px;text-align:left;border-bottom:2px solid #dee2e6;">推定価値</th>
              <th style="padding:8px;text-align:left;border-bottom:2px solid #dee2e6;">リンク</th>
            </tr>
          </thead>
          <tbody>{other_rows}</tbody>
        </table>"""

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
    <p style="margin:8px 0 0;font-size:13px;opacity:0.7;">
      📋 総案件数: {total}件 &nbsp;|&nbsp; 🔥 ホット: {hot_count}件
      {f"&nbsp;|&nbsp; 🆕 新着: {len(new_items)}件" if new_items else ""}
      {f"&nbsp;|&nbsp; ✏️ 変更: {len(changes)}件" if changes else ""}
    </p>
  </div>
  <div style="background:white;padding:24px;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
    {new_html}
    {changes_html}

    <h3 style="color:#dc3545;">🔥 今すぐ狙うべきホットエアドロップ TOP5</h3>
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

    {other_html}
    {trending_html}

    <hr style="margin:24px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:12px;margin:0;">
      ※ このメールはCrypto Airdrop Trackerから自動送信されています。毎日 08:00 JST に更新。<br>
      投資は自己責任で行ってください。掲載情報は参考目的のみです。
    </p>
  </div>
</body>
</html>"""


def send_daily_report(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    changes: list[dict] | None = None,
) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    subject = f"[Airdrop] {today} 更新 — ホット案件{hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"
    if changes:
        subject += f" ✏️変更{len(changes)}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, changes=changes)
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"変更: {len(changes)}件" if changes else f"変更: なし"
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
    """注目案件出現・昇格時の即時アラート"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        return False

    name = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd", 0)
    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,}の注目案件！"

    tasks_html = "".join(f"<li>{t}</li>" for t in airdrop.get("tasks", []))

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#dc3545,#ff6b6b);color:white;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;">🚨 ホットエアドロップ出現！</h2>
    <p style="margin:6px 0 0;opacity:0.9;">新しい注目案件が追加されました</p>
  </div>
  <div style="background:white;padding:20px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 8px 8px;">
    <table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
      <tr><td style="padding:8px;color:#666;width:120px;">プロジェクト</td>
          <td style="padding:8px;font-weight:bold;font-size:18px;">{name} ({airdrop.get('symbol','')})</td></tr>
      <tr style="background:#f8f9fa;"><td style="padding:8px;color:#666;">推定価値</td>
          <td style="padding:8px;color:#28a745;font-weight:bold;font-size:16px;">~${value:,}</td></tr>
      <tr><td style="padding:8px;color:#666;">カテゴリ</td>
          <td style="padding:8px;">{airdrop.get('category','')}</td></tr>
      <tr style="background:#f8f9fa;"><td style="padding:8px;color:#666;">難易度</td>
          <td style="padding:8px;">{airdrop.get('difficulty','').upper()}</td></tr>
      <tr><td style="padding:8px;color:#666;">期限</td>
          <td style="padding:8px;">{airdrop.get('end_date','未定')}</td></tr>
    </table>
    <p style="color:#555;">{airdrop.get('description','')}</p>
    {"<p><strong>📋 参加方法:</strong></p><ul>" + tasks_html + "</ul>" if tasks_html else ""}
    <div style="text-align:center;margin:20px 0;">
      <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#ff6b6b);color:white;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:16px;">
        🚀 今すぐ参加する
      </a>
    </div>
    <hr style="margin:20px 0;">
    <p style="color:#6c757d;font-size:12px;">投資は自己責任で行ってください。情報は参考目的のみです。</p>
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
