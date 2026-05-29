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
    diff = diff or {"added": [], "removed": [], "changed": []}

    # ===== 新着ホット案件アラート (最優先) =====
    newly_hot = [a for a in diff.get("added", []) if a.get("is_hot")]
    hot_alert_html = ""
    if newly_hot:
        alert_rows = ""
        for a in newly_hot:
            value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
            tasks_html = "".join(f"<li>{t}</li>" for t in a.get("tasks", []))
            alert_rows += f"""
            <div style="background:#fff0f0;border:2px solid #dc3545;border-radius:8px;padding:16px;margin-bottom:12px;">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                <span style="font-size:22px;">🚨</span>
                <div>
                  <strong style="font-size:16px;color:#dc3545;">{a['name']}</strong>
                  <span style="background:#dc3545;color:white;font-size:11px;padding:2px 8px;border-radius:12px;margin-left:8px;">NEW HOT</span>
                </div>
              </div>
              <p style="margin:0 0 6px;color:#333;">{a.get('description','')}</p>
              <p style="margin:0 0 4px;"><strong>推定価値:</strong> <span style="color:#28a745;font-weight:bold;font-size:15px;">{value}</span></p>
              <p style="margin:0 0 4px;"><strong>カテゴリ:</strong> {a.get('category','')} &nbsp; <strong>難易度:</strong> {a.get('difficulty','').upper()}</p>
              <p style="margin:0 0 8px;"><strong>期限:</strong> {a.get('end_date','未定')}</p>
              {'<p style="margin:0 0 4px;"><strong>参加方法:</strong></p><ul style="margin:4px 0;">' + tasks_html + '</ul>' if tasks_html else ''}
              <a href="{a.get('url','#')}" style="display:inline-block;background:#dc3545;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold;margin-top:8px;">今すぐ参加する →</a>
            </div>"""
        hot_alert_html = f"""
        <div style="margin-bottom:24px;">
          <h2 style="color:#dc3545;margin:0 0 12px;font-size:18px;">🚨 注目の新着ホット案件！</h2>
          {alert_rows}
        </div>"""

    # ===== 変更サマリーバナー =====
    added_count = len(diff.get("added", []))
    removed_count = len(diff.get("removed", []))
    changed_count = len(diff.get("changed", []))

    summary_chips = ""
    if added_count:
        summary_chips += f'<span style="background:#d4edda;color:#155724;border:1px solid #c3e6cb;padding:4px 12px;border-radius:20px;font-size:13px;font-weight:700;margin:3px;">🆕 新着 {added_count}件</span>'
    if removed_count:
        summary_chips += f'<span style="background:#f8d7da;color:#721c24;border:1px solid #f5c6cb;padding:4px 12px;border-radius:20px;font-size:13px;font-weight:700;margin:3px;">🗑 削除 {removed_count}件</span>'
    if changed_count:
        summary_chips += f'<span style="background:#fff3cd;color:#856404;border:1px solid #ffc107;padding:4px 12px;border-radius:20px;font-size:13px;font-weight:700;margin:3px;">✏️ 変更 {changed_count}件</span>'
    if not (added_count or removed_count or changed_count):
        summary_chips = '<span style="color:#6c757d;font-size:13px;">本日の変更なし (定期チェック)</span>'

    # ===== 新着一覧 =====
    new_html = ""
    if new_items:
        items_html = "".join(f"<li>{n}</li>" for n in new_items)
        new_html = f"""
        <div style="background:#d4edda;border-left:4px solid #28a745;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>🆕 新着エアドロップ ({len(new_items)}件)</strong>
          <ul style="margin:8px 0 0 0;">{items_html}</ul>
        </div>"""

    # ===== 削除された案件 =====
    removed_html = ""
    if diff.get("removed"):
        removed_items = "".join(f"<li>{n}</li>" for n in diff["removed"])
        removed_html = f"""
        <div style="background:#f8d7da;border-left:4px solid #dc3545;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>🗑 終了・削除された案件 ({len(diff['removed'])}件)</strong>
          <ul style="margin:8px 0 0 0;">{removed_items}</ul>
        </div>"""

    # ===== ステータス・価値変更 =====
    changed_html = ""
    if diff.get("changed"):
        ch_rows = ""
        for c in diff["changed"]:
            changes_text = " / ".join(c.get("changes", []))
            ch_rows += f"<tr><td style='padding:6px 10px;border-bottom:1px solid #dee2e6;'><strong>{c['name']}</strong></td><td style='padding:6px 10px;border-bottom:1px solid #dee2e6;color:#856404;'>{changes_text}</td></tr>"
        changed_html = f"""
        <div style="margin:16px 0;">
          <strong>✏️ 変更された案件</strong>
          <table style="width:100%;border-collapse:collapse;margin-top:8px;font-size:13px;">
            <thead><tr style="background:#fff3cd;"><th style="padding:6px 10px;text-align:left;">プロジェクト</th><th style="padding:6px 10px;text-align:left;">変更内容</th></tr></thead>
            <tbody>{ch_rows}</tbody>
          </table>
        </div>"""

    # ===== ホットエアドロップ一覧 =====
    hot_rows = ""
    for a in hot[:5]:
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
        <h3 style="color:#6f42c1;">📈 CoinGecko トレンドコイン</h3>
        <ul>{t_items}</ul>"""

    hot_count = len(hot)

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;background:#f8f9fa;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:24px;border-radius:8px 8px 0 0;">
    <h1 style="margin:0;font-size:22px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:4px 0 0;opacity:0.8;">{today} 更新レポート</p>
  </div>
  <div style="background:white;padding:24px;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">

    <!-- 変更サマリー -->
    <div style="background:#f8f9fa;border-radius:8px;padding:12px 16px;margin-bottom:20px;display:flex;flex-wrap:wrap;gap:6px;align-items:center;">
      <strong style="margin-right:8px;">📊 本日の更新:</strong>
      {summary_chips}
    </div>

    {hot_alert_html}
    {new_html}
    {removed_html}
    {changed_html}

    <h3 style="color:#dc3545;">🔥 注目のホットエアドロップ ({hot_count}件)</h3>
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

    diff = diff or {"added": [], "removed": [], "changed": []}
    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    newly_hot = [a for a in diff.get("added", []) if a.get("is_hot")]

    subject = f"[Airdrop] {today} 更新 — ホット案件{hot_count}件"
    if newly_hot:
        subject = f"🚨 [HOT] {today} 新着ホット案件{len(newly_hot)}件！ — {', '.join(a['name'] for a in newly_hot[:2])}"
    elif new_items:
        subject += f" 🆕新着{len(new_items)}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, diff)

    added_names = [a["name"] for a in diff.get("added", [])]
    removed_names = diff.get("removed", [])
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"追加: {', '.join(added_names) if added_names else 'なし'}\n"
        f"削除: {', '.join(removed_names) if removed_names else 'なし'}\n"
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

    tasks_html = "".join(f"<li>{t}</li>" for t in airdrop.get("tasks", []))
    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:#dc3545;color:white;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;">🚨 ホットエアドロップ出現！</h2>
  </div>
  <div style="background:white;padding:20px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 8px 8px;">
    <h3>{name} ({airdrop.get('symbol','')})</h3>
    <p><strong>推定価値:</strong> <span style="color:#28a745;font-size:18px;font-weight:bold;">~${value:,}</span></p>
    <p><strong>カテゴリ:</strong> {airdrop.get('category','')}</p>
    <p><strong>難易度:</strong> {airdrop.get('difficulty','').upper()}</p>
    <p><strong>概要:</strong> {airdrop.get('description','')}</p>
    <p><strong>参加方法:</strong></p>
    <ul>{tasks_html}</ul>
    <p><strong>期限:</strong> {airdrop.get('end_date','未定')}</p>
    <a href="{airdrop.get('url','#')}" style="display:inline-block;background:#dc3545;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold;">今すぐ参加する</a>
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
