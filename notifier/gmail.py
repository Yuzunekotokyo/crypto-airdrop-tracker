"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してメール送信。
毎日デイリーレポート + 緊急ホットアラートの2種類。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)

# 難易度カラーマッピング
_DIFF_COLOR = {"easy": "#2ed573", "medium": "#ff6348", "hard": "#ff4757"}
_DIFF_LABEL = {"easy": "EASY ✓", "medium": "MEDIUM", "hard": "HARD ★"}


def _diff_section_html(diff: dict) -> str:
    """変更内容セクションHTML"""
    if not diff:
        return ""

    sections = []

    if diff.get("added"):
        items_html = ""
        for a in diff["added"]:
            hot_mark = " 🔥" if a.get("is_hot") else ""
            val = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
            items_html += f"""
            <li style="margin:6px 0;">
              <strong>{a['name']}{hot_mark}</strong>
              <span style="color:#2ed573;margin-left:8px;">{val}</span>
              <span style="color:#9fa8da;font-size:12px;margin-left:8px;">{a.get('category','')}</span>
            </li>"""
        sections.append(f"""
        <div style="background:#0d2a1a;border-left:4px solid #2ed573;padding:14px 18px;margin:16px 0;border-radius:6px;">
          <strong style="color:#2ed573;">🆕 新規追加 ({len(diff['added'])}件)</strong>
          <ul style="margin:10px 0 0 0;padding-left:18px;">{items_html}</ul>
        </div>""")

    if diff.get("removed"):
        items_html = "".join(f"<li style='margin:4px 0;color:#9fa8da;'>{n}</li>" for n in diff["removed"])
        sections.append(f"""
        <div style="background:#2a0d0d;border-left:4px solid #ff4757;padding:14px 18px;margin:16px 0;border-radius:6px;">
          <strong style="color:#ff4757;">🗑 終了・削除 ({len(diff['removed'])}件)</strong>
          <ul style="margin:10px 0 0 0;padding-left:18px;">{items_html}</ul>
        </div>""")

    if diff.get("changed"):
        items_html = ""
        for c in diff["changed"]:
            changes_str = " / ".join(c.get("changes", []))
            items_html += f"<li style='margin:6px 0;'><strong>{c['name']}</strong>: <span style='color:#ffa502;'>{changes_str}</span></li>"
        sections.append(f"""
        <div style="background:#2a2200;border-left:4px solid #ffa502;padding:14px 18px;margin:16px 0;border-radius:6px;">
          <strong style="color:#ffa502;">✏️ 情報更新 ({len(diff['changed'])}件)</strong>
          <ul style="margin:10px 0 0 0;padding-left:18px;">{items_html}</ul>
        </div>""")

    return "".join(sections)


def _build_html_body(airdrops: list[dict], new_items: list[str], trending: list[dict], diff: dict = None) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]

    diff_html = _diff_section_html(diff or {})

    no_change_msg = ""
    if diff and not diff.get("added") and not diff.get("removed") and not diff.get("changed"):
        no_change_msg = """
        <div style="background:#1a1a2e;border:1px solid #2e3460;padding:12px 18px;margin:16px 0;border-radius:6px;color:#9fa8da;font-size:13px;">
          ℹ️ 本日の変更はありません。以下の継続中の注目案件をご確認ください。
        </div>"""

    hot_rows = ""
    for a in hot[:6]:
        diff_color = _DIFF_COLOR.get(a.get("difficulty", "easy"), "#9fa8da")
        diff_label = _DIFF_LABEL.get(a.get("difficulty", "easy"), a.get("difficulty", "").upper())
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        status_color = "#2ed573" if a.get("status") == "active" else "#ffa502"
        status_label = "アクティブ" if a.get("status") == "active" else "近日開始"
        hot_rows += f"""
        <tr style="border-bottom:1px solid #2e3460;">
          <td style="padding:12px 10px;">
            <div style="font-weight:700;color:#e8eaf6;">{a['name']}</div>
            <div style="font-size:11px;color:#7c4dff;margin-top:2px;">{a.get('category','')}</div>
          </td>
          <td style="padding:12px 10px;color:#2ed573;font-weight:800;font-size:16px;">{value}</td>
          <td style="padding:12px 10px;">
            <span style="background:rgba(0,0,0,0.3);color:{diff_color};border:1px solid {diff_color};padding:3px 8px;border-radius:12px;font-size:11px;font-weight:700;">
              {diff_label}
            </span>
          </td>
          <td style="padding:12px 10px;">
            <span style="color:{status_color};font-size:12px;font-weight:600;">{status_label}</span>
          </td>
          <td style="padding:12px 10px;font-size:12px;color:#9fa8da;">{a.get('end_date','未定')}</td>
          <td style="padding:12px 10px;">
            <a href="{a.get('url','#')}" style="background:linear-gradient(135deg,#7c4dff,#651fff);color:white;padding:6px 14px;border-radius:6px;font-size:12px;font-weight:700;text-decoration:none;">参加 →</a>
          </td>
        </tr>"""

    trending_html = ""
    if trending:
        t_items = "".join(
            f"""<li style="margin:6px 0;">
              <strong style="color:#e8eaf6;">{t['name']}</strong>
              <span style="color:#9fa8da;margin-left:6px;">({t['symbol']})</span>
              <span style="color:#7c4dff;margin-left:8px;font-size:12px;">スコア: {t.get('score', 0)}</span>
            </li>"""
            for t in trending[:5]
        )
        trending_html = f"""
        <div style="margin-top:28px;padding-top:20px;border-top:1px solid #2e3460;">
          <h3 style="color:#7c4dff;margin:0 0 12px;">📈 CoinGecko トレンドコイン</h3>
          <ul style="padding-left:18px;margin:0;">{t_items}</ul>
        </div>"""

    hot_count = len(hot)
    added_count = len(diff.get("added", [])) if diff else 0

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#0f0f1a;color:#e8eaf6;margin:0;padding:20px;">
  <div style="max-width:720px;margin:0 auto;">

    <!-- ヘッダー -->
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:24px 28px;border-radius:12px 12px 0 0;border-bottom:3px solid #7c4dff;">
      <h1 style="margin:0;font-size:22px;color:white;">🪂 Crypto Airdrop Tracker</h1>
      <p style="margin:6px 0 0;color:#9fa8da;font-size:14px;">{today} — 毎日自動更新レポート</p>
    </div>

    <!-- サマリーバー -->
    <div style="background:#16213e;padding:16px 28px;display:flex;gap:16px;flex-wrap:wrap;border-bottom:1px solid #2e3460;">
      <span style="background:rgba(30,144,255,0.15);border:1px solid #1e90ff;color:#1e90ff;padding:4px 14px;border-radius:20px;font-size:13px;font-weight:700;">
        📋 総数: {len(airdrops)}件
      </span>
      <span style="background:rgba(255,71,87,0.15);border:1px solid #ff4757;color:#ff6b81;padding:4px 14px;border-radius:20px;font-size:13px;font-weight:700;">
        🔥 ホット: {hot_count}件
      </span>
      {"<span style='background:rgba(46,213,115,0.15);border:1px solid #2ed573;color:#2ed573;padding:4px 14px;border-radius:20px;font-size:13px;font-weight:700;'>🆕 新着: " + str(added_count) + "件</span>" if added_count > 0 else ""}
    </div>

    <!-- メインコンテンツ -->
    <div style="background:#1e2240;padding:24px 28px;border-radius:0 0 12px 12px;">

      {diff_html}
      {no_change_msg}

      <!-- ホット案件テーブル -->
      <h3 style="color:#ff4757;margin:20px 0 14px;">🔥 注目のホットエアドロップ TOP6</h3>
      <div style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;background:#16213e;border-radius:8px;overflow:hidden;">
          <thead>
            <tr style="background:#0f0f1a;">
              <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">プロジェクト</th>
              <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;font-weight:700;text-transform:uppercase;">推定価値</th>
              <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;font-weight:700;text-transform:uppercase;">難易度</th>
              <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;font-weight:700;text-transform:uppercase;">状態</th>
              <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;font-weight:700;text-transform:uppercase;">期限</th>
              <th style="padding:10px;text-align:left;color:#9fa8da;font-size:12px;font-weight:700;text-transform:uppercase;">リンク</th>
            </tr>
          </thead>
          <tbody>{hot_rows}</tbody>
        </table>
      </div>

      {trending_html}

      <!-- フッター注意書き -->
      <div style="margin-top:28px;padding-top:20px;border-top:1px solid #2e3460;color:#6c757d;font-size:11px;line-height:1.7;">
        ※ このメールはCrypto Airdrop Trackerから毎日自動送信されています。<br>
        ※ 掲載情報は参考目的のみです。投資は自己責任で行ってください。<br>
        ※ 新しいホット案件が出現した際は別途即時アラートを送信します。
      </div>
    </div>

  </div>
</body>
</html>"""


def send_daily_report(airdrops: list[dict], new_items: list[str], trending: list[dict], diff: dict = None) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    added_count = len(diff.get("added", [])) if diff else len(new_items)

    # 件名: 変更内容を明示
    subject = f"[Airdrop Daily] {today} — ホット{hot_count}件"
    if added_count > 0:
        added_names = [a["name"] if isinstance(a, dict) else a for a in (diff.get("added", []) if diff else [])]
        hot_new = [a for a in (diff.get("added", []) if diff else []) if isinstance(a, dict) and a.get("is_hot")]
        if hot_new:
            subject += f" 🚨新着HOT{len(hot_new)}件: {hot_new[0]['name']}"
        else:
            subject += f" 🆕新着{added_count}件"
    else:
        subject += " (変更なし・定期レポート)"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, diff)

    changed_summary = ""
    if diff:
        if diff.get("added"):
            changed_summary += f"新着: {', '.join(a['name'] for a in diff['added'])}\n"
        if diff.get("removed"):
            changed_summary += f"削除: {', '.join(diff['removed'])}\n"
        if diff.get("changed"):
            changed_summary += f"更新: {', '.join(c['name'] for c in diff['changed'])}\n"
    no_change_line = "変更なし\n"
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"総件数: {len(airdrops)}件\n"
        f"{changed_summary if changed_summary else no_change_line}"
        f"送信先: {GMAIL_RECIPIENT}"
    )

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"デイリーレポート送信成功: {GMAIL_RECIPIENT} ({subject})")
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
    diff_color = _DIFF_COLOR.get(airdrop.get("difficulty", "easy"), "#9fa8da")
    diff_label = _DIFF_LABEL.get(airdrop.get("difficulty", "easy"), airdrop.get("difficulty", "").upper())
    tasks_html = "".join(f"<li style='margin:5px 0;'>{t}</li>" for t in airdrop.get("tasks", []))

    subject = f"🚨 [HOT Airdrop速報] {name} — 推定${value:,} の新案件が登場！"

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#0f0f1a;color:#e8eaf6;margin:0;padding:20px;">
  <div style="max-width:600px;margin:0 auto;">
    <div style="background:linear-gradient(135deg,#dc3545,#ff4757);padding:20px 24px;border-radius:12px 12px 0 0;">
      <h2 style="margin:0;color:white;font-size:20px;">🚨 緊急！ホットエアドロップ出現！</h2>
      <p style="margin:6px 0 0;color:rgba(255,255,255,0.85);font-size:13px;">Crypto Airdrop Tracker 即時アラート</p>
    </div>
    <div style="background:#1e2240;padding:24px;border-radius:0 0 12px 12px;border:1px solid #2e3460;border-top:none;">
      <h3 style="margin:0 0 16px;font-size:22px;color:white;">{name}
        {"<span style='color:#9fa8da;font-size:14px;margin-left:8px;'>({airdrop.get('symbol','')})</span>" if airdrop.get('symbol') else ""}
      </h3>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
        <div style="background:#16213e;padding:14px;border-radius:8px;">
          <div style="font-size:11px;color:#9fa8da;text-transform:uppercase;letter-spacing:0.5px;">推定価値</div>
          <div style="font-size:26px;font-weight:800;color:#2ed573;margin-top:4px;">~${value:,}</div>
        </div>
        <div style="background:#16213e;padding:14px;border-radius:8px;">
          <div style="font-size:11px;color:#9fa8da;text-transform:uppercase;letter-spacing:0.5px;">難易度</div>
          <div style="margin-top:8px;">
            <span style="background:rgba(0,0,0,0.3);color:{diff_color};border:1px solid {diff_color};padding:4px 12px;border-radius:12px;font-size:13px;font-weight:700;">{diff_label}</span>
          </div>
        </div>
      </div>

      <div style="margin-bottom:16px;">
        <div style="font-size:12px;color:#9fa8da;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">カテゴリ</div>
        <span style="background:rgba(124,77,255,0.2);color:#7c4dff;border:1px solid rgba(124,77,255,0.4);padding:4px 12px;border-radius:12px;font-size:13px;">{airdrop.get('category','')}</span>
      </div>

      <div style="background:#16213e;padding:14px;border-radius:8px;margin-bottom:16px;">
        <div style="font-size:12px;color:#9fa8da;margin-bottom:8px;font-weight:700;">概要</div>
        <p style="margin:0;color:#e8eaf6;font-size:14px;line-height:1.6;">{airdrop.get('description','')}</p>
      </div>

      {"<div style='background:#16213e;padding:14px;border-radius:8px;margin-bottom:16px;'><div style='font-size:12px;color:#9fa8da;margin-bottom:8px;font-weight:700;'>📋 参加方法</div><ul style='margin:0;padding-left:18px;color:#e8eaf6;font-size:13px;'>" + tasks_html + "</ul></div>" if tasks_html else ""}

      <div style="margin-bottom:20px;color:#9fa8da;font-size:13px;">
        <strong>期限:</strong> {airdrop.get('end_date','未定')}
      </div>

      <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#dc3545,#ff4757);color:white;padding:14px 28px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;letter-spacing:0.5px;">
        今すぐ参加する →
      </a>

      <div style="margin-top:24px;padding-top:16px;border-top:1px solid #2e3460;color:#6c757d;font-size:11px;">
        ※ 投資は自己責任で行ってください。情報は参考目的のみです。
      </div>
    </div>
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
        logger.info(f"ホットアラート送信成功: {name} → {GMAIL_RECIPIENT}")
        return True
    except Exception as e:
        logger.error(f"ホットアラート送信失敗: {e}")
        return False
