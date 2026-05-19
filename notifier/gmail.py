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
    diff = diff or {}
    changes = diff.get("changed", [])
    removed = diff.get("removed", [])

    # ===== 新着セクション =====
    new_html = ""
    if new_items:
        items_html = "".join(
            f'<li style="margin:6px 0;"><strong>{n}</strong></li>' for n in new_items
        )
        new_html = f"""
        <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:14px 18px;margin:16px 0;border-radius:6px;">
          <p style="margin:0 0 8px;font-weight:700;font-size:15px;">🆕 新着エアドロップ ({len(new_items)}件)</p>
          <ul style="margin:0;padding-left:20px;">{items_html}</ul>
        </div>"""

    # ===== 変更セクション =====
    change_html = ""
    if changes:
        change_rows = ""
        for ch in changes[:8]:
            change_rows += f"""
            <tr>
              <td style="padding:8px 12px;border-bottom:1px solid #e9ecef;font-weight:600;">{ch['name']}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #e9ecef;color:#6c757d;">{'<br>'.join(ch['changes'])}</td>
            </tr>"""
        change_html = f"""
        <div style="background:#e8f4f8;border-left:4px solid #17a2b8;padding:14px 18px;margin:16px 0;border-radius:6px;">
          <p style="margin:0 0 10px;font-weight:700;font-size:15px;">✏️ 更新された案件 ({len(changes)}件)</p>
          <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead>
              <tr style="background:#d1ecf1;">
                <th style="padding:8px 12px;text-align:left;">プロジェクト</th>
                <th style="padding:8px 12px;text-align:left;">変更内容</th>
              </tr>
            </thead>
            <tbody>{change_rows}</tbody>
          </table>
        </div>"""

    # ===== 削除セクション =====
    removed_html = ""
    if removed:
        removed_html = f"""
        <div style="background:#f8d7da;border-left:4px solid #dc3545;padding:10px 14px;margin:16px 0;border-radius:6px;font-size:13px;">
          <strong>🗑 削除された案件:</strong> {', '.join(removed)}
        </div>"""

    # ===== ホット案件テーブル =====
    hot_rows = ""
    for a in hot[:6]:
        difficulty_color = {
            "easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"
        }.get(a.get("difficulty", "easy"), "#6c757d")
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "不明"
        status_label = {"active": "● アクティブ", "upcoming": "◎ 近日", "ended": "✕ 終了"}.get(
            a.get("status", ""), a.get("status", "")
        )
        status_color = {"active": "#28a745", "upcoming": "#ffc107", "ended": "#6c757d"}.get(
            a.get("status", ""), "#6c757d"
        )
        hot_rows += f"""
        <tr>
          <td style="padding:10px 12px;border-bottom:1px solid #dee2e6;">
            <strong>{a['name']}</strong><br>
            <span style="color:#6c757d;font-size:11px;">{a.get('category','')}</span>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:700;">{value}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #dee2e6;">
            <span style="background:{difficulty_color};color:white;padding:2px 8px;border-radius:12px;font-size:11px;">
              {a.get('difficulty','').upper()}
            </span>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #dee2e6;color:{status_color};font-size:12px;">{status_label}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #dee2e6;font-size:12px;">{a.get('end_date','未定')}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #dee2e6;">
            <a href="{a.get('url','#')}" style="color:#0d6efd;font-size:12px;">参加する →</a>
          </td>
        </tr>"""

    # ===== トレンドセクション =====
    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li style='margin:4px 0;'><strong>{t['name']}</strong> ({t['symbol']}) "
            f"— スコア: {t.get('score', 0)} "
            f"{'| ランク #' + str(t['rank']) if t.get('rank') else ''}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <div style="margin-top:24px;">
          <h3 style="color:#6f42c1;margin-bottom:8px;">📈 CoinGecko トレンドコイン TOP5</h3>
          <ul style="padding-left:20px;color:#495057;">{t_items}</ul>
        </div>"""

    # ===== サマリー数値 =====
    total = len(airdrops)
    hot_count = len(hot)
    new_count = len(new_items)

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:'Hiragino Sans','Meiryo',Arial,sans-serif;max-width:720px;margin:0 auto;background:#f4f6f9;padding:16px;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:24px 28px;border-radius:10px 10px 0 0;">
    <h1 style="margin:0 0 6px;font-size:22px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:0;opacity:0.8;font-size:14px;">{today} 日次更新レポート</p>
  </div>

  <!-- サマリーバー -->
  <div style="background:#0d6efd;padding:14px 28px;display:flex;gap:20px;flex-wrap:wrap;">
    <span style="color:white;font-size:14px;">📋 総案件数: <strong>{total}</strong></span>
    <span style="color:#ffd700;font-size:14px;">🔥 ホット: <strong>{hot_count}</strong></span>
    {'<span style="color:#90ee90;font-size:14px;">🆕 新着: <strong>' + str(new_count) + '</strong></span>' if new_count else ''}
    {'<span style="color:#ffb347;font-size:14px;">✏️ 変更: <strong>' + str(len(changes)) + '</strong></span>' if changes else ''}
  </div>

  <!-- コンテンツ -->
  <div style="background:white;padding:24px 28px;border-radius:0 0 10px 10px;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

    {new_html}
    {change_html}
    {removed_html}

    <!-- ホット案件 -->
    <h3 style="color:#dc3545;border-bottom:2px solid #dc3545;padding-bottom:8px;margin-top:24px;">
      🔥 注目のホットエアドロップ ({hot_count}件)
    </h3>
    <div style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;min-width:500px;">
        <thead>
          <tr style="background:#f8f9fa;">
            <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">プロジェクト</th>
            <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">推定価値</th>
            <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">難易度</th>
            <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">状態</th>
            <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">期限</th>
            <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">リンク</th>
          </tr>
        </thead>
        <tbody>{hot_rows}</tbody>
      </table>
    </div>

    {trending_html}

    <!-- 免責 -->
    <hr style="margin:28px 0 16px;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#adb5bd;font-size:11px;margin:0;line-height:1.7;">
      ※ このメールはCrypto Airdrop Trackerから自動送信されています。<br>
      掲載情報は参考目的のみです。投資・参加は自己責任で行ってください。<br>
      配信停止は .env の GMAIL_RECIPIENT を空にしてください。
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
    diff = diff or {}
    changes = diff.get("changed", [])

    subject_parts = [f"[Airdrop] {today} 日次レポート — HOT {hot_count}件"]
    if new_items:
        subject_parts.append(f"🆕新着{len(new_items)}件")
    if changes:
        subject_parts.append(f"✏️変更{len(changes)}件")

    subject = " | ".join(subject_parts)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, diff)
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"変更: {len(changes)}件\n"
        f"トレンド: {', '.join(t['name'] for t in trending[:3])}"
    )

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"日次レポートメール送信成功: {GMAIL_RECIPIENT}")
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
    difficulty = airdrop.get("difficulty", "").upper()
    subject = f"🚨 [HOT新着] {name} — 推定${value:,} | 今すぐチェック！"

    tasks_html = "".join(f"<li>{t}</li>" for t in airdrop.get("tasks", []))

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:'Hiragino Sans','Meiryo',Arial,sans-serif;max-width:600px;margin:0 auto;background:#f4f6f9;padding:16px;">
  <div style="background:linear-gradient(135deg,#dc3545,#c62535);color:white;padding:24px;border-radius:10px 10px 0 0;">
    <h2 style="margin:0 0 4px;font-size:20px;">🚨 ホット新着エアドロップ！</h2>
    <p style="margin:0;opacity:0.9;font-size:13px;">見逃し厳禁 — 今すぐ参加チェックを！</p>
  </div>
  <div style="background:white;padding:24px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 10px 10px;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <h3 style="color:#dc3545;margin:0 0 16px;font-size:22px;">{name}</h3>
    <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:16px;">
      <tr style="background:#f8f9fa;">
        <td style="padding:10px;border:1px solid #dee2e6;font-weight:700;width:35%;">推定価値</td>
        <td style="padding:10px;border:1px solid #dee2e6;color:#28a745;font-weight:700;font-size:18px;">~${value:,}</td>
      </tr>
      <tr>
        <td style="padding:10px;border:1px solid #dee2e6;font-weight:700;">カテゴリ</td>
        <td style="padding:10px;border:1px solid #dee2e6;">{airdrop.get('category','')}</td>
      </tr>
      <tr style="background:#f8f9fa;">
        <td style="padding:10px;border:1px solid #dee2e6;font-weight:700;">難易度</td>
        <td style="padding:10px;border:1px solid #dee2e6;">
          <span style="background:#dc3545;color:white;padding:2px 10px;border-radius:12px;font-size:12px;">{difficulty}</span>
        </td>
      </tr>
      <tr>
        <td style="padding:10px;border:1px solid #dee2e6;font-weight:700;">期限</td>
        <td style="padding:10px;border:1px solid #dee2e6;">{airdrop.get('end_date','未定')}</td>
      </tr>
    </table>
    <p style="color:#495057;margin-bottom:8px;"><strong>📝 概要:</strong> {airdrop.get('description','')}</p>
    {'<p style="font-weight:700;margin:16px 0 6px;">📋 参加タスク:</p><ul style="padding-left:20px;color:#495057;">' + tasks_html + '</ul>' if tasks_html else ''}
    <div style="margin-top:20px;text-align:center;">
      <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#c62535);color:white;padding:14px 36px;border-radius:8px;text-decoration:none;font-weight:700;font-size:16px;">
        🚀 今すぐ参加する
      </a>
    </div>
    <hr style="margin:20px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#adb5bd;font-size:11px;margin:0;">投資・参加は自己責任で行ってください。情報は参考目的のみです。</p>
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
        logger.info(f"ホットアラート送信成功: {name} → {GMAIL_RECIPIENT}")
        return True
    except Exception as e:
        logger.error(f"ホットアラート送信失敗: {e}")
        return False
