"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してメール送信。
毎日デイリーレポート + HOT案件出現時の即時アラートを送信。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)

DIFFICULTY_COLOR = {
    "easy": "#2ed573",
    "medium": "#ff6348",
    "hard": "#ff4757",
}


def _send_mail(subject: str, html_body: str, plain_body: str) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning(
            "Gmail認証情報が未設定のためメール送信をスキップ。"
            ".envにGMAIL_SENDERとGMAIL_APP_PASSWORDを設定してください。"
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"メール送信成功: {GMAIL_RECIPIENT} | 件名: {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗。アプリパスワードを確認してください。")
        return False
    except Exception as e:
        logger.error(f"メール送信失敗: {e}")
        return False


def _build_daily_report_html(
    airdrops: list[dict],
    new_items: list[str],
    diff: dict,
    trending: list[dict],
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    newly_hot_names = {a["name"] for a in diff.get("added", []) if a.get("is_hot")}

    # ===== 新着HOT案件ブロック =====
    new_hot_html = ""
    new_hot_airdrops = [a for a in diff.get("added", []) if a.get("is_hot")]
    if new_hot_airdrops:
        cards = ""
        for a in new_hot_airdrops:
            value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
            diff_color = DIFFICULTY_COLOR.get(a.get("difficulty", "easy"), "#6c757d")
            tasks_html = "".join(f"<li>{t}</li>" for t in a.get("tasks", []))
            cards += f"""
            <div style="background:#1a0a0a;border:2px solid #ff4757;border-radius:10px;padding:16px;margin-bottom:12px;">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                <span style="background:linear-gradient(135deg,#ff4757,#ff6b81);color:white;font-size:11px;font-weight:800;padding:3px 10px;border-radius:20px;">🔥 NEW HOT</span>
                <strong style="font-size:16px;color:#ffffff;">{a['name']} ({a.get('symbol','')})</strong>
              </div>
              <p style="color:#cccccc;font-size:13px;margin:0 0 10px;">{a.get('description','')}</p>
              <table style="width:100%;border-collapse:collapse;">
                <tr>
                  <td style="padding:4px 8px 4px 0;color:#888;font-size:12px;width:80px;">推定価値</td>
                  <td style="padding:4px 0;color:#2ed573;font-weight:800;font-size:16px;">{value}</td>
                  <td style="padding:4px 8px 4px 0;color:#888;font-size:12px;width:60px;">難易度</td>
                  <td style="padding:4px 0;"><span style="background:{diff_color};color:white;font-size:11px;padding:2px 8px;border-radius:12px;">{a.get('difficulty','').upper()}</span></td>
                  <td style="padding:4px 8px 4px 0;color:#888;font-size:12px;width:40px;">期限</td>
                  <td style="padding:4px 0;color:#e8eaf6;font-size:13px;">{a.get('end_date','未定')}</td>
                </tr>
              </table>
              {'<ul style="margin:8px 0 10px;padding-left:20px;color:#cccccc;font-size:13px;">' + tasks_html + '</ul>' if tasks_html else ''}
              <a href="{a.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#ff4757,#c0392b);color:white;padding:10px 22px;border-radius:8px;text-decoration:none;font-weight:800;font-size:14px;">今すぐ参加する →</a>
            </div>"""
        new_hot_html = f"""
        <div style="background:#120a0a;border-left:4px solid #ff4757;border-radius:4px;padding:16px;margin:0 0 20px;">
          <h3 style="color:#ff6b81;margin:0 0 12px;font-size:16px;">🚨 新着HOT案件 {len(new_hot_airdrops)}件 — 今すぐチェック！</h3>
          {cards}
        </div>"""

    # ===== 変更点ブロック =====
    changes_html = ""
    if diff.get("changed"):
        rows = ""
        for ch in diff["changed"]:
            diffs_str = " / ".join(ch["changes"])
            rows += f"""
            <tr>
              <td style="padding:8px 12px;border-bottom:1px solid #2e3460;color:#e8eaf6;font-weight:600;">{ch['name']}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #2e3460;color:#ffa502;font-size:13px;">{diffs_str}</td>
            </tr>"""
        changes_html = f"""
        <div style="margin:0 0 20px;">
          <h3 style="color:#ffa502;margin:0 0 10px;font-size:15px;">✏️ 情報が更新された案件 ({len(diff['changed'])}件)</h3>
          <table style="width:100%;border-collapse:collapse;background:#1e2240;border-radius:8px;overflow:hidden;">
            <thead><tr style="background:#252b4a;">
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;">プロジェクト</th>
              <th style="padding:8px 12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;">変更内容</th>
            </tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>"""

    # ===== 新着エアドロップ (HOT以外) =====
    new_items_html = ""
    non_hot_new = [n for n in new_items if n not in newly_hot_names]
    if non_hot_new:
        items_li = "".join(f"<li style='margin-bottom:4px;color:#cccccc;'>{n}</li>" for n in non_hot_new)
        new_items_html = f"""
        <div style="background:#0d1a0d;border-left:4px solid #2ed573;padding:12px 16px;margin:0 0 20px;border-radius:4px;">
          <strong style="color:#2ed573;">🆕 新着エアドロップ ({len(non_hot_new)}件)</strong>
          <ul style="margin:8px 0 0;padding-left:20px;">{items_li}</ul>
        </div>"""

    # ===== 終了案件 =====
    removed_html = ""
    if diff.get("removed"):
        names = "、".join(diff["removed"])
        removed_html = f"""
        <div style="background:#1a1a1a;border-left:4px solid #888;padding:10px 16px;margin:0 0 20px;border-radius:4px;color:#888;font-size:13px;">
          ❌ <strong>終了・削除された案件:</strong> {names}
        </div>"""

    # ===== ホット一覧テーブル =====
    hot_rows = ""
    for a in hot[:8]:
        diff_color = DIFFICULTY_COLOR.get(a.get("difficulty", "easy"), "#6c757d")
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        new_mark = " 🆕" if a["name"] in newly_hot_names else ""
        hot_rows += f"""
        <tr style="{'background:#1a0f0f;' if a['name'] in newly_hot_names else ''}">
          <td style="padding:10px 12px;border-bottom:1px solid #2e3460;">
            <strong style="color:#e8eaf6;">{a['name']}{new_mark}</strong><br>
            <span style="color:#9fa8da;font-size:11px;">{a.get('category','')}</span>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #2e3460;color:#2ed573;font-weight:800;">{value}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #2e3460;">
            <span style="background:{diff_color};color:white;padding:2px 8px;border-radius:12px;font-size:11px;">{a.get('difficulty','').upper()}</span>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #2e3460;color:#9fa8da;font-size:12px;">{a.get('end_date','未定')}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #2e3460;">
            <a href="{a.get('url','#')}" style="background:#7c4dff;color:white;padding:5px 12px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:700;">参加</a>
          </td>
        </tr>"""

    # ===== トレンドコイン =====
    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li style='margin-bottom:4px;color:#cccccc;font-size:13px;'>"
            f"<strong style='color:#b39ddb;'>{t['name']}</strong> ({t.get('symbol','')}) — スコア: {t.get('score', 0)}"
            f"</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <div style="margin:20px 0 0;">
          <h3 style="color:#b39ddb;margin:0 0 10px;font-size:15px;">📈 CoinGecko トレンドコイン TOP5</h3>
          <ul style="padding-left:20px;margin:0;">{t_items}</ul>
        </div>"""

    # 統計サマリー
    total = len(airdrops)
    hot_count = len(hot)
    added_count = len(diff.get("added", []))
    changed_count = len(diff.get("changed", []))
    removed_count = len(diff.get("removed", []))

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#0f0f1a;color:#e8eaf6;margin:0;padding:0;">
<div style="max-width:680px;margin:0 auto;padding:20px;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px 12px 0 0;padding:24px;margin-bottom:0;">
    <h1 style="margin:0 0 4px;font-size:22px;color:#ffffff;">🪂 Crypto Airdrop Tracker</h1>
    <p style="margin:0;color:#9fa8da;font-size:14px;">{today} 日次更新レポート</p>
  </div>

  <!-- 統計バー -->
  <div style="background:#16213e;padding:16px 24px;border-bottom:1px solid #2e3460;display:flex;gap:20px;flex-wrap:wrap;">
    <div style="text-align:center;">
      <div style="font-size:24px;font-weight:900;color:#5bb3ff;">{total}</div>
      <div style="font-size:10px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">総案件数</div>
    </div>
    <div style="text-align:center;">
      <div style="font-size:24px;font-weight:900;color:#ff6b81;">{hot_count}</div>
      <div style="font-size:10px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">🔥 HOT</div>
    </div>
    <div style="text-align:center;">
      <div style="font-size:24px;font-weight:900;color:#2ed573;">{added_count}</div>
      <div style="font-size:10px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">🆕 新着</div>
    </div>
    <div style="text-align:center;">
      <div style="font-size:24px;font-weight:900;color:#ffa502;">{changed_count}</div>
      <div style="font-size:10px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">✏️ 変更</div>
    </div>
    {'<div style="text-align:center;"><div style="font-size:24px;font-weight:900;color:#888;">' + str(removed_count) + '</div><div style="font-size:10px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">❌ 終了</div></div>' if removed_count else ''}
  </div>

  <!-- メインコンテンツ -->
  <div style="background:#1e2240;padding:20px 24px;border-radius:0 0 12px 12px;box-shadow:0 4px 20px rgba(0,0,0,0.4);">

    {new_hot_html}
    {new_items_html}
    {changes_html}
    {removed_html}

    <!-- 現在のHOT案件テーブル -->
    <h3 style="color:#ff6b81;margin:0 0 12px;font-size:15px;">🔥 現在の全HOT案件 ({hot_count}件)</h3>
    <table style="width:100%;border-collapse:collapse;background:#16213e;border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#1a1a2e;">
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;">プロジェクト</th>
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;">推定価値</th>
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;">難易度</th>
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;">期限</th>
          <th style="padding:10px 12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;">参加</th>
        </tr>
      </thead>
      <tbody>{hot_rows}</tbody>
    </table>

    {trending_html}

    <hr style="margin:24px 0;border:none;border-top:1px solid #2e3460;">
    <p style="color:#6c757d;font-size:11px;margin:0;line-height:1.6;">
      ※ このメールはCrypto Airdrop Trackerから毎日08:00 JSTに自動送信されています。<br>
      ※ 掲載情報は参考目的のみです。投資は自己責任で行ってください。<br>
      送信先: {GMAIL_RECIPIENT}
    </p>
  </div>
</div>
</body>
</html>"""


def send_daily_report(
    airdrops: list[dict],
    new_items: list[str],
    diff: dict,
    trending: list[dict],
) -> bool:
    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    added_count = len(diff.get("added", []))
    newly_hot = [a for a in diff.get("added", []) if a.get("is_hot")]

    subject = f"[Airdrop Daily] {today} — HOT {hot_count}件"
    if newly_hot:
        subject += f" 🚨新着HOT {len(newly_hot)}件: {', '.join(a['name'] for a in newly_hot[:2])}"
    elif added_count:
        subject += f" 🆕新着 {added_count}件"

    html_body = _build_daily_report_html(airdrops, new_items, diff, trending)

    added_names = ", ".join(a["name"] for a in diff.get("added", [])) or "なし"
    changed_names = ", ".join(ch["name"] for ch in diff.get("changed", [])) or "なし"
    plain_body = (
        f"{today} Airdrop日次レポート\n"
        f"HOT案件: {hot_count}件\n"
        f"新着: {added_names}\n"
        f"変更: {changed_names}\n"
        f"トレンド: {', '.join(t['name'] for t in trending[:5])}"
    )

    return _send_mail(subject, html_body, plain_body)


def send_hot_alert(airdrop: dict) -> bool:
    """新規HOT案件出現時の即時アラート"""
    name = airdrop.get("name", "不明")
    symbol = airdrop.get("symbol", "")
    value = airdrop.get("estimated_value_usd", 0)
    diff_color = DIFFICULTY_COLOR.get(airdrop.get("difficulty", "easy"), "#6c757d")
    tasks_html = "".join(f"<li style='color:#cccccc;margin-bottom:4px;'>{t}</li>" for t in airdrop.get("tasks", []))

    subject = f"🚨 [HOT Alert] {name} — 推定${value:,} の新案件！"

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#0f0f1a;color:#e8eaf6;margin:0;padding:20px;">
<div style="max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#7b0000,#c0392b);border-radius:12px 12px 0 0;padding:20px 24px;">
    <h2 style="margin:0;color:white;font-size:20px;">🚨 新着HOTエアドロップ出現！</h2>
    <p style="margin:4px 0 0;color:rgba(255,255,255,0.8);font-size:13px;">今すぐ確認してください</p>
  </div>
  <div style="background:#1e2240;border:2px solid #ff4757;border-top:none;border-radius:0 0 12px 12px;padding:24px;">
    <h3 style="margin:0 0 4px;font-size:22px;color:#ffffff;">{name} {f'({symbol})' if symbol else ''}</h3>
    <p style="color:#9fa8da;font-size:13px;margin:0 0 16px;">{airdrop.get('category','')} / {airdrop.get('type','')}</p>

    <div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:16px;">
      <div>
        <div style="font-size:11px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">推定価値</div>
        <div style="font-size:28px;font-weight:900;color:#2ed573;">~${value:,}</div>
      </div>
      <div>
        <div style="font-size:11px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">難易度</div>
        <div style="margin-top:4px;"><span style="background:{diff_color};color:white;padding:4px 12px;border-radius:20px;font-weight:700;">{airdrop.get('difficulty','').upper()}</span></div>
      </div>
      <div>
        <div style="font-size:11px;color:#9fa8da;text-transform:uppercase;letter-spacing:1px;">参加期限</div>
        <div style="font-size:16px;font-weight:700;color:#ffffff;margin-top:2px;">{airdrop.get('end_date','未定')}</div>
      </div>
    </div>

    <p style="color:#cccccc;font-size:14px;margin:0 0 14px;">{airdrop.get('description','')}</p>

    {'<div style="background:#16213e;border-radius:8px;padding:12px;margin-bottom:16px;"><div style="font-size:12px;font-weight:700;color:#9fa8da;margin-bottom:6px;">📋 参加方法</div><ul style="padding-left:20px;margin:0;">' + tasks_html + '</ul></div>' if tasks_html else ''}

    <a href="{airdrop.get('url','#')}" style="display:inline-block;background:linear-gradient(135deg,#ff4757,#c0392b);color:white;padding:14px 28px;border-radius:10px;text-decoration:none;font-weight:800;font-size:16px;">今すぐ参加する →</a>

    <hr style="margin:20px 0;border:none;border-top:1px solid #2e3460;">
    <p style="color:#6c757d;font-size:11px;margin:0;">投資は自己責任で行ってください。このメールはCrypto Airdrop Trackerから自動送信されています。</p>
  </div>
</div>
</body>
</html>"""

    plain = (
        f"[HOT Alert] {name}\n"
        f"推定価値: ~${value:,}\n"
        f"難易度: {airdrop.get('difficulty','').upper()}\n"
        f"期限: {airdrop.get('end_date','未定')}\n"
        f"URL: {airdrop.get('url','')}"
    )

    return _send_mail(subject, html, plain)
