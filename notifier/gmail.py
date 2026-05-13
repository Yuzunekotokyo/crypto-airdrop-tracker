"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してメール送信。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT, UPDATE_HOUR, UPDATE_MINUTE

logger = logging.getLogger(__name__)


def _difficulty_label(d: str) -> tuple[str, str]:
    """(日本語ラベル, カラー)"""
    return {
        "easy":   ("かんたん", "#2ed573"),
        "medium": ("普通",     "#ff6348"),
        "hard":   ("難しい",   "#ff4757"),
    }.get(d, (d.upper(), "#9fa8da"))


def _build_change_section(diff: dict) -> str:
    """変更サマリーHTMLブロック"""
    blocks = []

    if diff.get("added"):
        items = "".join(
            f'<li><strong>{a["name"]}</strong>'
            f'{"&nbsp;🔥" if a.get("is_hot") else ""}'
            f' — 推定 <span style="color:#2ed573;">~${a.get("estimated_value_usd",0):,}</span>'
            f' ({a.get("category","")}) '
            f'<a href="{a.get("url","#")}" style="color:#7c4dff;">参加する</a></li>'
            for a in diff["added"]
        )
        blocks.append(f"""
        <div style="background:#0a2a1a;border-left:4px solid #2ed573;padding:14px 18px;margin:12px 0;border-radius:6px;">
          <strong style="color:#2ed573;">🆕 新着エアドロップ ({len(diff["added"])}件)</strong>
          <ul style="margin:10px 0 0 0;padding-left:20px;line-height:2;">{items}</ul>
        </div>""")

    if diff.get("changed"):
        rows = ""
        for c in diff["changed"]:
            changes_html = " / ".join(c["changes"])
            rows += f'<li><strong>{c["name"]}</strong>: {changes_html}</li>'
        blocks.append(f"""
        <div style="background:#2a2200;border-left:4px solid #ffa502;padding:14px 18px;margin:12px 0;border-radius:6px;">
          <strong style="color:#ffa502;">✏️ ステータス変更 ({len(diff["changed"])}件)</strong>
          <ul style="margin:10px 0 0 0;padding-left:20px;line-height:2;">{rows}</ul>
        </div>""")

    if diff.get("removed"):
        names = "、".join(diff["removed"])
        blocks.append(f"""
        <div style="background:#2a0a0a;border-left:4px solid #ff4757;padding:14px 18px;margin:12px 0;border-radius:6px;">
          <strong style="color:#ff4757;">🗑️ 終了/削除 ({len(diff["removed"])}件)</strong>
          <p style="margin:6px 0 0;color:#ccc;">{names}</p>
        </div>""")

    if not blocks:
        blocks.append("""
        <div style="background:#1a1a2e;border-left:4px solid #555;padding:14px 18px;margin:12px 0;border-radius:6px;">
          <span style="color:#9fa8da;">本日の新着・変更はありませんでした。</span>
        </div>""")

    return "\n".join(blocks)


def _build_hot_table(airdrops: list[dict]) -> str:
    hot = [a for a in airdrops if a.get("is_hot")]
    if not hot:
        return "<p style='color:#9fa8da;'>現在のホット案件はありません。</p>"

    rows = ""
    for a in hot[:6]:
        dlabel, dcolor = _difficulty_label(a.get("difficulty", "easy"))
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        rows += f"""
        <tr>
          <td style="padding:11px 12px;border-bottom:1px solid #2e3460;">
            {"<img src='" + a['logo'] + "' width='24' height='24' style='border-radius:50%;vertical-align:middle;margin-right:8px;' onerror=\"this.style.display='none'\">" if a.get('logo') else ""}
            <strong>{a['name']}</strong>
            {"&nbsp;<span style='background:#ff4757;color:white;font-size:10px;padding:1px 6px;border-radius:10px;'>🔥 HOT</span>" if a.get('is_hot') else ""}
            <br><span style="color:#9fa8da;font-size:11px;">{a.get('category','')}</span>
          </td>
          <td style="padding:11px 12px;border-bottom:1px solid #2e3460;color:#2ed573;font-weight:bold;font-size:16px;">{value}</td>
          <td style="padding:11px 12px;border-bottom:1px solid #2e3460;">
            <span style="background:{dcolor}22;color:{dcolor};border:1px solid {dcolor};padding:2px 8px;border-radius:12px;font-size:12px;font-weight:bold;">{dlabel}</span>
          </td>
          <td style="padding:11px 12px;border-bottom:1px solid #2e3460;color:#9fa8da;font-size:13px;">{a.get('end_date','未定')}</td>
          <td style="padding:11px 12px;border-bottom:1px solid #2e3460;">
            <a href="{a.get('url','#')}" style="background:#7c4dff;color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:bold;">参加</a>
          </td>
        </tr>"""

    return f"""
    <table style="width:100%;border-collapse:collapse;background:#1e2240;border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#16213e;">
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:1px;">プロジェクト</th>
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;">推定価値</th>
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;">難易度</th>
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;">期限</th>
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;">リンク</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>"""


def _build_html_body(
    airdrops: list[dict],
    diff: dict,
    trending: list[dict],
    is_significant: bool,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    total = len(airdrops)

    alert_bar = ""
    if is_significant:
        newly_hot_names = ", ".join(a["name"] for a in diff.get("added", []) if a.get("is_hot"))
        alert_bar = f"""
    <div style="background:linear-gradient(135deg,#7c0000,#c0392b);color:white;padding:16px 24px;margin:-24px -24px 20px;border-radius:0;">
      <strong style="font-size:16px;">🚨 注目の新案件が登場しました！</strong>
      <p style="margin:6px 0 0;opacity:0.9;">{newly_hot_names or "高価値の新着エアドロップあり"}</p>
    </div>"""

    trending_html = ""
    if trending:
        t_items = "".join(
            f'<span style="display:inline-block;background:#1e2240;border:1px solid #2e3460;'
            f'padding:4px 12px;border-radius:20px;margin:3px;font-size:13px;">'
            f'<strong>{t["name"]}</strong> ({t["symbol"]})</span>'
            for t in trending[:8]
        )
        trending_html = f"""
        <h3 style="color:#9fa8da;font-size:14px;text-transform:uppercase;letter-spacing:1px;margin:24px 0 10px;">
          📈 CoinGecko トレンドコイン
        </h3>
        <div>{t_items}</div>"""

    change_html = _build_change_section(diff)
    hot_table = _build_hot_table(airdrops)

    stats = f"""
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin:16px 0;">
      <div style="flex:1;min-width:80px;background:#1e2240;border:1px solid #2e3460;border-radius:8px;padding:14px;text-align:center;">
        <div style="font-size:24px;font-weight:900;color:#1e90ff;">{total}</div>
        <div style="font-size:11px;color:#9fa8da;margin-top:2px;">総案件数</div>
      </div>
      <div style="flex:1;min-width:80px;background:#1e2240;border:1px solid #ff4757;border-radius:8px;padding:14px;text-align:center;">
        <div style="font-size:24px;font-weight:900;color:#ff4757;">{hot_count}</div>
        <div style="font-size:11px;color:#9fa8da;margin-top:2px;">🔥 ホット</div>
      </div>
      <div style="flex:1;min-width:80px;background:#1e2240;border:1px solid #2ed573;border-radius:8px;padding:14px;text-align:center;">
        <div style="font-size:24px;font-weight:900;color:#2ed573;">{len(diff.get('added', []))}</div>
        <div style="font-size:11px;color:#9fa8da;margin-top:2px;">🆕 新着</div>
      </div>
      <div style="flex:1;min-width:80px;background:#1e2240;border:1px solid #ffa502;border-radius:8px;padding:14px;text-align:center;">
        <div style="font-size:24px;font-weight:900;color:#ffa502;">{len(diff.get('changed', []))}</div>
        <div style="font-size:11px;color:#9fa8da;margin-top:2px;">✏️ 変更</div>
      </div>
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:'Helvetica Neue',Arial,'Hiragino Sans',sans-serif;background:#0f0f1a;color:#e8eaf6;margin:0;padding:20px;">
  <div style="max-width:680px;margin:0 auto;">

    <!-- ヘッダー -->
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:24px;border-radius:12px 12px 0 0;border-bottom:2px solid #7c4dff;">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
        <div>
          <h1 style="margin:0;font-size:20px;font-weight:900;">🪂 Crypto Airdrop Tracker</h1>
          <p style="margin:4px 0 0;color:#9fa8da;font-size:13px;">{today} 日次更新レポート</p>
        </div>
        <div style="background:#7c4dff22;border:1px solid #7c4dff;padding:6px 14px;border-radius:20px;font-size:12px;color:#9fa8da;">
          毎日 {UPDATE_HOUR:02d}:{UPDATE_MINUTE:02d} JST 自動更新
        </div>
      </div>
    </div>

    <!-- 本文 -->
    <div style="background:#16213e;padding:24px;border-radius:0 0 12px 12px;border:1px solid #2e3460;border-top:none;">
      {alert_bar}

      <!-- 統計 -->
      {stats}

      <!-- 本日の変更 -->
      <h3 style="color:#9fa8da;font-size:14px;text-transform:uppercase;letter-spacing:1px;margin:24px 0 10px;">
        📋 本日の変更サマリー
      </h3>
      {change_html}

      <!-- ホット案件一覧 -->
      <h3 style="color:#9fa8da;font-size:14px;text-transform:uppercase;letter-spacing:1px;margin:24px 0 10px;">
        🔥 今すぐ狙うべきホット案件
      </h3>
      {hot_table}

      <!-- トレンド -->
      {trending_html}

      <!-- フッター -->
      <hr style="margin:28px 0;border:none;border-top:1px solid #2e3460;">
      <p style="color:#555;font-size:11px;margin:0;line-height:1.7;">
        ※ このメールは Crypto Airdrop Tracker から毎日自動送信されています。<br>
        ※ 掲載情報は参考目的のみです。投資は自己責任で行ってください。<br>
        送信先: {GMAIL_RECIPIENT}
      </p>
    </div>

  </div>
</body>
</html>"""


def send_daily_report(
    airdrops: list[dict],
    diff: dict,
    trending: list[dict],
    is_significant: bool = False,
) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    added_count = len(diff.get("added", []))

    subject = f"[Airdrop Daily] {today} — ホット{hot_count}件"
    if added_count:
        subject += f" 🆕新着{added_count}件"
    if is_significant:
        subject += " 🚨注目案件あり"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, diff, trending, is_significant)

    # テキスト版
    added_names = ", ".join(a["name"] for a in diff.get("added", [])) or "なし"
    changed_names = ", ".join(c["name"] for c in diff.get("changed", [])) or "なし"
    plain = (
        f"{today} Airdrop日次レポート\n"
        f"ホット案件: {hot_count}件 / 総数: {len(airdrops)}件\n"
        f"新着: {added_names}\n"
        f"変更: {changed_names}\n"
        f"{'🚨 注目の新案件あり！' if is_significant else ''}"
    )

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"日次レポート送信成功: {GMAIL_RECIPIENT} / 件名: {subject}")
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
    dlabel, dcolor = _difficulty_label(airdrop.get("difficulty", "easy"))
    subject = f"🚨 [HOT Airdrop] {name} — ~${value:,} の新案件が登場！"

    tasks_html = "".join(f"<li style='margin:4px 0;'>{t}</li>" for t in airdrop.get("tasks", []))

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"></head>
<body style="font-family:'Helvetica Neue',Arial,sans-serif;background:#0f0f1a;color:#e8eaf6;margin:0;padding:20px;">
  <div style="max-width:600px;margin:0 auto;">
    <div style="background:linear-gradient(135deg,#7c0000,#c0392b);padding:20px 24px;border-radius:12px 12px 0 0;">
      <h2 style="margin:0;font-size:20px;">🚨 ホットエアドロップ出現！</h2>
      <p style="margin:6px 0 0;opacity:0.85;font-size:13px;">今すぐチェックしてください</p>
    </div>
    <div style="background:#16213e;padding:24px;border:1px solid #2e3460;border-top:none;border-radius:0 0 12px 12px;">
      <h3 style="margin:0 0 16px;font-size:22px;color:#ff6b81;">{name}
        {"&nbsp;<span style='font-size:14px;background:#7c4dff;color:white;padding:2px 10px;border-radius:20px;vertical-align:middle;'>{airdrop.get('symbol','')}</span>" if airdrop.get('symbol') else ""}
      </h3>
      <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:20px;">
        <div style="background:#1e2240;border:1px solid #2e3460;border-radius:8px;padding:14px;">
          <div style="font-size:11px;color:#9fa8da;text-transform:uppercase;margin-bottom:4px;">推定価値</div>
          <div style="font-size:22px;font-weight:900;color:#2ed573;">~${value:,}</div>
        </div>
        <div style="background:#1e2240;border:1px solid #2e3460;border-radius:8px;padding:14px;">
          <div style="font-size:11px;color:#9fa8da;text-transform:uppercase;margin-bottom:4px;">難易度</div>
          <div style="font-size:16px;font-weight:700;color:{dcolor};">{dlabel}</div>
        </div>
        <div style="background:#1e2240;border:1px solid #2e3460;border-radius:8px;padding:14px;">
          <div style="font-size:11px;color:#9fa8da;text-transform:uppercase;margin-bottom:4px;">カテゴリ</div>
          <div style="font-size:15px;font-weight:700;">{airdrop.get('category','')}</div>
        </div>
        <div style="background:#1e2240;border:1px solid #2e3460;border-radius:8px;padding:14px;">
          <div style="font-size:11px;color:#9fa8da;text-transform:uppercase;margin-bottom:4px;">期限</div>
          <div style="font-size:15px;font-weight:700;">{airdrop.get('end_date','未定')}</div>
        </div>
      </div>
      <p style="color:#9fa8da;font-size:14px;line-height:1.6;margin:0 0 16px;">{airdrop.get('description','')}</p>
      {"<div style='background:#1e2240;border-radius:8px;padding:14px;margin-bottom:20px;'><p style='margin:0 0 8px;font-size:13px;font-weight:700;color:#9fa8da;'>📋 参加方法</p><ul style='margin:0;padding-left:18px;color:#e8eaf6;font-size:13px;line-height:1.8;'>" + tasks_html + "</ul></div>" if airdrop.get('tasks') else ""}
      <a href="{airdrop.get('url','#')}"
         style="display:block;text-align:center;background:linear-gradient(135deg,#ff4757,#7c4dff);color:white;
                padding:14px 24px;border-radius:8px;text-decoration:none;font-size:16px;font-weight:900;">
        🚀 今すぐ参加する
      </a>
      <hr style="margin:20px 0;border:none;border-top:1px solid #2e3460;">
      <p style="color:#555;font-size:11px;margin:0;">投資は自己責任で行ってください。情報は参考目的のみです。</p>
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
        logger.info(f"ホットアラート送信成功: {name} → {GMAIL_RECIPIENT}")
        return True
    except Exception as e:
        logger.error(f"ホットアラート送信失敗: {e}")
        return False
