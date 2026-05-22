"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用して自動メール送信。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)

_STYLE = """
  body { font-family: 'Hiragino Sans', 'Meiryo', Arial, sans-serif; background: #0f0f1a; margin: 0; padding: 0; }
  .wrap { max-width: 680px; margin: 0 auto; background: #1e2240; border-radius: 12px; overflow: hidden; }
  .hdr  { background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 28px 28px 20px; border-bottom: 2px solid #7c4dff; }
  .hdr h1 { color: #fff; margin: 0; font-size: 22px; }
  .hdr p  { color: #9fa8da; margin: 6px 0 0; font-size: 13px; }
  .body { padding: 24px 28px; }
  .stat-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
  .chip { padding: 5px 14px; border-radius: 20px; font-size: 13px; font-weight: 700; }
  .chip-total   { background: rgba(30,144,255,0.15); border: 1px solid #1e90ff; color: #1e90ff; }
  .chip-hot     { background: rgba(255,71,87,0.15);  border: 1px solid #ff4757; color: #ff6b81; }
  .chip-new     { background: rgba(46,213,115,0.15); border: 1px solid #2ed573; color: #2ed573; }
  .chip-changed { background: rgba(255,165,2,0.15);  border: 1px solid #ffa502; color: #ffa502; }
  .section-title { color: #e8eaf6; font-size: 16px; font-weight: 700; margin: 20px 0 10px; padding-bottom: 6px; border-bottom: 1px solid #2e3460; }
  .alert-box { background: rgba(255,71,87,0.1); border: 1px solid #ff4757; border-radius: 8px; padding: 14px 16px; margin-bottom: 18px; }
  .alert-box h3 { color: #ff6b81; margin: 0 0 6px; font-size: 15px; }
  .new-box { background: rgba(46,213,115,0.08); border: 1px solid #2ed573; border-radius: 8px; padding: 14px 16px; margin-bottom: 18px; }
  .new-box h3 { color: #2ed573; margin: 0 0 6px; font-size: 15px; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  th { padding: 10px 12px; background: #16213e; color: #9fa8da; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; text-align: left; }
  td { padding: 11px 12px; border-bottom: 1px solid #2e3460; color: #e8eaf6; font-size: 13px; vertical-align: middle; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #252b4a; }
  .badge { display: inline-block; padding: 3px 9px; border-radius: 12px; font-size: 11px; font-weight: 700; }
  .easy   { background: rgba(46,213,115,0.15); color: #2ed573; border: 1px solid #2ed573; }
  .medium { background: rgba(255,99,72,0.15);  color: #ff6348; border: 1px solid #ff6348; }
  .hard   { background: rgba(255,71,87,0.15);  color: #ff4757; border: 1px solid #ff4757; }
  .value  { color: #2ed573; font-weight: 700; }
  .btn    { display: inline-block; background: linear-gradient(135deg,#7c4dff,#651fff); color: #fff !important; padding: 8px 18px; border-radius: 8px; font-size: 13px; font-weight: 700; text-decoration: none; }
  .footer { background: #16213e; padding: 16px 28px; text-align: center; color: #9fa8da; font-size: 11px; border-top: 1px solid #2e3460; }
  .trending-list { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 6px; }
  .trending-list li { background: rgba(124,77,255,0.12); border: 1px solid rgba(124,77,255,0.3); color: #b39dff; padding: 3px 10px; border-radius: 12px; font-size: 12px; }
"""


def _difficulty_badge(diff: str) -> str:
    cls = diff.lower() if diff.lower() in ("easy", "medium", "hard") else "easy"
    return f'<span class="badge {cls}">{diff.upper()}</span>'


def _build_html_body(airdrops: list[dict], new_items: list[str], trending: list[dict]) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot   = [a for a in airdrops if a.get("is_hot")]
    new_hot = [a for a in hot if a.get("name") in new_items]
    total = len(airdrops)
    hot_count = len(hot)

    # ---- 新着ホット案件アラートブロック ----
    new_hot_html = ""
    if new_hot:
        rows = ""
        for a in new_hot:
            value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
            tasks_html = "".join(f"<li>{t}</li>" for t in a.get("tasks", [])[:3])
            rows += f"""
            <tr>
              <td><strong>{a['name']}</strong><br><span style="color:#9fa8da;font-size:11px;">{a.get('category','')}</span></td>
              <td class="value">{value}</td>
              <td>{_difficulty_badge(a.get('difficulty','easy'))}</td>
              <td>{a.get('end_date','未定')}</td>
              <td><a href="{a.get('url','#')}" class="btn">参加する</a></td>
            </tr>"""
        new_hot_html = f"""
        <div class="alert-box">
          <h3>🚨 注目！新着ホット案件 ({len(new_hot)}件)</h3>
          <p style="color:#9fa8da;font-size:13px;margin:0 0 10px;">本日新たに登録された高ポテンシャル案件です。早めの参加を推奨します。</p>
          <table><thead><tr>
            <th>プロジェクト</th><th>推定価値</th><th>難易度</th><th>期限</th><th>リンク</th>
          </tr></thead><tbody>{rows}</tbody></table>
        </div>"""

    # ---- 新着一般案件ブロック ----
    regular_new = [n for n in new_items if n not in [a["name"] for a in new_hot]]
    new_items_html = ""
    if regular_new:
        items_li = "".join(f"<li style='color:#e8eaf6;margin:3px 0;'>• {n}</li>" for n in regular_new)
        new_items_html = f"""
        <div class="new-box">
          <h3>🆕 新着エアドロップ ({len(regular_new)}件)</h3>
          <ul style="list-style:none;padding:0;margin:0;">{items_li}</ul>
        </div>"""

    # ---- ホット案件テーブル ----
    hot_rows = ""
    for a in hot[:8]:
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        hot_rows += f"""
        <tr>
          <td>
            <strong>{a['name']}</strong>
            {'<span style="background:#2ed573;color:#000;font-size:9px;font-weight:900;padding:1px 5px;border-radius:3px;margin-left:5px;">NEW</span>' if a.get('name') in new_items else ''}
            <br>
            <span style="color:#9fa8da;font-size:11px;">{a.get('category','')} · {a.get('type','')}</span>
          </td>
          <td class="value">{value}</td>
          <td>{_difficulty_badge(a.get('difficulty','easy'))}</td>
          <td style="color:#9fa8da;">{a.get('end_date','未定')}</td>
          <td><a href="{a.get('url','#')}" class="btn">参加</a></td>
        </tr>"""

    # ---- トレンドコイン ----
    trending_html = ""
    if trending:
        items_li = "".join(
            f"<li><strong>{t['name']}</strong> ({t['symbol']})</li>"
            for t in trending[:8]
        )
        trending_html = f"""
        <p class="section-title">📈 CoinGecko トレンドコイン</p>
        <ul class="trending-list">{items_li}</ul>"""

    stat_chips = f"""
    <div class="stat-row">
      <span class="chip chip-total">📋 計 {total}件</span>
      <span class="chip chip-hot">🔥 ホット {hot_count}件</span>
      {'<span class="chip chip-new">🆕 新着 ' + str(len(new_items)) + '件</span>' if new_items else ''}
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><style>{_STYLE}</style></head>
<body>
<div class="wrap">
  <div class="hdr">
    <h1>🪂 Crypto Airdrop Tracker</h1>
    <p>{today} — 日次更新レポート</p>
  </div>
  <div class="body">
    {stat_chips}
    {new_hot_html}
    {new_items_html}

    <p class="section-title">🔥 現在のホット案件 (上位8件)</p>
    <table>
      <thead><tr>
        <th>プロジェクト</th>
        <th>推定価値</th>
        <th>難易度</th>
        <th>期限</th>
        <th>リンク</th>
      </tr></thead>
      <tbody>{hot_rows}</tbody>
    </table>

    {trending_html}
  </div>
  <div class="footer">
    <p>このメールは Crypto Airdrop Tracker から自動送信されています。</p>
    <p style="margin-top:4px;">⚠️ 投資は自己責任で行ってください。掲載情報は参考目的のみです。</p>
  </div>
</div>
</body>
</html>"""


def send_daily_report(airdrops: list[dict], new_items: list[str], trending: list[dict]) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報未設定 — .envにGMAIL_SENDER/GMAIL_APP_PASSWORDを設定してください")
        return False

    today     = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    hot_new   = [a for a in airdrops if a.get("is_hot") and a.get("name") in new_items]

    subject = f"[Airdrop] {today} 更新 — 🔥ホット{hot_count}件"
    if hot_new:
        subject += f" 🚨新着ホット{len(hot_new)}件！"
    elif new_items:
        subject += f" 🆕新着{len(new_items)}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_SENDER
    msg["To"]      = GMAIL_RECIPIENT

    plain = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"トレンド: {', '.join(t['name'] for t in trending[:5])}"
    )
    html = _build_html_body(airdrops, new_items, trending)

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html,  "html",  "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"日次レポート送信成功: {GMAIL_RECIPIENT} / 件名: {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗 — アプリパスワードを確認してください")
        return False
    except Exception as e:
        logger.error(f"メール送信失敗: {e}")
        return False


def send_hot_alert(airdrop: dict) -> bool:
    """新規ホット案件出現時の即時アラートメール"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        return False

    name  = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd", 0)
    diff  = airdrop.get("difficulty", "easy")
    tasks_html = "".join(f"<li style='margin:4px 0;color:#e8eaf6;'>{t}</li>" for t in airdrop.get("tasks", []))

    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,} の新案件が登場！"

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><style>{_STYLE}</style></head>
<body>
<div class="wrap">
  <div class="hdr" style="background:linear-gradient(135deg,#7b0000,#dc3545);">
    <h1>🚨 ホットエアドロップ出現！</h1>
    <p style="color:#ffcdd2;">{datetime.now().strftime('%Y年%m月%d日 %H:%M')} — 即時アラート</p>
  </div>
  <div class="body">
    <div class="alert-box">
      <h3 style="font-size:20px;">{name}</h3>
      <div class="stat-row" style="margin-top:10px;">
        <span class="chip chip-hot">推定価値: ~${value:,}</span>
        <span class="chip">{_difficulty_badge(diff)}</span>
        <span class="chip chip-changed">期限: {airdrop.get('end_date','未定')}</span>
      </div>
    </div>

    <p style="color:#9fa8da;font-size:14px;margin-bottom:12px;"><strong style="color:#e8eaf6;">カテゴリ:</strong> {airdrop.get('category','')}</p>
    <p style="color:#9fa8da;font-size:14px;margin-bottom:16px;"><strong style="color:#e8eaf6;">概要:</strong> {airdrop.get('description','')}</p>

    <p class="section-title">📋 参加手順</p>
    <ol style="padding-left:20px;margin:0;">{tasks_html}</ol>

    <p style="margin-top:24px;">
      <a href="{airdrop.get('url','#')}" class="btn" style="font-size:15px;padding:12px 28px;">今すぐ参加する →</a>
    </p>
  </div>
  <div class="footer">
    <p>⚠️ 投資は自己責任で行ってください。情報は参考目的のみです。</p>
  </div>
</div>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_SENDER
    msg["To"]      = GMAIL_RECIPIENT
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
