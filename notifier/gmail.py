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

_DIFFICULTY_COLOR = {"easy": "#2ed573", "medium": "#ff6348", "hard": "#ff4757"}
_STATUS_COLOR = {"active": "#2ed573", "upcoming": "#ffa502", "ended": "#888888"}
_STATUS_LABEL = {"active": "● アクティブ", "upcoming": "◎ 近日開始", "ended": "✕ 終了"}


def _hot_card_html(a: dict) -> str:
    value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
    diff_color = _DIFFICULTY_COLOR.get(a.get("difficulty", "easy"), "#888")
    tasks_html = "".join(f"<li style='margin:3px 0;'>{t}</li>" for t in a.get("tasks", [])[:3])
    return f"""
    <div style="background:#1e2240;border:1px solid #2e3460;border-radius:10px;padding:18px;margin-bottom:14px;border-left:4px solid #ff4757;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
        {'<img src="' + a["logo"] + '" style="width:36px;height:36px;border-radius:50%;" alt="">' if a.get("logo") else ''}
        <div>
          <strong style="font-size:16px;color:#e8eaf6;">{a["name"]}</strong>
          <span style="background:rgba(124,77,255,0.25);color:#9b8ff5;font-size:11px;padding:2px 8px;border-radius:12px;margin-left:8px;">{a.get("category","")}</span>
          <span style="background:#ff4757;color:white;font-size:10px;font-weight:700;padding:2px 7px;border-radius:12px;margin-left:4px;">🔥 HOT</span>
        </div>
      </div>
      <p style="color:#9fa8da;font-size:13px;margin:0 0 12px;">{a.get("description","")}</p>
      <div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:12px;">
        <div>
          <div style="font-size:10px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">推定価値</div>
          <div style="font-size:20px;font-weight:800;color:#2ed573;">{value}</div>
        </div>
        <div>
          <div style="font-size:10px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">難易度</div>
          <div style="background:{diff_color};color:white;display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:700;margin-top:4px;">{a.get("difficulty","").upper()}</div>
        </div>
        <div>
          <div style="font-size:10px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">期限</div>
          <div style="font-size:14px;font-weight:600;color:#e8eaf6;margin-top:4px;">{a.get("end_date","未定")}</div>
        </div>
      </div>
      {'<div style="background:#0f0f1a;border-radius:6px;padding:10px;margin-bottom:12px;"><div style="font-size:11px;color:#9fa8da;font-weight:700;margin-bottom:6px;">📋 参加ステップ</div><ul style="margin:0;padding-left:18px;color:#9fa8da;font-size:13px;">' + tasks_html + '</ul></div>' if tasks_html else ''}
      <a href="{a.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#7c4dff,#651fff);color:white;padding:9px 22px;border-radius:8px;text-decoration:none;font-weight:700;font-size:14px;">今すぐ参加する →</a>
    </div>"""


def _change_row_html(ch: dict) -> str:
    changes_html = " / ".join(ch.get("changes", []))
    return f"""
    <tr>
      <td style="padding:8px 12px;border-bottom:1px solid #2e3460;color:#e8eaf6;font-weight:600;">{ch["name"]}</td>
      <td style="padding:8px 12px;border-bottom:1px solid #2e3460;color:#ffa502;">{changes_html}</td>
    </tr>"""


def _build_html_body(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    changes: list[dict] | None = None,
    removed: list[str] | None = None,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    total = len(airdrops)
    hot_count = len(hot)

    # 新着セクション
    new_section = ""
    if new_items:
        items_html = "".join(f"<li style='margin:4px 0;color:#e8eaf6;'>{n}</li>" for n in new_items)
        new_section = f"""
        <div style="background:rgba(46,213,115,0.1);border:1px solid #2ed573;border-radius:8px;padding:14px 18px;margin-bottom:20px;">
          <div style="font-weight:700;color:#2ed573;margin-bottom:8px;">🆕 新着エアドロップ ({len(new_items)}件)</div>
          <ul style="margin:0;padding-left:18px;">{items_html}</ul>
        </div>"""

    # 変更セクション
    change_section = ""
    if changes:
        rows_html = "".join(_change_row_html(c) for c in changes)
        change_section = f"""
        <div style="margin-bottom:20px;">
          <h3 style="color:#ffa502;font-size:15px;margin:0 0 10px;">✏️ ステータス変更 ({len(changes)}件)</h3>
          <table style="width:100%;border-collapse:collapse;background:#1e2240;border-radius:8px;overflow:hidden;">
            <thead><tr style="background:#0f0f1a;">
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:12px;">プロジェクト</th>
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:12px;">変更内容</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>"""

    # 終了セクション
    removed_section = ""
    if removed:
        removed_html = "".join(f"<span style='background:rgba(136,136,136,0.2);color:#888;padding:2px 8px;border-radius:12px;font-size:12px;margin:2px 3px;display:inline-block;'>{n}</span>" for n in removed)
        removed_section = f"""
        <div style="margin-bottom:20px;">
          <h3 style="color:#888;font-size:15px;margin:0 0 8px;">✕ 終了・削除 ({len(removed)}件)</h3>
          <div>{removed_html}</div>
        </div>"""

    # ホット案件カード
    hot_cards_html = "".join(_hot_card_html(a) for a in hot[:5])

    # トレンドコイン
    trending_html = ""
    if trending:
        t_rows = "".join(
            f'<tr><td style="padding:8px 12px;border-bottom:1px solid #2e3460;color:#e8eaf6;font-weight:600;">{t["name"]}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #2e3460;color:#9fa8da;">{t["symbol"]}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #2e3460;color:#7c4dff;">#{t.get("rank","—")}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #2e3460;color:#ffa502;">スコア {t.get("score",0)}</td></tr>'
            for t in trending[:7]
        )
        trending_html = f"""
        <div style="margin-bottom:20px;">
          <h3 style="color:#7c4dff;font-size:15px;margin:0 0 10px;">📈 CoinGecko トレンドコイン</h3>
          <table style="width:100%;border-collapse:collapse;background:#1e2240;border-radius:8px;overflow:hidden;">
            <thead><tr style="background:#0f0f1a;">
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:12px;">コイン名</th>
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:12px;">シンボル</th>
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:12px;">時価総額ランク</th>
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:12px;">スコア</th>
            </tr></thead>
            <tbody>{t_rows}</tbody>
          </table>
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0f0f1a;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;padding:20px;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);border:1px solid #2e3460;border-radius:12px 12px 0 0;padding:24px 28px;">
    <div style="font-size:26px;font-weight:800;color:white;margin-bottom:4px;">🪂 Crypto Airdrop Tracker</div>
    <div style="color:#9fa8da;font-size:13px;">{today} 日次更新レポート — 自動配信</div>
  </div>

  <!-- サマリーバー -->
  <div style="background:#16213e;border:1px solid #2e3460;border-top:none;padding:16px 28px;display:flex;gap:0;">
    <div style="flex:1;text-align:center;border-right:1px solid #2e3460;">
      <div style="font-size:28px;font-weight:800;color:#1e90ff;">{total}</div>
      <div style="font-size:11px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">総案件数</div>
    </div>
    <div style="flex:1;text-align:center;border-right:1px solid #2e3460;">
      <div style="font-size:28px;font-weight:800;color:#ff4757;">{hot_count}</div>
      <div style="font-size:11px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">🔥 ホット案件</div>
    </div>
    <div style="flex:1;text-align:center;border-right:1px solid #2e3460;">
      <div style="font-size:28px;font-weight:800;color:#2ed573;">{len(new_items)}</div>
      <div style="font-size:11px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">🆕 新着</div>
    </div>
    <div style="flex:1;text-align:center;">
      <div style="font-size:28px;font-weight:800;color:#ffa502;">{len(changes) if changes else 0}</div>
      <div style="font-size:11px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">✏️ 変更</div>
    </div>
  </div>

  <!-- メインコンテンツ -->
  <div style="background:#0f0f1a;border:1px solid #2e3460;border-top:none;border-radius:0 0 12px 12px;padding:24px 28px;">

    {new_section}
    {change_section}
    {removed_section}

    <!-- ホット案件 -->
    <h3 style="color:#ff4757;font-size:16px;margin:0 0 14px;padding-bottom:8px;border-bottom:1px solid #2e3460;">🔥 今すぐ狙うべきホット案件</h3>
    {hot_cards_html if hot_cards_html else '<p style="color:#9fa8da;">現在ホット案件はありません。</p>'}

    {trending_html}

    <!-- フッター -->
    <div style="margin-top:24px;padding-top:16px;border-top:1px solid #2e3460;">
      <p style="color:#9fa8da;font-size:11px;margin:0;">
        ※ このメールはCrypto Airdrop Trackerから毎日自動送信されています。<br>
        掲載情報は参考目的のみです。投資・参加判断は必ずご自身でご確認の上、自己責任で行ってください。
      </p>
    </div>
  </div>

</div>
</body>
</html>"""


def send_daily_report(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    changes: list[dict] | None = None,
    removed: list[str] | None = None,
) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))

    subject_parts = [f"[Airdrop日報] {today}"]
    subject_parts.append(f"🔥ホット{hot_count}件")
    if new_items:
        subject_parts.append(f"🆕新着{len(new_items)}件")
    if changes:
        subject_parts.append(f"✏️変更{len(changes)}件")
    subject = " | ".join(subject_parts)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, changes, removed)
    new_str = ", ".join(new_items) if new_items else "なし"
    plain_body = (
        f"{today} Airdrop日次レポート\n"
        f"総案件数: {len(airdrops)}件 | ホット: {hot_count}件 | 新着: {len(new_items)}件\n"
        f"新着案件: {new_str}\n"
        f"トレンド: {', '.join(t['name'] for t in trending[:5])}"
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
    """注目案件出現時の即時アラートメール"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        return False

    name = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd", 0)
    diff_color = _DIFFICULTY_COLOR.get(airdrop.get("difficulty", "easy"), "#888")
    tasks_html = "".join(f"<li style='margin:4px 0;'>{t}</li>" for t in airdrop.get("tasks", []))
    subject = f"🚨 [緊急HOT案件] {name} — 推定${value:,} の新規エアドロップ登場！"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:20px;background:#0f0f1a;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#dc3545,#7c4dff);border-radius:12px 12px 0 0;padding:22px 26px;color:white;">
    <div style="font-size:22px;font-weight:800;">🚨 HOT エアドロップ出現！</div>
    <div style="opacity:0.85;font-size:13px;margin-top:4px;">{datetime.now().strftime("%Y年%m月%d日 %H:%M")} 検知</div>
  </div>
  <div style="background:#1e2240;border:1px solid #2e3460;border-top:none;border-radius:0 0 12px 12px;padding:24px 26px;">
    <h2 style="color:#e8eaf6;margin:0 0 6px;">{name} <span style="color:#9fa8da;font-size:14px;font-weight:400;">({airdrop.get("symbol","")})</span></h2>
    <p style="color:#9fa8da;font-size:13px;margin:0 0 20px;">{airdrop.get("description","")}</p>
    <div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:20px;">
      <div><div style="font-size:10px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">推定価値</div>
        <div style="font-size:26px;font-weight:800;color:#2ed573;">~${value:,}</div></div>
      <div><div style="font-size:10px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">カテゴリ</div>
        <div style="color:#e8eaf6;font-weight:600;font-size:15px;">{airdrop.get("category","")}</div></div>
      <div><div style="font-size:10px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">難易度</div>
        <div style="background:{diff_color};color:white;display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:700;">{airdrop.get("difficulty","").upper()}</div></div>
      <div><div style="font-size:10px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">期限</div>
        <div style="color:#e8eaf6;font-weight:600;font-size:15px;">{airdrop.get("end_date","未定")}</div></div>
    </div>
    {'<div style="background:#0f0f1a;border-radius:8px;padding:14px;margin-bottom:20px;"><div style="color:#9fa8da;font-size:12px;font-weight:700;margin-bottom:8px;">📋 参加方法</div><ul style="margin:0;padding-left:18px;color:#9fa8da;font-size:13px;">' + tasks_html + "</ul></div>" if tasks_html else ""}
    <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#7c4dff);color:white;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px;">🚀 今すぐ参加する</a>
    <p style="color:#9fa8da;font-size:11px;margin-top:20px;">※ 投資は自己責任で行ってください。情報は参考目的のみです。</p>
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
        logger.info(f"ホットアラート送信: {name} → {GMAIL_RECIPIENT}")
        return True
    except Exception as e:
        logger.error(f"ホットアラート送信失敗: {e}")
        return False
