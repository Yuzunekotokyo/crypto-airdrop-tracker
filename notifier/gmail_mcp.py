"""
Gmail MCP経由でメール送信するためのヘルパーモジュール。
SMTPではなくGmail MCPサーバーを利用するため、アプリパスワード不要。
主にClaude Codeセッション中の通知に使用。

使い方:
  from notifier.gmail_mcp import build_report_email, build_hot_alert_email
  subject, plain, html = build_report_email(airdrops, new_items, trending)
  # → Claude Code の Gmail MCP ツールに渡す
"""

from datetime import datetime


def build_report_email(
    airdrops: list[dict],
    new_items: list[str],
    trending: list[dict],
    summary: dict | None = None,
) -> tuple[str, str, str]:
    """
    日次レポートメールを構築する。
    Returns: (subject, plain_body, html_body)
    """
    today = datetime.now().strftime("%Y/%m/%d")
    today_jp = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]
    hot_count = len(hot)

    subject = f"🪂 [Airdrop] {today} 更新レポート — ホット案件 {hot_count}件"
    if new_items:
        subject += f" 🆕新着{len(new_items)}件"

    # 新着セクション
    new_html = ""
    if new_items:
        items_html = "".join(f"<li>{n}</li>" for n in new_items[:10])
        new_html = f"""
        <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:14px 18px;
                    margin:16px 0;border-radius:6px;">
          <strong>🆕 新着エアドロップ ({len(new_items)}件)</strong>
          <ul style="margin:10px 0 0 0;padding-left:20px;">{items_html}</ul>
        </div>"""

    # 変更セクション
    changes_html = ""
    if summary and summary.get("changes"):
        ch_rows = ""
        for ch in summary["changes"][:5]:
            ch_rows += f"<li><strong>{ch['name']}</strong>: {' / '.join(ch['changes'])}</li>"
        changes_html = f"""
        <div style="background:#e8f4fd;border-left:4px solid #1e90ff;padding:14px 18px;
                    margin:16px 0;border-radius:6px;">
          <strong>✏️ ステータス変更 ({len(summary['changes'])}件)</strong>
          <ul style="margin:10px 0 0 0;padding-left:20px;">{ch_rows}</ul>
        </div>"""

    # ホット案件テーブル
    hot_rows = ""
    for a in hot[:5]:
        difficulty_color = {
            "easy": "#28a745", "medium": "#fd7e14", "hard": "#dc3545"
        }.get(a.get("difficulty", "easy"), "#6c757d")
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        tasks_html = ""
        if a.get("tasks"):
            tasks_html = "<ul style='margin:6px 0 0 0;padding-left:16px;'>" + \
                "".join(f"<li style='font-size:12px;color:#555;'>{t}</li>" for t in a["tasks"][:3]) + \
                "</ul>"
        hot_rows += f"""
        <tr style="border-bottom:1px solid #dee2e6;">
          <td style="padding:12px 10px;vertical-align:top;">
            <div style="display:flex;align-items:center;gap:8px;">
              {"<img src='" + a['logo'] + "' width='28' height='28' style='border-radius:50%;' onerror=''/>" if a.get('logo') else ""}
              <div>
                <strong style="font-size:14px;">{a['name']}</strong>
                {"<span style='margin-left:4px;font-size:11px;color:#888;'>(" + a.get('symbol','') + ")</span>" if a.get('symbol') else ""}
                <br><span style="color:#6c757d;font-size:11px;">{a.get('category','')}</span>
              </div>
            </div>
            {tasks_html}
          </td>
          <td style="padding:12px 10px;color:#28a745;font-weight:700;font-size:16px;vertical-align:top;">{value}</td>
          <td style="padding:12px 10px;vertical-align:top;">
            <span style="background:{difficulty_color};color:white;padding:3px 9px;
                         border-radius:12px;font-size:11px;font-weight:700;">
              {a.get('difficulty','').upper()}
            </span>
          </td>
          <td style="padding:12px 10px;color:#555;font-size:13px;vertical-align:top;">{a.get('end_date','未定')}</td>
          <td style="padding:12px 10px;vertical-align:top;">
            <a href="{a.get('url','#')}"
               style="background:#7c4dff;color:white;padding:6px 14px;border-radius:6px;
                      text-decoration:none;font-size:12px;font-weight:700;">参加する</a>
          </td>
        </tr>"""

    # トレンドセクション
    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li><strong>{t['name']}</strong> ({t.get('symbol','')}) "
            f"— スコア: {t.get('score',0)}</li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <h3 style="color:#6f42c1;margin-top:24px;">📈 CoinGecko トレンドコイン TOP5</h3>
        <ul style="margin:8px 0;padding-left:20px;">{t_items}</ul>"""

    # 統計バー
    stats = f"""
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin:16px 0;">
      <div style="background:#e8f4fd;border:1px solid #1e90ff;border-radius:8px;
                  padding:10px 16px;text-align:center;">
        <div style="font-size:22px;font-weight:800;color:#1e90ff;">{len(airdrops)}</div>
        <div style="font-size:11px;color:#555;">総エアドロップ</div>
      </div>
      <div style="background:#ffeef0;border:1px solid #dc3545;border-radius:8px;
                  padding:10px 16px;text-align:center;">
        <div style="font-size:22px;font-weight:800;color:#dc3545;">{hot_count}</div>
        <div style="font-size:11px;color:#555;">🔥 ホット案件</div>
      </div>
      <div style="background:#eafaf1;border:1px solid #28a745;border-radius:8px;
                  padding:10px 16px;text-align:center;">
        <div style="font-size:22px;font-weight:800;color:#28a745;">{len(new_items)}</div>
        <div style="font-size:11px;color:#555;">🆕 新着</div>
      </div>
    </div>"""

    html_body = f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="font-family:'Helvetica Neue',Arial,'Hiragino Sans',Meiryo,sans-serif;
             max-width:720px;margin:0 auto;background:#f4f6f9;padding:16px;">
  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;
              padding:28px 28px 20px;border-radius:12px 12px 0 0;">
    <h1 style="margin:0;font-size:24px;letter-spacing:0.5px;">
      🪂 Crypto Airdrop Tracker
    </h1>
    <p style="margin:6px 0 0;opacity:0.75;font-size:13px;">{today_jp} 日次更新レポート</p>
  </div>

  <!-- 本文 -->
  <div style="background:white;padding:28px;border-radius:0 0 12px 12px;
              box-shadow:0 4px 20px rgba(0,0,0,0.1);border:1px solid #dee2e6;border-top:none;">

    {stats}
    {new_html}
    {changes_html}

    <h3 style="color:#dc3545;margin:24px 0 12px;">🔥 今狙うべきホット案件 TOP5</h3>
    <table style="width:100%;border-collapse:collapse;border:1px solid #dee2e6;
                  border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#f8f9fa;">
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;color:#555;">プロジェクト</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;color:#555;">推定価値</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;color:#555;">難易度</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;color:#555;">期限</th>
          <th style="padding:10px;text-align:left;border-bottom:2px solid #dee2e6;font-size:12px;color:#555;">リンク</th>
        </tr>
      </thead>
      <tbody>{hot_rows}</tbody>
    </table>

    {trending_html}

    <hr style="margin:28px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#999;font-size:11px;margin:0;line-height:1.8;">
      ※ このメールはCrypto Airdrop Trackerから自動送信されています。<br>
      ※ 掲載情報は参考目的のみです。投資は自己責任で行ってください。<br>
      ※ 特に注目度の高い新規案件が出現した際は別途アラートを送信します。
    </p>
  </div>
</body>
</html>"""

    plain_body = (
        f"{today_jp} Crypto Airdrop Tracker 更新レポート\n"
        f"{'=' * 50}\n"
        f"総エアドロップ数: {len(airdrops)}件\n"
        f"ホット案件: {hot_count}件\n"
        f"新着: {len(new_items)}件\n"
        + (f"新着案件: {', '.join(new_items[:5])}\n" if new_items else "")
        + f"\n🔥 ホット案件 TOP3:\n"
        + "".join(
            f"  • {a['name']} — ~${a.get('estimated_value_usd',0):,} ({a.get('difficulty','').upper()})\n"
            for a in hot[:3]
        )
        + (f"\n📈 トレンド: {', '.join(t['name'] for t in trending[:5])}\n" if trending else "")
    )

    return subject, plain_body, html_body


def build_hot_alert_email(airdrop: dict) -> tuple[str, str, str]:
    """
    ホット案件出現アラートメールを構築する。
    Returns: (subject, plain_body, html_body)
    """
    name = airdrop.get("name", "不明")
    symbol = airdrop.get("symbol", "")
    value = airdrop.get("estimated_value_usd", 0)
    category = airdrop.get("category", "")
    difficulty = airdrop.get("difficulty", "").upper()
    end_date = airdrop.get("end_date", "未定")
    description = airdrop.get("description", "")
    url = airdrop.get("url", "#")
    tasks = airdrop.get("tasks", [])

    subject = f"🚨 [HOT Airdrop] {name} — 推定${value:,} の新案件が登場！"

    tasks_html = "".join(f"<li>{t}</li>" for t in tasks)

    html_body = f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"></head>
<body style="font-family:'Helvetica Neue',Arial,'Hiragino Sans',Meiryo,sans-serif;
             max-width:620px;margin:0 auto;background:#f4f6f9;padding:16px;">
  <div style="background:linear-gradient(135deg,#c0392b,#e74c3c);color:white;
              padding:24px;border-radius:12px 12px 0 0;">
    <h2 style="margin:0;font-size:20px;">🚨 ホットエアドロップ出現！</h2>
    <p style="margin:4px 0 0;opacity:0.85;font-size:13px;">新しい注目案件を検出しました</p>
  </div>
  <div style="background:white;padding:28px;border-radius:0 0 12px 12px;
              box-shadow:0 4px 20px rgba(0,0,0,0.1);border:1px solid #dee2e6;border-top:none;">
    <h3 style="font-size:22px;margin:0 0 4px;">{name}
      {"<span style='font-size:14px;color:#888;margin-left:6px;'>(" + symbol + ")</span>" if symbol else ""}
    </h3>
    <span style="background:#7c4dff;color:white;padding:3px 10px;border-radius:12px;
                 font-size:12px;font-weight:700;">{category}</span>

    <div style="display:flex;gap:16px;margin:20px 0;flex-wrap:wrap;">
      <div style="background:#eafaf1;border:1px solid #28a745;border-radius:8px;
                  padding:12px 20px;text-align:center;">
        <div style="font-size:26px;font-weight:800;color:#28a745;">~${value:,}</div>
        <div style="font-size:11px;color:#555;">推定価値 (USD)</div>
      </div>
      <div style="background:#ffeef0;border:1px solid #dc3545;border-radius:8px;
                  padding:12px 20px;text-align:center;">
        <div style="font-size:20px;font-weight:800;color:#dc3545;">{difficulty}</div>
        <div style="font-size:11px;color:#555;">難易度</div>
      </div>
      <div style="background:#e8f4fd;border:1px solid #1e90ff;border-radius:8px;
                  padding:12px 20px;text-align:center;">
        <div style="font-size:16px;font-weight:700;color:#1e90ff;">{end_date}</div>
        <div style="font-size:11px;color:#555;">参加期限</div>
      </div>
    </div>

    <p style="color:#333;line-height:1.7;margin:16px 0;">{description}</p>

    {"<h4 style='margin:16px 0 8px;'>📋 参加方法</h4><ul style='margin:0;padding-left:20px;color:#555;'>" + tasks_html + "</ul>" if tasks else ""}

    <div style="text-align:center;margin:28px 0 20px;">
      <a href="{url}"
         style="background:linear-gradient(135deg,#dc3545,#c0392b);color:white;
                padding:14px 32px;border-radius:8px;text-decoration:none;
                font-size:16px;font-weight:700;display:inline-block;">
        🚀 今すぐ参加する
      </a>
    </div>

    <hr style="margin:20px 0;border:none;border-top:1px solid #dee2e6;">
    <p style="color:#999;font-size:11px;margin:0;">
      ※ 投資は自己責任で行ってください。情報は参考目的のみです。
    </p>
  </div>
</body>
</html>"""

    plain_body = (
        f"🚨 ホットエアドロップ出現！\n"
        f"{'=' * 40}\n"
        f"プロジェクト: {name} ({symbol})\n"
        f"推定価値: ~${value:,}\n"
        f"カテゴリ: {category}\n"
        f"難易度: {difficulty}\n"
        f"参加期限: {end_date}\n"
        f"概要: {description}\n"
        + (f"\n参加方法:\n" + "\n".join(f"  • {t}" for t in tasks) + "\n" if tasks else "")
        + f"\nURL: {url}\n"
    )

    return subject, plain_body, html_body
