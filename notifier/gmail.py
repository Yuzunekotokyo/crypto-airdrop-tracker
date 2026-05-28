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


def _difficulty_color(d: str) -> str:
    return {"easy": "#2ed573", "medium": "#ff6348", "hard": "#ff4757"}.get(d, "#9fa8da")


def _build_changes_html(diff: dict) -> str:
    if not diff:
        return ""
    parts = []

    if diff.get("added"):
        items = "".join(
            f"""<li style="margin:6px 0;padding:8px 12px;background:rgba(46,213,115,0.1);border-left:3px solid #2ed573;border-radius:4px;">
              <strong style="color:#2ed573;">{a['name']}</strong>
              {' <span style="background:#ff4757;color:white;font-size:10px;padding:2px 6px;border-radius:10px;margin-left:6px;">🔥 HOT</span>' if a.get('is_hot') else ''}
              {'<br><span style="color:#9fa8da;font-size:12px;">推定: ~$' + f"{a.get('estimated_value_usd',0):,}" + ' | ' + a.get('difficulty','').upper() + ' | ' + a.get('category','') + '</span>' if a.get('estimated_value_usd') else ''}
            </li>"""
            for a in diff["added"]
        )
        parts.append(f"""
        <div style="margin:16px 0;">
          <h4 style="color:#2ed573;margin-bottom:10px;">🆕 新規追加 ({len(diff['added'])}件)</h4>
          <ul style="list-style:none;padding:0;margin:0;">{items}</ul>
        </div>""")

    if diff.get("changed"):
        items = "".join(
            f"""<li style="margin:6px 0;padding:8px 12px;background:rgba(255,165,2,0.1);border-left:3px solid #ffa502;border-radius:4px;">
              <strong style="color:#ffa502;">{c['name']}</strong>
              <br><span style="color:#9fa8da;font-size:12px;">{' / '.join(c['changes'])}</span>
            </li>"""
            for c in diff["changed"]
        )
        parts.append(f"""
        <div style="margin:16px 0;">
          <h4 style="color:#ffa502;margin-bottom:10px;">✏️ ステータス変更 ({len(diff['changed'])}件)</h4>
          <ul style="list-style:none;padding:0;margin:0;">{items}</ul>
        </div>""")

    if diff.get("removed"):
        names = ", ".join(diff["removed"])
        parts.append(f"""
        <div style="margin:16px 0;padding:10px 14px;background:rgba(150,150,150,0.1);border-left:3px solid #888;border-radius:4px;">
          <span style="color:#888;">✕ 終了・削除: {names}</span>
        </div>""")

    return "".join(parts)


def _build_hot_table(airdrops: list[dict]) -> str:
    hot = [a for a in airdrops if a.get("is_hot")][:5]
    if not hot:
        return "<p style='color:#9fa8da;'>現在ホット案件はありません。</p>"

    rows = ""
    for a in hot:
        dc = _difficulty_color(a.get("difficulty", ""))
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        rows += f"""
        <tr>
          <td style="padding:12px 10px;border-bottom:1px solid #2e3460;">
            {'<img src="' + a["logo"] + '" width="24" height="24" style="border-radius:50%;vertical-align:middle;margin-right:8px;" onerror="this.style.display=\'none\'">' if a.get("logo") else ""}
            <strong style="color:#e8eaf6;">{a['name']}</strong>
            {'<span style="background:#ff4757;color:white;font-size:10px;padding:1px 5px;border-radius:8px;margin-left:6px;">HOT</span>' if a.get('is_hot') else ''}
            <br><span style="color:#9fa8da;font-size:11px;">{a.get('category','')}</span>
          </td>
          <td style="padding:12px 10px;border-bottom:1px solid #2e3460;color:#2ed573;font-weight:700;font-size:16px;">{value}</td>
          <td style="padding:12px 10px;border-bottom:1px solid #2e3460;">
            <span style="background:{dc};color:white;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:700;">{a.get('difficulty','').upper()}</span>
          </td>
          <td style="padding:12px 10px;border-bottom:1px solid #2e3460;color:#9fa8da;font-size:13px;">{a.get('end_date','未定')}</td>
          <td style="padding:12px 10px;border-bottom:1px solid #2e3460;">
            <a href="{a.get('url','#')}" style="background:#7c4dff;color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:700;">参加する →</a>
          </td>
        </tr>"""
    return f"""
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr style="background:#1a1a2e;">
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;border-bottom:1px solid #2e3460;">プロジェクト</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;border-bottom:1px solid #2e3460;">推定価値</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;border-bottom:1px solid #2e3460;">難易度</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;border-bottom:1px solid #2e3460;">期限</th>
          <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;border-bottom:1px solid #2e3460;">リンク</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>"""


def _build_html_body(airdrops: list[dict], new_items: list[str], trending: list[dict], diff: dict = None) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    now_time = datetime.now().strftime("%H:%M")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    total = len(airdrops)
    diff = diff or {}

    changes_html = _build_changes_html(diff)
    no_change_msg = "" if changes_html else """
    <div style="padding:14px 16px;background:rgba(124,77,255,0.08);border:1px solid #2e3460;border-radius:8px;color:#9fa8da;font-size:14px;">
      📊 本日は新規追加・変更はありませんでした。引き続きホット案件を監視中です。
    </div>"""

    trending_html = ""
    if trending:
        t_items = "".join(
            f"""<li style="display:inline-block;margin:4px;padding:5px 12px;background:rgba(124,77,255,0.15);border:1px solid #7c4dff;border-radius:20px;color:#e8eaf6;font-size:13px;">
              <strong>{t['name']}</strong> <span style="color:#9fa8da;">({t['symbol']})</span>
            </li>"""
            for t in trending[:7]
        )
        trending_html = f"""
        <div style="margin-top:24px;">
          <h3 style="color:#7c4dff;font-size:16px;margin-bottom:12px;">📈 CoinGecko トレンドコイン</h3>
          <ul style="list-style:none;padding:0;margin:0;">{t_items}</ul>
        </div>"""

    hot_table = _build_hot_table(airdrops)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:'Hiragino Sans','Meiryo','Segoe UI',Arial,sans-serif;background:#0f0f1a;margin:0;padding:20px;">
<div style="max-width:700px;margin:0 auto;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:28px 24px;border-radius:12px 12px 0 0;border-bottom:3px solid #7c4dff;">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
      <span style="font-size:28px;">🪂</span>
      <h1 style="margin:0;font-size:22px;font-weight:800;background:linear-gradient(135deg,#fff,#7c4dff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Crypto Airdrop Tracker</h1>
    </div>
    <p style="margin:0;color:#9fa8da;font-size:14px;">{today}  {now_time} JST — 毎日自動更新レポート</p>
  </div>

  <!-- メインボディ -->
  <div style="background:#16213e;padding:24px;border-radius:0 0 12px 12px;border:1px solid #2e3460;border-top:none;">

    <!-- サマリー統計 -->
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:24px;">
      <div style="flex:1;min-width:120px;background:#1e2240;border:1px solid #2e3460;border-radius:10px;padding:14px;text-align:center;">
        <div style="font-size:24px;font-weight:800;color:#1e90ff;">{total}</div>
        <div style="font-size:12px;color:#9fa8da;margin-top:4px;">総エアドロップ</div>
      </div>
      <div style="flex:1;min-width:120px;background:#1e2240;border:1px solid #ff4757;border-radius:10px;padding:14px;text-align:center;">
        <div style="font-size:24px;font-weight:800;color:#ff4757;">{hot_count}</div>
        <div style="font-size:12px;color:#9fa8da;margin-top:4px;">🔥 ホット案件</div>
      </div>
      <div style="flex:1;min-width:120px;background:#1e2240;border:1px solid #2ed573;border-radius:10px;padding:14px;text-align:center;">
        <div style="font-size:24px;font-weight:800;color:#2ed573;">{len(diff.get('added', []))}</div>
        <div style="font-size:12px;color:#9fa8da;margin-top:4px;">🆕 新着</div>
      </div>
      <div style="flex:1;min-width:120px;background:#1e2240;border:1px solid #ffa502;border-radius:10px;padding:14px;text-align:center;">
        <div style="font-size:24px;font-weight:800;color:#ffa502;">{len(diff.get('changed', []))}</div>
        <div style="font-size:12px;color:#9fa8da;margin-top:4px;">✏️ 変更</div>
      </div>
    </div>

    <!-- 本日の変更点 -->
    <h3 style="color:#e8eaf6;font-size:16px;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #2e3460;">📋 本日の変更点</h3>
    {changes_html or no_change_msg}

    <!-- HOT案件一覧 -->
    <h3 style="color:#ff4757;font-size:16px;margin:24px 0 12px;padding-bottom:8px;border-bottom:1px solid #2e3460;">🔥 今狙うべき注目エアドロップ</h3>
    <div style="background:#1e2240;border-radius:10px;overflow:hidden;border:1px solid #2e3460;">
      {hot_table}
    </div>

    {trending_html}

    <!-- フッター -->
    <hr style="margin:28px 0;border:none;border-top:1px solid #2e3460;">
    <p style="color:#9fa8da;font-size:12px;margin:0;line-height:1.8;">
      ⚠️ このメールはCrypto Airdrop Trackerから毎日自動送信されています。<br>
      投資は必ず自己責任で行ってください。掲載情報は参考目的のみです。<br>
      ホット案件出現時は別途アラートメールを送信します。
    </p>
  </div>
</div>
</body>
</html>"""


def send_daily_report(airdrops: list[dict], new_items: list[str], trending: list[dict], diff: dict = None) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    diff = diff or {}
    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    added = len(diff.get("added", []))

    subject = f"🪂 [{today}] Airdrop日次レポート — ホット{hot_count}件"
    if added:
        subject += f" / 🆕新着{added}件"
    newly_hot = [a for a in diff.get("added", []) if a.get("is_hot")]
    if newly_hot:
        subject = f"🚨 [{today}] HOT新案件{len(newly_hot)}件登場！ — " + subject

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, diff)
    added_names = [a["name"] for a in diff.get("added", [])]
    changed_names = [c["name"] for c in diff.get("changed", [])]
    plain_body = (
        f"{today} Airdrop日次レポート\n"
        f"総件数: {len(airdrops)}件 | ホット: {hot_count}件\n"
        f"新着: {', '.join(added_names) if added_names else 'なし'}\n"
        f"変更: {', '.join(changed_names) if changed_names else 'なし'}\n"
        f"トレンド: {', '.join(t['name'] for t in trending[:5])}"
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
    dc = _difficulty_color(airdrop.get("difficulty", ""))
    subject = f"🚨 [HOT Airdrop速報] {name} — 推定${value:,} の新案件登場！"

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"></head>
<body style="font-family:'Hiragino Sans','Meiryo','Segoe UI',Arial,sans-serif;background:#0f0f1a;margin:0;padding:20px;">
<div style="max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#7f0000,#dc3545);color:white;padding:24px;border-radius:12px 12px 0 0;text-align:center;">
    <div style="font-size:40px;margin-bottom:8px;">🚨</div>
    <h2 style="margin:0;font-size:22px;font-weight:800;">HOTエアドロップ速報</h2>
    <p style="margin:6px 0 0;opacity:0.9;font-size:14px;">見逃し厳禁の新案件が登場しました！</p>
  </div>
  <div style="background:#16213e;border:1px solid #dc3545;border-top:none;padding:28px;border-radius:0 0 12px 12px;">
    <div style="text-align:center;margin-bottom:24px;">
      {'<img src="' + airdrop.get("logo","") + '" width="64" height="64" style="border-radius:50%;border:3px solid #dc3545;" onerror="this.style.display=\'none\'">' if airdrop.get("logo") else ""}
      <h3 style="color:#e8eaf6;font-size:26px;font-weight:800;margin:12px 0 4px;">{name}</h3>
      <span style="color:#9fa8da;">{airdrop.get('symbol','')}</span>
    </div>

    <div style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;">
      <div style="flex:1;background:#1e2240;border:2px solid #2ed573;border-radius:10px;padding:16px;text-align:center;min-width:120px;">
        <div style="font-size:22px;font-weight:800;color:#2ed573;">~${value:,}</div>
        <div style="font-size:12px;color:#9fa8da;margin-top:4px;">推定価値</div>
      </div>
      <div style="flex:1;background:#1e2240;border:2px solid {dc};border-radius:10px;padding:16px;text-align:center;min-width:120px;">
        <div style="font-size:18px;font-weight:800;color:{dc};">{airdrop.get('difficulty','').upper()}</div>
        <div style="font-size:12px;color:#9fa8da;margin-top:4px;">難易度</div>
      </div>
      <div style="flex:1;background:#1e2240;border:2px solid #ffa502;border-radius:10px;padding:16px;text-align:center;min-width:120px;">
        <div style="font-size:16px;font-weight:800;color:#ffa502;">{airdrop.get('end_date','未定')}</div>
        <div style="font-size:12px;color:#9fa8da;margin-top:4px;">期限</div>
      </div>
    </div>

    <div style="background:#1e2240;border-radius:10px;padding:16px;margin-bottom:20px;">
      <p style="color:#9fa8da;font-size:14px;line-height:1.7;margin:0;">{airdrop.get('description','')}</p>
    </div>

    <div style="background:#1e2240;border-radius:10px;padding:16px;margin-bottom:24px;">
      <h4 style="color:#e8eaf6;margin:0 0 10px;font-size:14px;">📋 参加方法</h4>
      <ul style="padding-left:20px;margin:0;color:#9fa8da;font-size:14px;line-height:1.8;">
        {"".join(f"<li>{t}</li>" for t in airdrop.get("tasks", []))}
      </ul>
    </div>

    <div style="text-align:center;">
      <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#7c4dff);color:white;padding:16px 40px;border-radius:10px;text-decoration:none;font-size:18px;font-weight:800;letter-spacing:0.5px;">今すぐ参加する →</a>
    </div>

    <hr style="margin:24px 0;border:none;border-top:1px solid #2e3460;">
    <p style="color:#9fa8da;font-size:12px;margin:0;text-align:center;">投資は必ず自己責任で行ってください。情報は参考目的のみです。</p>
  </div>
</div>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"HOTアラート送信成功: {name}")
        return True
    except Exception as e:
        logger.error(f"HOTアラート送信失敗: {e}")
        return False
