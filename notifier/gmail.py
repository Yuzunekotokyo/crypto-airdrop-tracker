"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してメール送信。
毎日日次ダイジェスト + ホットアラートを送信。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)


def _difficulty_color(diff: str) -> str:
    return {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}.get(diff, "#6c757d")


def _build_added_section(added: list[dict]) -> str:
    if not added:
        return ""
    rows = ""
    for a in added:
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        hot_badge = '<span style="background:#dc3545;color:white;padding:1px 6px;border-radius:10px;font-size:11px;margin-left:6px;">🔥 HOT</span>' if a.get("is_hot") else ""
        rows += f"""
        <tr style="background:#f0fff4;">
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <strong>{a["name"]}</strong>{hot_badge}<br>
            <span style="color:#6c757d;font-size:12px;">{a.get("category","")} · {a.get("type","")}</span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:bold;">{value}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <span style="background:{_difficulty_color(a.get('difficulty',''))};color:white;padding:2px 8px;border-radius:10px;font-size:11px;">
              {a.get("difficulty","").upper()}
            </span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;font-size:12px;">{a.get("end_date","未定")}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <a href="{a.get('url','#')}" style="color:#0d6efd;">参加 →</a>
          </td>
        </tr>"""
    return f"""
    <div style="margin:20px 0;">
      <h3 style="color:#28a745;border-left:4px solid #28a745;padding-left:10px;">🆕 新着エアドロップ ({len(added)}件)</h3>
      <table style="width:100%;border-collapse:collapse;margin-top:10px;">
        <thead><tr style="background:#f8f9fa;">
          <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">プロジェクト</th>
          <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">推定価値</th>
          <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">難易度</th>
          <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">期限</th>
          <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">リンク</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""


def _build_changed_section(changed: list[dict]) -> str:
    if not changed:
        return ""
    items = ""
    for c in changed:
        hot_tag = " 🔥" if c.get("is_hot") else ""
        change_list = "".join(f"<li style='margin:3px 0;'>{ch}</li>" for ch in c["changes"])
        items += f"""
        <div style="background:#fff8e1;border-left:3px solid #ffc107;padding:10px 14px;margin:8px 0;border-radius:4px;">
          <strong>{c["name"]}{hot_tag}</strong>
          <ul style="margin:6px 0 0 0;padding-left:18px;font-size:13px;color:#555;">{change_list}</ul>
        </div>"""
    return f"""
    <div style="margin:20px 0;">
      <h3 style="color:#fd7e14;border-left:4px solid #fd7e14;padding-left:10px;">✏️ 情報更新 ({len(changed)}件)</h3>
      {items}
    </div>"""


def _build_hot_section(airdrops: list[dict]) -> str:
    hot = [a for a in airdrops if a.get("is_hot")][:5]
    if not hot:
        return ""
    rows = ""
    for a in hot:
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <strong>{a["name"]}</strong><br>
            <span style="color:#6c757d;font-size:12px;">{a.get("category","")}</span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:bold;">{value}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <span style="background:{_difficulty_color(a.get('difficulty',''))};color:white;padding:2px 8px;border-radius:10px;font-size:11px;">
              {a.get("difficulty","").upper()}
            </span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;font-size:12px;">{a.get("end_date","未定")}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <a href="{a.get('url','#')}" style="color:#0d6efd;">参加 →</a>
          </td>
        </tr>"""
    return f"""
    <div style="margin:20px 0;">
      <h3 style="color:#dc3545;border-left:4px solid #dc3545;padding-left:10px;">🔥 現在のホット案件 TOP5</h3>
      <table style="width:100%;border-collapse:collapse;margin-top:10px;">
        <thead><tr style="background:#f8f9fa;">
          <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">プロジェクト</th>
          <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">推定価値</th>
          <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">難易度</th>
          <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">期限</th>
          <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">リンク</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""


def _build_trending_section(trending: list[dict]) -> str:
    if not trending:
        return ""
    items = "".join(
        f"<li style='margin:5px 0;'><strong>{t['name']}</strong> "
        f"<span style='color:#888;font-size:12px;'>({t['symbol']})</span> "
        f"— トレンドスコア: {t.get('score', 0)}</li>"
        for t in trending[:7]
    )
    return f"""
    <div style="margin:20px 0;background:#f3f0ff;border-radius:8px;padding:16px;">
      <h3 style="color:#6f42c1;margin:0 0 10px;">📈 CoinGecko トレンドコイン</h3>
      <ul style="margin:0;padding-left:20px;">{items}</ul>
    </div>"""


def _build_html_body(
    airdrops: list[dict],
    added: list[dict],
    changed: list[dict],
    trending: list[dict],
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    total = len(airdrops)

    no_change_notice = ""
    if not added and not changed:
        no_change_notice = """
        <div style="background:#e8f4fd;border-left:4px solid #0d6efd;padding:12px 16px;margin:16px 0;border-radius:4px;color:#555;">
          本日は新着・変更案件はありませんでした。引き続き最新情報をお届けします。
        </div>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Helvetica Neue',Arial,'Hiragino Kaku Gothic ProN',sans-serif;max-width:720px;margin:0 auto;background:#f0f2f5;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);color:white;padding:28px 24px;border-radius:10px 10px 0 0;">
    <h1 style="margin:0;font-size:22px;letter-spacing:1px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:6px 0 0;opacity:0.75;font-size:14px;">{today} 日次更新レポート</p>
    <div style="display:flex;gap:16px;margin-top:16px;flex-wrap:wrap;">
      <span style="background:rgba(255,255,255,0.15);padding:4px 12px;border-radius:20px;font-size:13px;">📋 計 {total} 件</span>
      <span style="background:rgba(220,53,69,0.4);padding:4px 12px;border-radius:20px;font-size:13px;">🔥 ホット {hot_count} 件</span>
      {"<span style='background:rgba(40,167,69,0.4);padding:4px 12px;border-radius:20px;font-size:13px;'>🆕 新着 " + str(len(added)) + " 件</span>" if added else ""}
      {"<span style='background:rgba(255,165,2,0.4);padding:4px 12px;border-radius:20px;font-size:13px;'>✏️ 変更 " + str(len(changed)) + " 件</span>" if changed else ""}
    </div>
  </div>

  <div style="background:white;padding:24px;border-radius:0 0 10px 10px;box-shadow:0 4px 16px rgba(0,0,0,0.1);">
    {no_change_notice}
    {_build_added_section(added)}
    {_build_changed_section(changed)}
    {_build_hot_section(airdrops)}
    {_build_trending_section(trending)}

    <hr style="margin:24px 0;border:none;border-top:1px solid #e9ecef;">
    <p style="color:#6c757d;font-size:11px;margin:0;line-height:1.7;">
      このメールはCrypto Airdrop Trackerから毎日自動送信されています。<br>
      ※ 掲載情報は参考目的のみです。投資は自己責任で行ってください。
    </p>
  </div>
</body>
</html>"""


def send_daily_report(
    airdrops: list[dict],
    added: list[dict],
    changed: list[dict],
    trending: list[dict],
) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))

    parts = [f"ホット{hot_count}件"]
    if added:
        parts.append(f"🆕新着{len(added)}件")
    if changed:
        parts.append(f"✏️変更{len(changed)}件")
    if not added and not changed:
        parts.append("変更なし")

    subject = f"[Airdrop] {today} 更新 — {' · '.join(parts)}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, added, changed, trending)
    plain_parts = [f"{today} Airdrop更新レポート", f"ホット案件: {hot_count}件"]
    if added:
        plain_parts.append(f"新着: {', '.join(a['name'] for a in added)}")
    if changed:
        plain_parts.append(f"変更: {', '.join(c['name'] for c in changed)}")
    plain_body = "\n".join(plain_parts)

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"日次レポート送信成功: {GMAIL_RECIPIENT} / {subject}")
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
    value_str = f"~${value:,}" if value else "未定"
    tasks_html = "".join(f"<li style='margin:4px 0;'>{t}</li>" for t in airdrop.get("tasks", []))
    subject = f"🚨 [HOT Airdrop] {name} — 推定{value_str}の注目案件！"

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:600px;margin:0 auto;background:#f0f2f5;">
  <div style="background:linear-gradient(135deg,#dc3545,#c0392b);color:white;padding:24px;border-radius:10px 10px 0 0;">
    <h2 style="margin:0;font-size:20px;">🚨 ホットエアドロップ出現！</h2>
    <p style="margin:6px 0 0;opacity:0.85;font-size:13px;">今すぐ参加をご検討ください</p>
  </div>
  <div style="background:white;padding:24px;border-radius:0 0 10px 10px;box-shadow:0 4px 16px rgba(0,0,0,0.1);">
    <h3 style="margin:0 0 16px;font-size:20px;">{name}
      {"<span style='font-size:13px;color:#888;'> ({})".format(airdrop.get('symbol','')) + "</span>" if airdrop.get('symbol') else ""}
    </h3>
    <table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
      <tr><td style="padding:8px 0;color:#888;font-size:13px;width:100px;">推定価値</td>
          <td style="padding:8px 0;font-weight:bold;font-size:18px;color:#28a745;">{value_str}</td></tr>
      <tr><td style="padding:8px 0;color:#888;font-size:13px;">カテゴリ</td>
          <td style="padding:8px 0;">{airdrop.get('category','')}</td></tr>
      <tr><td style="padding:8px 0;color:#888;font-size:13px;">難易度</td>
          <td style="padding:8px 0;"><span style="background:{_difficulty_color(airdrop.get('difficulty',''))};color:white;padding:2px 10px;border-radius:10px;font-size:12px;">{airdrop.get('difficulty','').upper()}</span></td></tr>
      <tr><td style="padding:8px 0;color:#888;font-size:13px;">期限</td>
          <td style="padding:8px 0;font-weight:600;">{airdrop.get('end_date','未定')}</td></tr>
    </table>
    <p style="color:#444;margin:0 0 8px;">{airdrop.get('description','')}</p>
    {"<div style='background:#f8f9fa;border-radius:8px;padding:14px;margin:16px 0;'><p style='margin:0 0 8px;font-weight:700;font-size:13px;'>📋 参加方法</p><ul style='margin:0;padding-left:20px;'>" + tasks_html + "</ul></div>" if tasks_html else ""}
    <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#c0392b);color:white;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:15px;margin-top:8px;">今すぐ参加する →</a>
    <hr style="margin:20px 0;border:none;border-top:1px solid #e9ecef;">
    <p style="color:#aaa;font-size:11px;margin:0;">※ 投資は自己責任で行ってください。</p>
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
