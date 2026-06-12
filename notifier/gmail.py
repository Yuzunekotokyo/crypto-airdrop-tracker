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

_DIFFICULTY_COLOR = {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}
_STATUS_LABEL = {"active": "アクティブ", "upcoming": "近日開始", "ended": "終了"}


def _value_str(a: dict) -> str:
    v = a.get("estimated_value_usd", 0)
    return f"~${v:,}" if v else "未定"


def _airdrop_card_html(a: dict) -> str:
    diff_color = _DIFFICULTY_COLOR.get(a.get("difficulty", "easy"), "#6c757d")
    status_label = _STATUS_LABEL.get(a.get("status", "active"), a.get("status", ""))
    hot_badge = '<span style="background:#dc3545;color:white;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700;margin-left:8px;">🔥 HOT</span>' if a.get("is_hot") else ""
    tasks_html = ""
    if a.get("tasks"):
        items = "".join(f"<li style='margin:3px 0;font-size:13px;color:#555;'>{t}</li>" for t in a["tasks"][:4])
        tasks_html = f"<ul style='margin:6px 0 0 16px;padding:0;'>{items}</ul>"

    return f"""
<div style="border:1px solid #dee2e6;border-radius:10px;padding:16px;margin:12px 0;background:#fff;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
    <strong style="font-size:16px;">{a['name']}</strong>
    {hot_badge}
    <span style="margin-left:auto;color:#28a745;font-size:18px;font-weight:800;">{_value_str(a)}</span>
  </div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
    <span style="background:#e9ecef;color:#495057;padding:2px 8px;border-radius:12px;font-size:12px;">{a.get('category','')}</span>
    <span style="background:{diff_color};color:white;padding:2px 8px;border-radius:12px;font-size:12px;">{a.get('difficulty','').upper()}</span>
    <span style="background:#f8f9fa;color:#6c757d;padding:2px 8px;border-radius:12px;font-size:12px;">{status_label}</span>
    <span style="color:#6c757d;font-size:12px;">期限: {a.get('end_date','未定')}</span>
  </div>
  <p style="color:#555;font-size:13px;margin:0 0 8px;">{a.get('description','')}</p>
  {tasks_html}
  <div style="margin-top:12px;">
    <a href="{a.get('url','#')}" style="background:linear-gradient(135deg,#7c4dff,#651fff);color:white;padding:8px 20px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:700;">今すぐ参加する →</a>
  </div>
</div>"""


def _build_html_body(airdrops: list[dict], new_items: list[str], trending: list[dict], diff: dict | None = None) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = sorted([a for a in airdrops if a.get("is_hot")], key=lambda x: -x.get("estimated_value_usd", 0))
    top_value = sorted(airdrops, key=lambda x: -x.get("estimated_value_usd", 0))[:5]

    # 新着セクション
    new_html = ""
    if new_items:
        items_html = "".join(f"<li style='margin:4px 0;'><strong>{n}</strong></li>" for n in new_items)
        new_html = f"""
    <div style="background:#d4edda;border-left:5px solid #28a745;padding:14px 16px;margin:16px 0;border-radius:6px;">
      <strong style="color:#155724;font-size:15px;">🆕 本日の新着エアドロップ ({len(new_items)}件)</strong>
      <ul style="margin:8px 0 0 0;color:#155724;">{items_html}</ul>
    </div>"""

    # 変更セクション
    changes_html = ""
    if diff and diff.get("changed"):
        rows = ""
        for c in diff["changed"][:5]:
            changes_str = " / ".join(c.get("changes", []))
            rows += f"<li style='margin:4px 0;'><strong>{c['name']}</strong>: {changes_str}</li>"
        changes_html = f"""
    <div style="background:#fff3cd;border-left:5px solid #ffc107;padding:14px 16px;margin:16px 0;border-radius:6px;">
      <strong style="color:#856404;font-size:15px;">✏️ 本日の変更 ({len(diff['changed'])}件)</strong>
      <ul style="margin:8px 0 0 0;color:#856404;">{rows}</ul>
    </div>"""

    # 終了案件
    removed_html = ""
    if diff and diff.get("removed"):
        names = "、".join(diff["removed"][:5])
        removed_html = f"""
    <div style="background:#f8d7da;border-left:5px solid #dc3545;padding:10px 16px;margin:10px 0;border-radius:6px;">
      <strong style="color:#721c24;font-size:13px;">⚠️ 終了・削除: {names}</strong>
    </div>"""

    # ホット案件カード
    hot_cards = "".join(_airdrop_card_html(a) for a in hot[:4])

    # Top5 価値ランキング表
    top_rows = ""
    for i, a in enumerate(top_value, 1):
        medal = ["🥇", "🥈", "🥉", "4.", "5."][i - 1]
        diff_color = _DIFFICULTY_COLOR.get(a.get("difficulty", "easy"), "#6c757d")
        top_rows += f"""
    <tr style="{'background:#fff8e1;' if i==1 else ''}">
      <td style="padding:10px;border-bottom:1px solid #dee2e6;">{medal}</td>
      <td style="padding:10px;border-bottom:1px solid #dee2e6;"><strong>{a['name']}</strong></td>
      <td style="padding:10px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:800;">{_value_str(a)}</td>
      <td style="padding:10px;border-bottom:1px solid #dee2e6;">
        <span style="background:{diff_color};color:white;padding:2px 8px;border-radius:12px;font-size:11px;">{a.get('difficulty','').upper()}</span>
      </td>
      <td style="padding:10px;border-bottom:1px solid #dee2e6;">{a.get('end_date','未定')}</td>
      <td style="padding:10px;border-bottom:1px solid #dee2e6;">
        <a href="{a.get('url','#')}" style="color:#7c4dff;font-weight:700;">参加</a>
      </td>
    </tr>"""

    # トレンドコイン
    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li style='margin:4px 0;'><strong>{t['name']}</strong> ({t['symbol']}) — スコア: {t.get('score', 0)}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
    <h3 style="color:#6f42c1;margin-top:28px;">📈 CoinGecko トレンドコイン TOP5</h3>
    <ul style="color:#555;">{t_items}</ul>"""

    hot_count = len(hot)
    active_count = sum(1 for a in airdrops if a.get("status") == "active")

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;max-width:720px;margin:0 auto;background:#f4f6f9;padding:20px;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:28px 24px;border-radius:12px 12px 0 0;">
    <h1 style="margin:0;font-size:24px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:6px 0 0;opacity:0.8;font-size:14px;">{today} 日次更新レポート</p>
    <div style="display:flex;gap:16px;margin-top:14px;flex-wrap:wrap;">
      <span style="background:rgba(255,255,255,0.15);padding:4px 14px;border-radius:20px;font-size:13px;">📋 総案件数: {len(airdrops)}件</span>
      <span style="background:rgba(220,53,69,0.4);padding:4px 14px;border-radius:20px;font-size:13px;">🔥 HOT: {hot_count}件</span>
      <span style="background:rgba(40,167,69,0.4);padding:4px 14px;border-radius:20px;font-size:13px;">● アクティブ: {active_count}件</span>
    </div>
  </div>

  <div style="background:white;padding:24px;border-radius:0 0 12px 12px;box-shadow:0 4px 16px rgba(0,0,0,0.1);">

    {new_html}
    {changes_html}
    {removed_html}

    <!-- 今日狙うべきホット案件 -->
    <h2 style="color:#dc3545;margin-top:24px;border-bottom:2px solid #dc3545;padding-bottom:8px;">🔥 今日狙うべきホット案件</h2>
    {hot_cards if hot_cards else '<p style="color:#6c757d;">現在HOT案件はありません</p>'}

    <!-- 価値ランキング Top5 -->
    <h2 style="color:#0d6efd;margin-top:28px;border-bottom:2px solid #0d6efd;padding-bottom:8px;">💰 推定価値ランキング TOP5</h2>
    <table style="width:100%;border-collapse:collapse;margin-top:8px;">
      <thead>
        <tr style="background:#f8f9fa;">
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">#</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">プロジェクト</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">推定価値</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">難易度</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">期限</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">参加</th>
        </tr>
      </thead>
      <tbody>{top_rows}</tbody>
    </table>

    {trending_html}

    <hr style="margin:28px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:12px;margin:0;line-height:1.7;">
      ※ このメールはCrypto Airdrop Trackerから自動送信されています。<br>
      ※ 掲載情報は参考目的のみです。投資は必ず自己責任で行ってください。<br>
      ※ エアドロップの条件・価値は変動する場合があります。
    </p>
  </div>

</body>
</html>"""


def send_daily_report(airdrops: list[dict], new_items: list[str], trending: list[dict], diff: dict | None = None) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    top_value = max((a.get("estimated_value_usd", 0) for a in airdrops if a.get("is_hot")), default=0)

    subject = f"[Airdrop日報] {today} — 🔥HOT {hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"
    if top_value >= 1000:
        subject += f" 💰最高~${top_value:,}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, diff)
    plain_body = (
        f"{today} Airdrop日次レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"変更: {len(diff['changed']) if diff else 0}件\n"
        f"CoinGeckoトレンド: {', '.join(t['name'] for t in trending[:3]) if trending else 'なし'}"
    )

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"日次レポート送信成功: {GMAIL_RECIPIENT}")
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
    diff_color = _DIFFICULTY_COLOR.get(airdrop.get("difficulty", "easy"), "#6c757d")
    tasks_html = "".join(f"<li style='margin:4px 0;'>{t}</li>" for t in airdrop.get("tasks", []))

    subject = f"🚨 [新着HOT] {name} — 推定${value:,} | 今すぐ確認！"

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;background:#f4f6f9;padding:20px;">
  <div style="background:linear-gradient(135deg,#dc3545,#ff6b6b);color:white;padding:24px;border-radius:12px 12px 0 0;">
    <div style="font-size:13px;opacity:0.9;margin-bottom:6px;">🚨 新着ホットエアドロップ出現！</div>
    <h2 style="margin:0;font-size:26px;">{name}</h2>
    <div style="margin-top:10px;font-size:28px;font-weight:900;">推定 ~${value:,}</div>
  </div>
  <div style="background:white;padding:24px;border-radius:0 0 12px 12px;box-shadow:0 4px 16px rgba(0,0,0,0.15);">
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px;">
      <span style="background:#e9ecef;color:#495057;padding:4px 12px;border-radius:20px;font-size:13px;">🏷 {airdrop.get('category','')}</span>
      <span style="background:{diff_color};color:white;padding:4px 12px;border-radius:20px;font-size:13px;">{airdrop.get('difficulty','').upper()}</span>
      <span style="background:#fff3cd;color:#856404;padding:4px 12px;border-radius:20px;font-size:13px;">期限: {airdrop.get('end_date','未定')}</span>
    </div>
    <p style="color:#333;font-size:14px;line-height:1.7;">{airdrop.get('description','')}</p>
    <h4 style="color:#333;margin-bottom:8px;">📋 参加ステップ</h4>
    <ul style="color:#555;font-size:14px;padding-left:20px;">{tasks_html}</ul>
    <div style="text-align:center;margin-top:24px;">
      <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#ff6b6b);color:white;padding:14px 36px;border-radius:8px;text-decoration:none;font-weight:900;font-size:16px;letter-spacing:0.5px;">🔥 今すぐ参加する</a>
    </div>
    <hr style="margin:24px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:12px;margin:0;">投資は自己責任で行ってください。情報は参考目的のみです。</p>
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
        logger.info(f"ホットアラート送信成功: {name}")
        return True
    except Exception as e:
        logger.error(f"ホットアラート送信失敗: {e}")
        return False
