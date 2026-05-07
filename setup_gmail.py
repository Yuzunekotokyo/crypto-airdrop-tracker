"""
Gmail アプリパスワードの設定ガイドと接続テスト

使用方法:
  python setup_gmail.py
"""

import sys


def print_setup_guide():
    print("""
========================================
 Gmail アプリパスワード 設定ガイド
========================================

1. Googleアカウントで2段階認証を有効化
   https://myaccount.google.com/security

2. アプリパスワードを生成
   https://myaccount.google.com/apppasswords
   → 「アプリ」= メール、「デバイス」= その他(任意の名前)
   → 生成された16文字のパスワードをコピー

3. .env ファイルを作成 (.env.example をコピーして編集)
   cp .env.example .env

   以下を設定:
   GMAIL_SENDER=あなたのGmailアドレス@gmail.com
   GMAIL_APP_PASSWORD=生成した16文字のパスワード
   GMAIL_RECIPIENT=tsukamoto.kei@gmail.com

4. 接続テスト (このスクリプトを再実行)
   python setup_gmail.py --test

""")


def test_connection():
    import os
    from dotenv import load_dotenv
    load_dotenv()

    sender = os.getenv("GMAIL_SENDER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    recipient = os.getenv("GMAIL_RECIPIENT", "tsukamoto.kei@gmail.com")

    if not sender or not password:
        print("ERROR: .env に GMAIL_SENDER と GMAIL_APP_PASSWORD を設定してください")
        sys.exit(1)

    print(f"送信元: {sender}")
    print(f"送信先: {recipient}")
    print("接続テスト中...")

    import smtplib
    from email.mime.text import MIMEText
    msg = MIMEText("Crypto Airdrop Tracker の Gmail 接続テストです。\nこのメールが届いたら設定は完了です！", "plain", "utf-8")
    msg["Subject"] = "[Airdrop Tracker] 接続テスト"
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        print(f"SUCCESS: テストメールを {recipient} に送信しました！")
    except smtplib.SMTPAuthenticationError:
        print("ERROR: 認証失敗。アプリパスワードが正しいか確認してください。")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        test_connection()
    else:
        print_setup_guide()
