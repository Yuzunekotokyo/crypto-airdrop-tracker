"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) でメール送信。
.envに GMAIL_SENDER / GMAIL_APP_PASSWORD / GMAIL_RECIPIENT を設定してください。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)


def _difficulty_color(d: str) -> str:
    return {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}.get(d, "#6c757d")


def _status_label(s: str) -> str:
    return {"active": "● アクティブ", "upcoming": "◎ 近日開始", "ended": "✕ 終了"}.get(s, s)


def build_daily_report_html(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    diff: dict | None = None,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    diff = diff or {}

    # ── 新着セクション ──
    new_html = ""
    if new_items:
        rows = "".join(f"<li style='margin:4px 0;'><strong>{n}</strong></li>" for n in new_items)
        new_html = f"""
        <div style="background:#fff8e1;border-left:4px solid #ffc107;padding:14px 18px;margin:16px 0;border-radius:6px;">
          <p style="margin:0 0 8px;font-weight:700;color:#856404;">🆕 新着エアドロップ ({len(new_items)}件)</p>
          <ul style="margin:0;padding-left:20px;">{rows}</ul>
        </div>"""

    # ── 変更セクション ──
    changed_html = ""
    if diff.get("changed"):
        rows = ""
        for item in diff["changed"]:
            changes = " / ".join(item.get("changes", []))
            rows += f"<li style='margin:4px 0;'><strong>{item['name']}</strong>: {changes}</li>"
        changed_html = f"""
        <div style="background:#e8f4f8;border-left:4px solid #17a2b8;padding:14px 18px;margin:16px 0;border-radius:6px;">
          <p style="margin:0 0 8px;font-weight:700;color:#0c5460;">✏️ 変更された案件 ({len(diff['changed'])}件)</p>
          <ul style="margin:0;padding-left:20px;">{rows}</ul>
        </div>"""

    # ── ホット案件テーブル ──
    hot_rows = ""
    for a in hot[:6]:
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "不明"
        dc = _difficulty_color(a.get("difficulty", ""))
        hot_rows += f"""
        <tr>
          <td style="padding:10px 12px;border-bottom:1px solid #dee2e6;">
            <strong style="color:#1a1a2e;">{a['name']}</strong><br>
            <span style="color:#6c757d;font-size:11px;">{a.get('category','')} · {a.get('type','')}</span>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:700;">{value}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #dee2e6;">
            <span style="background:{dc};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;">{a.get('difficulty','').upper()}</span>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #dee2e6;font-size:12px;">{a.get('end_date','未定')}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #dee2e6;">
            <a href="{a.get('url','#')}" style="color:#0d6efd;font-weight:600;">参加 →</a>
          </td>
        </tr>"""

    # ── トレンドコイン ──
    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li><strong>{t['name']}</strong> ({t['symbol']}) — スコア: {t.get('score',0)}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#6f42c1;margin:24px 0 8px;">📈 CoinGecko トレンドコイン</h3>
        <ul style="padding-left:20px;color:#444;">{t_items}</ul>"""

    total = len(airdrops)
    hot_count = len(hot)

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:'Helvetica Neue',Arial,'Hiragino Sans',sans-serif;">
<div style="max-width:680px;margin:20px auto;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.12);">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);color:#fff;padding:28px 28px 20px;">
    <h1 style="margin:0 0 4px;font-size:22px;font-weight:800;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:0;opacity:0.75;font-size:13px;">{today} 日次更新レポート</p>
    <div style="margin-top:16px;display:flex;gap:12px;flex-wrap:wrap;">
      <span style="background:rgba(255,255,255,0.15);padding:4px 14px;border-radius:20px;font-size:13px;font-weight:600;">📋 計 {total} 件</span>
      <span style="background:rgba(255,71,87,0.3);padding:4px 14px;border-radius:20px;font-size:13px;font-weight:600;">🔥 ホット {hot_count} 件</span>
      {'<span style="background:rgba(46,213,115,0.3);padding:4px 14px;border-radius:20px;font-size:13px;font-weight:600;">🆕 新着 '+str(len(new_items))+' 件</span>' if new_items else ''}
    </div>
  </div>

  <!-- 本文 -->
  <div style="background:#fff;padding:24px 28px;">
    {new_html}
    {changed_html}

    <h3 style="color:#dc3545;margin:20px 0 12px;">🔥 注目のホットエアドロップ</h3>
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
      <thead>
        <tr style="background:#f8f9fa;">
          <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">プロジェクト</th>
          <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">推定価値</th>
          <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">難易度</th>
          <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">期限</th>
          <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;color:#495057;">リンク</th>
        </tr>
      </thead>
      <tbody>{hot_rows}</tbody>
    </table>

    {trending_html}

    <hr style="margin:24px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:11px;margin:0;line-height:1.8;">
      ※ このメールは Crypto Airdrop Tracker から自動送信されています。<br>
      ※ 掲載情報は参考目的のみです。投資は必ず自己責任で行ってください。
    </p>
  </div>
</div>
</body></html>"""


def build_hot_alert_html(airdrop: dict) -> str:
    name = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd", 0)
    dc = _difficulty_color(airdrop.get("difficulty", ""))
    tasks_html = "".join(f"<li style='margin:4px 0;'>{t}</li>" for t in airdrop.get("tasks", []))
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:'Helvetica Neue',Arial,'Hiragino Sans',sans-serif;">
<div style="max-width:600px;margin:20px auto;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.15);">
  <div style="background:linear-gradient(135deg,#dc3545,#c82333);color:#fff;padding:24px 28px;">
    <p style="margin:0 0 4px;font-size:12px;opacity:0.8;font-weight:700;letter-spacing:1px;">🚨 HOT AIRDROP ALERT</p>
    <h2 style="margin:0;font-size:24px;font-weight:800;">{name}</h2>
    <p style="margin:8px 0 0;font-size:28px;font-weight:900;color:#ffd700;">~${value:,}</p>
  </div>
  <div style="background:#fff;padding:24px 28px;">
    <table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
      <tr>
        <td style="padding:8px 0;color:#6c757d;font-size:13px;width:100px;">カテゴリ</td>
        <td style="padding:8px 0;font-weight:600;">{airdrop.get('category','')}</td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#6c757d;font-size:13px;">難易度</td>
        <td style="padding:8px 0;">
          <span style="background:{dc};color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:700;">
            {airdrop.get('difficulty','').upper()}
          </span>
        </td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#6c757d;font-size:13px;">期限</td>
        <td style="padding:8px 0;font-weight:600;">{airdrop.get('end_date','未定')}</td>
      </tr>
    </table>
    <p style="color:#333;margin:0 0 12px;">{airdrop.get('description','')}</p>
    {"<p style='font-weight:700;margin:16px 0 8px;'>📋 参加方法</p><ul style='margin:0;padding-left:20px;color:#444;font-size:13px;'>"+tasks_html+"</ul>" if tasks_html else ""}
    <div style="margin-top:24px;">
      <a href="{airdrop.get('url','#')}"
         style="display:inline-block;background:linear-gradient(135deg,#dc3545,#c82333);color:#fff;
                padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px;">
        今すぐ参加する →
      </a>
    </div>
    <hr style="margin:24px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:11px;margin:0;">※ 投資は自己責任で行ってください。</p>
  </div>
</div>
</body></html>"""


def _send_smtp(subject: str, html_body: str, plain_body: str) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定 (.envを確認) — メール送信スキップ")
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            srv.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"メール送信成功 → {GMAIL_RECIPIENT}: {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗。アプリパスワードを確認してください。")
        return False
    except Exception as e:
        logger.error(f"メール送信失敗: {e}")
        return False


def send_daily_report(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    diff: dict | None = None,
) -> bool:
    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    subject = f"[Airdrop日報] {today} — 🔥ホット{hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"
    if diff and diff.get("changed"):
        subject += f" ✏️変更{len(diff['changed'])}件"

    html = build_daily_report_html(airdrops, new_items, trending, diff)
    plain = (
        f"{today} Airdrop日報\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"変更: {len(diff.get('changed', []))}件\n"
        f"合計: {len(airdrops)}件"
    )
    return _send_smtp(subject, html, plain)


def send_hot_alert(airdrop: dict) -> bool:
    """注目案件出現時の即時アラート"""
    name = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd", 0)
    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,} 新案件出現！"
    html = build_hot_alert_html(airdrop)
    plain = (
        f"HOT Airdrop: {name}\n"
        f"推定価値: ~${value:,}\n"
        f"カテゴリ: {airdrop.get('category','')}\n"
        f"難易度: {airdrop.get('difficulty','')}\n"
        f"URL: {airdrop.get('url','')}"
    )
    return _send_smtp(subject, html, plain)
