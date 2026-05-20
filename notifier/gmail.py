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


def _difficulty_label(d: str) -> tuple[str, str]:
    """(ラベル, カラー) を返す"""
    return {
        "easy":   ("EASY",   "#28a745"),
        "medium": ("MEDIUM", "#fd7e14"),
        "hard":   ("HARD",   "#dc3545"),
    }.get(d, (d.upper() if d else "-", "#6c757d"))


def _build_html_body(
    airdrops: list[dict],
    diff: dict,
    trending: list[dict],
    summary: dict,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = sorted(
        [a for a in airdrops if a.get("is_hot")],
        key=lambda x: -(x.get("estimated_value_usd") or 0),
    )
    added = diff.get("added", [])
    changed = diff.get("changed", [])
    newly_hot_names = set(summary.get("newly_hot_names", []))

    # ===== ホット新着アラートセクション =====
    hot_alert_html = ""
    if newly_hot_names:
        alert_items = [a for a in added if a["name"] in newly_hot_names]
        rows = ""
        for a in alert_items:
            val = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "不明"
            label, color = _difficulty_label(a.get("difficulty", ""))
            rows += f"""
            <tr style="background:#fff8f0;">
              <td style="padding:12px;border-bottom:1px solid #ffe0b2;">
                <strong style="font-size:16px;">{a['name']}</strong><br>
                <span style="color:#888;font-size:12px;">{a.get('category','')}</span>
              </td>
              <td style="padding:12px;border-bottom:1px solid #ffe0b2;color:#e65100;font-weight:bold;font-size:16px;">{val}</td>
              <td style="padding:12px;border-bottom:1px solid #ffe0b2;">
                <span style="background:{color};color:white;padding:3px 10px;border-radius:12px;font-size:12px;">{label}</span>
              </td>
              <td style="padding:12px;border-bottom:1px solid #ffe0b2;font-size:13px;">{a.get('end_date','未定')}</td>
              <td style="padding:12px;border-bottom:1px solid #ffe0b2;">
                <a href="{a.get('url','#')}" style="background:#e65100;color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:13px;">今すぐ参加</a>
              </td>
            </tr>"""
        hot_alert_html = f"""
        <div style="background:#fff3e0;border:2px solid #ff6f00;border-radius:8px;padding:16px 20px;margin:16px 0;">
          <h2 style="color:#e65100;margin:0 0 12px;font-size:18px;">🚨 ホット新案件が登場！</h2>
          <table style="width:100%;border-collapse:collapse;">
            <thead>
              <tr style="background:#ffe0b2;">
                <th style="padding:10px;text-align:left;font-size:13px;">プロジェクト</th>
                <th style="padding:10px;text-align:left;font-size:13px;">推定価値</th>
                <th style="padding:10px;text-align:left;font-size:13px;">難易度</th>
                <th style="padding:10px;text-align:left;font-size:13px;">期限</th>
                <th style="padding:10px;text-align:left;font-size:13px;">参加</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>"""

    # ===== 新着エアドロップセクション =====
    new_html = ""
    non_hot_added = [a for a in added if a["name"] not in newly_hot_names]
    if non_hot_added:
        items_html = "".join(f"<li>{n['name']}</li>" for n in non_hot_added)
        new_html = f"""
        <div style="background:#f3f8ff;border-left:4px solid #1e90ff;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>🆕 その他の新着エアドロップ ({len(non_hot_added)}件)</strong>
          <ul style="margin:8px 0 0 0;">{items_html}</ul>
        </div>"""

    # ===== 変更セクション =====
    changes_html = ""
    if changed:
        change_rows = ""
        for c in changed[:5]:
            change_rows += f"""
            <tr>
              <td style="padding:8px 10px;border-bottom:1px solid #dee2e6;font-weight:bold;">{c['name']}</td>
              <td style="padding:8px 10px;border-bottom:1px solid #dee2e6;color:#6c757d;font-size:13px;">{"　/　".join(c['changes'])}</td>
            </tr>"""
        changes_html = f"""
        <div style="margin:16px 0;">
          <h3 style="color:#6c757d;font-size:15px;">✏️ 変更情報 ({len(changed)}件)</h3>
          <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead>
              <tr style="background:#f8f9fa;">
                <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;">プロジェクト</th>
                <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #dee2e6;">変更内容</th>
              </tr>
            </thead>
            <tbody>{change_rows}</tbody>
          </table>
        </div>"""

    # ===== TOP5 ホット案件テーブル =====
    hot_rows = ""
    for i, a in enumerate(hot[:5], 1):
        label, color = _difficulty_label(a.get("difficulty", ""))
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "不明"
        tasks_html = ""
        if a.get("tasks"):
            tasks_html = "<br><span style='color:#888;font-size:11px;'>" + " / ".join(a["tasks"][:2]) + "</span>"
        hot_rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <span style="color:#aaa;font-size:12px;">#{i}</span>
            <strong style="margin-left:6px;">{a['name']}</strong>
            {tasks_html}
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:bold;">{value}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <span style="background:{color};color:white;padding:2px 8px;border-radius:12px;font-size:12px;">{label}</span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;font-size:13px;">{a.get('end_date','未定')}</td>
          <td style="padding:10px;border-bottom:1px solid #dee2e6;">
            <a href="{a.get('url','#')}" style="color:#0d6efd;font-weight:bold;">参加 →</a>
          </td>
        </tr>"""

    # ===== CoinGeckoトレンド =====
    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li><strong>{t['name']}</strong> ({t.get('symbol','')}) "
            f"<span style='color:#888;font-size:12px;'>スコア: {t.get('score', 0)}</span></li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <div style="background:#f8f4ff;border-left:4px solid #7c4dff;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <h3 style="color:#6f42c1;margin:0 0 8px;">📈 CoinGecko トレンドコイン</h3>
          <ul style="margin:0;">{t_items}</ul>
        </div>"""

    # ===== サマリー統計 =====
    stats_html = f"""
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin:16px 0;">
      <div style="background:#e8f5e9;border:1px solid #a5d6a7;border-radius:8px;padding:10px 16px;text-align:center;min-width:80px;">
        <div style="font-size:22px;font-weight:bold;color:#2e7d32;">{summary.get('total_airdrops',0)}</div>
        <div style="font-size:11px;color:#666;">総案件数</div>
      </div>
      <div style="background:#ffebee;border:1px solid #ef9a9a;border-radius:8px;padding:10px 16px;text-align:center;min-width:80px;">
        <div style="font-size:22px;font-weight:bold;color:#c62828;">{summary.get('hot_count',0)}</div>
        <div style="font-size:11px;color:#666;">🔥 ホット</div>
      </div>
      <div style="background:#e3f2fd;border:1px solid #90caf9;border-radius:8px;padding:10px 16px;text-align:center;min-width:80px;">
        <div style="font-size:22px;font-weight:bold;color:#1565c0;">{summary.get('added_count',0)}</div>
        <div style="font-size:11px;color:#666;">🆕 新着</div>
      </div>
      <div style="background:#fff8e1;border:1px solid #ffe082;border-radius:8px;padding:10px 16px;text-align:center;min-width:80px;">
        <div style="font-size:22px;font-weight:bold;color:#f57f17;">{summary.get('changed_count',0)}</div>
        <div style="font-size:11px;color:#666;">✏️ 変更</div>
      </div>
    </div>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:'Hiragino Sans','Meiryo',Arial,sans-serif;max-width:720px;margin:0 auto;background:#f8f9fa;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:24px 28px;border-radius:8px 8px 0 0;">
    <h1 style="margin:0;font-size:22px;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:4px 0 0;opacity:0.8;font-size:14px;">{today} 自動更新レポート</p>
  </div>
  <div style="background:white;padding:24px 28px;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">

    {stats_html}
    {hot_alert_html}
    {new_html}
    {changes_html}

    <h3 style="color:#dc3545;margin:20px 0 12px;">🔥 注目のホットエアドロップ TOP5 (価値順)</h3>
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
    newly_hot_names = summary.get("newly_hot_names", [])

    # 件名: ホット新着があれば強調
    if newly_hot_names:
        subject = f"🚨 [HOT] {today} — 注目新案件{len(newly_hot_names)}件! ホット{hot_count}件"
    elif added:
        subject = f"🆕 [Airdrop] {today} — 新着{len(added)}件 / ホット{hot_count}件"
    else:
        subject = f"[Airdrop] {today} 更新 — ホット案件{hot_count}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, diff, trending, summary)
    added_names = [a["name"] for a in added]
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {', '.join(added_names) if added_names else 'なし'}\n"
        f"注目新案件: {', '.join(newly_hot_names) if newly_hot_names else 'なし'}"
    )

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"メール送信成功: {GMAIL_RECIPIENT} / 件名: {subject}")
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
    value = airdrop.get("estimated_value_usd", 0) or 0
    category = airdrop.get("category", "")
    difficulty = airdrop.get("difficulty", "")
    diff_label, diff_color = _difficulty_label(difficulty)
    tasks_html = "".join(f"<li>{t}</li>" for t in airdrop.get("tasks", []))

    subject = f"🚨 [HOT Airdrop 速報] {name} — 推定${value:,}の新案件！今すぐ確認を"

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:'Hiragino Sans','Meiryo',Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;">
  <div style="background:linear-gradient(135deg,#b71c1c,#e53935);color:white;padding:20px 24px;border-radius:8px 8px 0 0;">
    <div style="font-size:13px;opacity:0.9;margin-bottom:4px;">🚨 ホットエアドロップ速報</div>
    <h2 style="margin:0;font-size:22px;">{name}</h2>
    <div style="margin-top:8px;font-size:24px;font-weight:bold;">推定 ~${value:,}</div>
  </div>
  <div style="background:white;padding:24px;border:1px solid #ffcdd2;border-top:none;border-radius:0 0 8px 8px;">
    <table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
      <tr>
        <td style="padding:8px;width:120px;color:#888;font-size:13px;">カテゴリ</td>
        <td style="padding:8px;font-weight:bold;">{category}</td>
      </tr>
      <tr style="background:#fafafa;">
        <td style="padding:8px;color:#888;font-size:13px;">難易度</td>
        <td style="padding:8px;">
          <span style="background:{diff_color};color:white;padding:2px 10px;border-radius:12px;font-size:12px;">{diff_label}</span>
        </td>
      </tr>
      <tr>
        <td style="padding:8px;color:#888;font-size:13px;">期限</td>
        <td style="padding:8px;font-weight:bold;">{airdrop.get('end_date','未定')}</td>
      </tr>
    </table>

    <p style="color:#333;line-height:1.7;">{airdrop.get('description','')}</p>

    {"<h4 style='color:#333;margin:16px 0 8px;'>📋 参加方法</h4><ul style='margin:0;padding-left:20px;line-height:2;'>" + tasks_html + "</ul>" if tasks_html else ""}

    <div style="margin-top:24px;text-align:center;">
      <a href="{airdrop.get('url','#')}"
         style="display:inline-block;background:linear-gradient(135deg,#e53935,#b71c1c);color:white;
                padding:14px 36px;border-radius:8px;text-decoration:none;font-weight:bold;
                font-size:16px;letter-spacing:0.5px;">
        今すぐ参加する →
      </a>
    </div>

    <hr style="margin:24px 0;border:none;border-top:1px solid #eee;">
    <p style="color:#aaa;font-size:11px;text-align:center;">
      ※ このメールはCrypto Airdrop Trackerから自動送信されています。投資は自己責任で行ってください。
    </p>
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
        logger.info(f"ホットアラート送信: {name} → {GMAIL_RECIPIENT}")
        return True
    except Exception as e:
        logger.error(f"ホットアラート送信失敗: {e}")
        return False
