"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してメール送信。
毎日必ず日次ダイジェストを送信し、ホット案件出現時は即時アラートも送信。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)

_DIFFICULTY_COLOR = {"easy": "#2ed573", "medium": "#ff6348", "hard": "#ff4757"}
_STATUS_LABEL = {"active": "● アクティブ", "upcoming": "◎ 近日開始", "ended": "✕ 終了"}


def _hot_table_rows(airdrops: list[dict]) -> str:
    rows = ""
    for a in airdrops[:5]:
        color = _DIFFICULTY_COLOR.get(a.get("difficulty", "easy"), "#6c757d")
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "不明"
        tasks_html = "".join(f"<li style='margin:3px 0;font-size:12px;'>{t}</li>" for t in a.get("tasks", [])[:3])
        rows += f"""
        <tr>
          <td style="padding:12px 10px;border-bottom:1px solid #2e3460;vertical-align:top;">
            <div style="display:flex;align-items:center;gap:8px;">
              {'<img src="' + a["logo"] + '" style="width:32px;height:32px;border-radius:50%;vertical-align:middle;" onerror="this.style.display=none">' if a.get("logo") else ''}
              <div>
                <strong style="color:#e8eaf6;">{a['name']}</strong>
                {'<span style="color:#7c4dff;font-size:11px;margin-left:6px;">(' + a.get('symbol','') + ')</span>' if a.get('symbol') else ''}
                <br><span style="color:#9fa8da;font-size:11px;">{a.get('category','')}</span>
              </div>
            </div>
            {('<ul style="margin:8px 0 0 0;padding-left:18px;color:#9fa8da;">' + tasks_html + '</ul>') if tasks_html else ''}
          </td>
          <td style="padding:12px 10px;border-bottom:1px solid #2e3460;color:#2ed573;font-weight:700;font-size:16px;white-space:nowrap;">{value}</td>
          <td style="padding:12px 10px;border-bottom:1px solid #2e3460;">
            <span style="background:{color};color:white;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;">{a.get('difficulty','').upper()}</span>
          </td>
          <td style="padding:12px 10px;border-bottom:1px solid #2e3460;color:#9fa8da;font-size:12px;white-space:nowrap;">{a.get('end_date','未定')}</td>
          <td style="padding:12px 10px;border-bottom:1px solid #2e3460;">
            <a href="{a.get('url','#')}" style="background:#7c4dff;color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:700;">参加 →</a>
          </td>
        </tr>"""
    return rows


def _build_html_body(airdrops: list[dict], new_items: list[str], trending: list[dict], diff: dict) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    total = len(airdrops)
    hot_count = len(hot)

    # ===== 新着セクション =====
    new_html = ""
    if new_items:
        items_html = "".join(
            f"<li style='margin:6px 0;color:#2ed573;'><strong>{n}</strong></li>" for n in new_items
        )
        new_html = f"""
        <div style="background:rgba(46,213,115,0.1);border-left:4px solid #2ed573;padding:14px 18px;margin:16px 0;border-radius:0 8px 8px 0;">
          <div style="color:#2ed573;font-weight:700;font-size:14px;margin-bottom:8px;">🆕 本日の新着エアドロップ ({len(new_items)}件)</div>
          <ul style="margin:0;padding-left:20px;">{items_html}</ul>
        </div>"""

    # ===== 変更詳細セクション =====
    changed_html = ""
    changes = diff.get("changed", []) if diff else []
    if changes:
        change_rows = "".join(
            f"""<li style="margin:8px 0;">
                <strong style="color:#e8eaf6;">{c['name']}</strong>:
                <span style="color:#ffa502;">{' / '.join(c['changes'])}</span>
              </li>"""
            for c in changes
        )
        changed_html = f"""
        <div style="background:rgba(255,165,2,0.1);border-left:4px solid #ffa502;padding:14px 18px;margin:16px 0;border-radius:0 8px 8px 0;">
          <div style="color:#ffa502;font-weight:700;font-size:14px;margin-bottom:8px;">✏️ 本日の変更 ({len(changes)}件)</div>
          <ul style="margin:0;padding-left:20px;">{change_rows}</ul>
        </div>"""

    # ===== 削除セクション =====
    removed_html = ""
    removed = diff.get("removed", []) if diff else []
    if removed:
        removed_items = "".join(f"<li style='color:#ff4757;margin:4px 0;'>{n}</li>" for n in removed)
        removed_html = f"""
        <div style="background:rgba(255,71,87,0.1);border-left:4px solid #ff4757;padding:14px 18px;margin:16px 0;border-radius:0 8px 8px 0;">
          <div style="color:#ff4757;font-weight:700;font-size:14px;margin-bottom:8px;">🗑️ 終了・削除 ({len(removed)}件)</div>
          <ul style="margin:0;padding-left:20px;">{removed_items}</ul>
        </div>"""

    # ===== ホット案件テーブル =====
    hot_rows = _hot_table_rows(hot)

    # ===== トレンドコイン =====
    trending_html = ""
    if trending:
        t_items = "".join(
            f"""<li style="margin:8px 0;padding:8px 12px;background:rgba(124,77,255,0.1);border-radius:6px;">
                <strong style="color:#e8eaf6;">{t['name']}</strong>
                <span style="color:#7c4dff;font-size:12px;"> ({t['symbol']})</span>
                <span style="color:#9fa8da;font-size:11px;float:right;">スコア: {t.get('score', 0)}</span>
              </li>"""
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#9c88ff;margin:24px 0 12px;">📈 CoinGecko トレンドコイン</h3>
        <ul style="list-style:none;margin:0;padding:0;">{t_items}</ul>"""

    no_change_msg = ""
    if not new_items and not changes and not removed:
        no_change_msg = """
        <div style="background:rgba(159,168,218,0.1);border:1px dashed #4a5568;padding:12px 18px;margin:16px 0;border-radius:8px;color:#9fa8da;font-size:13px;">
          本日の新着・変更はありません。引き続き既存案件をご確認ください。
        </div>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#0f0f1a;margin:0;padding:20px;">
<div style="max-width:720px;margin:0 auto;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:28px 24px;border-radius:12px 12px 0 0;border-bottom:2px solid #7c4dff;">
    <h1 style="margin:0;font-size:24px;font-weight:800;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:6px 0 0;color:#9fa8da;font-size:14px;">{today} 日次更新レポート</p>
  </div>

  <!-- サマリー -->
  <div style="background:#16213e;padding:18px 24px;display:flex;gap:0;border-bottom:1px solid #2e3460;">
    <div style="flex:1;text-align:center;padding:8px;">
      <div style="font-size:28px;font-weight:800;color:#1e90ff;">{total}</div>
      <div style="font-size:11px;color:#9fa8da;margin-top:2px;">総案件数</div>
    </div>
    <div style="flex:1;text-align:center;padding:8px;border-left:1px solid #2e3460;">
      <div style="font-size:28px;font-weight:800;color:#ff4757;">{hot_count}</div>
      <div style="font-size:11px;color:#9fa8da;margin-top:2px;">🔥 ホット案件</div>
    </div>
    <div style="flex:1;text-align:center;padding:8px;border-left:1px solid #2e3460;">
      <div style="font-size:28px;font-weight:800;color:#2ed573;">{len(new_items)}</div>
      <div style="font-size:11px;color:#9fa8da;margin-top:2px;">🆕 本日の新着</div>
    </div>
    <div style="flex:1;text-align:center;padding:8px;border-left:1px solid #2e3460;">
      <div style="font-size:28px;font-weight:800;color:#ffa502;">{len(changes)}</div>
      <div style="font-size:11px;color:#9fa8da;margin-top:2px;">✏️ 変更</div>
    </div>
  </div>

  <!-- 本文 -->
  <div style="background:#1e2240;padding:24px;border-radius:0 0 12px 12px;">

    {new_html}
    {changed_html}
    {removed_html}
    {no_change_msg}

    <h3 style="color:#ff6b81;margin:24px 0 12px;font-size:16px;">🔥 注目ホットエアドロップ TOP{min(len(hot),5)}</h3>
    <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;background:#16213e;border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#0d2137;">
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:11px;font-weight:700;text-transform:uppercase;border-bottom:1px solid #2e3460;">プロジェクト</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:11px;font-weight:700;text-transform:uppercase;border-bottom:1px solid #2e3460;">推定価値</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:11px;font-weight:700;text-transform:uppercase;border-bottom:1px solid #2e3460;">難易度</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:11px;font-weight:700;text-transform:uppercase;border-bottom:1px solid #2e3460;">期限</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:11px;font-weight:700;text-transform:uppercase;border-bottom:1px solid #2e3460;">リンク</th>
        </tr>
      </thead>
      <tbody>{hot_rows}</tbody>
    </table>
    </div>

    {trending_html}

    <hr style="margin:24px 0;border:none;border-top:1px solid #2e3460;">
    <p style="color:#4a5568;font-size:11px;margin:0;text-align:center;">
      このメールは Crypto Airdrop Tracker から毎日自動送信されています。<br>
      投資は自己責任で行ってください。掲載情報は参考目的のみです。
    </p>
  </div>

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
    subject = f"[Airdrop] {today} 日次レポート — ホット{hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"
    if diff and diff.get("changed"):
        subject += f" ✏️変更{len(diff['changed'])}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    diff = diff or {}
    html_body = _build_html_body(airdrops, new_items, trending, diff)
    plain_body = (
        f"{today} Airdrop 日次レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"変更: {len(diff.get('changed', []))}件\n"
        f"削除: {', '.join(diff.get('removed', [])) if diff.get('removed') else 'なし'}"
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
    symbol = airdrop.get("symbol", "")
    category = airdrop.get("category", "")
    difficulty = airdrop.get("difficulty", "").upper()
    diff_color = _DIFFICULTY_COLOR.get(airdrop.get("difficulty", "easy"), "#6c757d")
    tasks_html = "".join(f"<li style='margin:5px 0;'>{t}</li>" for t in airdrop.get("tasks", []))
    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,} の注目新案件！"

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#0f0f1a;margin:0;padding:20px;">
<div style="max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#dc3545,#7c4dff);color:white;padding:24px;border-radius:12px 12px 0 0;">
    <div style="font-size:13px;opacity:0.85;margin-bottom:6px;">🚨 ホットエアドロップ出現アラート</div>
    <h2 style="margin:0;font-size:22px;">{name} {('(' + symbol + ')') if symbol else ''}</h2>
    <div style="margin-top:8px;font-size:13px;opacity:0.85;">{category}</div>
  </div>
  <div style="background:#1e2240;padding:24px;border-radius:0 0 12px 12px;border:1px solid #2e3460;border-top:none;">
    <div style="display:flex;gap:20px;margin-bottom:20px;flex-wrap:wrap;">
      <div style="flex:1;min-width:120px;background:#16213e;padding:14px;border-radius:8px;text-align:center;">
        <div style="font-size:24px;font-weight:800;color:#2ed573;">~${value:,}</div>
        <div style="font-size:11px;color:#9fa8da;margin-top:4px;">推定価値 (USD)</div>
      </div>
      <div style="flex:1;min-width:120px;background:#16213e;padding:14px;border-radius:8px;text-align:center;">
        <span style="background:{diff_color};color:white;padding:4px 14px;border-radius:20px;font-size:13px;font-weight:700;">{difficulty}</span>
        <div style="font-size:11px;color:#9fa8da;margin-top:8px;">難易度</div>
      </div>
      <div style="flex:1;min-width:120px;background:#16213e;padding:14px;border-radius:8px;text-align:center;">
        <div style="font-size:14px;font-weight:700;color:#e8eaf6;">{airdrop.get('end_date','未定')}</div>
        <div style="font-size:11px;color:#9fa8da;margin-top:4px;">期限</div>
      </div>
    </div>
    <p style="color:#9fa8da;font-size:14px;line-height:1.6;margin:0 0 16px;">{airdrop.get('description','')}</p>
    {('<div style="margin-bottom:20px;"><div style="color:#e8eaf6;font-weight:700;margin-bottom:8px;">📋 参加ステップ</div><ul style="color:#9fa8da;padding-left:20px;margin:0;">' + tasks_html + '</ul></div>') if tasks_html else ''}
    <a href="{airdrop.get('url','#')}" style="display:block;text-align:center;background:linear-gradient(135deg,#dc3545,#7c4dff);color:white;padding:14px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px;">今すぐ参加する →</a>
    <p style="color:#4a5568;font-size:11px;margin:16px 0 0;text-align:center;">投資は自己責任で行ってください。</p>
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
        logger.info(f"ホットアラート送信: {name}")
        return True
    except Exception as e:
        logger.error(f"ホットアラート送信失敗: {e}")
        return False
