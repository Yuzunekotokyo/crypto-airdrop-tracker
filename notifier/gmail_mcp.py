"""
Gmail MCPを使ったメール下書き作成モジュール。
SMTPが設定されていない場合のフォールバックとして使用。
このモジュールはエージェント環境からのみ呼び出せる（MCP依存）。
"""

import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def build_update_summary(airdrops: list[dict], new_items: list[str], trending: list[dict], diff: dict = None) -> str:
    """更新サマリーテキストを生成（メール・通知用）"""
    today = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    hot = [a for a in airdrops if a.get("is_hot")]

    lines = [f"=== Crypto Airdrop Tracker 更新レポート {today} ===\n"]

    if new_items:
        lines.append(f"🆕 新着エアドロップ ({len(new_items)}件):")
        for n in new_items:
            lines.append(f"  • {n}")
        lines.append("")

    lines.append(f"🔥 ホット案件 ({len(hot)}件):")
    for a in hot[:5]:
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        lines.append(f"  • {a['name']} ({a.get('category','')}) — {value} [{a.get('difficulty','').upper()}]")
        lines.append(f"    {a.get('description', '')[:80]}...")
        lines.append(f"    URL: {a.get('url','')}")
    lines.append("")

    if trending:
        lines.append("📈 CoinGecko トレンドコイン:")
        for t in trending[:5]:
            lines.append(f"  • {t['name']} ({t['symbol']})")
        lines.append("")

    lines.append(f"📊 合計: {len(airdrops)}件のエアドロップを追跡中")
    lines.append("\n※ 投資は自己責任で行ってください。")

    return "\n".join(lines)


def build_html_draft(airdrops: list[dict], new_items: list[str], trending: list[dict]) -> str:
    """HTMLメール本文を生成"""
    today = datetime.now().strftime("%Y年%m月%d日")
    hot = [a for a in airdrops if a.get("is_hot")]

    new_html = ""
    if new_items:
        items_li = "".join(f"<li style='margin:4px 0;'><strong>{n}</strong></li>" for n in new_items)
        new_html = f"""
        <div style="background:linear-gradient(135deg,#0d4a1a,#1a3a0d);border:1px solid #2ed573;border-left:4px solid #2ed573;padding:16px;margin:16px 0;border-radius:8px;">
          <strong style="color:#2ed573;font-size:15px;">🆕 新着エアドロップ ({len(new_items)}件)</strong>
          <ul style="margin:10px 0 0 0;color:#e8eaf6;">{items_li}</ul>
        </div>"""

    hot_rows = ""
    for a in hot[:6]:
        diff_color = {"easy": "#2ed573", "medium": "#ff6348", "hard": "#ff4757"}.get(
            a.get("difficulty", "easy"), "#9fa8da"
        )
        value = f"~${a.get('estimated_value_usd', 0):,}" if a.get("estimated_value_usd") else "未定"
        tasks_html = "".join(f"<li style='font-size:11px;color:#9fa8da;margin:2px 0;'>{t}</li>" for t in a.get("tasks", [])[:3])
        hot_rows += f"""
        <tr>
          <td style="padding:12px;border-bottom:1px solid #2e3460;vertical-align:top;">
            <div style="font-weight:700;color:#e8eaf6;">{a['name']}</div>
            <div style="font-size:11px;color:#7c4dff;margin-top:2px;">{a.get('category','')}</div>
            <ul style="margin:6px 0 0 16px;padding:0;">{tasks_html}</ul>
          </td>
          <td style="padding:12px;border-bottom:1px solid #2e3460;color:#2ed573;font-weight:800;font-size:16px;white-space:nowrap;">{value}</td>
          <td style="padding:12px;border-bottom:1px solid #2e3460;">
            <span style="background:{diff_color}22;color:{diff_color};border:1px solid {diff_color};padding:3px 8px;border-radius:12px;font-size:11px;font-weight:700;">
              {a.get('difficulty','').upper()}
            </span>
          </td>
          <td style="padding:12px;border-bottom:1px solid #2e3460;color:#9fa8da;font-size:12px;">{a.get('end_date','未定')}</td>
          <td style="padding:12px;border-bottom:1px solid #2e3460;">
            <a href="{a.get('url','#')}" style="background:#7c4dff;color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:700;">参加する</a>
          </td>
        </tr>"""

    trending_html = ""
    if trending:
        t_items = "".join(
            f"<li style='margin:4px 0;color:#e8eaf6;'><strong>{t['name']}</strong> <span style='color:#9fa8da;'>({t['symbol']})</span></li>"
            for t in trending[:5]
        )
        trending_html = f"""
        <div style="margin-top:20px;">
          <h3 style="color:#7c4dff;margin:0 0 10px 0;">📈 CoinGecko トレンドコイン</h3>
          <ul style="margin:0;padding-left:20px;">{t_items}</ul>
        </div>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="font-family:'Segoe UI','Hiragino Sans',Arial,sans-serif;background:#0f0f1a;color:#e8eaf6;margin:0;padding:20px;">
  <div style="max-width:700px;margin:0 auto;">
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:28px;border-radius:12px 12px 0 0;border-bottom:3px solid #7c4dff;">
      <h1 style="margin:0;font-size:24px;background:linear-gradient(135deg,#fff,#7c4dff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🪂 Crypto Airdrop Tracker</h1>
      <p style="margin:6px 0 0;color:#9fa8da;font-size:14px;">{today} 日次更新レポート</p>
      <div style="margin-top:12px;">
        <span style="background:rgba(255,71,87,0.2);border:1px solid #ff4757;color:#ff6b81;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;margin-right:8px;">🔥 ホット {len(hot)}件</span>
        <span style="background:rgba(46,213,115,0.2);border:1px solid #2ed573;color:#2ed573;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;margin-right:8px;">📋 合計 {len(airdrops)}件</span>
        {f'<span style="background:rgba(46,213,115,0.2);border:1px solid #2ed573;color:#2ed573;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;">🆕 新着 {len(new_items)}件</span>' if new_items else ''}
      </div>
    </div>

    <div style="background:#16213e;padding:24px;border-radius:0 0 12px 12px;border:1px solid #2e3460;border-top:none;">
      {new_html}

      <h3 style="color:#ff6b81;margin:0 0 12px 0;font-size:16px;">🔥 注目のホットエアドロップ</h3>
      <div style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;background:#1e2240;border-radius:8px;overflow:hidden;">
          <thead>
            <tr style="background:#1a1a2e;">
              <th style="padding:12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:1px;border-bottom:2px solid #2e3460;">プロジェクト / 参加方法</th>
              <th style="padding:12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:1px;border-bottom:2px solid #2e3460;">推定価値</th>
              <th style="padding:12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:1px;border-bottom:2px solid #2e3460;">難易度</th>
              <th style="padding:12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:1px;border-bottom:2px solid #2e3460;">期限</th>
              <th style="padding:12px;text-align:left;color:#9fa8da;font-size:11px;text-transform:uppercase;letter-spacing:1px;border-bottom:2px solid #2e3460;">リンク</th>
            </tr>
          </thead>
          <tbody>{hot_rows}</tbody>
        </table>
      </div>

      {trending_html}

      <div style="margin-top:24px;padding-top:16px;border-top:1px solid #2e3460;">
        <p style="color:#9fa8da;font-size:11px;margin:0;line-height:1.6;">
          ※ このメールはCrypto Airdrop Trackerから自動送信されています。<br>
          ※ 掲載情報は参考目的のみです。投資は必ず自己責任で行ってください。<br>
          ※ エアドロップは詐欺リスクがあります。公式サイトを必ず確認してください。
        </p>
      </div>
    </div>
  </div>
</body>
</html>"""
