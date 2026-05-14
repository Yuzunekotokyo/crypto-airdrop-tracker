"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してメール送信。
送信先: tsukamoto.kei@gmail.com
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)

_DIFF_COLORS = {
    "easy":   ("#2ed573", "rgba(46,213,115,0.15)"),
    "medium": ("#ff6348", "rgba(255,99,72,0.15)"),
    "hard":   ("#ff4757", "rgba(255,71,87,0.15)"),
}


def _difficulty_badge(diff: str) -> str:
    color, bg = _DIFF_COLORS.get(diff, ("#9fa8da", "rgba(159,168,218,0.15)"))
    return (
        f'<span style="background:{bg};color:{color};border:1px solid {color};'
        f'padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700;">'
        f'{diff.upper()}</span>'
    )


def _build_changes_html(diff: dict) -> str:
    parts = []

    if diff.get("added"):
        names = "".join(
            f'<li style="margin:4px 0;"><strong>{a["name"]}</strong>'
            f'{"&nbsp;🔥 HOT" if a.get("is_hot") else ""}'
            f'{"&nbsp;— 推定$" + f"{a.get(\"estimated_value_usd\",0):,}" if a.get("estimated_value_usd") else ""}'
            f"</li>"
            for a in diff["added"]
        )
        parts.append(f"""
        <div style="background:rgba(46,213,115,0.08);border-left:4px solid #2ed573;
                    padding:12px 16px;margin:12px 0;border-radius:4px;">
          <strong style="color:#2ed573;">🆕 新規追加 ({len(diff["added"])}件)</strong>
          <ul style="margin:8px 0 0 16px;color:#e8eaf6;">{names}</ul>
        </div>""")

    if diff.get("removed"):
        names = "".join(f"<li>{n}</li>" for n in diff["removed"])
        parts.append(f"""
        <div style="background:rgba(150,150,150,0.08);border-left:4px solid #888;
                    padding:12px 16px;margin:12px 0;border-radius:4px;">
          <strong style="color:#aaa;">🗑 終了・削除 ({len(diff["removed"])}件)</strong>
          <ul style="margin:8px 0 0 16px;color:#9fa8da;">{names}</ul>
        </div>""")

    if diff.get("changed"):
        rows = "".join(
            f'<li style="margin:4px 0;"><strong>{c["name"]}</strong>: '
            + " / ".join(c["changes"]) + "</li>"
            for c in diff["changed"]
        )
        parts.append(f"""
        <div style="background:rgba(255,165,2,0.08);border-left:4px solid #ffa502;
                    padding:12px 16px;margin:12px 0;border-radius:4px;">
          <strong style="color:#ffa502;">✏️ 変更あり ({len(diff["changed"])}件)</strong>
          <ul style="margin:8px 0 0 16px;color:#e8eaf6;">{rows}</ul>
        </div>""")

    return "".join(parts) if parts else ""


def _build_hot_table(airdrops: list[dict]) -> str:
    hot = sorted(
        [a for a in airdrops if a.get("is_hot")],
        key=lambda x: -x.get("estimated_value_usd", 0),
    )[:5]

    if not hot:
        return "<p style='color:#9fa8da;'>現在ホット案件なし</p>"

    rows = ""
    for a in hot:
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        rows += f"""
        <tr style="border-bottom:1px solid #2e3460;">
          <td style="padding:10px 12px;">
            <strong style="color:#e8eaf6;">{a['name']}</strong>
            {"&nbsp;<span style='color:#ff4757;font-size:11px;'>🔥 HOT</span>" if a.get("is_hot") else ""}
            <br><span style="color:#9fa8da;font-size:11px;">{a.get('category','')}</span>
          </td>
          <td style="padding:10px 12px;color:#2ed573;font-weight:700;">{value}</td>
          <td style="padding:10px 12px;">{_difficulty_badge(a.get('difficulty',''))}</td>
          <td style="padding:10px 12px;color:#9fa8da;font-size:12px;">{a.get('end_date','未定')}</td>
          <td style="padding:10px 12px;">
            <a href="{a.get('url','#')}" style="background:#7c4dff;color:white;padding:5px 12px;
               border-radius:6px;text-decoration:none;font-size:12px;font-weight:700;">参加 →</a>
          </td>
        </tr>"""

    return f"""
    <table style="width:100%;border-collapse:collapse;background:#1e2240;border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#1a1a2e;">
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;">プロジェクト</th>
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
    new_items: list[str],
    trending: list[dict],
    diff: dict | None = None,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    diff = diff or {}

    # 変更サマリーバー
    stat_html = ""
    chips = [
        (f"📋 総件数 {len(airdrops)}", "#1e90ff"),
        (f"🔥 ホット {hot_count}件", "#ff4757"),
    ]
    if diff.get("added"):
        chips.append((f"🆕 新着 {len(diff['added'])}件", "#2ed573"))
    if diff.get("changed"):
        chips.append((f"✏️ 変更 {len(diff['changed'])}件", "#ffa502"))
    if diff.get("removed"):
        chips.append((f"🗑 終了 {len(diff['removed'])}件", "#888"))
    stat_html = "".join(
        f'<span style="background:rgba(255,255,255,0.1);color:{c};border:1px solid {c};'
        f'padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700;margin:2px;">{t}</span>'
        for t, c in chips
    )

    changes_html = _build_changes_html(diff)
    hot_table = _build_hot_table(airdrops)

    trending_html = ""
    if trending:
        items = "".join(
            f"<li style='margin:4px 0;'><strong style='color:#e8eaf6;'>{t['name']}</strong> "
            f"<span style='color:#9fa8da;'>({t['symbol']})</span> — スコア: {t.get('score', 0)}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#7c4dff;margin:24px 0 10px;">📈 CoinGecko トレンドコイン Top5</h3>
        <ul style="padding-left:18px;color:#9fa8da;">{items}</ul>"""

    return f"""
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0f0f1a;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:700px;margin:0 auto;padding:20px;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;
              padding:24px 28px;border-radius:12px 12px 0 0;
              border-bottom:3px solid #7c4dff;">
    <h1 style="margin:0;font-size:24px;font-weight:800;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:6px 0 0;opacity:0.7;font-size:13px;">{today} 日次更新レポート</p>
    <div style="margin-top:14px;display:flex;flex-wrap:wrap;gap:6px;">{stat_html}</div>
  </div>

  <!-- ボディ -->
  <div style="background:#16213e;padding:24px 28px;border-radius:0 0 12px 12px;">

    <!-- 変更ハイライト -->
    {changes_html if changes_html else
      '<div style="color:#9fa8da;font-size:13px;padding:12px 0;">前回から変更なし</div>'}

    <!-- ホット案件テーブル -->
    <h3 style="color:#ff4757;margin:24px 0 12px;font-size:16px;">🔥 今狙うべきホット案件 Top5</h3>
    {hot_table}

    <!-- トレンド -->
    {trending_html}

    <hr style="margin:28px 0;border:none;border-top:1px solid #2e3460;">
    <p style="color:#6c757d;font-size:11px;margin:0;line-height:1.8;">
      ※ このメールはCrypto Airdrop Trackerから自動送信されています。<br>
      ※ 投資は自己責任で行ってください。掲載情報は参考目的のみです。
    </p>
  </div>
</div>
</body>
</html>"""


def send_daily_report(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    diff: dict | None = None,
) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    diff = diff or {}
    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    subject = f"[Airdrop] {today} 日次レポート — ホット{hot_count}件"
    if diff.get("added"):
        subject += f" 🆕新着{len(diff['added'])}件"
    if diff.get("changed"):
        subject += f" ✏️変更{len(diff['changed'])}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    plain = (
        f"{today} Airdrop日次レポート\n"
        f"総件数: {len(airdrops)}件 / ホット: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"変更: {len(diff.get('changed', []))}件"
    )
    html = _build_html_body(airdrops, new_items, trending, diff)

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"デイリーレポート送信成功 → {GMAIL_RECIPIENT}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗。アプリパスワードを確認してください。")
        return False
    except Exception as e:
        logger.error(f"メール送信失敗: {e}")
        return False


def send_hot_alert(airdrop: dict) -> bool:
    """注目案件出現時の即時アラートメール"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail未設定のためホットアラートをスキップ")
        return False

    name = airdrop.get("name", "不明")
    symbol = airdrop.get("symbol", "")
    value = airdrop.get("estimated_value_usd", 0)
    diff_label = airdrop.get("difficulty", "").upper()
    diff_color = {"EASY": "#2ed573", "MEDIUM": "#ff6348", "HARD": "#ff4757"}.get(diff_label, "#9fa8da")

    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,} の新案件が登場！今すぐ確認を"

    tasks_html = "".join(
        f"<li style='margin:5px 0;color:#e8eaf6;'>{t}</li>"
        for t in airdrop.get("tasks", [])
    )

    html = f"""
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0f0f1a;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:20px;">

  <!-- 緊急ヘッダー -->
  <div style="background:linear-gradient(135deg,#dc3545,#ff4757);
              color:white;padding:20px 24px;border-radius:12px 12px 0 0;text-align:center;">
    <div style="font-size:40px;margin-bottom:8px;">🚨</div>
    <h1 style="margin:0;font-size:22px;font-weight:900;">ホット案件アラート！</h1>
    <p style="margin:6px 0 0;opacity:0.85;font-size:14px;">儲かりそうな新規エアドロップを検出しました</p>
  </div>

  <!-- 案件詳細 -->
  <div style="background:#16213e;padding:24px;border-radius:0 0 12px 12px;">
    <h2 style="color:#ff4757;margin:0 0 16px;font-size:20px;">
      {name} {f"({symbol})" if symbol else ""}
    </h2>

    <!-- スタットカード -->
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px;">
      <div style="background:#1e2240;border:1px solid #2e3460;border-radius:8px;padding:12px 16px;flex:1;min-width:100px;">
        <div style="color:#9fa8da;font-size:10px;text-transform:uppercase;letter-spacing:1px;">推定価値</div>
        <div style="color:#2ed573;font-size:22px;font-weight:800;margin-top:4px;">~${value:,}</div>
      </div>
      <div style="background:#1e2240;border:1px solid #2e3460;border-radius:8px;padding:12px 16px;flex:1;min-width:100px;">
        <div style="color:#9fa8da;font-size:10px;text-transform:uppercase;letter-spacing:1px;">難易度</div>
        <div style="color:{diff_color};font-size:18px;font-weight:800;margin-top:4px;">{diff_label}</div>
      </div>
      <div style="background:#1e2240;border:1px solid #2e3460;border-radius:8px;padding:12px 16px;flex:1;min-width:100px;">
        <div style="color:#9fa8da;font-size:10px;text-transform:uppercase;letter-spacing:1px;">カテゴリ</div>
        <div style="color:#7c4dff;font-size:16px;font-weight:700;margin-top:4px;">{airdrop.get('category','')}</div>
      </div>
      <div style="background:#1e2240;border:1px solid #2e3460;border-radius:8px;padding:12px 16px;flex:1;min-width:100px;">
        <div style="color:#9fa8da;font-size:10px;text-transform:uppercase;letter-spacing:1px;">期限</div>
        <div style="color:#ffa502;font-size:16px;font-weight:700;margin-top:4px;">{airdrop.get('end_date','未定')}</div>
      </div>
    </div>

    <!-- 概要 -->
    <p style="color:#9fa8da;font-size:14px;line-height:1.6;margin:0 0 16px;">
      {airdrop.get('description','')}
    </p>

    <!-- 参加手順 -->
    {"<div style='background:#1a1a2e;border-radius:8px;padding:14px 18px;margin-bottom:20px;'><p style='color:#ffa502;font-weight:700;margin:0 0 8px;font-size:13px;'>📋 参加手順</p><ul style='padding-left:18px;margin:0;'>" + tasks_html + "</ul></div>" if tasks_html else ""}

    <!-- CTAボタン -->
    <div style="text-align:center;margin:24px 0 16px;">
      <a href="{airdrop.get('url','#')}"
         style="display:inline-block;background:linear-gradient(135deg,#dc3545,#ff4757);
                color:white;padding:14px 36px;border-radius:10px;text-decoration:none;
                font-size:16px;font-weight:800;letter-spacing:0.5px;
                box-shadow:0 4px 20px rgba(220,53,69,0.4);">
        🚀 今すぐ参加する →
      </a>
    </div>

    <hr style="margin:20px 0;border:none;border-top:1px solid #2e3460;">
    <p style="color:#6c757d;font-size:11px;margin:0;text-align:center;">
      ※ 投資は自己責任で行ってください。情報は参考目的のみです。<br>
      Crypto Airdrop Tracker 自動アラート
    </p>
  </div>
</div>
</body>
</html>"""

    plain = (
        f"🚨 HOT Airdrop検出: {name}\n"
        f"推定価値: ~${value:,}\n"
        f"難易度: {diff_label}\n"
        f"URL: {airdrop.get('url','')}\n"
        f"概要: {airdrop.get('description','')}"
    )

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
        logger.info(f"ホットアラート送信成功: {name} → {GMAIL_RECIPIENT}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗。アプリパスワードを確認してください。")
        return False
    except Exception as e:
        logger.error(f"ホットアラート送信失敗: {e}")
        return False
