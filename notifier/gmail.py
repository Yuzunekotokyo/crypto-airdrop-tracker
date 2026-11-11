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


def _build_html_body(airdrops: list[dict], new_items: list[str], trending: list[dict]) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]

    new_html = ""
    if new_items:
        items_html = "".join(f"<li>{n}</li>" for n in new_items)
        new_html = f"""
        <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>🆕 新着エアドロップ ({len(new_items)}件)</strong>
          <ul style="margin:8px 0 0 0;">{items_html}</ul>
        </div>"""

    hot_rows = ""
    for a in hot[:5]:
        difficulty_color = {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}.get(
            a.get("difficulty", "easy"), "#6c757d"
        )
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "不明"
        hot_rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <strong>{a['name']}</strong><br>
            <span style="color:#6c757d;font-size:12px;">{a.get('category','')}</span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:bold;">{value}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <span style="background:{difficulty_color};color:white;padding:2px 8px;border-radius:12px;font-size:12px;">
              {a.get('difficulty','').upper()}
            </span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">{a.get('end_date','未定')}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <a href="{a.get('url','#')}" style="color:#0d6efd;">参加する</a>
          </td>
        </tr>"""

    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li><strong>{t['name']}</strong> ({t['symbol']}) — スコア: {t.get('score', 0)}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#6f42c1;">📈 CoinGecko トレンドコイン</h3>
        <ul>{t_items}</ul>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;background:#f8f9fa;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:24px;border-radius:8px 8px 0 0;">
    <h1 style="margin:0;font-size:22px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:4px 0 0;opacity:0.8;">{today} 更新レポート</p>
  </div>
  <div style="background:white;padding:24px;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
    {new_html}

    <h3 style="color:#dc3545;">🔥 注目のホットエアドロップ</h3>
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
      <tbody>{hot_rows}</tbody>
    </table>

    {trending_html}

    <hr style="margin:24px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:12px;margin:0;">
      ※ このメールはCrypto Airdrop Trackerから自動送信されています。<br>
      投資は自己責任で行ってください。情報は参考目的のみです。
    </p>
  </div>
</body>
</html>"""


def send_daily_report(airdrops: list[dict], new_items: list[str], trending: list[dict]) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    subject = f"[Airdrop] {today} 更新 — ホット案件{hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending)
    plain_body = f"{today} Airdrop更新レポート\nホット案件: {hot_count}件\n新着: {', '.join(new_items) if new_items else 'なし'}"

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
    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,}の新案件が登場！"

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:#dc3545;color:white;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;">🚨 ホットエアドロップ出現！</h2>
  </div>
  <div style="background:white;padding:20px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 8px 8px;">
    <h3>{name} ({airdrop.get('symbol','')})</h3>
    <p><strong>推定価値:</strong> ~${value:,}</p>
    <p><strong>カテゴリ:</strong> {airdrop.get('category','')}</p>
    <p><strong>難易度:</strong> {airdrop.get('difficulty','').upper()}</p>
    <p><strong>概要:</strong> {airdrop.get('description','')}</p>
    <p><strong>参加方法:</strong></p>
    <ul>{"".join(f"<li>{t}</li>" for t in airdrop.get('tasks', []))}</ul>
    <p><strong>期限:</strong> {airdrop.get('end_date','未定')}</p>
    <a href="{airdrop.get('url','#')}" style="display:inline-block;background:#dc3545;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold;">今すぐ参加する</a>
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


# ---------------------------------------------------------------------------
# 週足コンフルエンス・シグナル通知
# ---------------------------------------------------------------------------

_SIGNAL_STYLE = {
    "LONG": ("🚀", "LONGシグナル", "#198754", "支持線が重なるゾーンに到達しました"),
    "WATCH": ("👀", "ゾーン接近中", "#fd7e14", "下に行くならこの辺りで反発候補です"),
    "BROKEN": ("⚠️", "ゾーン割れ", "#dc3545", "支持ゾーンを下抜け。ロングのシナリオは無効です"),
}
_SIGNAL_DEFAULT = ("📊", "現在の判定", "#6c757d", "現在シグナルは出ていません")


def _usd(v: float) -> str:
    return f"${v:,.0f}"


def build_signal_email(result: dict) -> tuple[str, str, str]:
    """Returns: (subject, html, plain)"""
    from signals.engine import LEVEL_LABELS

    symbol = result["symbol"]
    status = result["status"]
    emoji, title, color, lead = _SIGNAL_STYLE.get(status, _SIGNAL_DEFAULT)
    if result.get("touched"):
        lead = "今週の安値が支持ゾーンにタッチ済み。反発を確認中です"
    zone = result.get("zone")
    plan = result.get("plan")
    in_zone = set(zone["levels"]) if zone else set()

    subject = f"{emoji} [{symbol} {title}] {_usd(result['price'])}"
    if zone:
        subject += f" — 週足{zone['strength']}本コンフルエンス {_usd(zone['low'])}〜{_usd(zone['high'])}"

    lines = [f"{symbol} {title}: {lead}", f"現在値: {_usd(result['price'])}"]
    level_rows = ""
    for key, value in sorted(result["levels"].items(), key=lambda kv: -kv[1]):
        mark = "● ゾーン構成" if key in in_zone else "—"
        lines.append(f"  {LEVEL_LABELS[key]}: {_usd(value)} {mark}")
        level_rows += (
            f'<tr><td style="padding:8px;border-bottom:1px solid #dee2e6;">{LEVEL_LABELS[key]}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #dee2e6;text-align:right;font-weight:bold;">{_usd(value)}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #dee2e6;color:#6c757d;">{mark}</td></tr>'
        )

    plan_html = ""
    if plan:
        entry_label = "エントリー (現在値)" if status == "LONG" else "エントリー候補 (ゾーン上限)"
        rows = [(entry_label, _usd(plan["entry"])), ("損切り目安 (ゾーン割れ)", _usd(plan["stop"]))]
        rows += [(f"利確目標: {t['label']}", f"{_usd(t['price'])} (RR {t['rr']:.1f})") for t in plan["targets"]]
        lines.append("")
        lines += [f"{k}: {v}" for k, v in rows]
        plan_html = '<h3 style="margin:20px 0 8px;">トレードプラン (参考)</h3><table style="width:100%;border-collapse:collapse;">' + "".join(
            f'<tr><td style="padding:8px;border-bottom:1px solid #dee2e6;">{k}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #dee2e6;text-align:right;font-weight:bold;">{v}</td></tr>'
            for k, v in rows
        ) + "</table>"

    zone_html = ""
    if zone:
        zone_html = (
            f'<p style="font-size:16px;margin:12px 0;">支持ゾーン: <strong>{_usd(zone["low"])} 〜 {_usd(zone["high"])}</strong>'
            f' <span style="color:#6c757d;">(現在値から {zone["distance_pct"] * 100:+.1f}%)</span></p>'
        )

    disclaimer = "※ 機械的な条件判定による自動通知です。売買の推奨ではありません。投資は自己責任で。"
    lines += ["", f"フィボ計算の起点: 安値 {_usd(result['swing_low'])} → 高値 {_usd(result['swing_high'])}", disclaimer]

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:{color};color:white;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;">{emoji} {symbol} {title}</h2>
    <p style="margin:6px 0 0;opacity:0.9;">{lead}</p>
  </div>
  <div style="background:white;padding:20px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 8px 8px;">
    <p style="font-size:22px;margin:0;">現在値 <strong>{_usd(result['price'])}</strong></p>
    {zone_html}
    <table style="width:100%;border-collapse:collapse;">{level_rows}</table>
    {plan_html}
    <p style="color:#6c757d;font-size:12px;margin-top:20px;">
      フィボ計算の起点: 安値 {_usd(result['swing_low'])} → 高値 {_usd(result['swing_high'])}
      (データ: {result.get('source', '-')} 週足)<br>{disclaimer}
    </p>
  </div>
</body></html>"""
    return subject, html, "\n".join(lines)


def send_signal_alert(result: dict) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためシグナル通知をスキップ (.envを確認してください)")
        return False

    subject, html, plain = build_signal_email(result)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"シグナル通知送信: {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗。アプリパスワードを確認してください。")
        return False
    except Exception as e:
        logger.error(f"シグナル通知送信失敗: {e}")
        return False
