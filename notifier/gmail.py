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

DIFFICULTY_COLOR = {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}
DIFFICULTY_JP = {"easy": "簡単", "medium": "普通", "hard": "難しい"}


def _hot_card_html(a: dict) -> str:
    value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
    diff_color = DIFFICULTY_COLOR.get(a.get("difficulty", "easy"), "#6c757d")
    diff_jp = DIFFICULTY_JP.get(a.get("difficulty", "easy"), "")
    tasks_html = "".join(f"<li style='margin-bottom:4px;'>{t}</li>" for t in a.get("tasks", [])[:4])
    return f"""
    <div style="background:#1e2240;border:1px solid #2e3460;border-radius:10px;padding:16px;margin-bottom:14px;border-left:4px solid #ff4757;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
        <div>
          <strong style="font-size:16px;color:#e8eaf6;">{a['name']}</strong>
          <span style="background:#7c4dff22;color:#9c7dff;font-size:11px;padding:2px 8px;border-radius:12px;margin-left:8px;">{a.get('category','')}</span>
        </div>
        <span style="background:#ff475722;color:#ff6b81;font-size:11px;padding:3px 10px;border-radius:20px;font-weight:700;">🔥 HOT</span>
      </div>
      <p style="color:#9fa8da;font-size:13px;margin:0 0 10px;">{a.get('description','')}</p>
      <div style="display:flex;gap:20px;margin-bottom:10px;flex-wrap:wrap;">
        <div><span style="font-size:11px;color:#9fa8da;display:block;">推定価値</span><strong style="color:#2ed573;font-size:18px;">{value}</strong></div>
        <div><span style="font-size:11px;color:#9fa8da;display:block;">難易度</span><span style="background:{diff_color}33;color:{diff_color};padding:2px 10px;border-radius:12px;font-size:12px;font-weight:700;">{diff_jp}</span></div>
        <div><span style="font-size:11px;color:#9fa8da;display:block;">期限</span><strong style="color:#e8eaf6;font-size:13px;">{a.get('end_date','未定')}</strong></div>
      </div>
      {f'<div style="background:#0f0f1a;border-radius:6px;padding:8px 12px;margin-bottom:10px;"><p style="font-size:11px;color:#9fa8da;font-weight:700;margin:0 0 4px;">📋 参加方法</p><ul style="margin:0;padding-left:16px;color:#9fa8da;font-size:12px;">{tasks_html}</ul></div>' if tasks_html else ''}
      <a href="{a.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#7c4dff,#651fff);color:white;padding:10px 22px;border-radius:8px;text-decoration:none;font-weight:700;font-size:13px;">今すぐ参加する →</a>
    </div>"""


def _build_html_body(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    changes: list[dict] | None = None,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    newly_added = [a for a in airdrops if a["name"] in new_items]
    newly_hot = [a for a in newly_added if a.get("is_hot")]

    # 新規ホット案件バナー
    hot_alert_html = ""
    if newly_hot:
        hot_cards = "".join(_hot_card_html(a) for a in newly_hot)
        hot_alert_html = f"""
        <div style="background:#dc354522;border:2px solid #dc3545;border-radius:10px;padding:16px;margin:16px 0;">
          <h3 style="color:#ff4757;margin:0 0 12px;">🚨 注目の新着ホット案件 ({len(newly_hot)}件)</h3>
          {hot_cards}
        </div>"""

    # 新着案件リスト
    new_html = ""
    if new_items:
        new_rows = ""
        for a in newly_added:
            value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
            hot_mark = "🔥 " if a.get("is_hot") else ""
            new_rows += f"<li style='margin-bottom:6px;'>{hot_mark}<strong>{a['name']}</strong> — {a.get('category','')} / 推定価値 {value}</li>"
        new_html = f"""
        <div style="background:#28a74522;border-left:4px solid #28a745;padding:12px 16px;margin:16px 0;border-radius:6px;">
          <strong style="color:#2ed573;">🆕 新着エアドロップ ({len(new_items)}件)</strong>
          <ul style="margin:8px 0 0;color:#e8eaf6;">{new_rows}</ul>
        </div>"""

    # 変更詳細
    changes_html = ""
    if changes:
        change_rows = ""
        for c in changes:
            diffs = " / ".join(c.get("changes", []))
            change_rows += f"<li style='margin-bottom:4px;'><strong>{c['name']}</strong>: <span style='color:#ffa502;'>{diffs}</span></li>"
        changes_html = f"""
        <div style="background:#ffa50222;border-left:4px solid #ffa502;padding:12px 16px;margin:16px 0;border-radius:6px;">
          <strong style="color:#ffa502;">✏️ 変更情報 ({len(changes)}件)</strong>
          <ul style="margin:8px 0 0;color:#e8eaf6;">{change_rows}</ul>
        </div>"""

    # ホットエアドロップ一覧テーブル
    hot_rows = ""
    for a in hot[:6]:
        diff_color = DIFFICULTY_COLOR.get(a.get("difficulty", "easy"), "#6c757d")
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        hot_rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #2e3460;">
            <strong style="color:#e8eaf6;">{a['name']}</strong><br>
            <span style="color:#9fa8da;font-size:12px;">{a.get('category','')}</span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #2e3460;color:#2ed573;font-weight:bold;">{value}</td>
          <td style="padding:10px;border-bottom:1px solid #2e3460;">
            <span style="background:{diff_color}33;color:{diff_color};padding:2px 8px;border-radius:12px;font-size:12px;font-weight:700;">
              {a.get('difficulty','').upper()}
            </span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #2e3460;color:#9fa8da;font-size:13px;">{a.get('end_date','未定')}</td>
          <td style="padding:10px;border-bottom:1px solid #2e3460;">
            <a href="{a.get('url','#')}" style="background:#7c4dff;color:white;padding:5px 12px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:700;">参加する</a>
          </td>
        </tr>"""

    # トレンドコイン
    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li style='margin-bottom:6px;'><strong style='color:#e8eaf6;'>{t['name']}</strong> <span style='color:#9fa8da;'>({t['symbol']})</span> — スコア: {t.get('score', 0)}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <div style="margin-top:20px;">
          <h3 style="color:#9c7dff;margin:0 0 10px;">📈 CoinGecko トレンドコイン</h3>
          <ul style="margin:0;padding-left:18px;color:#9fa8da;">{t_items}</ul>
        </div>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Helvetica Neue',Arial,'Hiragino Sans','Meiryo',sans-serif;max-width:720px;margin:0 auto;background:#0f0f1a;color:#e8eaf6;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:28px 24px;border-radius:10px 10px 0 0;border-bottom:2px solid #7c4dff;">
    <h1 style="margin:0;font-size:22px;background:linear-gradient(135deg,#fff,#9c7dff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:6px 0 0;opacity:0.7;font-size:13px;">{today} 日次更新レポート</p>
  </div>

  <!-- メイン -->
  <div style="background:#16213e;padding:24px;border-radius:0 0 10px 10px;border:1px solid #2e3460;border-top:none;">

    {hot_alert_html}
    {new_html}
    {changes_html}

    <!-- ホット案件一覧 -->
    <h3 style="color:#ff4757;margin:20px 0 12px;">🔥 注目のホットエアドロップ ({len(hot)}件)</h3>
    <table style="width:100%;border-collapse:collapse;background:#1e2240;border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#0f0f1a;">
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #2e3460;">プロジェクト</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #2e3460;">推定価値</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #2e3460;">難易度</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #2e3460;">期限</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #2e3460;">リンク</th>
        </tr>
      </thead>
      <tbody>{hot_rows}</tbody>
    </table>

    {trending_html}

    <hr style="margin:24px 0;border:none;border-top:1px solid #2e3460;">
    <p style="color:#9fa8da;font-size:11px;margin:0;line-height:1.6;">
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
    changes: list[dict] | None = None,
) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    newly_hot = [a for a in airdrops if a["name"] in new_items and a.get("is_hot")]

    subject = f"[Airdrop] {today} 更新 — ホット案件{hot_count}件"
    if newly_hot:
        subject += f" 🚨新着HOT {len(newly_hot)}件"
    elif new_items:
        subject += f" 🆕新着{len(new_items)}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, changes)
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
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
    diff_color = DIFFICULTY_COLOR.get(airdrop.get("difficulty", "easy"), "#6c757d")
    diff_jp = DIFFICULTY_JP.get(airdrop.get("difficulty", "easy"), "")
    tasks_html = "".join(f"<li>{t}</li>" for t in airdrop.get("tasks", []))
    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,} の新着HOT案件！"

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:'Helvetica Neue',Arial,'Hiragino Sans',sans-serif;max-width:600px;margin:0 auto;background:#0f0f1a;color:#e8eaf6;">
  <div style="background:linear-gradient(135deg,#dc3545,#7c4dff);padding:24px;border-radius:10px 10px 0 0;">
    <h2 style="margin:0;color:white;font-size:20px;">🚨 ホットエアドロップ出現！</h2>
    <p style="margin:4px 0 0;color:rgba(255,255,255,0.8);font-size:13px;">今すぐ確認してください</p>
  </div>
  <div style="background:#16213e;padding:24px;border:1px solid #2e3460;border-top:none;border-radius:0 0 10px 10px;">
    <h3 style="color:#e8eaf6;font-size:22px;margin:0 0 4px;">{name}</h3>
    <span style="background:#7c4dff22;color:#9c7dff;font-size:12px;padding:2px 10px;border-radius:20px;">{airdrop.get('category','')}</span>

    <div style="display:flex;gap:20px;margin:16px 0;flex-wrap:wrap;">
      <div><p style="color:#9fa8da;font-size:11px;margin:0 0 2px;">推定価値</p><strong style="color:#2ed573;font-size:24px;">~${value:,}</strong></div>
      <div><p style="color:#9fa8da;font-size:11px;margin:0 0 2px;">難易度</p><span style="background:{diff_color}33;color:{diff_color};padding:4px 12px;border-radius:12px;font-size:13px;font-weight:700;">{diff_jp}</span></div>
      <div><p style="color:#9fa8da;font-size:11px;margin:0 0 2px;">タイプ</p><strong style="color:#e8eaf6;font-size:14px;">{airdrop.get('type','')}</strong></div>
      <div><p style="color:#9fa8da;font-size:11px;margin:0 0 2px;">期限</p><strong style="color:#e8eaf6;font-size:14px;">{airdrop.get('end_date','未定')}</strong></div>
    </div>

    <p style="color:#9fa8da;font-size:13px;line-height:1.6;">{airdrop.get('description','')}</p>

    {f'<div style="background:#0f0f1a;border-radius:8px;padding:12px 16px;margin:12px 0;"><p style="color:#9fa8da;font-size:12px;font-weight:700;margin:0 0 6px;">📋 参加方法</p><ul style="margin:0;padding-left:16px;color:#9fa8da;font-size:13px;line-height:1.8;">{tasks_html}</ul></div>' if tasks_html else ''}

    <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#7c4dff);color:white;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px;margin-top:8px;">🚀 今すぐ参加する</a>

    <hr style="margin:20px 0;border:none;border-top:1px solid #2e3460;">
    <p style="color:#9fa8da;font-size:11px;margin:0;">投資は自己責任で行ってください。情報は参考目的のみです。</p>
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
