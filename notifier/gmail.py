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

_DIFF_COLOR = {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}


def _difficulty_badge(d: str) -> str:
    color = _DIFF_COLOR.get(d, "#6c757d")
    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700;">{d.upper()}</span>'


def _value_str(a: dict) -> str:
    v = a.get("estimated_value_usd") or 0
    return f"~${v:,}" if v else "未定"


def _build_hot_rows(hot_list: list[dict]) -> str:
    rows = ""
    for a in hot_list[:8]:
        rows += f"""
        <tr>
          <td style="padding:10px 12px;border-bottom:1px solid #2e3460;">
            <strong style="color:#e8eaf6;">{a['name']}</strong><br>
            <span style="color:#9fa8da;font-size:12px;">{a.get('category','')}</span>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #2e3460;color:#2ed573;font-weight:700;">{_value_str(a)}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #2e3460;">{_difficulty_badge(a.get('difficulty','easy'))}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #2e3460;color:#9fa8da;font-size:13px;">{a.get('end_date','未定')}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #2e3460;">
            <a href="{a.get('url','#')}" style="background:#7c4dff;color:white;padding:5px 12px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:700;">参加 →</a>
          </td>
        </tr>"""
    return rows


def _build_html_body(airdrops: list[dict], new_items: list[str], trending: list[dict], diff: dict | None = None) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    diff = diff or {}
    added_details = diff.get("added", [])
    changed_list = diff.get("changed", [])
    newly_hot = diff.get("newly_hot", [])
    removed = diff.get("removed", [])

    # 🚨 新規HOT案件ブロック
    newly_hot_html = ""
    if newly_hot:
        hot_items_html = ""
        for a in newly_hot:
            hot_items_html += f"""
            <div style="background:#1a0a0a;border:1px solid #ff4757;border-radius:8px;padding:14px;margin-bottom:10px;">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                <span style="background:#ff4757;color:white;font-size:11px;padding:2px 8px;border-radius:12px;font-weight:700;">🔥 HOT NEW</span>
                <strong style="color:#ff6b81;font-size:16px;">{a['name']}</strong>
                <span style="color:#9fa8da;font-size:13px;">({a.get('symbol','')})</span>
              </div>
              <p style="color:#e8eaf6;margin:4px 0;font-size:13px;">{a.get('description','')}</p>
              <p style="margin:6px 0;"><strong style="color:#2ed573;">推定価値: {_value_str(a)}</strong>
              　{_difficulty_badge(a.get('difficulty','easy'))}　期限: <span style="color:#9fa8da;">{a.get('end_date','未定')}</span></p>
              <a href="{a.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#ff4757,#7c4dff);color:white;padding:8px 18px;border-radius:6px;text-decoration:none;font-weight:700;font-size:13px;">今すぐ参加する →</a>
            </div>"""
        newly_hot_html = f"""
        <div style="background:#0d0d1a;border:2px solid #ff4757;border-radius:10px;padding:16px;margin:16px 0;">
          <h3 style="color:#ff4757;margin:0 0 12px;font-size:16px;">🚨 注目！新規HOT案件 ({len(newly_hot)}件)</h3>
          {hot_items_html}
        </div>"""

    # 🆕 新着エアドロップブロック
    new_html = ""
    if added_details:
        items_html = ""
        for a in added_details:
            items_html += f"""
            <li style="margin-bottom:6px;">
              <strong style="color:#e8eaf6;">{a['name']}</strong>
              <span style="color:#9fa8da;font-size:12px;"> — {a.get('category','')}</span>
              <span style="color:#2ed573;font-weight:700;"> {_value_str(a)}</span>
              {'　🔥' if a.get('is_hot') else ''}
            </li>"""
        new_html = f"""
        <div style="background:#071a0d;border-left:4px solid #2ed573;padding:14px 16px;margin:12px 0;border-radius:4px;">
          <strong style="color:#2ed573;">🆕 新着エアドロップ ({len(added_details)}件)</strong>
          <ul style="margin:8px 0 0 0;padding-left:18px;color:#e8eaf6;">{items_html}</ul>
        </div>"""

    # ✏️ 変更ブロック
    changed_html = ""
    if changed_list:
        c_items = ""
        for c in changed_list:
            changes_text = "、".join(c["changes"])
            c_items += f"""
            <li style="margin-bottom:6px;">
              <strong style="color:#e8eaf6;">{c['name']}</strong>:
              <span style="color:#ffa502;">{changes_text}</span>
            </li>"""
        changed_html = f"""
        <div style="background:#1a150a;border-left:4px solid #ffa502;padding:14px 16px;margin:12px 0;border-radius:4px;">
          <strong style="color:#ffa502;">✏️ 変更された案件 ({len(changed_list)}件)</strong>
          <ul style="margin:8px 0 0 0;padding-left:18px;">{c_items}</ul>
        </div>"""

    # 🗑️ 終了・削除ブロック
    removed_html = ""
    if removed:
        r_items = "".join(f'<li style="color:#9fa8da;">{n}</li>' for n in removed)
        removed_html = f"""
        <div style="background:#0d0d0d;border-left:4px solid #666;padding:12px 16px;margin:12px 0;border-radius:4px;">
          <strong style="color:#888;">🗑️ 終了・削除 ({len(removed)}件)</strong>
          <ul style="margin:6px 0 0 0;padding-left:18px;">{r_items}</ul>
        </div>"""

    # 🔥 HOT案件テーブル
    hot_rows = _build_hot_rows(hot)
    hot_table = f"""
    <h3 style="color:#ff4757;margin:20px 0 10px;">🔥 現在のHOT案件一覧 ({len(hot)}件)</h3>
    <table style="width:100%;border-collapse:collapse;background:#16213e;border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#0d1b2a;">
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:12px;">プロジェクト</th>
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:12px;">推定価値</th>
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:12px;">難易度</th>
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:12px;">期限</th>
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:12px;">リンク</th>
        </tr>
      </thead>
      <tbody>{hot_rows}</tbody>
    </table>""" if hot_rows else ""

    # 📈 トレンドブロック
    trending_html = ""
    if trending:
        t_items = "".join(
            f'<li style="margin-bottom:4px;"><strong style="color:#e8eaf6;">{t["name"]}</strong> '
            f'<span style="color:#9fa8da;">({t["symbol"]})</span> — スコア: <span style="color:#7c4dff;">{t.get("score", 0)}</span></li>'
            for t in trending[:5]
        )
        trending_html = f"""
        <div style="margin-top:20px;">
          <h3 style="color:#7c4dff;margin:0 0 10px;font-size:15px;">📈 CoinGecko トレンドコイン</h3>
          <ul style="padding-left:18px;margin:0;">{t_items}</ul>
        </div>"""

    total = len(airdrops)
    hot_count = len(hot)
    new_count = len(added_details)
    changed_count = len(changed_list)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;max-width:720px;margin:0 auto;background:#0f0f1a;color:#e8eaf6;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:24px;border-radius:10px 10px 0 0;border-bottom:2px solid #7c4dff;">
    <h1 style="margin:0;font-size:22px;color:white;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:6px 0 0;color:#9fa8da;font-size:13px;">{today} 更新レポート</p>
  </div>

  <!-- サマリーバー -->
  <div style="background:#16213e;padding:16px 24px;display:flex;gap:16px;flex-wrap:wrap;">
    <div style="background:#1e2240;border:1px solid #2e3460;border-radius:20px;padding:4px 14px;font-size:13px;color:#1e90ff;">
      📋 計 <strong>{total}</strong> 件
    </div>
    <div style="background:#1e2240;border:1px solid #ff4757;border-radius:20px;padding:4px 14px;font-size:13px;color:#ff6b81;">
      🔥 ホット <strong>{hot_count}</strong> 件
    </div>
    {'<div style="background:#1e2240;border:1px solid #2ed573;border-radius:20px;padding:4px 14px;font-size:13px;color:#2ed573;">🆕 新着 <strong>' + str(new_count) + '</strong> 件</div>' if new_count else ''}
    {'<div style="background:#1e2240;border:1px solid #ffa502;border-radius:20px;padding:4px 14px;font-size:13px;color:#ffa502;">✏️ 変更 <strong>' + str(changed_count) + '</strong> 件</div>' if changed_count else ''}
  </div>

  <!-- 本文 -->
  <div style="background:#1a1a2e;padding:24px;border-radius:0 0 10px 10px;">
    {newly_hot_html}
    {new_html}
    {changed_html}
    {removed_html}
    {hot_table}
    {trending_html}

    <hr style="margin:24px 0;border:none;border-top:1px solid #2e3460;">
    <p style="color:#666;font-size:11px;margin:0;">
      ※ このメールはCrypto Airdrop Trackerから自動送信されています。<br>
      投資は自己責任で行ってください。掲載情報は参考目的のみです。
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

    diff = diff or {}
    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    new_count = len(diff.get("added", []))
    newly_hot_count = len(diff.get("newly_hot", []))

    subject_parts = [f"[Airdrop] {today} 更新"]
    if newly_hot_count:
        subject_parts.append(f"🚨 HOT昇格{newly_hot_count}件")
    if new_count:
        subject_parts.append(f"🆕 新着{new_count}件")
    subject_parts.append(f"🔥 ホット{hot_count}件")
    subject = " — ".join(subject_parts)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, diff)
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"変更: {len(diff.get('changed', []))}件"
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
    """注目案件出現・HOT昇格時の即時アラート"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        return False

    name = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd") or 0
    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,} の注目案件！"

    tasks_html = "".join(f"<li style='margin-bottom:6px;color:#e8eaf6;'>{t}</li>" for t in airdrop.get("tasks", []))

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;background:#0f0f1a;">
  <div style="background:linear-gradient(135deg,#dc3545,#7c4dff);color:white;padding:24px;border-radius:10px 10px 0 0;">
    <h2 style="margin:0;font-size:20px;">🚨 ホットエアドロップ出現！</h2>
    <p style="margin:4px 0 0;opacity:0.9;font-size:13px;">今すぐ行動が必要な案件です</p>
  </div>
  <div style="background:#1a1a2e;padding:24px;border-radius:0 0 10px 10px;border:1px solid #2e3460;border-top:none;">
    <h3 style="color:#ff6b81;margin:0 0 16px;font-size:18px;">{name} ({airdrop.get('symbol','')})</h3>
    <table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
      <tr>
        <td style="padding:8px 12px;background:#16213e;border-radius:6px;width:50%;color:#9fa8da;font-size:13px;">
          <div>推定価値</div>
          <strong style="color:#2ed573;font-size:20px;">~${value:,}</strong>
        </td>
        <td style="width:8px;"></td>
        <td style="padding:8px 12px;background:#16213e;border-radius:6px;color:#9fa8da;font-size:13px;">
          <div>カテゴリ / 難易度</div>
          <strong style="color:#e8eaf6;">{airdrop.get('category','')} / {airdrop.get('difficulty','').upper()}</strong>
        </td>
      </tr>
    </table>
    <p style="color:#e8eaf6;font-size:14px;line-height:1.6;">{airdrop.get('description','')}</p>
    <div style="background:#16213e;border-radius:8px;padding:14px;margin:14px 0;">
      <p style="color:#9fa8da;font-size:12px;font-weight:700;margin:0 0 8px;text-transform:uppercase;">📋 参加方法</p>
      <ul style="padding-left:18px;margin:0;">{tasks_html}</ul>
    </div>
    <p style="color:#9fa8da;font-size:13px;">期限: <strong style="color:#e8eaf6;">{airdrop.get('end_date','未定')}</strong></p>
    <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#7c4dff);color:white;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px;margin-top:8px;">今すぐ参加する →</a>
    <hr style="margin:20px 0;border:none;border-top:1px solid #2e3460;">
    <p style="color:#666;font-size:11px;margin:0;">投資は自己責任で行ってください。掲載情報は参考目的のみです。</p>
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
