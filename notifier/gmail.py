"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してメール送信。
毎日の日次サマリー + ホット案件出現時の即時アラートを送信。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)


def _deadline_warning_html(airdrops: list[dict]) -> str:
    """7日以内に期限切れになるエアドロップの警告セクション"""
    today = datetime.utcnow().date()
    soon = []
    for a in airdrops:
        end_str = a.get("end_date", "")
        try:
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
            days_left = (end_date - today).days
            if 0 <= days_left <= 7:
                soon.append((a, days_left))
        except ValueError:
            pass
    if not soon:
        return ""
    rows = "".join(
        f'<li><strong>{a["name"]}</strong> — あと <span style="color:#dc3545;font-weight:bold;">{d}日</span>'
        f' (<a href="{a.get("url","#")}" style="color:#0d6efd;">参加する</a>)</li>'
        for a, d in sorted(soon, key=lambda x: x[1])
    )
    return f"""
    <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:12px 16px;margin:16px 0;border-radius:4px;">
      <strong>⏰ 間もなく期限切れ ({len(soon)}件)</strong>
      <ul style="margin:8px 0 0 0;">{rows}</ul>
    </div>"""


def _new_items_html(new_items: list[str]) -> str:
    if not new_items:
        return ""
    items_html = "".join(f"<li>{n}</li>" for n in new_items)
    return f"""
    <div style="background:#d4edda;border-left:4px solid #28a745;padding:12px 16px;margin:16px 0;border-radius:4px;">
      <strong>🆕 本日の新着エアドロップ ({len(new_items)}件)</strong>
      <ul style="margin:8px 0 0 0;">{items_html}</ul>
    </div>"""


def _hot_airdrops_table(airdrops: list[dict]) -> str:
    hot = [a for a in airdrops if a.get("is_hot") and a.get("source") != "defillama"]
    if not hot:
        return "<p style='color:#6c757d;'>現在のホット案件はありません。</p>"
    rows = ""
    for a in hot[:6]:
        color = {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}.get(
            a.get("difficulty", "easy"), "#6c757d"
        )
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "不明"
        rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <strong>{a['name']}</strong><br>
            <span style="color:#6c757d;font-size:12px;">{a.get('category','')}</span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:bold;">{value}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <span style="background:{color};color:white;padding:2px 8px;border-radius:12px;font-size:12px;">
              {a.get('difficulty','').upper()}
            </span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">{a.get('end_date','未定')}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <a href="{a.get('url','#')}" style="color:#0d6efd;">参加する</a>
          </td>
        </tr>"""
    return f"""
    <table style="width:100%;border-collapse:collapse;margin-top:8px;">
      <thead>
        <tr style="background:#f8f9fa;">
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">プロジェクト</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">推定価値</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">難易度</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">期限</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">リンク</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>"""


def _defi_watchlist_html(defi_watchlist: list[dict]) -> str:
    if not defi_watchlist:
        return ""
    hot_items = [p for p in defi_watchlist if p.get("is_hot")]
    all_items = defi_watchlist[:6]
    rows = ""
    for p in all_items:
        tvl = p.get("tvl_usd", 0)
        tvl_str = f"${tvl/1e6:.1f}M" if tvl >= 1_000_000 else f"${tvl:,}"
        hot_mark = "🔥 " if p.get("is_hot") else ""
        rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <strong>{hot_mark}{p['name']}</strong><br>
            <span style="color:#6c757d;font-size:12px;">{p.get('category','DeFi')}</span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;color:#6f42c1;font-weight:bold;">{tvl_str}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">~${p.get('estimated_value_usd',0):,}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            {', '.join((p.get('chains') or p.get('description','').split('チェーン')[0].split('・')[-1:])[:2])}
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <a href="{p.get('url','#')}" style="color:#0d6efd;">確認する</a>
          </td>
        </tr>"""
    hot_badge = f'<span style="background:#dc3545;color:white;padding:2px 8px;border-radius:12px;font-size:11px;margin-left:8px;">HOT {len(hot_items)}件</span>' if hot_items else ""
    return f"""
    <h3 style="color:#6f42c1;margin-top:24px;">
      🔭 DeFiLlama エアドロップ候補ウォッチリスト{hot_badge}
    </h3>
    <p style="color:#6c757d;font-size:13px;margin-bottom:8px;">
      トークン未発行・高TVLのプロトコル。今のうちに積極利用でエアドロップ獲得を狙えます。
    </p>
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr style="background:#f3e5f5;">
          <th style="padding:10px;text-align:left;border-bottom:2px solid #ce93d8;">プロトコル</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #ce93d8;">TVL</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #ce93d8;">推定価値/人</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #ce93d8;">チェーン</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #ce93d8;">リンク</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>"""


def _build_html_body(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    defi_watchlist: list[dict] | None = None,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    total = len(airdrops)
    hot_count = len(hot)

    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li><strong>{t['name']}</strong> ({t['symbol']}) — スコア: {t.get('score', 0)}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#6f42c1;margin-top:24px;">📈 CoinGecko トレンドコイン</h3>
        <ul>{t_items}</ul>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:720px;margin:0 auto;background:#f8f9fa;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:24px;border-radius:8px 8px 0 0;">
    <h1 style="margin:0;font-size:22px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:4px 0 0;opacity:0.8;">{today} 日次アップデートレポート</p>
  </div>

  <!-- サマリーバー -->
  <div style="background:#0d2137;color:white;padding:12px 24px;display:flex;gap:20px;flex-wrap:wrap;">
    <span>📋 総数: <strong>{total}</strong>件</span>
    <span>🔥 ホット: <strong>{hot_count}</strong>件</span>
    {'<span style="color:#90ee90;">🆕 新着: <strong>' + str(len(new_items)) + '</strong>件</span>' if new_items else ''}
  </div>

  <div style="background:white;padding:24px;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">

    {_new_items_html(new_items)}
    {_deadline_warning_html(airdrops)}

    <h3 style="color:#dc3545;">🔥 注目のホットエアドロップ</h3>
    {_hot_airdrops_table(airdrops)}

    {_defi_watchlist_html(defi_watchlist or [])}

    {trending_html}

    <hr style="margin:24px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:12px;margin:0;">
      ※ このメールはCrypto Airdrop Trackerから毎日08:00 JST に自動送信されています。<br>
      投資は自己責任で行ってください。掲載情報は参考目的のみです。
    </p>
  </div>

</body>
</html>"""


def send_daily_report(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    defi_watchlist: list[dict] | None = None,
) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    defi_hot = sum(1 for p in (defi_watchlist or []) if p.get("is_hot"))

    subject = f"[Airdrop] {today} 日次レポート — ホット{hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"
    if defi_hot:
        subject += f" 🔭DeFi候補{defi_hot}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, defi_watchlist)
    plain_body = (
        f"{today} Airdrop日次レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"DeFiLlama候補: {len(defi_watchlist or [])}件"
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
    source_label = "DeFiLlama発見" if airdrop.get("source") == "defillama" else "新規エアドロップ"
    tvl_str = ""
    if airdrop.get("tvl_usd"):
        tvl_str = f"<p><strong>TVL:</strong> ${airdrop['tvl_usd']/1e6:.1f}M</p>"

    subject = f"🚨 [HOT Airdrop] {name} — {source_label}！推定${value:,}"

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:#dc3545;color:white;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;">🚨 ホットエアドロップ発見！</h2>
    <p style="margin:4px 0 0;opacity:0.9;">{source_label}</p>
  </div>
  <div style="background:white;padding:20px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 8px 8px;">
    <h3>{name} ({airdrop.get('symbol','')})</h3>
    <p><strong>推定価値:</strong> ~${value:,}</p>
    <p><strong>カテゴリ:</strong> {airdrop.get('category','')}</p>
    <p><strong>難易度:</strong> {airdrop.get('difficulty','').upper()}</p>
    {tvl_str}
    <p><strong>概要:</strong> {airdrop.get('description','')}</p>
    <p><strong>参加方法:</strong></p>
    <ul>{"".join(f"<li>{t}</li>" for t in airdrop.get('tasks', []))}</ul>
    <p><strong>期限:</strong> {airdrop.get('end_date','未定')}</p>
    <a href="{airdrop.get('url','#')}" style="display:inline-block;background:#dc3545;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold;">今すぐ確認する</a>
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
