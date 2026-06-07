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


def _difficulty_color(diff: str) -> str:
    return {"easy": "#2ed573", "medium": "#ff6348", "hard": "#ff4757"}.get(diff, "#999")


def _build_hot_section(hot_items: list[dict]) -> str:
    if not hot_items:
        return ""
    rows = ""
    for a in hot_items[:5]:
        val = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        color = _difficulty_color(a.get("difficulty", "easy"))
        tasks_html = "".join(f"<li style='margin:3px 0;'>{t}</li>" for t in a.get("tasks", [])[:3])
        rows += f"""
        <tr style="vertical-align:top;">
          <td style="padding:14px 12px;border-bottom:1px solid #2a2a4a;">
            <div style="font-weight:700;font-size:15px;color:#fff;">{a['name']}</div>
            <div style="color:#9fa8da;font-size:12px;margin-top:2px;">{a.get('category','')}</div>
          </td>
          <td style="padding:14px 12px;border-bottom:1px solid #2a2a4a;color:#2ed573;font-weight:700;font-size:16px;white-space:nowrap;">{val}</td>
          <td style="padding:14px 12px;border-bottom:1px solid #2a2a4a;">
            <span style="background:{color};color:#fff;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;">{a.get('difficulty','').upper()}</span>
          </td>
          <td style="padding:14px 12px;border-bottom:1px solid #2a2a4a;color:#9fa8da;font-size:13px;">{a.get('end_date','未定')}</td>
          <td style="padding:14px 12px;border-bottom:1px solid #2a2a4a;">
            <div style="font-size:12px;color:#bbb;margin-bottom:6px;">{a.get('description','')[:80]}...</div>
            <ul style="margin:0;padding-left:16px;font-size:12px;color:#9fa8da;">{tasks_html}</ul>
          </td>
          <td style="padding:14px 12px;border-bottom:1px solid #2a2a4a;">
            <a href="{a.get('url','#')}"
               style="display:inline-block;background:linear-gradient(135deg,#7c4dff,#651fff);color:#fff;
                      padding:8px 16px;border-radius:8px;text-decoration:none;font-size:13px;font-weight:700;white-space:nowrap;">
              参加する →
            </a>
          </td>
        </tr>"""
    return rows


def _build_new_section(new_items: list[str]) -> str:
    if not new_items:
        return ""
    items_html = "".join(f"<li style='margin:4px 0;font-size:14px;color:#e8eaf6;'>{n}</li>" for n in new_items)
    return f"""
    <div style="background:rgba(46,213,115,0.1);border:1px solid #2ed573;border-radius:10px;
                padding:16px 20px;margin:20px 0;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
        <span style="background:#2ed573;color:#000;font-size:11px;font-weight:700;
                     padding:3px 10px;border-radius:20px;">🆕 NEW</span>
        <strong style="color:#2ed573;font-size:15px;">新着エアドロップ {len(new_items)} 件</strong>
      </div>
      <ul style="margin:0;padding-left:18px;">{items_html}</ul>
    </div>"""


def _build_trending_section(trending: list[dict]) -> str:
    if not trending:
        return ""
    items = "".join(
        f"<div style='display:flex;justify-content:space-between;padding:8px 0;"
        f"border-bottom:1px solid #2a2a4a;'>"
        f"<span style='color:#e8eaf6;font-weight:600;'>{t['name']} "
        f"<span style='color:#9fa8da;font-size:12px;'>({t['symbol']})</span></span>"
        f"<span style='color:#a479e2;font-size:12px;'>スコア: {t.get('score', 0)}</span>"
        f"</div>"
        for t in trending[:7]
    )
    return f"""
    <div style="margin:24px 0;">
      <div style="color:#a479e2;font-size:16px;font-weight:700;margin-bottom:12px;">
        📈 CoinGecko トレンドコイン TOP7
      </div>
      <div style="background:#1a1a2e;border:1px solid #2e3460;border-radius:8px;padding:12px 16px;">
        {items}
      </div>
    </div>"""


def _build_html_body(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    summary: dict | None = None,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    hot_count = len(hot)
    total = len(airdrops)

    stats_html = f"""
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin:16px 0;">
      <div style="background:#1a1a2e;border:1px solid #2e3460;border-radius:8px;padding:12px 20px;text-align:center;">
        <div style="font-size:24px;font-weight:800;color:#1e90ff;">{total}</div>
        <div style="font-size:12px;color:#9fa8da;">総エアドロップ数</div>
      </div>
      <div style="background:#1a1a2e;border:1px solid #2e3460;border-radius:8px;padding:12px 20px;text-align:center;">
        <div style="font-size:24px;font-weight:800;color:#ff4757;">{hot_count}</div>
        <div style="font-size:12px;color:#9fa8da;">🔥 ホット案件</div>
      </div>
      <div style="background:#1a1a2e;border:1px solid #2e3460;border-radius:8px;padding:12px 20px;text-align:center;">
        <div style="font-size:24px;font-weight:800;color:#2ed573;">{len(new_items)}</div>
        <div style="font-size:12px;color:#9fa8da;">🆕 新着</div>
      </div>
    </div>"""

    changes_html = ""
    if summary and summary.get("changes"):
        change_rows = "".join(
            f"<li style='margin:4px 0;color:#ffa502;'>"
            f"<strong>{c['name']}</strong>: {'; '.join(c['changes'])}</li>"
            for c in summary["changes"][:5]
        )
        changes_html = f"""
        <div style="background:rgba(255,165,2,0.08);border:1px solid #ffa502;border-radius:8px;
                    padding:12px 16px;margin:16px 0;">
          <strong style="color:#ffa502;">✏️ 変更されたエアドロップ</strong>
          <ul style="margin:8px 0 0;padding-left:18px;">{change_rows}</ul>
        </div>"""

    hot_rows = _build_hot_section(hot)
    new_section = _build_new_section(new_items)
    trending_section = _build_trending_section(trending)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0f0f1a;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:720px;margin:0 auto;padding:20px;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:28px 24px;border-radius:12px 12px 0 0;
              border-bottom:2px solid #7c4dff;">
    <div style="font-size:24px;font-weight:800;color:#fff;">🪂 Crypto Airdrop Tracker</div>
    <div style="color:#9fa8da;font-size:14px;margin-top:4px;">
      {today} 更新レポート — 自動配信
    </div>
  </div>

  <!-- メインコンテンツ -->
  <div style="background:#16213e;padding:24px;border-radius:0 0 12px 12px;border:1px solid #2e3460;border-top:none;">

    {stats_html}
    {new_section}
    {changes_html}

    <!-- 注目エアドロップ -->
    <div style="margin:24px 0 12px;color:#ff4757;font-size:17px;font-weight:700;">
      🔥 今狙うべき注目エアドロップ TOP5
    </div>
    <div style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;background:#1a1a2e;border-radius:10px;overflow:hidden;">
        <thead>
          <tr style="background:#0d1117;color:#9fa8da;font-size:12px;text-transform:uppercase;letter-spacing:0.5px;">
            <th style="padding:12px;text-align:left;">プロジェクト</th>
            <th style="padding:12px;text-align:left;">推定価値</th>
            <th style="padding:12px;text-align:left;">難易度</th>
            <th style="padding:12px;text-align:left;">期限</th>
            <th style="padding:12px;text-align:left;">参加方法 (抜粋)</th>
            <th style="padding:12px;text-align:left;">リンク</th>
          </tr>
        </thead>
        <tbody>{hot_rows}</tbody>
      </table>
    </div>

    {trending_section}

    <!-- フッター -->
    <div style="margin-top:28px;padding-top:20px;border-top:1px solid #2e3460;
                color:#9fa8da;font-size:12px;line-height:1.8;">
      <p>🤖 このメールはCrypto Airdrop Trackerから毎日 08:00 JST に自動送信されています。</p>
      <p>⚠️ 掲載情報は参考目的のみです。暗号資産への投資は自己責任で行ってください。</p>
    </div>
  </div>

</div>
</body>
</html>"""


def _smtp_send(subject: str, html_body: str, plain_body: str = "") -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    if plain_body:
        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"メール送信成功 → {GMAIL_RECIPIENT}: {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗。アプリパスワードを確認してください。")
        return False
    except Exception as e:
        logger.error(f"メール送信失敗: {e}")
        return False


def send_daily_report(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    summary: dict | None = None,
) -> bool:
    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))

    subject = f"[Airdrop] {today} 更新 — 🔥ホット{hot_count}件"
    if new_items:
        subject += f" | 🆕新着{len(new_items)}件: {', '.join(new_items[:2])}"
        if len(new_items) > 2:
            subject += f" 他{len(new_items)-2}件"

    html_body = _build_html_body(airdrops, new_items, trending, summary)
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"トレンドコイン: {', '.join(t['name'] for t in trending[:5])}"
    )

    return _smtp_send(subject, html_body, plain_body)


def send_hot_alert(airdrop: dict) -> bool:
    """注目案件出現時の即時アラートメール"""
    name = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd", 0)
    subject = f"🚨 [HOT Airdrop出現] {name} — 推定 ~${value:,} の新案件！今すぐチェック"

    color = _difficulty_color(airdrop.get("difficulty", "easy"))
    tasks_html = "".join(
        f"<li style='margin:6px 0;font-size:14px;color:#e8eaf6;'>{t}</li>"
        for t in airdrop.get("tasks", [])
    )

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0f0f1a;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:20px;">

  <!-- 緊急ヘッダー -->
  <div style="background:linear-gradient(135deg,#dc3545,#7c4dff);padding:24px;border-radius:12px 12px 0 0;text-align:center;">
    <div style="font-size:36px;margin-bottom:8px;">🚨</div>
    <div style="font-size:22px;font-weight:800;color:#fff;">ホットエアドロップ出現！</div>
    <div style="color:rgba(255,255,255,0.85);font-size:14px;margin-top:4px;">見逃すと損かも</div>
  </div>

  <!-- メイン -->
  <div style="background:#16213e;padding:24px;border-radius:0 0 12px 12px;border:1px solid #2e3460;border-top:none;">

    <h2 style="margin:0 0 4px;color:#fff;font-size:22px;">
      {name}
      <span style="font-size:14px;color:#9fa8da;font-weight:400;">({airdrop.get('symbol','')})</span>
    </h2>
    <span style="background:rgba(124,77,255,0.2);color:#b39ddb;font-size:12px;
                 padding:3px 10px;border-radius:20px;">{airdrop.get('category','')}</span>

    <!-- 詳細 -->
    <div style="display:flex;gap:16px;margin:20px 0;flex-wrap:wrap;">
      <div style="background:#1a1a2e;border:1px solid #2e3460;border-radius:8px;padding:12px 20px;text-align:center;flex:1;">
        <div style="font-size:26px;font-weight:800;color:#2ed573;">~${value:,}</div>
        <div style="font-size:12px;color:#9fa8da;">推定価値 (USD)</div>
      </div>
      <div style="background:#1a1a2e;border:1px solid #2e3460;border-radius:8px;padding:12px 20px;text-align:center;flex:1;">
        <div style="font-size:18px;font-weight:800;color:{color};">{airdrop.get('difficulty','').upper()}</div>
        <div style="font-size:12px;color:#9fa8da;">難易度</div>
      </div>
      <div style="background:#1a1a2e;border:1px solid #2e3460;border-radius:8px;padding:12px 20px;text-align:center;flex:1;">
        <div style="font-size:14px;font-weight:700;color:#ffa502;">{airdrop.get('end_date','未定')}</div>
        <div style="font-size:12px;color:#9fa8da;">期限</div>
      </div>
    </div>

    <p style="color:#c5cae9;font-size:14px;line-height:1.7;">{airdrop.get('description','')}</p>

    <!-- 参加方法 -->
    <div style="background:#1a1a2e;border-radius:8px;padding:16px;margin:16px 0;">
      <div style="font-size:13px;font-weight:700;color:#9fa8da;margin-bottom:8px;">📋 参加方法</div>
      <ul style="margin:0;padding-left:20px;">{tasks_html}</ul>
    </div>

    <!-- CTA -->
    <div style="text-align:center;margin:24px 0;">
      <a href="{airdrop.get('url','#')}"
         style="display:inline-block;background:linear-gradient(135deg,#dc3545,#ff6b81);
                color:#fff;padding:14px 36px;border-radius:10px;text-decoration:none;
                font-size:16px;font-weight:800;letter-spacing:0.5px;">
        🚀 今すぐ参加する
      </a>
    </div>

    <p style="color:#9fa8da;font-size:12px;text-align:center;margin-top:20px;
              border-top:1px solid #2e3460;padding-top:16px;">
      ⚠️ 投資は自己責任で行ってください。情報は参考目的のみです。
    </p>
  </div>
</div>
</body>
</html>"""

    return _smtp_send(subject, html)
