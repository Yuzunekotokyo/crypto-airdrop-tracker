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


def _price_row(sym: str, data: dict) -> str:
    sign = "▲" if data.get("up") else "▼"
    color = "#2ed573" if data.get("up") else "#ff4757"
    change = data.get("change_24h", 0)
    usd = data.get("usd", 0)
    jpy = data.get("jpy", 0)
    return f"""
    <tr>
      <td style="padding:8px 12px;border-bottom:1px solid #2e3460;font-weight:bold;color:#e8eaf6;">
        {sym} <span style="color:#9fa8da;font-size:12px;">({data.get('name_ja','')})</span>
      </td>
      <td style="padding:8px 12px;border-bottom:1px solid #2e3460;color:#e8eaf6;">${usd:,.0f}</td>
      <td style="padding:8px 12px;border-bottom:1px solid #2e3460;color:#9fa8da;">¥{jpy:,.0f}</td>
      <td style="padding:8px 12px;border-bottom:1px solid #2e3460;color:{color};font-weight:bold;">
        {sign} {abs(change):.2f}%
      </td>
    </tr>"""


def _build_html_body(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    news_data: dict | None = None,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    news_data = news_data or {}

    # --- 新着バナー ---
    new_html = ""
    if new_items:
        items_html = "".join(f"<li>{n}</li>" for n in new_items)
        new_html = f"""
        <div style="background:#0d2a1a;border-left:4px solid #2ed573;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong style="color:#2ed573;">🆕 新着エアドロップ ({len(new_items)}件)</strong>
          <ul style="margin:8px 0 0 0;color:#e8eaf6;">{items_html}</ul>
        </div>"""

    # --- 市場価格テーブル ---
    prices = news_data.get("prices", {})
    global_m = news_data.get("global_market", {})
    price_rows = "".join(_price_row(sym, d) for sym, d in prices.items())
    market_change = global_m.get("market_cap_change_24h", 0)
    market_color = "#2ed573" if market_change >= 0 else "#ff4757"
    market_sign = "▲" if market_change >= 0 else "▼"
    total_cap = global_m.get("total_market_cap_usd", 0)
    btc_dom = global_m.get("btc_dominance", 0)

    market_html = ""
    if prices:
        market_html = f"""
        <h3 style="color:#9fa8da;margin-top:20px;">📊 本日の市場価格</h3>
        <div style="background:#16213e;border-radius:8px;padding:12px;margin-bottom:8px;font-size:13px;color:#9fa8da;">
          時価総額 ${total_cap/1e12:.2f}T&nbsp;&nbsp;|&nbsp;&nbsp;
          24h変動 <span style="color:{market_color};font-weight:bold;">{market_sign}{abs(market_change):.2f}%</span>&nbsp;&nbsp;|&nbsp;&nbsp;
          BTC支配率 {btc_dom:.1f}%
        </div>
        <table style="width:100%;border-collapse:collapse;background:#1e2240;border-radius:8px;overflow:hidden;">
          <thead>
            <tr style="background:#252b4a;">
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:12px;">コイン</th>
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:12px;">USD</th>
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:12px;">JPY</th>
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:12px;">24h</th>
            </tr>
          </thead>
          <tbody>{price_rows}</tbody>
        </table>"""

    # --- DeFiLlama エアドロップ候補 ---
    candidates = news_data.get("new_candidates", []) or news_data.get("airdrop_candidates", [])[:5]
    cand_html = ""
    if candidates:
        cand_rows = ""
        for c in candidates[:5]:
            tvl_b = c.get("tvl_usd", 0) / 1e9
            tvl_m = c.get("tvl_usd", 0) / 1e6
            tvl_str = f"${tvl_b:.2f}B" if tvl_b >= 1 else f"${tvl_m:.0f}M"
            cand_rows += f"""
            <tr>
              <td style="padding:8px 12px;border-bottom:1px solid #2e3460;color:#e8eaf6;font-weight:bold;">{c['name']}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #2e3460;color:#ffa502;">{tvl_str}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #2e3460;color:#9fa8da;">{c.get('chain','')}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #2e3460;">
                <a href="{c.get('url','#')}" style="color:#7c4dff;">参加する</a>
              </td>
            </tr>"""
        label = "🆕 注目の新候補" if news_data.get("new_candidates") else "💡 エアドロップ有望候補"
        cand_html = f"""
        <h3 style="color:#7c4dff;margin-top:24px;">{label} (トークン未発行・高TVL)</h3>
        <p style="color:#9fa8da;font-size:12px;margin:0 0 8px;">DeFiLlamaより: トークンを未発行のまま高いTVLを誇るプロトコルはエアドロップの可能性大</p>
        <table style="width:100%;border-collapse:collapse;background:#1e2240;border-radius:8px;overflow:hidden;">
          <thead>
            <tr style="background:#252b4a;">
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:12px;">プロトコル</th>
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:12px;">TVL</th>
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:12px;">チェーン</th>
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:12px;">リンク</th>
            </tr>
          </thead>
          <tbody>{cand_rows}</tbody>
        </table>"""

    # --- ホット案件テーブル ---
    hot_rows = ""
    for a in hot[:5]:
        difficulty_color = {"easy": "#2ed573", "medium": "#ff6348", "hard": "#ff4757"}.get(
            a.get("difficulty", "easy"), "#6c757d"
        )
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "不明"
        hot_rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #2e3460;color:#e8eaf6;">
            <strong>{a['name']}</strong><br>
            <span style="color:#9fa8da;font-size:12px;">{a.get('category','')}</span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #2e3460;color:#2ed573;font-weight:bold;">{value}</td>
          <td style="padding:10px;border-bottom:1px solid #2e3460;">
            <span style="background:{difficulty_color};color:white;padding:2px 8px;border-radius:12px;font-size:12px;">
              {a.get('difficulty','').upper()}
            </span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #2e3460;color:#9fa8da;">{a.get('end_date','未定')}</td>
          <td style="padding:10px;border-bottom:1px solid #2e3460;">
            <a href="{a.get('url','#')}" style="color:#7c4dff;">参加する</a>
          </td>
        </tr>"""

    # --- トレンドコイン ---
    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li style='color:#e8eaf6;margin-bottom:4px;'>"
            f"<strong>{t['name']}</strong> ({t['symbol']}) — スコア: {t.get('score', 0)}"
            f"</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#1e90ff;margin-top:24px;">📈 CoinGecko トレンドコイン</h3>
        <ul style="background:#1e2240;padding:14px 20px;border-radius:8px;">{t_items}</ul>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:720px;margin:0 auto;background:#0f0f1a;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:24px;border-radius:8px 8px 0 0;">
    <h1 style="margin:0;font-size:22px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:4px 0 0;opacity:0.7;">{today} 日次更新レポート</p>
  </div>
  <div style="background:#16213e;padding:24px;border-radius:0 0 8px 8px;border:1px solid #2e3460;">
    {new_html}
    {market_html}
    {cand_html}

    <h3 style="color:#ff4757;margin-top:24px;">🔥 注目のホットエアドロップ</h3>
    <table style="width:100%;border-collapse:collapse;background:#1e2240;border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#252b4a;">
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;">プロジェクト</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;">推定価値</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;">難易度</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;">期限</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;">リンク</th>
        </tr>
      </thead>
      <tbody>{hot_rows}</tbody>
    </table>

    {trending_html}

    <hr style="margin:24px 0;border:none;border-top:1px solid #2e3460;">
    <p style="color:#6c757d;font-size:12px;margin:0;">
      ※ このメールはCrypto Airdrop Trackerから自動送信されています。<br>
      投資は自己責任で行ってください。情報は参考目的のみです。
    </p>
  </div>
</body>
</html>"""


def send_daily_report(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    news_data: dict | None = None,
) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    new_cand_count = len((news_data or {}).get("new_candidates", []))
    btc = (news_data or {}).get("prices", {}).get("BTC", {}).get("usd", 0)

    subject = f"[Airdrop] {today} — 🔥ホット{hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"
    if new_cand_count:
        subject += f" 💡新候補{new_cand_count}件"
    if btc:
        subject += f" | BTC ${btc:,.0f}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, news_data)
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"新候補: {new_cand_count}件\n"
        f"BTC: ${btc:,.0f}"
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
    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,}の新案件が登場！"

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0f0f1a;">
  <div style="background:linear-gradient(135deg,#dc3545,#7c4dff);color:white;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;">🚨 ホットエアドロップ出現！</h2>
    <p style="margin:4px 0 0;opacity:0.8;">新しい高価値案件を検出しました</p>
  </div>
  <div style="background:#16213e;padding:20px;border:1px solid #2e3460;border-top:none;border-radius:0 0 8px 8px;color:#e8eaf6;">
    <h3 style="color:#ff4757;">{name} ({airdrop.get('symbol','')})</h3>
    <table style="width:100%;font-size:14px;">
      <tr><td style="color:#9fa8da;padding:4px 0;">推定価値:</td><td style="color:#2ed573;font-weight:bold;">~${value:,}</td></tr>
      <tr><td style="color:#9fa8da;padding:4px 0;">カテゴリ:</td><td>{airdrop.get('category','')}</td></tr>
      <tr><td style="color:#9fa8da;padding:4px 0;">難易度:</td><td>{airdrop.get('difficulty','').upper()}</td></tr>
      <tr><td style="color:#9fa8da;padding:4px 0;">期限:</td><td>{airdrop.get('end_date','未定')}</td></tr>
    </table>
    <p style="color:#9fa8da;margin-top:12px;">{airdrop.get('description','')}</p>
    <p style="font-weight:bold;color:#e8eaf6;">📋 参加方法:</p>
    <ul style="color:#9fa8da;">{"".join(f"<li>{t}</li>" for t in airdrop.get('tasks', []))}</ul>
    <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#7c4dff);color:white;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:bold;margin-top:8px;">今すぐ参加する →</a>
    <hr style="margin:20px 0;border:none;border-top:1px solid #2e3460;">
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


def send_new_candidate_alert(candidates: list[dict]) -> bool:
    """DeFiLlamaで新たに発見された高TVLエアドロップ候補の即時アラート"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD or not candidates:
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    subject = f"💡 [新候補] {today} — トークン未発行の高TVLプロトコル{len(candidates)}件を検出！"

    rows = ""
    for c in candidates[:10]:
        tvl = c.get("tvl_usd", 0)
        tvl_str = f"${tvl/1e9:.2f}B" if tvl >= 1e9 else f"${tvl/1e6:.0f}M"
        rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #2e3460;color:#e8eaf6;font-weight:bold;">{c['name']}</td>
          <td style="padding:10px;border-bottom:1px solid #2e3460;color:#ffa502;font-weight:bold;">{tvl_str}</td>
          <td style="padding:10px;border-bottom:1px solid #2e3460;color:#9fa8da;">{c.get('chain','')}</td>
          <td style="padding:10px;border-bottom:1px solid #2e3460;color:#9fa8da;">{c.get('category','')}</td>
          <td style="padding:10px;border-bottom:1px solid #2e3460;">
            <a href="{c.get('url','#')}" style="color:#7c4dff;">確認する</a>
          </td>
        </tr>"""

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:720px;margin:0 auto;background:#0f0f1a;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#7c4dff33);color:white;padding:20px;border-radius:8px 8px 0 0;border-bottom:2px solid #7c4dff;">
    <h2 style="margin:0;">💡 新しいエアドロップ候補を検出！</h2>
    <p style="margin:4px 0 0;opacity:0.7;">DeFiLlamaでトークン未発行・高TVLプロトコルを発見</p>
  </div>
  <div style="background:#16213e;padding:20px;border:1px solid #2e3460;border-top:none;border-radius:0 0 8px 8px;color:#e8eaf6;">
    <p style="color:#9fa8da;font-size:13px;">
      以下のプロトコルはまだトークンを発行していませんが、高いTVL (Total Value Locked) を誇ります。<br>
      過去の事例 (Uniswap, dYdX, Optimism 等) から、こうしたプロトコルはエアドロップを実施する傾向があります。
    </p>
    <table style="width:100%;border-collapse:collapse;background:#1e2240;border-radius:8px;overflow:hidden;margin-top:12px;">
      <thead>
        <tr style="background:#252b4a;">
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;">プロトコル</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;">TVL</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;">チェーン</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;">カテゴリ</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;">リンク</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    <hr style="margin:20px 0;border:none;border-top:1px solid #2e3460;">
    <p style="color:#6c757d;font-size:12px;">投資は自己責任で行ってください。情報は参考目的のみです。</p>
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
        logger.info(f"新候補アラート送信: {len(candidates)}件")
        return True
    except Exception as e:
        logger.error(f"新候補アラート送信失敗: {e}")
        return False
