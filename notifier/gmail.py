"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してHTML形式のメール送信。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)


def _build_daily_report_html(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    changes: list[dict] = None,
    removed: list[str] = None,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    hot_count = len(hot)
    changes = changes or []
    removed = removed or []

    # 新着セクション
    new_html = ""
    if new_items:
        items_html = "".join(f"<li style='margin:4px 0;'>{n}</li>" for n in new_items[:10])
        new_html = f"""
        <div style="background:#1a3a1a;border-left:4px solid #2ed573;padding:14px 18px;margin:16px 0;border-radius:6px;">
          <div style="color:#2ed573;font-weight:700;font-size:15px;margin-bottom:8px;">🆕 新着エアドロップ {len(new_items)}件</div>
          <ul style="margin:0;padding-left:20px;color:#c8f7c5;">{items_html}</ul>
        </div>"""

    # 変更セクション
    changed_html = ""
    if changes:
        change_items = ""
        for c in changes[:5]:
            ch_list = "".join(
                f"<li style='color:#ffd700;font-size:12px;'>{ch}</li>"
                for ch in c.get("changes", [])
            )
            change_items += f"<li style='margin:6px 0;'><strong style='color:#e8eaf6;'>{c['name']}</strong><ul>{ch_list}</ul></li>"
        changed_html = f"""
        <div style="background:#2a2500;border-left:4px solid #ffa502;padding:14px 18px;margin:16px 0;border-radius:6px;">
          <div style="color:#ffa502;font-weight:700;font-size:15px;margin-bottom:8px;">✏️ 情報更新 {len(changes)}件</div>
          <ul style="margin:0;padding-left:20px;color:#e8e0b0;">{change_items}</ul>
        </div>"""

    # ホット案件テーブル
    hot_rows = ""
    for a in hot[:6]:
        diff_color = {"easy": "#2ed573", "medium": "#ff6348", "hard": "#ff4757"}.get(
            a.get("difficulty", "easy"), "#888"
        )
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        tasks_preview = a.get("tasks", [])[:2]
        tasks_html = "".join(f"<li style='color:#9fa8da;font-size:12px;margin:2px 0;'>{t}</li>" for t in tasks_preview)
        hot_rows += f"""
        <tr>
          <td style="padding:14px;border-bottom:1px solid #2e3460;vertical-align:top;">
            <div style="font-weight:700;color:#e8eaf6;font-size:14px;">{a['name']}</div>
            <div style="color:#7c4dff;font-size:11px;margin-top:2px;background:rgba(124,77,255,0.15);display:inline-block;padding:1px 6px;border-radius:10px;">{a.get('category', '')}</div>
            {f'<ul style="margin:6px 0 0;padding-left:14px;">{tasks_html}</ul>' if tasks_html else ''}
          </td>
          <td style="padding:14px;border-bottom:1px solid #2e3460;color:#2ed573;font-weight:800;font-size:18px;white-space:nowrap;">{value}</td>
          <td style="padding:14px;border-bottom:1px solid #2e3460;white-space:nowrap;">
            <span style="background:{diff_color}22;color:{diff_color};border:1px solid {diff_color};padding:3px 8px;border-radius:12px;font-size:11px;font-weight:700;">
              {a.get('difficulty', '').upper()}
            </span>
          </td>
          <td style="padding:14px;border-bottom:1px solid #2e3460;color:#9fa8da;font-size:13px;white-space:nowrap;">{a.get('end_date', '未定')}</td>
          <td style="padding:14px;border-bottom:1px solid #2e3460;">
            <a href="{a.get('url', '#')}" style="background:linear-gradient(135deg,#7c4dff,#651fff);color:white;padding:7px 14px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:700;white-space:nowrap;">参加する →</a>
          </td>
        </tr>"""

    # トレンドコイン
    trending_html = ""
    if trending:
        t_items = "".join(
            f"""<li style="margin:6px 0;color:#c0c8f0;">
              <strong style="color:#e8eaf6;">{t['name']}</strong>
              <span style="color:#9fa8da;"> ({t.get('symbol', '')})</span>
              <span style="color:#ffa502;font-size:12px;"> — Trendスコア: {t.get('score', 0)}</span>
            </li>"""
            for t in trending[:7]
        )
        trending_html = f"""
        <div style="background:#1a1a35;border:1px solid #2e3460;border-radius:8px;padding:16px;margin-top:20px;">
          <h3 style="color:#7c4dff;font-size:16px;margin:0 0 12px;">📈 CoinGeckoトレンドコイン</h3>
          <ul style="padding-left:20px;margin:0;">{t_items}</ul>
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;background:#0a0a15;color:#e8eaf6;margin:0;padding:20px;">
<div style="max-width:720px;margin:0 auto;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:28px 32px;border-radius:12px 12px 0 0;border-bottom:3px solid #7c4dff;">
    <h1 style="margin:0;font-size:26px;color:#ffffff;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:6px 0 0;color:#9fa8da;font-size:14px;">{today} 自動更新レポート</p>
  </div>

  <!-- メインコンテンツ -->
  <div style="background:#12122a;padding:28px 32px;border-radius:0 0 12px 12px;border:1px solid #2e3460;border-top:none;">

    <!-- 統計ダッシュボード -->
    <table style="width:100%;border-collapse:separate;border-spacing:8px;margin-bottom:8px;">
      <tr>
        <td style="background:#1e2240;border:1px solid #1e90ff44;padding:14px;border-radius:8px;text-align:center;width:25%;">
          <div style="color:#9fa8da;font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">合計案件</div>
          <div style="color:#1e90ff;font-size:26px;font-weight:800;">{len(airdrops)}</div>
          <div style="color:#6070a0;font-size:11px;">件</div>
        </td>
        <td style="background:#1e2240;border:1px solid #ff475744;padding:14px;border-radius:8px;text-align:center;width:25%;">
          <div style="color:#9fa8da;font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">🔥 ホット</div>
          <div style="color:#ff4757;font-size:26px;font-weight:800;">{hot_count}</div>
          <div style="color:#6070a0;font-size:11px;">件</div>
        </td>
        <td style="background:#1e2240;border:1px solid #2ed57344;padding:14px;border-radius:8px;text-align:center;width:25%;">
          <div style="color:#9fa8da;font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">🆕 新着</div>
          <div style="color:#2ed573;font-size:26px;font-weight:800;">{len(new_items)}</div>
          <div style="color:#6070a0;font-size:11px;">件</div>
        </td>
        <td style="background:#1e2240;border:1px solid #ffa50244;padding:14px;border-radius:8px;text-align:center;width:25%;">
          <div style="color:#9fa8da;font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">✏️ 更新</div>
          <div style="color:#ffa502;font-size:26px;font-weight:800;">{len(changes)}</div>
          <div style="color:#6070a0;font-size:11px;">件</div>
        </td>
      </tr>
    </table>

    {new_html}
    {changed_html}

    <!-- ホット案件 -->
    <h3 style="color:#ff6b81;font-size:18px;margin:24px 0 14px;border-bottom:2px solid #ff475733;padding-bottom:8px;">
      🔥 今狙うべき注目エアドロップ TOP6
    </h3>
    <table style="width:100%;border-collapse:collapse;background:#1e2240;border-radius:8px;overflow:hidden;border:1px solid #2e3460;">
      <thead>
        <tr style="background:#252b4a;border-bottom:2px solid #2e3460;">
          <th style="padding:12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">プロジェクト & タスク</th>
          <th style="padding:12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">推定価値</th>
          <th style="padding:12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">難易度</th>
          <th style="padding:12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">期限</th>
          <th style="padding:12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">参加</th>
        </tr>
      </thead>
      <tbody>
        {hot_rows if hot_rows else '<tr><td colspan="5" style="padding:20px;text-align:center;color:#9fa8da;">現在ホット案件なし</td></tr>'}
      </tbody>
    </table>

    {trending_html}

    <hr style="border:none;border-top:1px solid #2e3460;margin:28px 0 20px;">
    <p style="color:#4a5070;font-size:11px;text-align:center;margin:0;line-height:1.8;">
      🪂 Crypto Airdrop Tracker — 自動送信メール (毎日 08:00 JST)<br>
      ※ 投資は自己責任で行ってください。掲載情報は参考目的のみです。
    </p>
  </div>

</div>
</body>
</html>"""


def _send_email(subject: str, html_body: str, plain_body: str = "") -> bool:
    """SMTPでGmailを送信する共通関数"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning(
            "Gmail認証情報が未設定のためメール送信をスキップ "
            "(.envのGMAIL_SENDER, GMAIL_APP_PASSWORDを設定してください)"
        )
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
        logger.info(f"✅ メール送信成功: {GMAIL_RECIPIENT}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("❌ Gmail認証失敗。Googleアカウントのアプリパスワードを確認してください。")
        logger.error("   設定方法: https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        logger.error(f"❌ メール送信失敗: {e}")
        return False


def send_daily_report(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    changes: list[dict] = None,
    removed: list[str] = None,
) -> bool:
    """日次レポートメールを送信"""
    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    changes = changes or []
    removed = removed or []

    subject = f"🪂 [{today}] Airdrop更新レポート — 🔥ホット{hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"
    if changes:
        subject += f" ✏️更新{len(changes)}件"

    html_body = _build_daily_report_html(airdrops, new_items, trending, changes, removed)
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(new_items[:5]) if new_items else 'なし'}\n"
        f"変更: {len(changes)}件\n"
        f"トレンド: {', '.join(t['name'] for t in trending[:3]) if trending else 'なし'}"
    )

    return _send_email(subject, html_body, plain_body)


def send_hot_alert(airdrop: dict) -> bool:
    """🚨 注目案件出現時の即時アラートメール"""
    name = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd", 0)
    diff_color = {"easy": "#2ed573", "medium": "#ff6348", "hard": "#ff4757"}.get(
        airdrop.get("difficulty", "easy"), "#888"
    )

    subject = f"🚨 【HOT Airdrop登場】{name} — 推定${value:,} | 今すぐ確認！"

    tasks_html = "".join(
        f"<li style='margin:6px 0;color:#e8eaf6;'>{t}</li>"
        for t in airdrop.get("tasks", [])
    )

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;background:#0a0a15;margin:0;padding:20px;">
<div style="max-width:600px;margin:0 auto;">

  <!-- アラートヘッダー -->
  <div style="background:linear-gradient(135deg,#ff4757,#7c4dff);padding:28px;border-radius:12px 12px 0 0;text-align:center;">
    <div style="font-size:48px;margin-bottom:8px;">🚨</div>
    <h1 style="margin:0;color:white;font-size:22px;">ホットエアドロップ登場！</h1>
    <p style="margin:6px 0 0;color:rgba(255,255,255,0.85);font-size:14px;">見逃し厳禁の新案件が追加されました</p>
  </div>

  <!-- コンテンツ -->
  <div style="background:#12122a;padding:28px;border-radius:0 0 12px 12px;border:1px solid #2e3460;border-top:none;">

    <h2 style="color:#ff6b81;font-size:24px;margin:0 0 6px;">{name}</h2>
    <span style="background:rgba(124,77,255,0.2);color:#7c4dff;border:1px solid #7c4dff44;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:700;">{airdrop.get('category', '')}</span>

    <!-- 指標 -->
    <table style="width:100%;border-collapse:separate;border-spacing:8px;margin:20px 0;">
      <tr>
        <td style="background:#1e2240;border:1px solid #2ed57344;padding:16px;border-radius:8px;text-align:center;">
          <div style="color:#9fa8da;font-size:10px;text-transform:uppercase;margin-bottom:4px;">推定価値</div>
          <div style="color:#2ed573;font-size:26px;font-weight:800;">~${value:,}</div>
        </td>
        <td style="background:#1e2240;border:1px solid {diff_color}44;padding:16px;border-radius:8px;text-align:center;">
          <div style="color:#9fa8da;font-size:10px;text-transform:uppercase;margin-bottom:4px;">難易度</div>
          <div style="color:{diff_color};font-size:20px;font-weight:800;">{airdrop.get('difficulty', '').upper()}</div>
        </td>
        <td style="background:#1e2240;border:1px solid #ffa50244;padding:16px;border-radius:8px;text-align:center;">
          <div style="color:#9fa8da;font-size:10px;text-transform:uppercase;margin-bottom:4px;">期限</div>
          <div style="color:#ffa502;font-size:16px;font-weight:700;">{airdrop.get('end_date', '未定')}</div>
        </td>
      </tr>
    </table>

    <p style="color:#9fa8da;font-size:14px;line-height:1.7;background:#1a1a2e;padding:14px;border-radius:8px;border-left:3px solid #7c4dff;">
      {airdrop.get('description', '')}
    </p>

    {f'''<div style="background:#1e2240;border-radius:8px;padding:16px;margin:16px 0;">
      <h4 style="color:#e8eaf6;font-size:14px;margin:0 0 10px;">📋 参加方法</h4>
      <ul style="padding-left:20px;margin:0;">{tasks_html}</ul>
    </div>''' if tasks_html else ''}

    <div style="text-align:center;margin-top:24px;">
      <a href="{airdrop.get('url', '#')}"
         style="display:inline-block;background:linear-gradient(135deg,#ff4757,#7c4dff);color:white;padding:14px 36px;border-radius:8px;text-decoration:none;font-size:16px;font-weight:800;letter-spacing:0.5px;">
        🚀 今すぐ参加する
      </a>
    </div>

    <hr style="border:none;border-top:1px solid #2e3460;margin:24px 0 16px;">
    <p style="color:#4a5070;font-size:11px;text-align:center;margin:0;">
      🪂 Crypto Airdrop Tracker — 自動アラートメール<br>
      投資は自己責任で行ってください。
    </p>
  </div>
</div>
</body>
</html>"""

    return _send_email(subject, html, f"🚨 HOT Airdrop: {name} — 推定${value:,}")
