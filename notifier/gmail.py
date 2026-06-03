"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) または Gmail API OAuth2 を使用してメール送信。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)


def _difficulty_color(diff: str) -> str:
    return {"easy": "#2ed573", "medium": "#ffa502", "hard": "#ff4757"}.get(diff, "#9fa8da")


def _urgency_label(airdrops: list[dict], new_items: list[str]) -> str:
    hot_new = [a for a in airdrops if a.get("is_hot") and a["name"] in new_items]
    if hot_new:
        return f"🚨 緊急: 注目ホット案件{len(hot_new)}件が新着！"
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    if hot_count >= 3:
        return f"🔥 ホット案件{hot_count}件稼働中"
    return "📋 定期更新レポート"


def _build_html_body(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    changes: list[dict] | None = None,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    new_hot = [a for a in hot if a["name"] in set(new_items)]

    # 新着セクション
    new_html = ""
    if new_items:
        items_html = "".join(f"<li style='margin:4px 0;'>{n}</li>" for n in new_items[:10])
        new_html = f"""
        <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:12px 16px;margin:16px 0;border-radius:6px;">
          <strong>🆕 新着エアドロップ ({len(new_items)}件)</strong>
          <ul style="margin:8px 0 0 16px;">{items_html}</ul>
        </div>"""

    # 新着ホット案件アラート
    new_hot_html = ""
    if new_hot:
        cards = ""
        for a in new_hot[:3]:
            value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
            diff_color = _difficulty_color(a.get("difficulty", ""))
            cards += f"""
            <div style="border:2px solid #dc3545;border-radius:8px;padding:12px;margin:8px 0;background:#fff5f5;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <strong style="font-size:16px;">🔥 {a['name']}</strong>
                <span style="background:#dc3545;color:white;padding:3px 10px;border-radius:12px;font-size:12px;">NEW HOT</span>
              </div>
              <p style="margin:6px 0;color:#495057;">{a.get('description','')[:100]}...</p>
              <div style="display:flex;gap:16px;margin-top:8px;font-size:13px;">
                <span><strong>💰 推定:</strong> <span style="color:#28a745;font-weight:bold;">{value}</span></span>
                <span><strong>難易度:</strong> <span style="color:{diff_color};font-weight:bold;">{a.get('difficulty','').upper()}</span></span>
                <span><strong>期限:</strong> {a.get('end_date','未定')}</span>
              </div>
              <div style="margin-top:8px;">
                <a href="{a.get('url','#')}" style="background:#dc3545;color:white;padding:8px 20px;border-radius:6px;text-decoration:none;font-weight:bold;display:inline-block;">今すぐ参加 →</a>
              </div>
            </div>"""
        new_hot_html = f"""
        <div style="margin:16px 0;">
          <h3 style="color:#dc3545;margin-bottom:8px;">🚨 新着ホット案件 — 今すぐ確認！</h3>
          {cards}
        </div>"""

    # 変更点セクション
    changes_html = ""
    if changes:
        change_items = "".join(
            f"<li><strong>{c['name']}</strong>: {'、'.join(c['changes'])}</li>"
            for c in changes[:5]
        )
        changes_html = f"""
        <div style="background:#e8f4fd;border-left:4px solid #1e90ff;padding:12px 16px;margin:16px 0;border-radius:6px;">
          <strong>✏️ 更新された案件 ({len(changes)}件)</strong>
          <ul style="margin:8px 0 0 16px;">{change_items}</ul>
        </div>"""

    # ホット案件テーブル
    hot_rows = ""
    for a in hot[:5]:
        diff_color = _difficulty_color(a.get("difficulty", ""))
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        new_badge = " 🆕" if a["name"] in set(new_items) else ""
        hot_rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <strong>{a['name']}{new_badge}</strong><br>
            <span style="color:#6c757d;font-size:12px;">{a.get('category','')}</span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:bold;">{value}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <span style="background:{diff_color};color:white;padding:2px 8px;border-radius:12px;font-size:12px;">
              {a.get('difficulty','').upper()}
            </span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">{a.get('end_date','未定')}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <a href="{a.get('url','#')}" style="color:#0d6efd;">参加する</a>
          </td>
        </tr>"""

    # トレンドコイン
    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li><strong>{t['name']}</strong> ({t['symbol']}) — スコア: {t.get('score', 0)}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#6f42c1;margin-top:20px;">📈 CoinGecko トレンドコイン</h3>
        <ul style="margin:8px 0 0 16px;">{t_items}</ul>"""

    stats = f"総案件: {len(airdrops)}件 | ホット: {len(hot)}件 | 新着: {len(new_items)}件"

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:Arial,'Hiragino Sans',sans-serif;max-width:700px;margin:0 auto;background:#f8f9fa;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:24px;border-radius:8px 8px 0 0;">
    <h1 style="margin:0;font-size:22px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:4px 0 0;opacity:0.8;">{today} 更新レポート</p>
    <p style="margin:8px 0 0;font-size:13px;opacity:0.7;">{stats}</p>
  </div>
  <div style="background:white;padding:24px;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">

    {new_hot_html}
    {new_html}
    {changes_html}

    <h3 style="color:#dc3545;margin-top:20px;">🔥 注目のホットエアドロップ TOP5</h3>
    <table style="width:100%;border-collapse:collapse;margin-top:8px;font-size:14px;">
      <thead>
        <tr style="background:#f8f9fa;">
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">プロジェクト</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">推定価値</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">難易度</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">期限</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">リンク</th>
        </tr>
      </thead>
      <tbody>{hot_rows}</tbody>
    </table>

    {trending_html}

    <hr style="margin:24px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:12px;margin:0;">
      ※ このメールはCrypto Airdrop Trackerから自動送信されています。<br>
      ※ 投資は自己責任で行ってください。情報は参考目的のみです。
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
    urgency = _urgency_label(airdrops, new_items)
    subject = f"[Airdrop] {today} — {urgency}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, changes)
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items[:5]) if new_items else 'なし'}\n"
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
    diff_color = _difficulty_color(airdrop.get("difficulty", ""))
    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,}の新案件が登場！"

    tasks_html = "".join(f"<li>{t}</li>" for t in airdrop.get("tasks", []))

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#dc3545,#a71d2a);color:white;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;">🚨 ホットエアドロップ出現！</h2>
    <p style="margin:4px 0 0;opacity:0.9;">今すぐ確認してください</p>
  </div>
  <div style="background:white;padding:20px;border:2px solid #dc3545;border-top:none;border-radius:0 0 8px 8px;">
    <h3 style="color:#dc3545;">{name} ({airdrop.get('symbol','')})</h3>
    <table style="width:100%;margin:12px 0;">
      <tr>
        <td style="padding:6px 0;width:120px;color:#6c757d;">💰 推定価値</td>
        <td style="font-weight:bold;color:#28a745;font-size:18px;">~${value:,}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6c757d;">📂 カテゴリ</td>
        <td>{airdrop.get('category','')}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6c757d;">⚡ 難易度</td>
        <td><span style="background:{diff_color};color:white;padding:2px 8px;border-radius:10px;font-size:13px;">{airdrop.get('difficulty','').upper()}</span></td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6c757d;">📅 期限</td>
        <td>{airdrop.get('end_date','未定')}</td>
      </tr>
    </table>
    <p style="color:#495057;">{airdrop.get('description','')}</p>
    <p style="font-weight:bold;margin-bottom:4px;">📋 参加方法:</p>
    <ul style="margin:0 0 16px 16px;">{tasks_html}</ul>
    <a href="{airdrop.get('url','#')}" style="display:inline-block;background:#dc3545;color:white;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:16px;">今すぐ参加する →</a>
    <hr style="margin:20px 0;border:none;border-top:1px solid #dee2e6;">
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


def build_html_body(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    changes: list[dict] | None = None,
) -> str:
    """外部からHTML本文を生成するための公開ヘルパー (MCP等から利用)"""
    return _build_html_body(airdrops, new_items, trending, changes)
