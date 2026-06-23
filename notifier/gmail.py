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


def _difficulty_label(d: str) -> str:
    return {"easy": "EASY ✅", "medium": "MEDIUM ⚠️", "hard": "HARD 🔴"}.get(d, d.upper())


def _difficulty_color(d: str) -> str:
    return {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}.get(d, "#6c757d")


def _build_html_body(airdrops: list[dict], new_items: list[str], trending: list[dict]) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    total = len(airdrops)
    hot_count = len(hot)

    new_html = ""
    if new_items:
        items_html = "".join(
            f'<li style="margin:6px 0;"><span style="color:#2ed573;font-weight:bold;">● </span>{n}</li>'
            for n in new_items
        )
        new_html = f"""
        <div style="background:#0d2a1a;border-left:4px solid #2ed573;padding:14px 18px;margin:16px 0;border-radius:6px;">
          <p style="margin:0 0 8px;font-weight:bold;color:#2ed573;font-size:14px;">🆕 新着エアドロップ ({len(new_items)}件)</p>
          <ul style="margin:0;padding-left:18px;color:#c8ffd4;">{items_html}</ul>
        </div>"""

    hot_rows = ""
    for a in hot[:6]:
        dc = _difficulty_color(a.get("difficulty", "easy"))
        dl = _difficulty_label(a.get("difficulty", "easy"))
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        status_color = "#2ed573" if a.get("status") == "active" else "#ffa502"
        status_label = "● アクティブ" if a.get("status") == "active" else "◎ 近日開始"
        hot_rows += f"""
        <tr>
          <td style="padding:12px 14px;border-bottom:1px solid #1e2240;vertical-align:top;">
            <div style="font-weight:bold;color:#e8eaf6;font-size:14px;">{a['name']}</div>
            <div style="color:#9fa8da;font-size:11px;margin-top:2px;">{a.get('category','')}</div>
            <div style="color:{status_color};font-size:11px;margin-top:4px;">{status_label}</div>
          </td>
          <td style="padding:12px 14px;border-bottom:1px solid #1e2240;color:#2ed573;font-weight:bold;font-size:16px;vertical-align:top;">{value}</td>
          <td style="padding:12px 14px;border-bottom:1px solid #1e2240;vertical-align:top;">
            <span style="background:{dc};color:white;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:bold;">{dl}</span>
          </td>
          <td style="padding:12px 14px;border-bottom:1px solid #1e2240;color:#9fa8da;font-size:13px;vertical-align:top;">{a.get('end_date','未定')}</td>
          <td style="padding:12px 14px;border-bottom:1px solid #1e2240;vertical-align:top;">
            <a href="{a.get('url','#')}" style="background:#7c4dff;color:white;padding:6px 14px;border-radius:6px;font-size:12px;font-weight:bold;text-decoration:none;">参加する →</a>
          </td>
        </tr>"""

    trending_html = ""
    if trending:
        t_items = "".join(
            f'<li style="margin:6px 0;color:#c8d3ff;"><strong style="color:#e8eaf6;">{t["name"]}</strong> <span style="color:#9fa8da;">({t["symbol"]})</span>'
            f'{"  🏆 ランク #"+str(t["rank"]) if t.get("rank") else ""}</li>'
            for t in trending[:5]
        )
        trending_html = f"""
        <div style="margin-top:24px;">
          <h3 style="color:#c084fc;font-size:15px;margin:0 0 12px;">📈 CoinGecko トレンドコイン TOP5</h3>
          <ul style="margin:0;padding-left:20px;">{t_items}</ul>
        </div>"""

    summary_html = f"""
        <div style="display:flex;gap:12px;flex-wrap:wrap;margin:16px 0;">
          <div style="background:#0d1b38;border:1px solid #1e90ff;border-radius:8px;padding:12px 20px;text-align:center;min-width:80px;">
            <div style="font-size:24px;font-weight:bold;color:#1e90ff;">{total}</div>
            <div style="font-size:11px;color:#9fa8da;margin-top:4px;">追跡中</div>
          </div>
          <div style="background:#1a0d0d;border:1px solid #ff4757;border-radius:8px;padding:12px 20px;text-align:center;min-width:80px;">
            <div style="font-size:24px;font-weight:bold;color:#ff4757;">{hot_count}</div>
            <div style="font-size:11px;color:#9fa8da;margin-top:4px;">🔥 ホット</div>
          </div>
          <div style="background:#0d1a0d;border:1px solid #2ed573;border-radius:8px;padding:12px 20px;text-align:center;min-width:80px;">
            <div style="font-size:24px;font-weight:bold;color:#2ed573;">{len(new_items)}</div>
            <div style="font-size:11px;color:#9fa8da;margin-top:4px;">🆕 新着</div>
          </div>
        </div>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#0f0f1a;margin:0;padding:20px;">
  <div style="max-width:680px;margin:0 auto;">

    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px 12px 0 0;padding:24px 28px;border-bottom:3px solid #7c4dff;">
      <h1 style="margin:0;font-size:22px;color:white;">🪂 Crypto Airdrop Tracker</h1>
      <p style="margin:6px 0 0;color:#9fa8da;font-size:13px;">{today} 日次更新レポート</p>
    </div>

    <div style="background:#16213e;padding:24px 28px;border-radius:0 0 12px 12px;border:1px solid #2e3460;border-top:none;">

      {summary_html}

      {new_html}

      <h3 style="color:#ff6b81;font-size:16px;margin:24px 0 14px;">🔥 今狙うべき注目エアドロップ</h3>
      <div style="border-radius:8px;overflow:hidden;border:1px solid #2e3460;">
        <table style="width:100%;border-collapse:collapse;background:#1e2240;">
          <thead>
            <tr style="background:#0f0f1a;">
              <th style="padding:10px 14px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;white-space:nowrap;">プロジェクト</th>
              <th style="padding:10px 14px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;white-space:nowrap;">推定価値</th>
              <th style="padding:10px 14px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;white-space:nowrap;">難易度</th>
              <th style="padding:10px 14px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;white-space:nowrap;">期限</th>
              <th style="padding:10px 14px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;white-space:nowrap;">参加</th>
            </tr>
          </thead>
          <tbody>{hot_rows}</tbody>
        </table>
      </div>

      {trending_html}

      <hr style="margin:28px 0 16px;border:none;border-top:1px solid #2e3460;">
      <p style="color:#6c757d;font-size:11px;margin:0;line-height:1.6;">
        🪂 Crypto Airdrop Tracker から自動送信 — 毎日8:00 JST 更新<br>
        ※ 掲載情報は参考目的のみです。投資は自己責任で行ってください。損失の補償はできません。
      </p>
    </div>

  </div>
</body>
</html>"""


def send_daily_report(airdrops: list[dict], new_items: list[str], trending: list[dict]) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    subject = f"🪂 [Airdrop] {today} 更新 — 🔥ホット{hot_count}件"
    if new_items:
        subject += f" · 🆕新着{len(new_items)}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending)
    hot_names = ", ".join(a["name"] for a in airdrops if a.get("is_hot"))
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"追跡中: {len(airdrops)}件 | ホット: {hot_count}件 | 新着: {len(new_items)}件\n"
        f"ホット案件: {hot_names or 'なし'}\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
    )

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"日次レポート送信成功 → {GMAIL_RECIPIENT}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗。.envのGMAIL_APP_PASSWORDを確認してください。")
        return False
    except Exception as e:
        logger.error(f"メール送信失敗: {e}")
        return False


def send_hot_alert(airdrop: dict) -> bool:
    """注目案件出現時の即時アラートメール"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        return False

    name = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd", 0)
    diff = airdrop.get("difficulty", "medium")
    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,}の新案件が登場！"

    tasks_html = "".join(f"<li style='margin:6px 0;color:#c8d3ff;'>{t}</li>" for t in airdrop.get("tasks", []))

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#0f0f1a;margin:0;padding:20px;">
  <div style="max-width:600px;margin:0 auto;">
    <div style="background:linear-gradient(135deg,#7f0000,#4a0000);border-radius:12px 12px 0 0;padding:22px 26px;">
      <h2 style="margin:0;color:white;font-size:20px;">🚨 注目エアドロップ出現！</h2>
      <p style="margin:6px 0 0;color:#ffb3b3;font-size:13px;">新しいホット案件を検出しました</p>
    </div>
    <div style="background:#16213e;padding:24px 26px;border:1px solid #2e3460;border-top:none;border-radius:0 0 12px 12px;">
      <h3 style="color:#ff6b81;font-size:20px;margin:0 0 16px;">{name}
        {"<span style='font-size:14px;color:#9fa8da;'>("+airdrop.get('symbol','')+")</span>" if airdrop.get('symbol') else ""}
      </h3>

      <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px;">
        <div style="background:#0d1a0d;border:1px solid #2ed573;border-radius:8px;padding:12px 18px;text-align:center;">
          <div style="font-size:22px;font-weight:bold;color:#2ed573;">~${value:,}</div>
          <div style="font-size:11px;color:#9fa8da;margin-top:4px;">推定価値</div>
        </div>
        <div style="background:#1a0d0d;border:1px solid {_difficulty_color(diff)};border-radius:8px;padding:12px 18px;text-align:center;">
          <div style="font-size:18px;font-weight:bold;color:{_difficulty_color(diff)};">{_difficulty_label(diff)}</div>
          <div style="font-size:11px;color:#9fa8da;margin-top:4px;">難易度</div>
        </div>
      </div>

      <p style="color:#c8d3ff;font-size:14px;line-height:1.6;">{airdrop.get('description','')}</p>

      <h4 style="color:#9fa8da;font-size:13px;margin:16px 0 10px;">📋 参加方法</h4>
      <ul style="margin:0;padding-left:20px;">{tasks_html}</ul>

      <p style="color:#9fa8da;font-size:13px;margin:16px 0 20px;">📅 期限: <strong style="color:#ffa502;">{airdrop.get('end_date','未定')}</strong></p>

      <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#7c4dff,#651fff);color:white;padding:14px 28px;border-radius:8px;font-size:15px;font-weight:bold;text-decoration:none;">今すぐ参加する →</a>

      <hr style="margin:24px 0 16px;border:none;border-top:1px solid #2e3460;">
      <p style="color:#6c757d;font-size:11px;margin:0;">投資は自己責任で行ってください。</p>
    </div>
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
