"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使ってメール送信。
認証情報が未設定の場合はログのみ出力。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)


def _build_html_body(airdrops: list[dict], new_items: list[str], trending: list[dict]) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]

    new_html = ""
    if new_items:
        items_html = "".join(f"<li>{n}</li>" for n in new_items)
        new_html = f"""
        <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:12px 16px;
                    margin:16px 0;border-radius:4px;">
          <strong>🆕 新着エアドロップ ({len(new_items)}件)</strong>
          <ul style="margin:8px 0 0 0;">{items_html}</ul>
        </div>"""

    hot_rows = ""
    for a in hot[:6]:
        difficulty_color = {
            "easy": "#28a745",
            "medium": "#fd7e14",
            "hard": "#dc3545",
        }.get(a.get("difficulty", "easy"), "#6c757d")
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        status_label = {
            "active": "● アクティブ",
            "upcoming": "◎ 近日開始",
            "ended": "✕ 終了",
        }.get(a.get("status", ""), a.get("status", ""))
        hot_rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <strong>{a['name']}</strong><br>
            <span style="color:#6c757d;font-size:12px;">{a.get('category','')} · {status_label}</span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:bold;">{value}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <span style="background:{difficulty_color};color:white;padding:2px 8px;
                         border-radius:12px;font-size:12px;">
              {a.get('difficulty','').upper()}
            </span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;font-size:13px;">{a.get('end_date','未定')}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <a href="{a.get('url','#')}" style="color:#0d6efd;">参加する →</a>
          </td>
        </tr>"""

    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li><strong>{t['name']}</strong> ({t['symbol']}) — スコア: {t.get('score', 0)}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#6f42c1;">📈 CoinGecko トレンドコイン (本日)</h3>
        <ul>{t_items}</ul>"""

    hot_count = len(hot)
    total = len(airdrops)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:720px;margin:0 auto;background:#f8f9fa;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:28px;border-radius:8px 8px 0 0;">
    <h1 style="margin:0;font-size:24px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:6px 0 0;opacity:0.8;font-size:15px;">{today} 日次更新レポート</p>
    <div style="margin-top:14px;display:flex;gap:12px;flex-wrap:wrap;">
      <span style="background:rgba(255,255,255,0.15);padding:4px 12px;border-radius:20px;font-size:13px;">
        📋 計 {total} 件
      </span>
      <span style="background:rgba(255,80,80,0.3);padding:4px 12px;border-radius:20px;font-size:13px;">
        🔥 ホット {hot_count} 件
      </span>
      {f'<span style="background:rgba(255,193,7,0.3);padding:4px 12px;border-radius:20px;font-size:13px;">🆕 新着 {len(new_items)} 件</span>' if new_items else ''}
    </div>
  </div>

  <div style="background:white;padding:24px;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
    {new_html}

    <h3 style="color:#dc3545;margin-top:20px;">🔥 今注目のホットエアドロップ</h3>
    <table style="width:100%;border-collapse:collapse;margin-top:8px;font-size:14px;">
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

    <div style="background:#e8f4fd;border-radius:6px;padding:14px 16px;margin:20px 0;">
      <p style="margin:0;font-size:13px;color:#0c5460;">
        💡 <strong>2026年のアドバイス</strong>: エアドロップファーミングは量より質。
        少額でも継続的・本物の利用実績がスナップショット時に有利です。
        毎日少しずつ複数プロジェクトを利用し続けましょう。
      </p>
    </div>

    <hr style="margin:20px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:12px;margin:0;">
      ※ このメールはCrypto Airdrop Trackerから自動送信されています。<br>
      掲載情報は参考目的のみです。投資は自己責任で行ってください。<br>
      詐欺に注意: 公式リンク以外のエアドロップ申請は必ず公式サイトで確認してください。
    </p>
  </div>
</body>
</html>"""


def _build_plain_body(airdrops: list[dict], new_items: list[str], trending: list[dict]) -> str:
    today = datetime.now().strftime("%Y/%m/%d")
    hot = [a for a in airdrops if a.get("is_hot")]
    lines = [
        f"=== Crypto Airdrop Tracker {today} 更新レポート ===",
        f"総案件数: {len(airdrops)}件 | ホット: {len(hot)}件",
        "",
    ]
    if new_items:
        lines.append(f"🆕 新着: {', '.join(new_items)}")
        lines.append("")
    lines.append("🔥 注目エアドロップ:")
    for a in hot[:6]:
        val = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        lines.append(f"  • {a['name']} ({a.get('difficulty','').upper()}) {val} — {a.get('url','')}")
    if trending:
        lines.append("")
        lines.append("📈 CoinGeckoトレンド: " + ", ".join(t["name"] for t in trending[:5]))
    return "\n".join(lines)


def send_daily_report(airdrops: list[dict], new_items: list[str], trending: list[dict]) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning(
            "Gmail認証情報が未設定のためメール送信をスキップ (.envにGMAIL_SENDER/GMAIL_APP_PASSWORDを設定)"
        )
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    subject = f"[Airdrop] {today} 更新 — 🔥ホット{hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    msg.attach(MIMEText(_build_plain_body(airdrops, new_items, trending), "plain", "utf-8"))
    msg.attach(MIMEText(_build_html_body(airdrops, new_items, trending), "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"日次レポート送信成功: {GMAIL_RECIPIENT}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗。アプリパスワードを確認してください (setup_gmail.py参照)")
        return False
    except Exception as e:
        logger.error(f"メール送信失敗: {e}")
        return False


def send_hot_alert(airdrop: dict) -> bool:
    """注目案件出現時の即時アラート"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.info(f"[HOT ALERT (unsent)] {airdrop.get('name')} — SMTP未設定のためスキップ")
        return False

    name = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd", 0)
    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,}の新案件が登場！"

    difficulty_color = {
        "easy": "#28a745",
        "medium": "#fd7e14",
        "hard": "#dc3545",
    }.get(airdrop.get("difficulty", "easy"), "#6c757d")

    tasks_html = "".join(f"<li>{t}</li>" for t in airdrop.get("tasks", []))

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:620px;margin:0 auto;">
  <div style="background:#dc3545;color:white;padding:24px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;font-size:22px;">🚨 ホットエアドロップ出現！</h2>
    <p style="margin:4px 0 0;opacity:0.9;">今すぐ行動が必要な新案件</p>
  </div>
  <div style="background:white;padding:24px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 8px 8px;">
    <h3 style="color:#1a1a2e;">{name} ({airdrop.get('symbol','')})</h3>
    <table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
      <tr>
        <td style="padding:6px 0;color:#6c757d;width:100px;">推定価値</td>
        <td style="padding:6px 0;font-weight:bold;color:#28a745;">~${value:,}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6c757d;">カテゴリ</td>
        <td style="padding:6px 0;">{airdrop.get('category','')}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6c757d;">難易度</td>
        <td style="padding:6px 0;">
          <span style="background:{difficulty_color};color:white;padding:2px 10px;
                       border-radius:12px;font-size:13px;">
            {airdrop.get('difficulty','').upper()}
          </span>
        </td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6c757d;">期限</td>
        <td style="padding:6px 0;">{airdrop.get('end_date','未定')}</td>
      </tr>
    </table>
    <p style="color:#333;">{airdrop.get('description','')}</p>
    <p><strong>📋 参加方法:</strong></p>
    <ul style="padding-left:20px;">{tasks_html}</ul>
    <a href="{airdrop.get('url','#')}"
       style="display:inline-block;background:#dc3545;color:white;padding:14px 28px;
              border-radius:6px;text-decoration:none;font-weight:bold;margin-top:8px;">
      今すぐ参加する →
    </a>
    <hr style="margin:20px 0;">
    <p style="color:#6c757d;font-size:12px;">
      ※ 投資は自己責任で行ってください。詐欺サイトに注意してください。
    </p>
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
