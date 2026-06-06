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


def _difficulty_color(diff: str) -> str:
    return {"easy": "#2ed573", "medium": "#ff6348", "hard": "#ff4757"}.get(diff, "#6c757d")


def _urgency_label(urgency: str) -> str:
    return {"urgent": "🚨 緊急", "normal": "📢 更新", "digest": "📋 日次"}.get(urgency, "📋 日次")


def _build_html_body(
    airdrops: list[dict],
    diff: dict,
    trending: list[dict],
    urgency: str,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    added = diff.get("added", [])
    changed = diff.get("changed", [])
    removed = diff.get("removed", [])

    urgency_color = {"urgent": "#dc3545", "normal": "#7c4dff", "digest": "#1e90ff"}.get(urgency, "#7c4dff")

    # 新着セクション
    added_html = ""
    if added:
        rows = ""
        for a in added:
            value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
            hot_mark = "🔥 " if a.get("is_hot") else ""
            rows += f"""
            <tr>
              <td style="padding:10px;border-bottom:1px solid #dee2e6;">
                <strong>{hot_mark}{a['name']}</strong>
                <span style="background:#e9ecef;color:#495057;padding:2px 6px;border-radius:4px;font-size:11px;margin-left:6px;">{a.get('category','')}</span>
              </td>
              <td style="padding:10px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:bold;">{value}</td>
              <td style="padding:10px;border-bottom:1px solid #dee2e6;">
                <span style="background:{_difficulty_color(a.get('difficulty',''))};color:white;padding:2px 8px;border-radius:12px;font-size:11px;">
                  {a.get('difficulty','').upper()}
                </span>
              </td>
              <td style="padding:10px;border-bottom:1px solid #dee2e6;">{a.get('end_date','未定')}</td>
              <td style="padding:10px;border-bottom:1px solid #dee2e6;">
                <a href="{a.get('url','#')}" style="color:#0d6efd;font-weight:600;">参加 →</a>
              </td>
            </tr>"""
        added_html = f"""
        <div style="background:#d4edda;border-left:4px solid #28a745;padding:4px 0;margin:20px 0 8px;border-radius:0 4px 4px 0;">
          <h3 style="margin:10px 16px;color:#155724;">🆕 新規追加 ({len(added)}件)</h3>
        </div>
        <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
          <thead>
            <tr style="background:#f8f9fa;">
              <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">プロジェクト</th>
              <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">推定価値</th>
              <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">難易度</th>
              <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">期限</th>
              <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">リンク</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>"""

    # 変更セクション
    changed_html = ""
    if changed:
        items = "".join(
            f"<li style='margin:6px 0;'><strong>{c['name']}</strong>: {' / '.join(c['changes'])}</li>"
            for c in changed
        )
        changed_html = f"""
        <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:12px 16px;margin:16px 0;border-radius:0 4px 4px 0;">
          <strong>✏️ 変更 ({len(changed)}件)</strong>
          <ul style="margin:8px 0 0 16px;">{items}</ul>
        </div>"""

    # 削除セクション
    removed_html = ""
    if removed:
        items = "".join(f"<li>{n}</li>" for n in removed)
        removed_html = f"""
        <div style="background:#f8d7da;border-left:4px solid #dc3545;padding:12px 16px;margin:16px 0;border-radius:0 4px 4px 0;">
          <strong>🗑 終了・削除 ({len(removed)}件)</strong>
          <ul style="margin:8px 0 0 16px;">{items}</ul>
        </div>"""

    # ホット案件テーブル
    hot_rows = ""
    for a in hot[:6]:
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        tasks_html = ""
        if a.get("tasks"):
            tasks_li = "".join(f"<li style='font-size:11px;color:#666;'>{t}</li>" for t in a["tasks"][:3])
            tasks_html = f"<ul style='margin:4px 0 0 16px;padding:0;'>{tasks_li}</ul>"
        hot_rows += f"""
        <tr>
          <td style="padding:12px 10px;border-bottom:1px solid #dee2e6;">
            <strong>{a['name']}</strong>
            <span style="font-size:11px;color:#888;margin-left:4px;">{a.get('symbol','')}</span><br>
            <span style="background:rgba(124,77,255,0.1);color:#7c4dff;padding:1px 6px;border-radius:4px;font-size:11px;">{a.get('category','')}</span>
            {tasks_html}
          </td>
          <td style="padding:12px 10px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:bold;font-size:16px;">{value}</td>
          <td style="padding:12px 10px;border-bottom:1px solid #dee2e6;">
            <span style="background:{_difficulty_color(a.get('difficulty',''))};color:white;padding:3px 10px;border-radius:12px;font-size:12px;">
              {a.get('difficulty','').upper()}
            </span>
          </td>
          <td style="padding:12px 10px;border-bottom:1px solid #dee2e6;font-size:13px;">{a.get('end_date','未定')}</td>
          <td style="padding:12px 10px;border-bottom:1px solid #dee2e6;">
            <a href="{a.get('url','#')}" style="display:inline-block;background:#7c4dff;color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:700;">参加 →</a>
          </td>
        </tr>"""

    # トレンドセクション
    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li style='margin:4px 0;'><strong>{t['name']}</strong> "
            f"<span style='color:#888;font-size:12px;'>({t['symbol']})</span></li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#6f42c1;margin-top:24px;">📈 CoinGecko トレンドコイン</h3>
        <ul style="column-count:2;column-gap:20px;">{t_items}</ul>"""

    # 変更なし時のメッセージ
    no_changes_html = ""
    if not added and not changed and not removed:
        no_changes_html = """
        <div style="background:#e9ecef;border-radius:8px;padding:14px;margin:16px 0;text-align:center;color:#6c757d;">
          本日は新規追加・変更はありませんでした。引き続きエアドロップを追跡中です。
        </div>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Hiragino Sans','Meiryo',Arial,sans-serif;max-width:720px;margin:0 auto;background:#f4f6f9;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:28px 24px;border-radius:10px 10px 0 0;">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
      <div>
        <h1 style="margin:0;font-size:22px;font-weight:800;">🪂 Crypto Airdrop Tracker</h1>
        <p style="margin:6px 0 0;opacity:0.75;font-size:14px;">{today} 更新レポート</p>
      </div>
      <span style="background:{urgency_color};color:white;padding:6px 16px;border-radius:20px;font-size:13px;font-weight:700;">
        {_urgency_label(urgency)}
      </span>
    </div>
  </div>

  <div style="background:white;padding:24px;border-radius:0 0 10px 10px;box-shadow:0 4px 20px rgba(0,0,0,0.1);">

    {added_html}
    {changed_html}
    {removed_html}
    {no_changes_html}

    <h3 style="color:#dc3545;margin-top:24px;border-bottom:2px solid #dc3545;padding-bottom:8px;">🔥 注目ホットエアドロップ一覧</h3>
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr style="background:#f8f9fa;">
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">プロジェクト</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">推定価値</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">難易度</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">期限</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;">参加</th>
        </tr>
      </thead>
      <tbody>{hot_rows}</tbody>
    </table>

    {trending_html}

    <hr style="margin:28px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:11px;margin:0;line-height:1.6;">
      ※ このメールはCrypto Airdrop Trackerから毎日08:00 JSTに自動送信されています。<br>
      情報は参考目的のみです。投資は自己責任で行ってください。
    </p>
  </div>
</body>
</html>"""


def send_daily_report(
    airdrops: list[dict],
    diff: dict,
    trending: list[dict],
    urgency: str = "digest",
) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    added = diff.get("added", [])
    changed = diff.get("changed", [])

    urgency_prefix = {"urgent": "🚨", "normal": "📢", "digest": "📋"}.get(urgency, "📋")
    subject = f"{urgency_prefix} [Airdrop {today}] ホット{hot_count}件"
    if added:
        subject += f" 🆕新着{len(added)}件"
    if any(a.get("is_hot") for a in added):
        subject += " 🔥注目新案件あり！"
    if changed:
        subject += f" ✏️変更{len(changed)}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, diff, trending, urgency)

    added_names = [a["name"] for a in added]
    plain = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(added_names) if added_names else 'なし'}\n"
        f"変更: {len(changed)}件\n"
    )

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"メール送信成功: {GMAIL_RECIPIENT} / 件名: {subject}")
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
    value = airdrop.get("estimated_value_usd", 0) or 0
    symbol = airdrop.get("symbol", "")
    subject = f"🚨 [緊急HOT] {name} — 推定${value:,}の注目新案件が出現！今すぐチェック"

    tasks_li = "".join(f"<li>{t}</li>" for t in airdrop.get("tasks", []))

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:'Hiragino Sans','Meiryo',Arial,sans-serif;max-width:620px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#dc3545,#ff6348);color:white;padding:24px;border-radius:10px 10px 0 0;">
    <h2 style="margin:0;font-size:20px;">🚨 新規ホットエアドロップ出現！</h2>
    <p style="margin:6px 0 0;opacity:0.9;">見逃さないでください！</p>
  </div>
  <div style="background:white;padding:24px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 10px 10px;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
    <h2 style="margin-top:0;color:#1a1a2e;">{name} {f'({symbol})' if symbol else ''}</h2>

    <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
      <tr>
        <td style="padding:10px;background:#f8f9fa;font-weight:700;width:35%;border-radius:6px 0 0 0;">💰 推定価値</td>
        <td style="padding:10px;background:#d4edda;color:#155724;font-weight:800;font-size:20px;border-radius:0 6px 0 0;">~${value:,}</td>
      </tr>
      <tr>
        <td style="padding:10px;background:#f8f9fa;font-weight:700;">📁 カテゴリ</td>
        <td style="padding:10px;">{airdrop.get('category','')}</td>
      </tr>
      <tr>
        <td style="padding:10px;background:#f8f9fa;font-weight:700;">🎯 難易度</td>
        <td style="padding:10px;">{airdrop.get('difficulty','').upper()}</td>
      </tr>
      <tr>
        <td style="padding:10px;background:#f8f9fa;font-weight:700;border-radius:0 0 0 6px;">📅 期限</td>
        <td style="padding:10px;border-radius:0 0 6px 0;">{airdrop.get('end_date','未定')}</td>
      </tr>
    </table>

    <p style="color:#333;"><strong>概要:</strong> {airdrop.get('description','')}</p>

    {"<p><strong>📋 参加方法:</strong></p><ul style='margin:4px 0;'>" + tasks_li + "</ul>" if tasks_li else ""}

    <div style="text-align:center;margin:24px 0 16px;">
      <a href="{airdrop.get('url','#')}"
         style="display:inline-block;background:linear-gradient(135deg,#dc3545,#ff6348);color:white;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:800;font-size:16px;letter-spacing:0.5px;">
        🔥 今すぐ参加する →
      </a>
    </div>
    <hr style="margin:20px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:11px;">投資は自己責任で行ってください。</p>
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
