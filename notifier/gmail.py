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


def _difficulty_label(d: str) -> str:
    return {"easy": "かんたん", "medium": "普通", "hard": "難しい"}.get(d, d)


def _difficulty_color(d: str) -> str:
    return {"easy": "#2ed573", "medium": "#ffa502", "hard": "#ff4757"}.get(d, "#6c757d")


def _build_html_body(
    airdrops: list[dict],
    diff: dict,
    trending: list[dict],
    summary: dict,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    added = diff.get("added", [])
    changed = diff.get("changed", [])

    # 新着セクション
    new_html = ""
    if added:
        rows = ""
        for a in added[:10]:
            value = f"~${a.get('estimated_value_usd',0):,}" if a.get("estimated_value_usd") else "未定"
            hot_tag = ' <span style="background:#ff4757;color:white;padding:1px 6px;border-radius:10px;font-size:11px;">🔥HOT</span>' if a.get("is_hot") else ""
            rows += f"""
            <tr>
              <td style="padding:10px;border-bottom:1px solid #dee2e6;">
                <strong>{a['name']}</strong>{hot_tag}<br>
                <span style="color:#6c757d;font-size:12px;">{a.get('category','')} / {a.get('type','')}</span>
              </td>
              <td style="padding:10px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:bold;">{value}</td>
              <td style="padding:10px;border-bottom:1px solid #dee2e6;">
                <span style="background:{_difficulty_color(a.get('difficulty',''))};color:white;padding:2px 8px;border-radius:12px;font-size:12px;">
                  {_difficulty_label(a.get('difficulty',''))}
                </span>
              </td>
              <td style="padding:10px;border-bottom:1px solid #dee2e6;">
                <a href="{a.get('url','#')}" style="color:#0d6efd;">参加する →</a>
              </td>
            </tr>"""
        new_html = f"""
        <div style="margin:20px 0;">
          <h3 style="color:#28a745;margin-bottom:12px;">🆕 新着エアドロップ ({len(added)}件)</h3>
          <table style="width:100%;border-collapse:collapse;background:#f8fff9;border-radius:8px;overflow:hidden;border:1px solid #28a745;">
            <thead>
              <tr style="background:#28a745;color:white;">
                <th style="padding:10px;text-align:left;">プロジェクト</th>
                <th style="padding:10px;text-align:left;">推定価値</th>
                <th style="padding:10px;text-align:left;">難易度</th>
                <th style="padding:10px;text-align:left;">リンク</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>"""

    # 変更セクション
    changed_html = ""
    if changed:
        items_html = ""
        for c in changed[:5]:
            changes_str = "、".join(c.get("changes", []))
            items_html += f"<li><strong>{c['name']}</strong>: {changes_str}</li>"
        changed_html = f"""
        <div style="background:#fff8e1;border-left:4px solid #ffc107;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>✏️ 変更あり ({len(changed)}件)</strong>
          <ul style="margin:8px 0 0 0;">{items_html}</ul>
        </div>"""

    # ホット案件テーブル
    hot_rows = ""
    for a in hot[:8]:
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "不明"
        tasks_html = ""
        if a.get("tasks"):
            tasks_items = "".join(f"<li style='font-size:12px;color:#555;'>{t}</li>" for t in a["tasks"][:3])
            tasks_html = f"<ul style='margin:4px 0 0 16px;padding:0;'>{tasks_items}</ul>"
        hot_rows += f"""
        <tr>
          <td style="padding:12px 10px;border-bottom:1px solid #dee2e6;vertical-align:top;">
            <strong>{a['name']}</strong><br>
            <span style="color:#6c757d;font-size:12px;">{a.get('category','')}</span>
            {tasks_html}
          </td>
          <td style="padding:12px 10px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:bold;white-space:nowrap;">{value}</td>
          <td style="padding:12px 10px;border-bottom:1px solid #dee2e6;white-space:nowrap;">
            <span style="background:{_difficulty_color(a.get('difficulty',''))};color:white;padding:2px 8px;border-radius:12px;font-size:12px;">
              {_difficulty_label(a.get('difficulty',''))}
            </span>
          </td>
          <td style="padding:12px 10px;border-bottom:1px solid #dee2e6;white-space:nowrap;">{a.get('end_date','未定')}</td>
          <td style="padding:12px 10px;border-bottom:1px solid #dee2e6;">
            <a href="{a.get('url','#')}" style="color:#0d6efd;font-weight:bold;">参加する →</a>
          </td>
        </tr>"""

    # トレンドセクション
    trending_html = ""
    if trending:
        t_items = "".join(
            f"""<li style="margin:4px 0;">
              <strong>{t['name']}</strong> <span style="color:#6c757d;">({t['symbol']})</span>
              {f" — ランク #{t['rank']}" if t.get('rank') else ""}
            </li>"""
            for t in trending[:7]
        )
        trending_html = f"""
        <div style="margin:20px 0;">
          <h3 style="color:#6f42c1;">📈 CoinGecko トレンドコイン (本日)</h3>
          <ul style="margin:8px 0;padding-left:20px;">{t_items}</ul>
        </div>"""

    total = summary.get("total_airdrops", len(airdrops))
    hot_count = summary.get("hot_count", len(hot))

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Helvetica Neue',Arial,'Hiragino Kaku Gothic ProN',sans-serif;max-width:750px;margin:0 auto;background:#f0f2f5;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);color:white;padding:28px 24px;border-radius:12px 12px 0 0;">
    <h1 style="margin:0;font-size:24px;letter-spacing:1px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:6px 0 0;opacity:0.85;font-size:15px;">{today} — 日次更新レポート</p>
    <div style="margin-top:16px;display:flex;gap:12px;flex-wrap:wrap;">
      <span style="background:rgba(255,255,255,0.15);padding:4px 14px;border-radius:20px;font-size:13px;">
        📋 総数 <strong>{total}件</strong>
      </span>
      <span style="background:rgba(255,71,87,0.4);padding:4px 14px;border-radius:20px;font-size:13px;">
        🔥 ホット <strong>{hot_count}件</strong>
      </span>
      {"" if not added else f'<span style="background:rgba(46,213,115,0.4);padding:4px 14px;border-radius:20px;font-size:13px;">🆕 新着 <strong>{len(added)}件</strong></span>'}
      {"" if not changed else f'<span style="background:rgba(255,165,2,0.4);padding:4px 14px;border-radius:20px;font-size:13px;">✏️ 変更 <strong>{len(changed)}件</strong></span>'}
    </div>
  </div>

  <!-- 本文 -->
  <div style="background:white;padding:24px;border-radius:0 0 12px 12px;box-shadow:0 4px 16px rgba(0,0,0,0.1);">

    {new_html}
    {changed_html}

    <!-- ホット案件 -->
    <div style="margin:20px 0;">
      <h3 style="color:#dc3545;margin-bottom:12px;">🔥 今すぐ狙うべきホットエアドロップ</h3>
      <table style="width:100%;border-collapse:collapse;border:1px solid #dee2e6;border-radius:8px;overflow:hidden;">
        <thead>
          <tr style="background:#1a1a2e;color:white;">
            <th style="padding:12px 10px;text-align:left;">プロジェクト / 参加方法</th>
            <th style="padding:12px 10px;text-align:left;">推定価値</th>
            <th style="padding:12px 10px;text-align:left;">難易度</th>
            <th style="padding:12px 10px;text-align:left;">期限</th>
            <th style="padding:12px 10px;text-align:left;">リンク</th>
          </tr>
        </thead>
        <tbody>{hot_rows}</tbody>
      </table>
    </div>

    {trending_html}

    <!-- フッター -->
    <hr style="margin:24px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:12px;margin:0;line-height:1.8;">
      ※ このメールはCrypto Airdrop Trackerから自動送信されています。<br>
      ※ 掲載情報は参考目的のみです。投資・参加は必ず自己責任で行ってください。<br>
      ※ 推定価値はあくまで予測であり、実際の金額を保証するものではありません。
    </p>
  </div>
</body>
</html>"""


def send_daily_report(
    airdrops: list[dict],
    diff: dict,
    trending: list[dict],
    summary: dict,
) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    added = diff.get("added", [])
    changed = diff.get("changed", [])

    subject = f"[Airdrop] {today} — 🔥ホット{hot_count}件"
    if added:
        subject += f" 🆕新着{len(added)}件"
    if changed:
        subject += f" ✏️変更{len(changed)}件"

    # 特にホット新着があれば件名を目立たせる
    newly_hot = [a for a in added if a.get("is_hot")]
    if newly_hot:
        names = "、".join(a["name"] for a in newly_hot[:2])
        subject = f"🚨 [HOT新着] {names} — {today} Airdropレポート"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, diff, trending, summary)

    added_names = ", ".join(a["name"] for a in added) if added else "なし"
    changed_names = ", ".join(c["name"] for c in changed) if changed else "なし"
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {added_names}\n"
        f"変更: {changed_names}\n"
        f"トレンド: {', '.join(t['name'] for t in trending[:5]) if trending else 'なし'}"
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
    difficulty = airdrop.get("difficulty", "")
    tasks_html = ""
    if airdrop.get("tasks"):
        items = "".join(f"<li>{t}</li>" for t in airdrop["tasks"])
        tasks_html = f"<ul>{items}</ul>"

    subject = f"🚨 [HOT Airdrop出現] {name} — 推定${value:,} / {_difficulty_label(difficulty)}"

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#dc3545,#ff6b81);color:white;padding:24px;border-radius:12px 12px 0 0;">
    <h2 style="margin:0;font-size:22px;">🚨 ホットエアドロップ出現！</h2>
    <p style="margin:6px 0 0;opacity:0.9;">見逃し注意 — 今すぐ確認してください</p>
  </div>
  <div style="background:white;padding:24px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 12px 12px;box-shadow:0 4px 16px rgba(0,0,0,0.1);">
    <h3 style="color:#1a1a2e;font-size:20px;">{name}
      {"<span style='font-size:14px;color:#6c757d;'> ({symbol})</span>".format(symbol=airdrop.get('symbol','')) if airdrop.get('symbol') else ""}
    </h3>
    <div style="display:flex;gap:16px;flex-wrap:wrap;margin:16px 0;padding:16px;background:#f8f9fa;border-radius:8px;">
      <div>
        <div style="font-size:11px;color:#6c757d;text-transform:uppercase;">推定価値</div>
        <div style="font-size:24px;font-weight:800;color:#28a745;">~${value:,}</div>
      </div>
      <div>
        <div style="font-size:11px;color:#6c757d;text-transform:uppercase;">難易度</div>
        <div style="font-size:16px;font-weight:700;color:{_difficulty_color(difficulty)};">{_difficulty_label(difficulty).upper()}</div>
      </div>
      <div>
        <div style="font-size:11px;color:#6c757d;text-transform:uppercase;">カテゴリ</div>
        <div style="font-size:16px;font-weight:700;">{airdrop.get('category','')}</div>
      </div>
      <div>
        <div style="font-size:11px;color:#6c757d;text-transform:uppercase;">期限</div>
        <div style="font-size:16px;font-weight:700;">{airdrop.get('end_date','未定')}</div>
      </div>
    </div>
    <p style="color:#333;line-height:1.6;">{airdrop.get('description','')}</p>
    {"<h4 style='color:#1a1a2e;margin-bottom:8px;'>📋 参加方法</h4>" + tasks_html if airdrop.get("tasks") else ""}
    <div style="margin-top:20px;">
      <a href="{airdrop.get('url','#')}"
         style="display:inline-block;background:linear-gradient(135deg,#dc3545,#ff4757);color:white;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:16px;">
        今すぐ参加する →
      </a>
    </div>
    <hr style="margin:20px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#6c757d;font-size:12px;">投資は自己責任で行ってください。このメールは参考目的のみです。</p>
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
