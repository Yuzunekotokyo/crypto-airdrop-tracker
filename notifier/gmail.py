"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) でメール送信。
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


def _status_label(s: str) -> str:
    return {"active": "● アクティブ", "upcoming": "◎ 近日開始", "ended": "✕ 終了"}.get(s, s)


def _build_html_body(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    diff: dict | None = None,
) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    diff = diff or {}

    # ── 新着バナー ──
    new_html = ""
    if new_items:
        items_html = "".join(
            f'<li style="margin:4px 0;">{n}</li>' for n in new_items
        )
        new_html = f"""
        <div style="background:#e8f5e9;border-left:5px solid #2ed573;padding:14px 18px;margin:20px 0;border-radius:6px;">
          <strong style="color:#1b5e20;">🆕 新着エアドロップ ({len(new_items)}件)</strong>
          <ul style="margin:8px 0 0 16px;color:#2e7d32;">{items_html}</ul>
        </div>"""

    # ── 変更サマリー ──
    changes_html = ""
    changed = diff.get("changed", [])
    removed = diff.get("removed", [])
    if changed or removed:
        rows = ""
        for c in changed[:5]:
            chg_list = "".join(f"<li>{ch}</li>" for ch in c["changes"])
            rows += f"""
            <tr>
              <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;font-weight:600;">{c['name']}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;"><ul style="margin:0;padding-left:18px;color:#555;">{chg_list}</ul></td>
            </tr>"""
        if removed:
            removed_list = ", ".join(removed[:5])
            rows += f"""
            <tr>
              <td colspan="2" style="padding:8px 12px;color:#c62828;font-size:13px;">
                ✕ 終了・削除: {removed_list}
              </td>
            </tr>"""
        changes_html = f"""
        <h3 style="color:#f57c00;margin-top:28px;">✏️ 変更・更新</h3>
        <table style="width:100%;border-collapse:collapse;margin-top:8px;font-size:14px;">
          <thead>
            <tr style="background:#fff3e0;">
              <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #ff9800;width:35%;">プロジェクト</th>
              <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #ff9800;">変更内容</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>"""

    # ── ホット案件テーブル ──
    hot_rows = ""
    for a in hot[:6]:
        dc = _difficulty_color(a.get("difficulty", "easy"))
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        hot_rows += f"""
        <tr>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;">
            <strong style="font-size:15px;">{a['name']}</strong><br>
            <span style="color:#888;font-size:12px;">{a.get('category','')}</span>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;color:#2e7d32;font-weight:700;font-size:16px;">{value}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;">
            <span style="background:{dc};color:white;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:700;">
              {a.get('difficulty','').upper()}
            </span>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;color:#666;font-size:13px;">{a.get('end_date','未定')}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;">
            <a href="{a.get('url','#')}"
               style="background:#7c4dff;color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:700;">
              参加する →
            </a>
          </td>
        </tr>"""

    # ── トップ3 詳細カード ──
    top3_cards = ""
    for a in hot[:3]:
        dc = _difficulty_color(a.get("difficulty", "easy"))
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        tasks_li = "".join(f"<li style='margin:3px 0;'>{t}</li>" for t in a.get("tasks", [])[:4])
        top3_cards += f"""
        <div style="border:1px solid #e0e0e0;border-radius:10px;overflow:hidden;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:16px 20px;display:flex;align-items:center;gap:12px;">
            <div style="flex:1;">
              <strong style="font-size:18px;">{a['name']}</strong>
              <span style="background:rgba(255,255,255,0.15);color:white;font-size:11px;padding:2px 8px;border-radius:12px;margin-left:8px;">{a.get('category','')}</span>
            </div>
            <span style="background:linear-gradient(135deg,#ff4757,#7c4dff);color:white;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;">🔥 HOT</span>
          </div>
          <div style="padding:16px 20px;background:white;">
            <p style="color:#555;font-size:14px;margin:0 0 12px;">{a.get('description','')}</p>
            <div style="display:flex;gap:20px;margin-bottom:12px;flex-wrap:wrap;">
              <div><span style="font-size:11px;color:#888;display:block;">推定価値</span><strong style="font-size:20px;color:#2e7d32;">{value}</strong></div>
              <div><span style="font-size:11px;color:#888;display:block;">難易度</span><span style="background:{dc};color:white;padding:3px 10px;border-radius:12px;font-size:13px;font-weight:700;">{a.get('difficulty','').upper()}</span></div>
              <div><span style="font-size:11px;color:#888;display:block;">ステータス</span><strong style="font-size:14px;">{_status_label(a.get('status',''))}</strong></div>
              <div><span style="font-size:11px;color:#888;display:block;">期限</span><strong style="font-size:14px;">{a.get('end_date','未定')}</strong></div>
            </div>
            {"<div style='background:#f5f5f5;border-radius:6px;padding:10px 14px;'><p style='font-size:12px;font-weight:700;color:#555;margin:0 0 6px;'>📋 参加方法</p><ul style='margin:0;padding-left:18px;font-size:13px;color:#444;'>" + tasks_li + "</ul></div>" if tasks_li else ""}
          </div>
          <div style="padding:12px 20px;background:#f9f9f9;text-align:right;border-top:1px solid #e0e0e0;">
            <a href="{a.get('url','#')}" style="background:linear-gradient(135deg,#7c4dff,#651fff);color:white;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:700;font-size:14px;">今すぐ参加する →</a>
          </div>
        </div>"""

    # ── トレンドコイン ──
    trending_html = ""
    if trending:
        t_items = "".join(
            f"""<li style="margin:6px 0;padding:8px 12px;background:#f5f5f5;border-radius:6px;">
              <strong>{t['name']}</strong>
              <span style="color:#888;font-size:12px;margin-left:6px;">({t['symbol']})</span>
              <span style="float:right;color:#7c4dff;font-size:12px;">スコア: {t.get('score',0)}</span>
            </li>"""
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#6f42c1;margin-top:28px;">📈 CoinGecko トレンドコイン TOP5</h3>
        <ul style="list-style:none;padding:0;margin-top:8px;">{t_items}</ul>"""

    total = len(airdrops)
    hot_count = len(hot)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:'Helvetica Neue',Arial,'Hiragino Sans','Meiryo',sans-serif;max-width:720px;margin:0 auto;background:#f0f0f0;padding:20px 10px;">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e,#0d2137);color:white;padding:28px 28px 20px;border-radius:12px 12px 0 0;">
    <div style="font-size:28px;margin-bottom:6px;">🪂 Crypto Airdrop Tracker</div>
    <div style="opacity:0.7;font-size:14px;">{today} — 毎日自動更新レポート</div>
    <div style="margin-top:16px;display:flex;gap:12px;flex-wrap:wrap;">
      <span style="background:rgba(255,255,255,0.1);padding:5px 14px;border-radius:20px;font-size:13px;">📋 総案件数: <strong>{total}</strong></span>
      <span style="background:rgba(255,71,87,0.3);border:1px solid #ff4757;padding:5px 14px;border-radius:20px;font-size:13px;">🔥 HOT案件: <strong>{hot_count}</strong></span>
      {"<span style='background:rgba(46,213,115,0.3);border:1px solid #2ed573;padding:5px 14px;border-radius:20px;font-size:13px;'>🆕 新着: <strong>" + str(len(new_items)) + "</strong></span>" if new_items else ""}
    </div>
  </div>

  <!-- メインコンテンツ -->
  <div style="background:white;padding:24px 28px;border-radius:0 0 12px 12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);">

    {new_html}
    {changes_html}

    <h3 style="color:#dc3545;margin-top:28px;padding-bottom:10px;border-bottom:2px solid #ffebee;">
      🔥 注目ホットエアドロップ — TOP {min(len(hot), 6)}件
    </h3>
    <table style="width:100%;border-collapse:collapse;margin-top:12px;font-size:14px;">
      <thead>
        <tr style="background:#f8f9fa;">
          <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;">プロジェクト</th>
          <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;">推定価値</th>
          <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;">難易度</th>
          <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;">期限</th>
          <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;">リンク</th>
        </tr>
      </thead>
      <tbody>{hot_rows}</tbody>
    </table>

    <h3 style="color:#1a1a2e;margin-top:32px;padding-bottom:10px;border-bottom:2px solid #e8eaf6;">
      🏆 今週の最注目案件 — 詳細
    </h3>
    <div style="margin-top:16px;">{top3_cards}</div>

    {trending_html}

    <hr style="margin:28px 0;border:none;border-top:1px solid #e0e0e0;">
    <p style="color:#999;font-size:11px;margin:0;text-align:center;">
      このメールは Crypto Airdrop Tracker から自動送信されています。<br>
      情報は参考目的のみです。投資は自己責任で行ってください。
    </p>
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
        logger.warning("Gmail認証情報未設定 — .envを確認してください (GMAIL_SENDER, GMAIL_APP_PASSWORD)")
        return False

    diff = diff or {}
    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    changed_count = len(diff.get("changed", []))

    subject = f"🪂 [Airdrop] {today} 更新 — HOT {hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"
    if changed_count:
        subject += f" ✏️変更{changed_count}件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, diff)
    plain_body = (
        f"{today} Airdrop更新レポート\n"
        f"HOT案件: {hot_count}件\n"
        f"新着: {', '.join(new_items) if new_items else 'なし'}\n"
        f"変更: {changed_count}件\n"
        f"トレンド: {', '.join(t['name'] for t in trending[:3])}"
    )

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"日次レポート送信成功 → {GMAIL_RECIPIENT}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗 — アプリパスワードを確認してください")
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
    dc = _difficulty_color(airdrop.get("difficulty", "easy"))
    tasks_li = "".join(
        f"<li style='margin:4px 0;'>{t}</li>" for t in airdrop.get("tasks", [])
    )
    subject = f"🚨 [HOT Airdrop登場！] {name} — 推定${value:,} 新案件"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:'Helvetica Neue',Arial,'Hiragino Sans',sans-serif;max-width:600px;margin:0 auto;background:#f0f0f0;padding:20px 10px;">
  <div style="background:linear-gradient(135deg,#dc3545,#c62828);color:white;padding:24px;border-radius:12px 12px 0 0;">
    <div style="font-size:32px;margin-bottom:8px;">🚨 NEW HOT AIRDROP!</div>
    <div style="font-size:22px;font-weight:700;">{name}</div>
    <div style="opacity:0.8;font-size:13px;margin-top:4px;">{airdrop.get('category','')} — {airdrop.get('type','')}</div>
  </div>
  <div style="background:white;padding:24px;border-radius:0 0 12px 12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
    <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px;padding:16px;background:#fff3f3;border-radius:8px;border-left:5px solid #dc3545;">
      <div style="text-align:center;">
        <div style="font-size:11px;color:#888;text-transform:uppercase;margin-bottom:4px;">推定価値</div>
        <div style="font-size:26px;font-weight:800;color:#2e7d32;">~${value:,}</div>
      </div>
      <div style="text-align:center;">
        <div style="font-size:11px;color:#888;text-transform:uppercase;margin-bottom:4px;">難易度</div>
        <div style="font-size:18px;font-weight:700;">
          <span style="background:{dc};color:white;padding:4px 14px;border-radius:20px;">{airdrop.get('difficulty','').upper()}</span>
        </div>
      </div>
      <div style="text-align:center;">
        <div style="font-size:11px;color:#888;text-transform:uppercase;margin-bottom:4px;">期限</div>
        <div style="font-size:16px;font-weight:700;">{airdrop.get('end_date','未定')}</div>
      </div>
    </div>
    <p style="color:#444;font-size:15px;line-height:1.7;margin-bottom:20px;">{airdrop.get('description','')}</p>
    {"<div style='background:#f5f5f5;border-radius:8px;padding:14px 16px;margin-bottom:20px;'><p style='font-weight:700;color:#333;margin:0 0 8px;font-size:14px;'>📋 参加方法</p><ul style='margin:0;padding-left:20px;color:#444;font-size:14px;line-height:1.8;'>" + tasks_li + "</ul></div>" if tasks_li else ""}
    <div style="text-align:center;margin-top:8px;">
      <a href="{airdrop.get('url','#')}"
         style="display:inline-block;background:linear-gradient(135deg,#dc3545,#c62828);color:white;padding:14px 36px;border-radius:10px;text-decoration:none;font-weight:700;font-size:16px;letter-spacing:0.5px;">
        🚀 今すぐ参加する！
      </a>
    </div>
    <hr style="margin:24px 0;border:none;border-top:1px solid #eee;">
    <p style="color:#999;font-size:11px;text-align:center;margin:0;">
      Crypto Airdrop Tracker からの自動アラートです。投資は自己責任で行ってください。
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
        logger.info(f"ホットアラート送信 → {name}")
        return True
    except Exception as e:
        logger.error(f"ホットアラート送信失敗: {e}")
        return False
