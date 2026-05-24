"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してメール送信。
毎日の更新レポートと即時ホットアラートを配信。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)


def _difficulty_badge(difficulty: str) -> str:
    colors = {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}
    color = colors.get(difficulty, "#6c757d")
    label = {"easy": "EASY", "medium": "MEDIUM", "hard": "HARD"}.get(difficulty, difficulty.upper())
    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700;">{label}</span>'


def _status_badge(status: str) -> str:
    cfg = {
        "active":   ("#28a745", "● アクティブ"),
        "upcoming": ("#ffc107", "◎ 近日開始"),
        "ended":    ("#6c757d", "✕ 終了"),
    }
    color, label = cfg.get(status, ("#6c757d", status))
    return f'<span style="color:{color};font-weight:700;">{label}</span>'


def _build_hot_cards_html(hot_airdrops: list[dict]) -> str:
    cards = ""
    for a in hot_airdrops[:5]:
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        tasks_html = ""
        if a.get("tasks"):
            items = "".join(f"<li style='margin:3px 0;color:#555;font-size:12px;'>{t}</li>" for t in a["tasks"][:3])
            tasks_html = f"<ul style='padding-left:16px;margin:6px 0 0;'>{items}</ul>"

        cards += f"""
        <div style="background:#fff;border:1px solid #dee2e6;border-left:4px solid #dc3545;border-radius:8px;padding:16px;margin-bottom:12px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">
            <div>
              <strong style="font-size:16px;">{a['name']}</strong>
              <span style="background:#f8f9fa;color:#6c757d;font-size:11px;padding:2px 6px;border-radius:4px;margin-left:6px;">{a.get('category','')}</span>
              <span style="background:linear-gradient(135deg,#dc3545,#7c4dff);color:white;font-size:11px;padding:2px 8px;border-radius:12px;margin-left:4px;">🔥 HOT</span>
            </div>
            <strong style="color:#28a745;font-size:18px;">{value}</strong>
          </div>
          <p style="color:#555;font-size:13px;margin:8px 0 4px;">{a.get('description','')}</p>
          <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:8px;">
            {_difficulty_badge(a.get('difficulty','easy'))}
            {_status_badge(a.get('status','active'))}
            <span style="color:#6c757d;font-size:12px;">期限: {a.get('end_date','未定')}</span>
            <a href="{a.get('url','#')}" style="background:#7c4dff;color:white;padding:5px 14px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:700;">参加する →</a>
          </div>
          {tasks_html}
        </div>"""
    return cards


def _build_changes_html(changed: list[dict]) -> str:
    if not changed:
        return ""
    rows = ""
    for c in changed[:8]:
        changes_text = " | ".join(c.get("changes", []))
        hot_mark = " 🔥" if c.get("is_hot") else ""
        rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;font-weight:600;">{c['name']}{hot_mark}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;color:#fd7e14;font-size:13px;">{changes_text}</td>
        </tr>"""
    return f"""
    <div style="margin:16px 0;">
      <h3 style="color:#fd7e14;margin:0 0 10px;font-size:15px;">✏️ 変更があった案件 ({len(changed)}件)</h3>
      <table style="width:100%;border-collapse:collapse;background:#fffdf5;border-radius:8px;overflow:hidden;">
        <thead>
          <tr style="background:#fff3cd;">
            <th style="padding:8px 12px;text-align:left;font-size:12px;color:#856404;">プロジェクト</th>
            <th style="padding:8px 12px;text-align:left;font-size:12px;color:#856404;">変更内容</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""


def _build_new_items_html(added: list[dict]) -> str:
    if not added:
        return ""
    hot_new = [a for a in added if a.get("is_hot")]
    normal_new = [a for a in added if not a.get("is_hot")]

    html = f"""
    <div style="background:#d4edda;border-left:4px solid #28a745;padding:12px 16px;margin:16px 0;border-radius:4px;">
      <strong style="color:#155724;">🆕 新着エアドロップ ({len(added)}件)</strong>"""

    if hot_new:
        html += f"""
      <div style="margin-top:8px;">
        <span style="color:#dc3545;font-weight:700;">🔥 新規ホット案件 ({len(hot_new)}件):</span>
        {"".join(f'<span style="display:inline-block;background:#dc3545;color:white;padding:2px 10px;border-radius:12px;font-size:12px;margin:3px 3px 0 0;">{a["name"]}</span>' for a in hot_new)}
      </div>"""

    if normal_new:
        html += f"""
      <div style="margin-top:6px;">
        {"".join(f'<span style="display:inline-block;background:#28a745;color:white;padding:2px 8px;border-radius:12px;font-size:12px;margin:3px 3px 0 0;">{a["name"]}</span>' for a in normal_new)}
      </div>"""

    html += "</div>"
    return html


def _build_trending_html(trending: list[dict]) -> str:
    if not trending:
        return ""
    def _rank_html(t):
        if t.get("rank"):
            return f"&nbsp;<span style='color:#dc3545;font-size:11px;'>Rank #{t['rank']}</span>"
        return ""

    items = "".join(
        f"<li style='margin:4px 0;'><strong>{t['name']}</strong> <span style='color:#6c757d;'>({t['symbol']})</span>{_rank_html(t)}</li>"
        for t in trending[:5]
    )
    return f"""
    <div style="margin:16px 0;">
      <h3 style="color:#6f42c1;margin:0 0 8px;font-size:15px;">📈 CoinGecko トレンドコイン TOP5</h3>
      <ul style="padding-left:20px;margin:0;color:#333;">{items}</ul>
    </div>"""


def _build_html_body(
    airdrops: list[dict],
    added: list[dict],
    changed: list[dict],
    trending: list[dict],
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    total = len(airdrops)
    hot_count = len(hot)

    new_html = _build_new_items_html(added)
    changes_html = _build_changes_html(changed)
    hot_cards_html = _build_hot_cards_html(hot)
    trending_html = _build_trending_html(trending)

    summary_bar = f"""
    <div style="display:flex;gap:16px;flex-wrap:wrap;margin:16px 0;">
      <div style="background:#e8f4fd;border-radius:8px;padding:12px 20px;text-align:center;min-width:100px;">
        <div style="font-size:22px;font-weight:800;color:#1e90ff;">{total}</div>
        <div style="font-size:11px;color:#6c757d;margin-top:2px;">掲載中</div>
      </div>
      <div style="background:#fdecea;border-radius:8px;padding:12px 20px;text-align:center;min-width:100px;">
        <div style="font-size:22px;font-weight:800;color:#dc3545;">{hot_count}</div>
        <div style="font-size:11px;color:#6c757d;margin-top:2px;">🔥 ホット</div>
      </div>
      <div style="background:#d4edda;border-radius:8px;padding:12px 20px;text-align:center;min-width:100px;">
        <div style="font-size:22px;font-weight:800;color:#28a745;">{len(added)}</div>
        <div style="font-size:11px;color:#6c757d;margin-top:2px;">🆕 新着</div>
      </div>
      <div style="background:#fff3cd;border-radius:8px;padding:12px 20px;text-align:center;min-width:100px;">
        <div style="font-size:22px;font-weight:800;color:#fd7e14;">{len(changed)}</div>
        <div style="font-size:11px;color:#6c757d;margin-top:2px;">✏️ 変更</div>
      </div>
    </div>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;max-width:720px;margin:0 auto;background:#f4f6f8;padding:20px;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:28px 24px;border-radius:12px 12px 0 0;">
    <h1 style="margin:0;font-size:22px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:6px 0 0;opacity:0.8;font-size:14px;">{today} 日次更新レポート</p>
  </div>

  <!-- 本文 -->
  <div style="background:white;padding:24px;border-radius:0 0 12px 12px;box-shadow:0 4px 20px rgba(0,0,0,0.08);">

    {summary_bar}
    {new_html}
    {changes_html}

    <!-- ホット案件 -->
    <h3 style="color:#dc3545;border-bottom:2px solid #dc3545;padding-bottom:8px;margin:20px 0 12px;">
      🔥 今狙うべきホットエアドロップ TOP5
    </h3>
    {hot_cards_html}

    {trending_html}

    <!-- フッター -->
    <hr style="margin:24px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:12px;margin:0;line-height:1.7;">
      ※ このメールはCrypto Airdrop Trackerから毎日自動送信されています。<br>
      ※ 投資は自己責任で行ってください。掲載情報は参考目的のみです。<br>
      ※ 特に注目のホット案件が出現した場合は別途アラートメールをお送りします。
    </p>
  </div>

</body>
</html>"""


def _send_smtp(subject: str, html_body: str, plain_body: str) -> bool:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"メール送信成功: {GMAIL_RECIPIENT} / 件名: {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗。.envのGMAIL_SENDER・GMAIL_APP_PASSWORDを確認してください。")
        return False
    except Exception as e:
        logger.error(f"メール送信失敗: {e}")
        return False


def send_daily_report(
    airdrops: list[dict],
    added: list[dict],
    changed: list[dict],
    trending: list[dict],
) -> bool:
    """毎日の更新レポートを送信"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))

    subject_parts = [f"[Airdrop Daily] {today} — ホット{hot_count}件"]
    if added:
        hot_new = [a for a in added if a.get("is_hot")]
        if hot_new:
            subject_parts.append(f"🚨新着ホット{len(hot_new)}件")
        else:
            subject_parts.append(f"🆕新着{len(added)}件")
    if changed:
        subject_parts.append(f"✏️変更{len(changed)}件")

    subject = " / ".join(subject_parts)

    html_body = _build_html_body(airdrops, added, changed, trending)
    added_names = [a.get("name", "") for a in added]
    changed_names = [c.get("name", "") for c in changed]
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件 / 全{len(airdrops)}件\n"
        f"新着: {', '.join(added_names) if added_names else 'なし'}\n"
        f"変更: {', '.join(changed_names) if changed_names else 'なし'}\n"
    )

    return _send_smtp(subject, html_body, plain_body)


def send_hot_alert(airdrop: dict) -> bool:
    """注目案件出現時の即時アラートメール"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        return False

    name = airdrop.get("name", "不明")
    symbol = airdrop.get("symbol", "")
    value = airdrop.get("estimated_value_usd", 0)
    category = airdrop.get("category", "")
    difficulty = airdrop.get("difficulty", "easy")
    description = airdrop.get("description", "")
    tasks = airdrop.get("tasks", [])
    end_date = airdrop.get("end_date", "未定")
    url = airdrop.get("url", "#")

    subject = f"🚨 [HOT新着] {name} — 推定${value:,} のエアドロップが登場！"

    tasks_html = ""
    if tasks:
        items = "".join(f"<li style='margin:4px 0;'>{t}</li>" for t in tasks)
        tasks_html = f"""
        <div style="background:#f8f9fa;border-radius:8px;padding:14px;margin:12px 0;">
          <strong style="font-size:13px;">📋 参加方法</strong>
          <ul style="padding-left:20px;margin:8px 0 0;">{items}</ul>
        </div>"""

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;background:#f4f6f8;padding:20px;">
  <div style="background:linear-gradient(135deg,#dc3545,#7c4dff);color:white;padding:24px;border-radius:12px 12px 0 0;">
    <h2 style="margin:0;font-size:20px;">🚨 新着ホットエアドロップ！</h2>
    <p style="margin:4px 0 0;opacity:0.9;font-size:13px;">今すぐ参加を検討してください</p>
  </div>
  <div style="background:white;padding:24px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 12px 12px;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
    <h3 style="margin:0 0 4px;font-size:20px;">{name} <span style="color:#6c757d;font-size:14px;">({symbol})</span></h3>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin:10px 0;">
      <span style="background:#fdecea;color:#dc3545;border:1px solid #dc3545;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700;">🔥 HOT</span>
      <span style="background:#e8f4fd;color:#1e90ff;padding:3px 10px;border-radius:20px;font-size:12px;">{category}</span>
      {_difficulty_badge(difficulty)}
    </div>
    <div style="background:linear-gradient(135deg,#d4edda,#c3e6cb);border-radius:8px;padding:14px;margin:12px 0;text-align:center;">
      <div style="font-size:28px;font-weight:800;color:#155724;">~${value:,}</div>
      <div style="font-size:12px;color:#155724;margin-top:2px;">推定エアドロップ価値 (USD)</div>
    </div>
    <p style="color:#555;font-size:14px;line-height:1.6;margin:12px 0;">{description}</p>
    {tasks_html}
    <div style="background:#f8f9fa;border-radius:8px;padding:10px 14px;margin:12px 0;font-size:13px;color:#555;">
      ⏰ <strong>参加期限:</strong> {end_date}
    </div>
    <a href="{url}" style="display:block;background:linear-gradient(135deg,#dc3545,#7c4dff);color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px;text-align:center;margin-top:16px;">
      今すぐ参加する →
    </a>
    <hr style="margin:20px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:11px;margin:0;">投資は自己責任で行ってください。情報は参考目的のみです。</p>
  </div>
</body></html>"""

    plain = f"新着ホットエアドロップ: {name}\n推定価値: ~${value:,}\n期限: {end_date}\nURL: {url}"
    return _send_smtp(subject, html, plain)
