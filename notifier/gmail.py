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


def _diff_section_html(diff: dict) -> str:
    added = diff.get("added", [])
    removed = diff.get("removed", [])
    changed = diff.get("changed", [])

    if not added and not removed and not changed:
        return """
        <div style="background:#e8f5e9;border-left:4px solid #43a047;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>✅ 本日は変更なし</strong> — データは最新の状態です。
        </div>"""

    html = ""
    if added:
        def _added_item_html(a):
            hot_span = (
                '&nbsp;<span style="background:#dc3545;color:white;padding:1px 6px;border-radius:10px;font-size:11px;">🔥 HOT</span>'
                if a.get("is_hot") else ""
            )
            val_usd = a.get("estimated_value_usd", 0)
            val_str = ("~$" + f"{val_usd:,}") if val_usd else "未定"
            return f"<li><strong>{a['name']}</strong>{hot_span} — 推定価値: {val_str} ({a.get('category','')})</li>"
        items_html = "".join(_added_item_html(a) for a in added)
        html += f"""
        <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>🆕 新着エアドロップ ({len(added)}件)</strong>
          <ul style="margin:8px 0 0 0;padding-left:20px;">{items_html}</ul>
        </div>"""

    if changed:
        ch_html = "".join(
            f"<li><strong>{c['name']}</strong>: {'; '.join(c.get('changes', []))}</li>"
            for c in changed
        )
        html += f"""
        <div style="background:#e3f2fd;border-left:4px solid #1976d2;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>✏️ 更新案件 ({len(changed)}件)</strong>
          <ul style="margin:8px 0 0 0;padding-left:20px;">{ch_html}</ul>
        </div>"""

    if removed:
        rm_html = "".join(f"<li>{n}</li>" for n in removed)
        html += f"""
        <div style="background:#fce4ec;border-left:4px solid #e53935;padding:12px 16px;margin:16px 0;border-radius:4px;">
          <strong>🗑️ 終了・削除 ({len(removed)}件)</strong>
          <ul style="margin:8px 0 0 0;padding-left:20px;">{rm_html}</ul>
        </div>"""

    return html


def _build_html_body(airdrops: list[dict], diff: dict, trending: list[dict], force_email: bool = False) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]

    diff_section = _diff_section_html(diff)

    hot_rows = ""
    for a in hot[:5]:
        difficulty_color = {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}.get(
            a.get("difficulty", "easy"), "#6c757d"
        )
        value_usd = a.get("estimated_value_usd", 0)
        value = ("~$" + f"{value_usd:,}") if value_usd else "不明"
        tasks = a.get("tasks", [])
        tasks_html = ("<br><small style='color:#888;'>" + " → ".join(tasks[:3]) + "</small>") if tasks else ""
        name = a.get("name", "")
        category = a.get("category", "")
        difficulty = a.get("difficulty", "").upper()
        end_date = a.get("end_date", "未定")
        url = a.get("url", "#")
        hot_rows += (
            "<tr>"
            f"<td style='padding:10px;border-bottom:1px solid #dee2e6;'><strong>{name}</strong>{tasks_html}</td>"
            f"<td style='padding:10px;border-bottom:1px solid #dee2e6;'><span style='color:#6c757d;font-size:12px;'>{category}</span></td>"
            f"<td style='padding:10px;border-bottom:1px solid #dee2e6;color:#28a745;font-weight:bold;'>{value}</td>"
            f"<td style='padding:10px;border-bottom:1px solid #dee2e6;'>"
            f"<span style='background:{difficulty_color};color:white;padding:2px 8px;border-radius:12px;font-size:12px;'>{difficulty}</span></td>"
            f"<td style='padding:10px;border-bottom:1px solid #dee2e6;color:#888;font-size:12px;'>{end_date}</td>"
            f"<td style='padding:10px;border-bottom:1px solid #dee2e6;'><a href='{url}' style='color:#0d6efd;font-weight:bold;'>参加 →</a></td>"
            "</tr>"
        )

    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li><strong>{t['name']}</strong> ({t['symbol']}) — スコア: {t.get('score', 0)}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#6f42c1;margin-top:24px;">📈 CoinGecko トレンドコイン Top5</h3>
        <ul style="padding-left:20px;">{t_items}</ul>"""

    added_count = len(diff.get("added", []))
    changed_count = len(diff.get("changed", []))
    total = len(airdrops)
    hot_count = len(hot)

    stats_html = f"""
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin:16px 0;">
      <div style="background:#e8f0fe;padding:10px 18px;border-radius:8px;text-align:center;">
        <div style="font-size:22px;font-weight:800;color:#1a73e8;">{total}</div>
        <div style="font-size:11px;color:#666;">総案件数</div>
      </div>
      <div style="background:#fce8e6;padding:10px 18px;border-radius:8px;text-align:center;">
        <div style="font-size:22px;font-weight:800;color:#d93025;">{hot_count}</div>
        <div style="font-size:11px;color:#666;">🔥 ホット</div>
      </div>
      <div style="background:#e6f4ea;padding:10px 18px;border-radius:8px;text-align:center;">
        <div style="font-size:22px;font-weight:800;color:#188038;">+{added_count}</div>
        <div style="font-size:11px;color:#666;">本日 新着</div>
      </div>
      <div style="background:#fef7e0;padding:10px 18px;border-radius:8px;text-align:center;">
        <div style="font-size:22px;font-weight:800;color:#b06000;">{changed_count}</div>
        <div style="font-size:11px;color:#666;">本日 変更</div>
      </div>
    </div>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:'Helvetica Neue',Arial,'Hiragino Sans',sans-serif;max-width:720px;margin:0 auto;background:#f4f6f8;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);color:white;padding:28px 24px;border-radius:12px 12px 0 0;">
    <div style="font-size:28px;margin-bottom:4px;">🪂 Crypto Airdrop Tracker</div>
    <div style="opacity:0.75;font-size:14px;">{today} — 日次更新レポート</div>
  </div>

  <!-- コンテンツ -->
  <div style="background:white;padding:24px;border-radius:0 0 12px 12px;box-shadow:0 4px 16px rgba(0,0,0,0.1);">

    <!-- 統計サマリー -->
    {stats_html}

    <!-- 本日の変更 -->
    <h3 style="color:#333;border-bottom:2px solid #eee;padding-bottom:8px;">📋 本日の変更サマリー</h3>
    {diff_section}

    <!-- ホット案件テーブル -->
    <h3 style="color:#dc3545;margin-top:24px;">🔥 今すぐ注目のエアドロップ Top5</h3>
    <p style="color:#666;font-size:13px;margin-bottom:12px;">推定価値が高く、参加しやすい案件をピックアップしています。</p>
    <table style="width:100%;border-collapse:collapse;font-size:14px;">
      <thead>
        <tr style="background:#f8f9fa;">
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;white-space:nowrap;">プロジェクト</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">カテゴリ</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">推定価値</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">難易度</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">期限</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;">リンク</th>
        </tr>
      </thead>
      <tbody>{hot_rows}</tbody>
    </table>

    {trending_html}

    <!-- フッター -->
    <hr style="margin:28px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#999;font-size:12px;margin:0;line-height:1.8;">
      🪂 このメールは Crypto Airdrop Tracker から毎日自動送信されています。<br>
      ※ 掲載情報は参考目的のみです。投資は自己責任で行ってください。
    </p>
  </div>

</body>
</html>"""


def send_daily_report(airdrops: list[dict], diff: dict, trending: list[dict], force_email: bool = False) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    added_count = len(diff.get("added", []))
    changed_count = len(diff.get("changed", []))

    subject = f"[Airdrop日報] {today} — ホット{hot_count}件"
    if added_count:
        subject += f" 🆕新着{added_count}件"
    if changed_count:
        subject += f" ✏️変更{changed_count}件"

    # 新規HOT案件があれば件名で強調
    newly_hot = [a for a in diff.get("added", []) if a.get("is_hot")]
    if newly_hot:
        names = "・".join(a["name"] for a in newly_hot[:2])
        subject = f"🚨 [HOT新着] {names} 他 — {subject}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, diff, trending, force_email=force_email)
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"ホット案件: {hot_count}件 / 新着: {added_count}件 / 変更: {changed_count}件\n"
        f"新着: {', '.join(a['name'] for a in diff.get('added', []))  or 'なし'}\n"
        f"変更: {', '.join(c['name'] for c in diff.get('changed', [])) or 'なし'}"
    )

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
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
    """注目案件出現時の即時アラートメール"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        return False

    name = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd", 0)
    subject = f"🚨 [HOT新案件] {name} — 推定${value:,} が登場！今すぐチェック"

    tasks_html = "".join(f"<li>{t}</li>" for t in airdrop.get("tasks", []))

    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:600px;margin:0 auto;background:#f4f6f8;">
  <div style="background:linear-gradient(135deg,#b71c1c,#d32f2f);color:white;padding:24px;border-radius:12px 12px 0 0;">
    <div style="font-size:28px;margin-bottom:6px;">🚨 ホット新案件アラート！</div>
    <div style="opacity:0.85;font-size:14px;">見逃し厳禁 — 今すぐ確認してください</div>
  </div>
  <div style="background:white;padding:24px;border-radius:0 0 12px 12px;box-shadow:0 4px 16px rgba(0,0,0,0.1);">
    <h2 style="color:#d32f2f;margin-top:0;">{name}
      {'&nbsp;<span style="font-size:14px;color:#666;">(' + airdrop.get("symbol","") + ')</span>' if airdrop.get("symbol") else ""}
    </h2>
    <div style="display:flex;gap:16px;flex-wrap:wrap;margin:16px 0;">
      <div style="background:#fce8e6;padding:12px 20px;border-radius:8px;text-align:center;flex:1;min-width:120px;">
        <div style="font-size:24px;font-weight:800;color:#d32f2f;">~${value:,}</div>
        <div style="font-size:11px;color:#888;margin-top:2px;">推定価値 (USD)</div>
      </div>
      <div style="background:#e8f0fe;padding:12px 20px;border-radius:8px;text-align:center;flex:1;min-width:120px;">
        <div style="font-size:18px;font-weight:700;color:#1a73e8;">{airdrop.get("category","")}</div>
        <div style="font-size:11px;color:#888;margin-top:2px;">カテゴリ</div>
      </div>
      <div style="background:#e6f4ea;padding:12px 20px;border-radius:8px;text-align:center;flex:1;min-width:120px;">
        <div style="font-size:18px;font-weight:700;color:#188038;">{airdrop.get("difficulty","").upper()}</div>
        <div style="font-size:11px;color:#888;margin-top:2px;">難易度</div>
      </div>
    </div>

    <h3 style="color:#333;">概要</h3>
    <p style="color:#555;line-height:1.6;">{airdrop.get("description","")}</p>

    <h3 style="color:#333;">📋 参加方法</h3>
    <ul style="color:#555;line-height:1.8;padding-left:20px;">{tasks_html}</ul>

    <p><strong>期限:</strong> <span style="color:#d32f2f;">{airdrop.get("end_date","未定")}</span></p>

    <div style="text-align:center;margin:24px 0;">
      <a href="{airdrop.get('url','#')}"
         style="display:inline-block;background:linear-gradient(135deg,#d32f2f,#b71c1c);color:white;padding:14px 36px;border-radius:8px;text-decoration:none;font-weight:800;font-size:16px;">
        🚀 今すぐ参加する
      </a>
    </div>

    <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
    <p style="color:#999;font-size:12px;">
      🪂 Crypto Airdrop Tracker からの自動アラートです。投資は自己責任で行ってください。
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
        logger.info(f"ホットアラート送信成功: {name} → {GMAIL_RECIPIENT}")
        return True
    except Exception as e:
        logger.error(f"ホットアラート送信失敗: {e}")
        return False
