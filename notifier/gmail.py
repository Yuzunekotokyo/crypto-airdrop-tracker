"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してメール送信。
SMTPが未設定の場合はdata/pending_email.jsonに保存。
"""

import json
import smtplib
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT, DATA_DIR

logger = logging.getLogger(__name__)

PENDING_EMAIL_FILE = os.path.join(DATA_DIR, "pending_email.json")


def _build_html_body(airdrops: list[dict], new_items: list[str], trending: list[dict], diff: dict = None) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    diff = diff or {}
    added = diff.get("added", [])
    changed = diff.get("changed", [])

    # 新着HOT案件アラートセクション
    newly_hot = [a for a in added if a.get("is_hot")]
    hot_alert_html = ""
    if newly_hot:
        alert_items = ""
        for a in newly_hot:
            value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
            alert_items += f"""
            <tr>
              <td style="padding:10px 14px;border-bottom:1px solid #dc3545;">
                <strong style="color:#fff;">{a['name']}</strong>
                <span style="font-size:12px;color:#ff8080;margin-left:8px;">{a.get('category','')}</span>
              </td>
              <td style="padding:10px 14px;border-bottom:1px solid #dc3545;color:#ffdd57;font-weight:bold;font-size:18px;">{value}</td>
              <td style="padding:10px 14px;border-bottom:1px solid #dc3545;">
                <a href="{a.get('url','#')}" style="background:#ff4757;color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold;">今すぐ参加</a>
              </td>
            </tr>"""
        hot_alert_html = f"""
        <div style="background:linear-gradient(135deg,#7b0000,#dc3545);border-radius:10px;padding:20px;margin:16px 0;animation:flash 1s;">
          <h2 style="color:#ffdd57;margin:0 0 12px;font-size:20px;">🚨 新着HOT案件 {len(newly_hot)}件！</h2>
          <table style="width:100%;border-collapse:collapse;">
            <tbody>{alert_items}</tbody>
          </table>
        </div>"""

    # 新着エアドロップセクション
    new_html = ""
    if new_items:
        items_html = "".join(f"<li style='margin:4px 0;'>{n}</li>" for n in new_items)
        new_html = f"""
        <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:14px 18px;margin:16px 0;border-radius:6px;">
          <strong>🆕 新着エアドロップ ({len(new_items)}件)</strong>
          <ul style="margin:8px 0 0 0;">{items_html}</ul>
        </div>"""

    # 変更情報セクション
    changed_html = ""
    if changed:
        ch_items = "".join(
            f"<li><strong>{c['name']}</strong>: {'、'.join(c['changes'])}</li>"
            for c in changed
        )
        changed_html = f"""
        <div style="background:#e8f4fd;border-left:4px solid #4a86e8;padding:14px 18px;margin:16px 0;border-radius:6px;">
          <strong>✏️ 更新情報 ({len(changed)}件)</strong>
          <ul style="margin:8px 0 0 0;">{ch_items}</ul>
        </div>"""

    # ホットエアドロップ表
    hot_rows = ""
    for a in hot[:5]:
        difficulty_color = {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}.get(
            a.get("difficulty", "easy"), "#6c757d"
        )
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "不明"
        hot_rows += f"""
        <tr>
          <td style="padding:12px 14px;border-bottom:1px solid #dee2e6;">
            <strong>{a['name']}</strong><br>
            <span style="color:#6c757d;font-size:12px;">{a.get('category','')}</span>
          </td>
          <td style="padding:12px 14px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:bold;font-size:16px;">{value}</td>
          <td style="padding:12px 14px;border-bottom:1px solid #dee2e6;">
            <span style="background:{difficulty_color};color:white;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:bold;">
              {a.get('difficulty','').upper()}
            </span>
          </td>
          <td style="padding:12px 14px;border-bottom:1px solid #dee2e6;color:#555;">{a.get('end_date','未定')}</td>
          <td style="padding:12px 14px;border-bottom:1px solid #dee2e6;">
            <a href="{a.get('url','#')}" style="background:#7c4dff;color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold;">参加する</a>
          </td>
        </tr>"""

    # トレンドコインセクション
    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li style='margin:4px 0;'><strong>{t['name']}</strong> ({t['symbol']}) — スコア: {t.get('score', 0)}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#6f42c1;margin-top:24px;">📈 CoinGecko トレンドコイン</h3>
        <ul style="padding-left:18px;">{t_items}</ul>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;max-width:720px;margin:0 auto;background:#f0f2f5;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:28px;border-radius:12px 12px 0 0;">
    <h1 style="margin:0;font-size:24px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:6px 0 0;opacity:0.8;font-size:14px;">{today} 日次更新レポート</p>
    <div style="margin-top:16px;display:flex;gap:12px;flex-wrap:wrap;">
      <span style="background:rgba(255,255,255,0.15);padding:4px 14px;border-radius:20px;font-size:13px;">
        📋 計 <strong>{len(airdrops)}</strong> 件
      </span>
      <span style="background:rgba(255,71,87,0.4);padding:4px 14px;border-radius:20px;font-size:13px;">
        🔥 ホット <strong>{len(hot)}</strong> 件
      </span>
      {f'<span style="background:rgba(46,213,115,0.4);padding:4px 14px;border-radius:20px;font-size:13px;">🆕 新着 <strong>{len(new_items)}</strong> 件</span>' if new_items else ''}
    </div>
  </div>
  <div style="background:white;padding:28px;border-radius:0 0 12px 12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
    {hot_alert_html}
    {new_html}
    {changed_html}

    <h3 style="color:#dc3545;margin-top:20px;">🔥 注目のホットエアドロップ TOP5</h3>
    <table style="width:100%;border-collapse:collapse;margin-top:10px;border-radius:8px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,0.08);">
      <thead>
        <tr style="background:#f8f9fa;">
          <th style="padding:12px 14px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">プロジェクト</th>
          <th style="padding:12px 14px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">推定価値</th>
          <th style="padding:12px 14px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">難易度</th>
          <th style="padding:12px 14px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">期限</th>
          <th style="padding:12px 14px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">参加</th>
        </tr>
      </thead>
      <tbody>{hot_rows}</tbody>
    </table>

    {trending_html}

    <hr style="margin:28px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:12px;margin:0;line-height:1.6;">
      ※ このメールはCrypto Airdrop Trackerから自動送信されています。<br>
      投資は自己責任で行ってください。掲載情報は参考目的のみです。
    </p>
  </div>
</body>
</html>"""


def _save_pending_email(subject: str, html_body: str, plain_body: str):
    """SMTPが未設定の場合、メール内容をファイルに保存"""
    os.makedirs(DATA_DIR, exist_ok=True)
    data = {
        "subject": subject,
        "to": GMAIL_RECIPIENT,
        "html_body": html_body,
        "plain_body": plain_body,
        "created_at": datetime.now().isoformat(),
        "sent": False,
    }
    with open(PENDING_EMAIL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"メール内容を保存: {PENDING_EMAIL_FILE}")


def send_daily_report(airdrops: list[dict], new_items: list[str], trending: list[dict], diff: dict = None) -> bool:
    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    diff = diff or {}
    newly_hot = [a for a in diff.get("added", []) if a.get("is_hot")]

    subject = f"[Airdrop] {today} 更新 — ホット案件{hot_count}件"
    if newly_hot:
        subject = f"🚨 [HOT] {today} — 新着HOT案件{len(newly_hot)}件！ | {subject}"
    elif new_items:
        subject += f" 🆕新着{len(new_items)}件"

    html_body = _build_html_body(airdrops, new_items, trending, diff)
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"新着HOT: {', '.join(a['name'] for a in newly_hot) if newly_hot else 'なし'}"
    )

    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail SMTP未設定 — メール内容をファイルに保存します")
        _save_pending_email(subject, html_body, plain_body)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

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
        _save_pending_email(subject, html_body, plain_body)
        return False
    except Exception as e:
        logger.error(f"メール送信失敗: {e}")
        _save_pending_email(subject, html_body, plain_body)
        return False


def send_hot_alert(airdrop: dict) -> bool:
    """注目案件出現時の即時アラート"""
    name = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd", 0)
    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,}の新案件が登場！"

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;background:#f0f2f5;">
  <div style="background:linear-gradient(135deg,#7b0000,#dc3545);color:white;padding:24px;border-radius:12px 12px 0 0;">
    <h2 style="margin:0;font-size:22px;">🚨 ホットエアドロップ出現！</h2>
    <p style="margin:6px 0 0;opacity:0.85;">今すぐ行動が必要です</p>
  </div>
  <div style="background:white;padding:24px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 12px 12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
    <h3 style="font-size:20px;margin-top:0;">{name} ({airdrop.get('symbol','')})</h3>
    <table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
      <tr>
        <td style="padding:8px 0;color:#6c757d;width:100px;">推定価値</td>
        <td style="padding:8px 0;font-size:24px;font-weight:bold;color:#28a745;">~${value:,}</td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#6c757d;">カテゴリ</td>
        <td style="padding:8px 0;">{airdrop.get('category','')}</td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#6c757d;">難易度</td>
        <td style="padding:8px 0;"><span style="background:#fd7e14;color:white;padding:3px 10px;border-radius:12px;font-size:13px;font-weight:bold;">{airdrop.get('difficulty','').upper()}</span></td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#6c757d;">期限</td>
        <td style="padding:8px 0;">{airdrop.get('end_date','未定')}</td>
      </tr>
    </table>
    <p style="color:#333;margin-bottom:12px;"><strong>概要:</strong> {airdrop.get('description','')}</p>
    <p style="color:#333;font-weight:bold;margin-bottom:8px;">📋 参加方法:</p>
    <ul style="padding-left:20px;color:#333;">{"".join(f"<li style='margin:6px 0;'>{t}</li>" for t in airdrop.get('tasks', []))}</ul>
    <div style="text-align:center;margin-top:24px;">
      <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#ff4757);color:white;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:16px;">🚀 今すぐ参加する</a>
    </div>
    <hr style="margin:24px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:12px;text-align:center;">投資は自己責任で行ってください。</p>
  </div>
</body></html>"""

    plain = f"HOT Airdrop: {name}\n推定価値: ~${value:,}\n参加: {airdrop.get('url','')}"

    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        _save_pending_email(subject, html, plain)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"ホットアラート送信: {name}")
        return True
    except Exception as e:
        logger.error(f"ホットアラート送信失敗: {e}")
        _save_pending_email(subject, html, plain)
        return False
