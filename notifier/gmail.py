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


def _build_html_body(airdrops: list[dict], new_items: list[str], trending: list[dict],
                     changes: list[dict] | None = None) -> str:
    today = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    hot = [a for a in airdrops if a.get("is_hot")]
    hot_count = len(hot)
    total_count = len(airdrops)

    # 新着セクション
    new_html = ""
    if new_items:
        tags = "".join(
            f'<span style="display:inline-block;background:#d4edda;color:#155724;'
            f'border:1px solid #c3e6cb;padding:3px 10px;border-radius:12px;'
            f'font-size:13px;margin:3px 4px 3px 0;">'
            f'🆕 {n}</span>'
            for n in new_items
        )
        new_html = f"""
        <div style="background:#f0fff4;border-left:5px solid #28a745;padding:14px 18px;margin:0 0 20px;border-radius:6px;">
          <strong style="color:#155724;font-size:15px;">🆕 新着エアドロップ {len(new_items)}件</strong>
          <div style="margin-top:10px;">{tags}</div>
        </div>"""

    # 変更点セクション
    changes_html = ""
    if changes:
        change_rows = "".join(
            f'<li style="margin-bottom:6px;"><strong>{c["name"]}</strong>: '
            f'{" / ".join(c.get("changes", []))}</li>'
            for c in changes[:5]
        )
        changes_html = f"""
        <div style="background:#fff8e1;border-left:5px solid #ffc107;padding:14px 18px;margin:0 0 20px;border-radius:6px;">
          <strong style="color:#856404;font-size:15px;">✏️ 変更された案件 {len(changes)}件</strong>
          <ul style="margin:10px 0 0;padding-left:20px;color:#533f03;">{change_rows}</ul>
        </div>"""

    # ホット案件テーブル
    hot_rows = ""
    for a in hot[:7]:
        diff_map = {"easy": ("#28a745", "EASY"), "medium": ("#fd7e14", "MEDIUM"), "hard": ("#dc3545", "HARD")}
        dc, dl = diff_map.get(a.get("difficulty", "easy"), ("#6c757d", "?"))
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        is_new = a.get("name") in new_items
        new_badge = '<span style="background:#28a745;color:white;font-size:10px;padding:1px 6px;border-radius:8px;margin-left:6px;">NEW</span>' if is_new else ""
        hot_rows += f"""
        <tr>
          <td style="padding:11px 10px;border-bottom:1px solid #e9ecef;">
            {f'<img src="{a["logo"]}" width="22" height="22" style="border-radius:50%;vertical-align:middle;margin-right:6px;" onerror="this.style.display=\'none\'">' if a.get('logo') else ''}
            <strong>{a['name']}</strong>{new_badge}<br>
            <span style="color:#6c757d;font-size:11px;">{a.get('description','')[:60]}{'...' if len(a.get('description',''))>60 else ''}</span>
          </td>
          <td style="padding:11px 10px;border-bottom:1px solid #e9ecef;color:#198754;font-weight:700;font-size:15px;">{value}</td>
          <td style="padding:11px 10px;border-bottom:1px solid #e9ecef;">
            <span style="background:{dc};color:white;padding:3px 8px;border-radius:10px;font-size:11px;font-weight:700;">{dl}</span>
          </td>
          <td style="padding:11px 10px;border-bottom:1px solid #e9ecef;color:#495057;font-size:13px;">{a.get('end_date','未定')}</td>
          <td style="padding:11px 10px;border-bottom:1px solid #e9ecef;">
            <a href="{a.get('url','#')}" style="background:#6f42c1;color:white;padding:5px 12px;border-radius:6px;font-size:12px;font-weight:700;text-decoration:none;">参加する</a>
          </td>
        </tr>"""

    # トレンドコイン
    trending_html = ""
    if trending:
        t_items = "".join(
            f'<tr><td style="padding:8px 10px;border-bottom:1px solid #e9ecef;">#{i+1}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #e9ecef;font-weight:700;">{t["name"]}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #e9ecef;color:#6c757d;">{t["symbol"]}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #e9ecef;">スコア: {t.get("score",0)}</td></tr>'
            for i, t in enumerate(trending[:5])
        )
        trending_html = f"""
        <h3 style="color:#6f42c1;margin:28px 0 12px;">📈 CoinGecko トレンドコイン TOP5</h3>
        <table style="width:100%;border-collapse:collapse;background:#f8f0ff;border-radius:8px;overflow:hidden;">
          <tbody>{t_items}</tbody>
        </table>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="font-family:'Helvetica Neue',Arial,'Hiragino Sans',sans-serif;max-width:720px;margin:0 auto;background:#f4f6f9;padding:20px 0;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);color:white;padding:28px 28px 20px;border-radius:12px 12px 0 0;">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
      <div>
        <h1 style="margin:0;font-size:24px;font-weight:800;">🪂 Crypto Airdrop Tracker</h1>
        <p style="margin:5px 0 0;opacity:0.75;font-size:14px;">デイリーレポート · {today} JST</p>
      </div>
      <div style="text-align:right;">
        <div style="font-size:28px;font-weight:900;color:#2ed573;">{total_count}<span style="font-size:14px;opacity:0.7;"> 件追跡中</span></div>
        <div style="font-size:14px;color:#ff6b81;">🔥 HOT: {hot_count}件</div>
      </div>
    </div>
  </div>

  <!-- サマリーバー -->
  <div style="background:#fff;border-left:1px solid #e0e0e0;border-right:1px solid #e0e0e0;padding:14px 28px;display:flex;gap:20px;flex-wrap:wrap;">
    <span style="font-size:13px;color:#495057;">📊 本日のサマリー:</span>
    <span style="font-size:13px;color:#198754;font-weight:700;">🆕 新着 {len(new_items)}件</span>
    <span style="font-size:13px;color:#fd7e14;font-weight:700;">✏️ 変更 {len(changes) if changes else 0}件</span>
    <span style="font-size:13px;color:#dc3545;font-weight:700;">🔥 ホット {hot_count}件</span>
  </div>

  <!-- メインコンテンツ -->
  <div style="background:white;padding:24px 28px;border:1px solid #e0e0e0;border-top:none;border-radius:0 0 12px 12px;box-shadow:0 4px 16px rgba(0,0,0,0.08);">

    {new_html}
    {changes_html}

    <!-- ホット案件テーブル -->
    <h3 style="color:#dc3545;margin:0 0 14px;font-size:17px;">🔥 注目のホットエアドロップ</h3>
    <table style="width:100%;border-collapse:collapse;margin-bottom:24px;border-radius:8px;overflow:hidden;border:1px solid #e9ecef;">
      <thead>
        <tr style="background:#fff5f5;">
          <th style="padding:11px 10px;text-align:left;border-bottom:2px solid #f8d7da;color:#dc3545;font-size:12px;">プロジェクト</th>
          <th style="padding:11px 10px;text-align:left;border-bottom:2px solid #f8d7da;color:#dc3545;font-size:12px;">推定価値</th>
          <th style="padding:11px 10px;text-align:left;border-bottom:2px solid #f8d7da;color:#dc3545;font-size:12px;">難易度</th>
          <th style="padding:11px 10px;text-align:left;border-bottom:2px solid #f8d7da;color:#dc3545;font-size:12px;">期限</th>
          <th style="padding:11px 10px;text-align:left;border-bottom:2px solid #f8d7da;color:#dc3545;font-size:12px;">参加</th>
        </tr>
      </thead>
      <tbody>{hot_rows if hot_rows else '<tr><td colspan="5" style="padding:16px;text-align:center;color:#6c757d;">現在ホット案件なし</td></tr>'}</tbody>
    </table>

    {trending_html}

    <hr style="margin:28px 0 20px;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:11px;margin:0;line-height:1.7;">
      ※ このメールは Crypto Airdrop Tracker から毎日 08:00 JST に自動送信されています。<br>
      ※ 掲載情報は参考目的のみです。投資は自己責任で行ってください。損失について一切の責任を負いません。
    </p>
  </div>
</body>
</html>"""


def send_daily_report(airdrops: list[dict], new_items: list[str], trending: list[dict],
                      changes: list[dict] | None = None) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    subject = f"[Airdrop] {today} デイリーレポート — ホット{hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"
    elif not changes:
        subject += " (変更なし)"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, changes)
    plain_body = (
        f"{today} Airdrop デイリーレポート\n"
        f"ホット案件: {hot_count}件 / 合計: {len(airdrops)}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"変更: {len(changes) if changes else 0}件"
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

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:#dc3545;color:white;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;">🚨 ホットエアドロップ出現！</h2>
  </div>
  <div style="background:white;padding:20px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 8px 8px;">
    <h3>{name} ({airdrop.get('symbol','')})</h3>
    <p><strong>推定価値:</strong> ~${value:,}</p>
    <p><strong>カテゴリ:</strong> {airdrop.get('category','')}</p>
    <p><strong>難易度:</strong> {airdrop.get('difficulty','').upper()}</p>
    <p><strong>概要:</strong> {airdrop.get('description','')}</p>
    <p><strong>参加方法:</strong></p>
    <ul>{"".join(f"<li>{t}</li>" for t in airdrop.get('tasks', []))}</ul>
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
