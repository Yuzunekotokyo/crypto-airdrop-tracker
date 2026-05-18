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


def _difficulty_label(d):
    return {"easy": "EASY (簡単)", "medium": "MEDIUM (中級)", "hard": "HARD (上級)"}.get(d, d.upper())


def _difficulty_color(d):
    return {"easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"}.get(d, "#6c757d")


def _build_html_body(airdrops, new_items, trending, diff=None):
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    diff = diff or {}

    # 新着バナー
    if new_items:
        items_html = "".join("<li style='margin:4px 0;'>" + n + "</li>" for n in new_items)
        new_html = (
            "<div style='background:#fff3cd;border-left:4px solid #ffc107;padding:14px 18px;margin:16px 0;border-radius:6px;'>"
            "<strong style='font-size:15px;'>&#x1F195; 新着エアドロップ (" + str(len(new_items)) + "件)</strong>"
            "<ul style='margin:10px 0 0 0;padding-left:20px;'>" + items_html + "</ul>"
            "</div>"
        )
    else:
        new_html = ""

    # 変更情報
    changes = diff.get("changed", [])
    if changes:
        change_rows = "".join(
            "<li style='margin:4px 0;'><strong>" + c["name"] + "</strong>: " + ", ".join(c["changes"]) + "</li>"
            for c in changes[:5]
        )
        changes_html = (
            "<div style='background:#e8f4fd;border-left:4px solid #1e90ff;padding:14px 18px;margin:16px 0;border-radius:6px;'>"
            "<strong style='font-size:15px;'>&#x270F;&#xFE0F; 更新された案件 (" + str(len(changes)) + "件)</strong>"
            "<ul style='margin:10px 0 0 0;padding-left:20px;'>" + change_rows + "</ul>"
            "</div>"
        )
    else:
        changes_html = ""

    # ホット案件テーブル行
    hot_rows = ""
    for a in hot[:6]:
        d_color = _difficulty_color(a.get("difficulty", "easy"))
        value = ("~$" + "{:,}".format(a.get("estimated_value_usd", 0))) if a.get("estimated_value_usd") else "不明"
        hot_rows += (
            "<tr>"
            "<td style='padding:12px 10px;border-bottom:1px solid #e9ecef;vertical-align:top;'>"
            "<strong style='font-size:14px;'>" + a["name"] + "</strong><br>"
            "<span style='color:#6c757d;font-size:12px;'>" + a.get("category", "") + "</span><br>"
            "<span style='color:#6c757d;font-size:11px;'>" + a.get("type", "") + "</span>"
            "</td>"
            "<td style='padding:12px 10px;border-bottom:1px solid #e9ecef;color:#28a745;font-weight:bold;font-size:16px;'>" + value + "</td>"
            "<td style='padding:12px 10px;border-bottom:1px solid #e9ecef;'>"
            "<span style='background:" + d_color + ";color:white;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:700;'>"
            + a.get("difficulty", "").upper() + "</span>"
            "</td>"
            "<td style='padding:12px 10px;border-bottom:1px solid #e9ecef;font-size:13px;'>" + a.get("end_date", "未定") + "</td>"
            "<td style='padding:12px 10px;border-bottom:1px solid #e9ecef;'>"
            "<a href='" + a.get("url", "#") + "' style='background:#0d6efd;color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:700;'>参加する</a>"
            "</td>"
            "</tr>"
        )

    # その他の注目案件
    other = [a for a in airdrops if not a.get("is_hot")][:5]
    other_rows = ""
    for a in other:
        value = ("~$" + "{:,}".format(a.get("estimated_value_usd", 0))) if a.get("estimated_value_usd") else "未定"
        other_rows += (
            "<tr>"
            "<td style='padding:8px 10px;border-bottom:1px solid #f0f0f0;font-size:13px;'>"
            "<strong>" + a["name"] + "</strong>"
            " <span style='color:#6c757d;'>(" + a.get("symbol", "") + ")</span>"
            "</td>"
            "<td style='padding:8px 10px;border-bottom:1px solid #f0f0f0;font-size:13px;color:#28a745;'>" + value + "</td>"
            "<td style='padding:8px 10px;border-bottom:1px solid #f0f0f0;font-size:12px;color:#6c757d;'>" + a.get("end_date", "未定") + "</td>"
            "<td style='padding:8px 10px;border-bottom:1px solid #f0f0f0;'>"
            "<a href='" + a.get("url", "#") + "' style='color:#0d6efd;font-size:12px;'>詳細&#x2192;</a>"
            "</td>"
            "</tr>"
        )
    if other_rows:
        other_section = (
            "<h3 style='color:#495057;margin-top:24px;font-size:15px;'>&#x1F4CC; その他の注目案件</h3>"
            "<table style='width:100%;border-collapse:collapse;'><tbody>" + other_rows + "</tbody></table>"
        )
    else:
        other_section = ""

    # トレンドコイン
    if trending:
        t_items = "".join(
            "<li style='margin:5px 0;'><strong>" + t["name"] + "</strong> (" + t["symbol"] + ")"
            " <span style='color:#6c757d;font-size:12px;'>スコア: " + str(t.get("score", 0))
            + " | 時価総額ランク: #" + str(t.get("rank", "?")) + "</span></li>"
            for t in trending[:5]
        )
        trending_html = (
            "<h3 style='color:#6f42c1;margin-top:24px;font-size:15px;'>&#x1F4C8; CoinGecko トレンドコイン Top5</h3>"
            "<ul style='padding-left:20px;'>" + t_items + "</ul>"
        )
    else:
        trending_html = ""

    total = len(airdrops)
    hot_count = len(hot)
    added_count = len(new_items)

    new_chip = (
        "<span style='background:rgba(46,213,115,0.3);padding:4px 14px;border-radius:20px;font-size:13px;'>"
        "&#x1F195; 新着 <strong>" + str(added_count) + "</strong>件</span>"
        if added_count else ""
    )

    return (
        "<!DOCTYPE html><html>"
        "<head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'></head>"
        "<body style='font-family:\"Hiragino Sans\",\"Meiryo\",Arial,sans-serif;max-width:700px;margin:0 auto;background:#f0f2f5;'>"

        # ヘッダー
        "<div style='background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);color:white;padding:28px 24px;border-radius:12px 12px 0 0;'>"
        "<h1 style='margin:0;font-size:22px;letter-spacing:1px;'>&#x1FA82; Crypto Airdrop Tracker</h1>"
        "<p style='margin:6px 0 0;opacity:0.85;font-size:14px;'>" + today + " 日次更新レポート</p>"
        "<div style='margin-top:16px;display:flex;gap:12px;flex-wrap:wrap;'>"
        "<span style='background:rgba(255,255,255,0.15);padding:4px 14px;border-radius:20px;font-size:13px;'>"
        "&#x1F4CB; 総数 <strong>" + str(total) + "</strong>件</span>"
        "<span style='background:rgba(255,71,87,0.3);padding:4px 14px;border-radius:20px;font-size:13px;'>"
        "&#x1F525; ホット <strong>" + str(hot_count) + "</strong>件</span>"
        + new_chip +
        "</div>"
        "</div>"

        # メインコンテンツ
        "<div style='background:white;padding:24px;border-radius:0 0 12px 12px;box-shadow:0 4px 20px rgba(0,0,0,0.08);'>"
        + new_html
        + changes_html

        # ホット案件テーブル
        + "<h3 style='color:#dc3545;margin-top:20px;font-size:16px;border-bottom:2px solid #dc3545;padding-bottom:8px;'>"
        "&#x1F525; 今すぐ狙うべきホット案件</h3>"
        "<table style='width:100%;border-collapse:collapse;margin-top:12px;'>"
        "<thead><tr style='background:#f8f9fa;'>"
        "<th style='padding:10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;color:#6c757d;'>プロジェクト</th>"
        "<th style='padding:10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;color:#6c757d;'>推定価値</th>"
        "<th style='padding:10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;color:#6c757d;'>難易度</th>"
        "<th style='padding:10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;color:#6c757d;'>期限</th>"
        "<th style='padding:10px;border-bottom:2px solid #dee2e6;'></th>"
        "</tr></thead>"
        "<tbody>" + hot_rows + "</tbody></table>"

        + other_section
        + trending_html

        # 免責事項
        + "<hr style='margin:24px 0;border:none;border-top:1px solid #dee2e6;'>"
        "<p style='color:#6c757d;font-size:11px;margin:0;line-height:1.7;'>"
        "※ このメールはCrypto Airdrop Trackerから自動送信されています（毎日08:00 JST）。<br>"
        "※ 掲載情報は参考目的のみです。投資・エアドロップ参加は自己責任で行ってください。<br>"
        "※ 暗号資産投資にはリスクが伴います。"
        "</p>"
        "</div>"
        "</body></html>"
    )


def send_daily_report(airdrops, new_items, trending, diff=None):
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためメール送信をスキップ (.envを確認してください)")
        return False

    diff = diff or {}
    today = datetime.now().strftime("%Y/%m/%d")
    hot_count = sum(1 for a in airdrops if a.get("is_hot"))
    added_count = len(new_items)
    changed_count = len(diff.get("changed", []))

    subject = "[Airdrop日報] " + today + " — HOT " + str(hot_count) + "件"
    if added_count:
        subject += " 新着" + str(added_count) + "件"
    if changed_count:
        subject += " 変更" + str(changed_count) + "件"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    html_body = _build_html_body(airdrops, new_items, trending, diff)
    plain_body = (
        today + " Airdrop更新レポート\n"
        "ホット案件: " + str(hot_count) + "件\n"
        "新着: " + (", ".join(new_items) if new_items else "なし") + "\n"
        "変更: " + str(changed_count) + "件\n"
        "トレンド: " + ", ".join(t["name"] for t in trending[:3])
    )

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info("日次レポート送信成功: " + GMAIL_RECIPIENT)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗。アプリパスワードを確認してください。")
        return False
    except Exception as e:
        logger.error("メール送信失敗: " + str(e))
        return False


def send_hot_alert(airdrop):
    """注目案件出現時・HOT昇格時の即時アラート"""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        return False

    name = airdrop.get("name", "不明")
    value = airdrop.get("estimated_value_usd", 0)
    symbol = airdrop.get("symbol", "")
    difficulty = airdrop.get("difficulty", "easy")
    d_color = _difficulty_color(difficulty)

    tasks_html = "".join(
        "<li style='margin:4px 0;'>" + t + "</li>"
        for t in airdrop.get("tasks", [])
    )
    tasks_section = (
        "<div style='background:#e8f5e9;border-radius:8px;padding:16px;margin-bottom:20px;'>"
        "<p style='margin:0 0 6px;font-weight:700;color:#2e7d32;'>&#x1F4CB; 参加方法</p>"
        "<ul style='margin:0;padding-left:20px;'>" + tasks_html + "</ul>"
        "</div>"
    ) if tasks_html else ""

    subject = "&#x1F6A8; [HOT新着] " + name + " — 推定$" + "{:,}".format(value) + " の高額エアドロップ！"

    html = (
        "<!DOCTYPE html><html>"
        "<head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'></head>"
        "<body style='font-family:\"Hiragino Sans\",\"Meiryo\",Arial,sans-serif;max-width:600px;margin:0 auto;background:#f0f2f5;'>"

        "<div style='background:linear-gradient(135deg,#dc3545,#c82333);color:white;padding:24px;border-radius:12px 12px 0 0;'>"
        "<p style='margin:0;font-size:12px;opacity:0.9;letter-spacing:2px;'>&#x1F6A8; HOT ALERT — 新着高額エアドロップ</p>"
        "<h2 style='margin:8px 0 0;font-size:24px;'>" + name + " (" + symbol + ")</h2>"
        "<p style='margin:8px 0 0;font-size:22px;font-weight:900;'>推定 ~$" + "{:,}".format(value) + "</p>"
        "</div>"

        "<div style='background:white;padding:24px;border:1px solid #dee2e6;border-top:none;border-radius:0 0 12px 12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);'>"
        "<table style='width:100%;border-collapse:collapse;margin-bottom:20px;'>"
        "<tr><td style='padding:8px;color:#6c757d;font-size:13px;width:100px;'>カテゴリ</td>"
        "<td style='padding:8px;font-weight:600;'>" + airdrop.get("category", "") + "</td></tr>"
        "<tr style='background:#f8f9fa;'><td style='padding:8px;color:#6c757d;font-size:13px;'>タイプ</td>"
        "<td style='padding:8px;font-weight:600;'>" + airdrop.get("type", "") + "</td></tr>"
        "<tr><td style='padding:8px;color:#6c757d;font-size:13px;'>難易度</td>"
        "<td style='padding:8px;'><span style='background:" + d_color + ";color:white;padding:3px 12px;border-radius:20px;font-size:13px;font-weight:700;'>"
        + difficulty.upper() + "</span></td></tr>"
        "<tr style='background:#f8f9fa;'><td style='padding:8px;color:#6c757d;font-size:13px;'>期限</td>"
        "<td style='padding:8px;font-weight:600;'>" + airdrop.get("end_date", "未定") + "</td></tr>"
        "</table>"

        "<div style='background:#f8f9fa;border-radius:8px;padding:16px;margin-bottom:20px;'>"
        "<p style='margin:0 0 6px;font-weight:700;color:#333;'>&#x1F4D6; 概要</p>"
        "<p style='margin:0;color:#495057;font-size:14px;line-height:1.6;'>" + airdrop.get("description", "") + "</p>"
        "</div>"

        + tasks_section

        + "<a href='" + airdrop.get("url", "#") + "' style='display:block;background:linear-gradient(135deg,#dc3545,#c82333);color:white;padding:14px 24px;border-radius:8px;text-decoration:none;font-weight:800;font-size:16px;text-align:center;'>"
        "&#x1F680; 今すぐ参加する &#x2192;</a>"

        "<hr style='margin:20px 0;border:none;border-top:1px solid #dee2e6;'>"
        "<p style='color:#6c757d;font-size:11px;margin:0;line-height:1.7;'>"
        "※ 投資・エアドロップ参加は自己責任で行ってください。<br>"
        "※ 情報は参考目的のみです。"
        "</p>"
        "</div>"
        "</body></html>"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[HOT新着] " + name + " — 推定$" + "{:,}".format(value) + " の高額エアドロップ！"
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info("HOTアラート送信成功: " + name + " -> " + GMAIL_RECIPIENT)
        return True
    except Exception as e:
        logger.error("HOTアラート送信失敗: " + str(e))
        return False
