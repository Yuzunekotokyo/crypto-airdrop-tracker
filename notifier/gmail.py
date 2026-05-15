"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してメール送信。
毎日必ず日次レポートを tsukamoto.kei@gmail.com に送信。
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
    added: list[dict],
    changed: list[dict],
    trending: list[dict],
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    newly_hot = [a for a in added if a.get("is_hot")]

    # ===== 新着HOT案件アラートブロック =====
    hot_alert_html = ""
    if newly_hot:
        hot_cards = ""
        for a in newly_hot:
            value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
            tasks_html = "".join(f"<li>{t}</li>" for t in a.get("tasks", []))
            hot_cards += f"""
        <div style="background:#fff0f0;border:2px solid #dc3545;border-radius:8px;padding:16px;margin:10px 0;">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
            {"<img src='"+a.get('logo','')+"' style='width:40px;height:40px;border-radius:50%;' onerror='this.style.display=none'>" if a.get('logo') else ""}
            <div>
              <strong style="font-size:16px;">{a['name']}</strong>
              <span style="background:#dc3545;color:white;padding:2px 8px;border-radius:12px;font-size:11px;margin-left:8px;">🔥 HOT NEW</span>
            </div>
          </div>
          <p style="color:#333;font-size:13px;margin:6px 0;">{a.get('description','')}</p>
          <table style="width:100%;font-size:13px;margin:8px 0;">
            <tr>
              <td><strong>推定価値:</strong> <span style="color:#28a745;font-weight:bold;">{value}</span></td>
              <td><strong>難易度:</strong> {a.get('difficulty','').upper()}</td>
              <td><strong>期限:</strong> {a.get('end_date','未定')}</td>
            </tr>
          </table>
          {"<ul style='margin:6px 0 0 0;padding-left:18px;font-size:12px;color:#555;'>" + tasks_html + "</ul>" if tasks_html else ""}
          <a href="{a.get('url','#')}" style="display:inline-block;background:#dc3545;color:white;padding:8px 20px;border-radius:6px;text-decoration:none;font-weight:bold;margin-top:10px;">今すぐ参加する →</a>
        </div>"""
        hot_alert_html = f"""
        <div style="background:#fff0f0;border-left:5px solid #dc3545;padding:16px;margin:16px 0;border-radius:4px;">
          <h3 style="color:#dc3545;margin:0 0 12px;">🚨 新着HOT案件が{len(newly_hot)}件登場！</h3>
          {hot_cards}
        </div>"""

    # ===== 新着エアドロップブロック =====
    new_html = ""
    non_hot_added = [a for a in added if not a.get("is_hot")]
    if non_hot_added:
        items_html = "".join(f"<li>{a['name']}{' — ~$'+str(a.get('estimated_value_usd',0)) if a.get('estimated_value_usd') else ''}</li>" for a in non_hot_added)
        new_html = f"""
        <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>🆕 新着エアドロップ ({len(non_hot_added)}件)</strong>
          <ul style="margin:8px 0 0 0;">{items_html}</ul>
        </div>"""

    # ===== 変更があったエアドロップ =====
    changes_html = ""
    if changed:
        change_rows = "".join(
            f"<li><strong>{c['name']}</strong>: {' / '.join(c['changes'])}</li>"
            for c in changed[:10]
        )
        changes_html = f"""
        <div style="background:#e8f4fd;border-left:4px solid #1e90ff;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>✏️ 情報更新 ({len(changed)}件)</strong>
          <ul style="margin:8px 0 0 0;font-size:13px;">{change_rows}</ul>
        </div>"""

    # ===== HOT案件テーブル =====
    hot_rows = ""
    for a in hot[:6]:
        difficulty_color = {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}.get(
            a.get("difficulty", "easy"), "#6c757d"
        )
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
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
        <h3 style="color:#6f42c1;margin-top:24px;">📈 CoinGecko トレンドコイン TOP5</h3>
        <ul style="font-size:13px;">{t_items}</ul>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:720px;margin:0 auto;background:#f8f9fa;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:24px;border-radius:8px 8px 0 0;">
    <h1 style="margin:0;font-size:22px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:4px 0 0;opacity:0.8;">{today} 日次更新レポート</p>
    <p style="margin:8px 0 0;font-size:13px;opacity:0.7;">
      総数: {len(airdrops)}件 &nbsp;|&nbsp; 🔥 ホット: {len(hot)}件 &nbsp;|&nbsp;
      🆕 新着: {len(added)}件 &nbsp;|&nbsp; ✏️ 変更: {len(changed)}件
    </p>
  </div>
  <div style="background:white;padding:24px;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">

    {hot_alert_html}
    {new_html}
    {changes_html}

    <h3 style="color:#dc3545;margin-top:20px;">🔥 注目のホットエアドロップ TOP6</h3>
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
      <tbody>{hot_rows if hot_rows else '<tr><td colspan="5" style="padding:16px;color:#6c757d;text-align:center;">HOT案件なし</td></tr>'}</tbody>
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
    added: list[dict],
    changed: list[dict],
    trending: list[dict],
) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    newly_hot = [a for a in added if a.get("is_hot")]

    subject = f"[Airdrop日報] {today} — ホット{hot_count}件"
    if newly_hot:
        subject = f"🚨 [Airdrop] {today} 新HOT案件{len(newly_hot)}件登場！ ホット総数{hot_count}件"
    elif added:
        subject += f" 🆕新着{len(added)}件"
    if changed:
        subject += f" ✏️変更{len(changed)}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, added, changed, trending)
    added_names = [a["name"] for a in added]
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(added_names) if added_names else 'なし'}\n"
        f"変更: {len(changed)}件\n"
        f"トレンド: {', '.join(t['name'] for t in trending[:5])}"
    )

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"日次メール送信成功: {GMAIL_RECIPIENT} / 件名: {subject}")
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
    subject = f"🚨 [HOT Airdrop速報] {name} — 推定${value:,}の新案件が登場！"

    tasks_html = "".join(f"<li>{t}</li>" for t in airdrop.get("tasks", []))
    logo_html = f"<img src='{airdrop.get('logo','')}' style='width:50px;height:50px;border-radius:50%;margin-bottom:12px;' onerror='this.style.display=none'>" if airdrop.get("logo") else ""

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:620px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#dc3545,#ff6b81);color:white;padding:24px;border-radius:8px 8px 0 0;text-align:center;">
    <h2 style="margin:0;font-size:24px;">🚨 新着HOTエアドロップ出現！</h2>
    <p style="margin:6px 0 0;opacity:0.9;">見逃し厳禁の注目案件です</p>
  </div>
  <div style="background:white;padding:24px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 8px 8px;">
    {logo_html}
    <h3 style="font-size:22px;margin:0 0 8px;">{name} <span style="font-size:14px;color:#6c757d;">({airdrop.get('symbol','')})</span></h3>
    <p style="color:#555;font-size:14px;margin:0 0 16px;">{airdrop.get('description','')}</p>
    <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:16px;">
      <tr style="background:#f8f9fa;">
        <td style="padding:10px;border:1px solid #dee2e6;"><strong>💰 推定価値</strong></td>
        <td style="padding:10px;border:1px solid #dee2e6;color:#28a745;font-weight:bold;font-size:18px;">~${value:,}</td>
      </tr>
      <tr>
        <td style="padding:10px;border:1px solid #dee2e6;"><strong>📊 カテゴリ</strong></td>
        <td style="padding:10px;border:1px solid #dee2e6;">{airdrop.get('category','')}</td>
      </tr>
      <tr style="background:#f8f9fa;">
        <td style="padding:10px;border:1px solid #dee2e6;"><strong>⚡ 難易度</strong></td>
        <td style="padding:10px;border:1px solid #dee2e6;">{airdrop.get('difficulty','').upper()}</td>
      </tr>
      <tr>
        <td style="padding:10px;border:1px solid #dee2e6;"><strong>⏰ 期限</strong></td>
        <td style="padding:10px;border:1px solid #dee2e6;">{airdrop.get('end_date','未定')}</td>
      </tr>
    </table>
    {"<h4 style='margin:0 0 8px;'>📋 参加方法</h4><ul style='font-size:13px;color:#555;'>"+tasks_html+"</ul>" if tasks_html else ""}
    <div style="text-align:center;margin-top:20px;">
      <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#c82333);color:white;padding:14px 36px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:16px;letter-spacing:0.5px;">🚀 今すぐ参加する</a>
    </div>
    <hr style="margin:20px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:11px;text-align:center;">投資は自己責任で行ってください。情報は参考目的のみです。</p>
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
        logger.info(f"HOTアラート送信成功: {name} → {GMAIL_RECIPIENT}")
        return True
    except Exception as e:
        logger.error(f"HOTアラート送信失敗: {e}")
        return False
