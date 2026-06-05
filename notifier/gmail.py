"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してメール送信。
毎日日次サマリーを送信し、ホット案件出現時は即時アラートも送信。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)


def _build_changes_html(diff: dict) -> str:
    """追加・削除・変更の差分セクションHTML"""
    if not diff:
        return ""

    added = diff.get("added", [])
    removed_names = diff.get("removed_names", [])
    changed = diff.get("changed", [])

    if not added and not removed_names and not changed:
        return ""

    sections = []

    if added:
        items_html = ""
        for a in added:
            value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
            hot_mark = " 🔥" if a.get("is_hot") else ""
            items_html += f"""
            <li style="margin:6px 0;">
              <strong>{a['name']}{hot_mark}</strong>
              <span style="color:#28a745;margin-left:8px;">{value}</span>
              <span style="color:#6c757d;font-size:12px;margin-left:8px;">{a.get('category','')}</span>
            </li>"""
        sections.append(f"""
        <div style="background:#d4edda;border-left:4px solid #28a745;padding:12px 16px;margin:12px 0;border-radius:4px;">
          <strong style="color:#155724;">🆕 新規追加 ({len(added)}件)</strong>
          <ul style="margin:8px 0 0 0;padding-left:20px;">{items_html}</ul>
        </div>""")

    if removed_names:
        items_html = "".join(f"<li style='margin:4px 0;color:#721c24;'>{n}</li>" for n in removed_names)
        sections.append(f"""
        <div style="background:#f8d7da;border-left:4px solid #dc3545;padding:12px 16px;margin:12px 0;border-radius:4px;">
          <strong style="color:#721c24;">🗑️ 終了・削除 ({len(removed_names)}件)</strong>
          <ul style="margin:8px 0 0 0;padding-left:20px;">{items_html}</ul>
        </div>""")

    if changed:
        items_html = ""
        for c in changed:
            change_list = "".join(f"<li style='color:#856404;font-size:12px;'>{ch}</li>" for ch in c.get("changes", []))
            items_html += f"""
            <li style="margin:6px 0;">
              <strong>{c['name']}</strong>
              <ul style="margin:4px 0 0 0;padding-left:16px;">{change_list}</ul>
            </li>"""
        sections.append(f"""
        <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:12px 16px;margin:12px 0;border-radius:4px;">
          <strong style="color:#856404;">✏️ 情報変更 ({len(changed)}件)</strong>
          <ul style="margin:8px 0 0 0;padding-left:20px;">{items_html}</ul>
        </div>""")

    return "".join(sections)


def _build_html_body(airdrops: list[dict], new_items: list[str], trending: list[dict], diff: dict = None) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    changes_html = _build_changes_html(diff)

    no_changes_notice = ""
    if not changes_html:
        no_changes_notice = """
        <div style="background:#e8f4f8;border-left:4px solid #17a2b8;padding:10px 16px;margin:12px 0;border-radius:4px;">
          <span style="color:#0c5460;">ℹ️ 本日の変更なし — 引き続き既存の案件をチェックしてください</span>
        </div>"""

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
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;background:#f8f9fa;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:24px;border-radius:8px 8px 0 0;">
    <h1 style="margin:0;font-size:22px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:4px 0 0;opacity:0.8;">{today} 日次更新レポート</p>
  </div>
  <div style="background:white;padding:24px;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">

    <!-- サマリー -->
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px;">
      <div style="background:#e8f4f8;border-radius:8px;padding:10px 16px;text-align:center;min-width:100px;">
        <div style="font-size:22px;font-weight:800;color:#17a2b8;">{total}</div>
        <div style="font-size:12px;color:#6c757d;">総案件数</div>
      </div>
      <div style="background:#fff0f0;border-radius:8px;padding:10px 16px;text-align:center;min-width:100px;">
        <div style="font-size:22px;font-weight:800;color:#dc3545;">{hot_count}</div>
        <div style="font-size:12px;color:#6c757d;">🔥 ホット案件</div>
      </div>
    </div>

    {changes_html}
    {no_changes_notice}

    <h3 style="color:#dc3545;margin-top:20px;">🔥 注目のホットエアドロップ TOP5</h3>
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
    """毎日の日次レポートをtsukamoto.kei@gmail.comに送信"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))

    added_count = len(diff.get("added", [])) if diff else len(new_items)
    removed_count = len(diff.get("removed_names", [])) if diff else 0
    changed_count = len(diff.get("changed", [])) if diff else 0

    subject_parts = [f"[Airdrop] {today} 日次レポート — ホット{hot_count}件"]
    if added_count:
        subject_parts.append(f"🆕新着{added_count}件")
    if removed_count:
        subject_parts.append(f"🗑️削除{removed_count}件")
    if changed_count:
        subject_parts.append(f"✏️変更{changed_count}件")
    subject = " ".join(subject_parts)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, diff)
    plain_parts = [
        f"{today} Airdrop日次レポート",
        f"ホット案件: {hot_count}件 / 総案件: {len(airdrops)}件",
    ]
    if added_count:
        plain_parts.append(f"新着: {', '.join(a['name'] for a in diff.get('added', []))}")
    if removed_count:
        plain_parts.append(f"削除: {', '.join(diff.get('removed_names', []))}")
    plain_body = "\n".join(plain_parts)

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"日次レポート送信成功: {GMAIL_RECIPIENT} ({subject})")
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
    subject = f"🚨 [HOT Airdrop出現] {name} — 推定${value:,} | 今すぐ確認！"

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#dc3545,#c82333);color:white;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;">🚨 新しいホットエアドロップが登場！</h2>
    <p style="margin:4px 0 0;opacity:0.9;">見逃し厳禁の注目案件です</p>
  </div>
  <div style="background:white;padding:20px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 8px 8px;">
    <h3 style="font-size:20px;">{name} <span style="color:#6c757d;font-size:14px;">({airdrop.get('symbol','')})</span></h3>
    <table style="width:100%;border-collapse:collapse;margin:12px 0;">
      <tr><td style="padding:8px 0;color:#6c757d;width:120px;">推定価値</td><td style="padding:8px 0;font-weight:800;color:#28a745;font-size:18px;">~${value:,}</td></tr>
      <tr><td style="padding:8px 0;color:#6c757d;">カテゴリ</td><td style="padding:8px 0;">{airdrop.get('category','')}</td></tr>
      <tr><td style="padding:8px 0;color:#6c757d;">難易度</td><td style="padding:8px 0;">{airdrop.get('difficulty','').upper()}</td></tr>
      <tr><td style="padding:8px 0;color:#6c757d;">期限</td><td style="padding:8px 0;">{airdrop.get('end_date','未定')}</td></tr>
    </table>
    <p style="background:#f8f9fa;padding:12px;border-radius:6px;color:#333;">{airdrop.get('description','')}</p>
    <p><strong>📋 参加方法:</strong></p>
    <ul style="padding-left:20px;">{"".join(f"<li style='margin:6px 0;'>{t}</li>" for t in airdrop.get('tasks', []))}</ul>
    <div style="margin-top:20px;">
      <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#c82333);color:white;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:16px;">🚀 今すぐ参加する</a>
    </div>
    <hr style="margin:20px 0;">
    <p style="color:#6c757d;font-size:12px;">投資は自己責任で行ってください。このアラートはCrypto Airdrop Trackerから自動送信されています。</p>
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
        logger.info(f"ホットアラート送信: {name} → {GMAIL_RECIPIENT}")
        return True
    except Exception as e:
        logger.error(f"ホットアラート送信失敗: {e}")
        return False
