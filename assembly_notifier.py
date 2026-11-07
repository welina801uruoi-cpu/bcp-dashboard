#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BCP非常参集基準 自動検知 ＆ LINE・メール即時通知モジュール
- 非常参集基準の自動判定:
  1. 一都三県（東京・神奈川・千葉・埼玉）で震度6弱以上
  2. 一都三県以外で震度7以上
  3. 富士山の噴火警戒レベル4以上
- 通知手段:
  - LINE Messaging API (Flex Message リッチカード)
  - メール送信 (HTML & プレーンテキスト / Gmail SMTP)
- 二重送信防止（履歴ファイル管理）
"""

import os
import sys
import re
import json
import smtplib
import urllib.request
import urllib.error
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DISASTER_NOTIFIER_CONFIG = os.path.join(os.path.dirname(BASE_DIR), "disaster_relief_notifier", "config.json")
HISTORY_FILE = os.path.join(BASE_DIR, "data", "assembly_notified_history.json")

DASHBOARD_URL = "https://welina801uruoi-cpu.github.io/bcp-dashboard/"

# KDDI 4大参集拠点
KDDI_FACILITIES = [
    {
        "name": "KDDI 高輪ビル",
        "role": "災害対策本部事務局 拠点",
        "address": "東京都港区高輪3-19-20",
        "station": "品川駅 高輪口 徒歩6分 / 泉岳寺駅 徒歩7分"
    },
    {
        "name": "KDDI 新宿ビル",
        "role": "運用部門 拠点",
        "address": "東京都新宿区西新宿2-3-2",
        "station": "都庁前駅 徒歩3分 / 新宿駅西口 徒歩6分"
    },
    {
        "name": "KDDI 多摩センター",
        "role": "運用部門 拠点",
        "address": "東京都多摩市鶴牧3-5-1",
        "station": "多摩センター駅 徒歩8分"
    },
    {
        "name": "KDDI ガーデンエアータワー",
        "role": "情報システム部門 拠点",
        "address": "東京都千代田区飯田橋3-10-10",
        "station": "飯田橋駅東口 徒歩5分 / 水道橋駅 徒歩4分"
    }
]

KANTO_KEYWORDS = [
    "東京", "東京都", "神奈川", "神奈川県", "千葉", "千葉県", "埼玉", "埼玉県",
    "23区", "多摩", "横浜", "川崎", "相模原", "さいたま", "千葉市"
]


def load_config():
    """設定ファイルの読み込み（ローカル設定、またはdisaster_relief_notifier設定、環境変数による上書き）"""
    config = {
        "line": {"enabled": False, "channel_access_token": "", "to_user_id": ""},
        "mail": {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": True,
            "use_ssl": False,
            "username": "",
            "password": "",
            "from_address": "",
            "to_addresses": [],
            "subject_prefix": "【緊急非常参集】"
        }
    }

    # 1. ローカル config.json または disaster_relief_notifier/config.json を参照
    target_cfg = None
    if os.path.exists(CONFIG_FILE):
        target_cfg = CONFIG_FILE
    elif os.path.exists(DISASTER_NOTIFIER_CONFIG):
        target_cfg = DISASTER_NOTIFIER_CONFIG

    if target_cfg:
        try:
            with open(target_cfg, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if "line" in loaded:
                    config["line"].update(loaded["line"])
                if "mail" in loaded:
                    config["mail"].update(loaded["mail"])
        except Exception as e:
            print(f"[WARN] 設定ファイル読み込み警告 ({target_cfg}): {e}")

    # 2. 環境変数（GitHub Secrets 等）による上書き
    env_line_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    if env_line_token:
        config["line"]["channel_access_token"] = env_line_token.strip()
        config["line"]["enabled"] = True

    env_line_user = os.environ.get("LINE_TO_USER_ID")
    if env_line_user is not None:
        config["line"]["to_user_id"] = env_line_user.strip()

    env_gmail_pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if env_gmail_pwd:
        config["mail"]["password"] = env_gmail_pwd.strip().replace(" ", "")
        config["mail"]["enabled"] = True

    env_gmail_user = os.environ.get("GMAIL_USERNAME") or os.environ.get("GMAIL_FROM_ADDRESS")
    if env_gmail_user:
        config["mail"]["username"] = env_gmail_user.strip()
        config["mail"]["from_address"] = env_gmail_user.strip()

    env_gmail_to = os.environ.get("GMAIL_TO_ADDRESSES")
    if env_gmail_to:
        to_list = [addr.strip() for addr in env_gmail_to.split(",") if addr.strip()]
        if to_list:
            config["mail"]["to_addresses"] = to_list

    return config


def load_history():
    """通知済み履歴の読み込み"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_history(history):
    """通知済み履歴の保存"""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] 履歴保存失敗: {e}")


def is_already_notified(event_id, history):
    """重複チェック"""
    return any(item.get("event_id") == event_id for item in history)


# =========================================================
# 参集基準の判定ロジック
# =========================================================
def evaluate_assembly_criteria(data):
    """
    データ構造から非常参集基準に合致するか判定する
    戻り値: (is_triggered: bool, event_info: dict or None)
    基準:
      #1 一都三県で震度6弱以上
      #2 一都三県以外で震度7
      #3 富士山の噴火警戒レベル4以上
    """
    if not data or not isinstance(data, dict):
        return False, None

    # --- A. 地震の判定 ---
    eq = data.get("earthquake") or {}
    history = eq.get("history") or []
    candidates = []
    if eq.get("shindo"):
        candidates.append({
            "time": eq.get("time", ""),
            "place": eq.get("place", ""),
            "shindo": eq.get("shindo", ""),
            "magnitude": eq.get("magnitude", ""),
            "maxScale": -1
        })
    candidates.extend(history[:5])

    for item in candidates:
        shindo_str = str(item.get("shindo", ""))
        place = str(item.get("place", ""))
        time_str = str(item.get("time", ""))
        scale = item.get("maxScale", -1)

        is_kanto = any(kw in place for kw in KANTO_KEYWORDS)

        # 震度6弱以上: 6弱, 6強, 7 または scale >= 55
        is_shindo6_plus = (
            any(s in shindo_str for s in ["6弱", "6強", "7"]) or
            (isinstance(scale, (int, float)) and scale >= 55)
        )
        # 震度7: '7' または scale >= 70
        is_shindo7 = ("7" in shindo_str) or (isinstance(scale, (int, float)) and scale >= 70)

        if is_kanto and is_shindo6_plus:
            event_id = f"quake_{time_str}_{place}_{shindo_str}".replace(" ", "_")
            return True, {
                "type": "EARTHQUAKE_KANTO_6",
                "event_id": event_id,
                "title": f"🚨【緊急非常参集】一都三県 震度{shindo_str} 検知 ({place})",
                "reason": f"一都三県（{place}）にて震度{shindo_str}（M{item.get('magnitude', '-')})を観測",
                "detail": f"首都圏での震度6弱以上の大地震発生により、BCP第1種非常参集基準に到達しました。全社非常対策態勢へ直ちに移行し、指定の参集拠点へ移動・安否確認を行ってください。",
                "time": time_str or datetime.now().strftime("%Y-%m-%d %H:%M"),
                "place": place,
                "shindo": shindo_str,
                "magnitude": item.get("magnitude", "-")
            }

        if (not is_kanto) and is_shindo7:
            event_id = f"quake_{time_str}_{place}_7".replace(" ", "_")
            return True, {
                "type": "EARTHQUAKE_NATIONWIDE_7",
                "event_id": event_id,
                "title": f"🚨【緊急非常参集】全国震度7 極大地震 検知 ({place})",
                "reason": f"一都三県外（{place}）にて最大震度7（M{item.get('magnitude', '-')})を観測",
                "detail": f"国内での震度7極大地震の発生により、全社非常参集基準に到達しました。大規模通信維持・災害復旧のため統括参集体制へ移行してください。",
                "time": time_str or datetime.now().strftime("%Y-%m-%d %H:%M"),
                "place": place,
                "shindo": "7",
                "magnitude": item.get("magnitude", "-")
            }

    # --- B. 富士山噴火警戒レベルの判定 ---
    vol = data.get("volcano") or {}
    v_summary = (vol.get("summary") or "") + " " + (vol.get("status") or "") + " " + (vol.get("detail") or "")
    if "富士山" in v_summary:
        level_match = re.search(r"レベル([1-5])", v_summary)
        if level_match:
            lvl = int(level_match.group(1))
            if lvl >= 4:
                date_str = datetime.now().strftime("%Y%m%d")
                event_id = f"volcano_fuji_level{lvl}_{date_str}"
                return True, {
                    "type": "VOLCANO_FUJI_4PLUS",
                    "event_id": event_id,
                    "title": f"🚨【緊急非常参集】富士山 噴火警戒レベル{lvl} 発表",
                    "reason": f"気象庁より富士山に噴火警戒レベル{lvl}（避難準備・避難）が発表",
                    "detail": f"富士山噴火警戒レベル4以上発令に伴い、降灰・電力遮断・交通麻痺に備えた非常参集基準に合致しました。指定拠点への安全参集態勢を確保してください。",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "place": "富士山",
                    "shindo": "-",
                    "level": lvl
                }

    return False, None


# =========================================================
# LINE 送信ロジック (Flex Message)
# =========================================================
def build_assembly_flex_message(event):
    """非常参集用のLINE Flex Message（リッチデザインカード）を生成"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    reason = event.get("reason", "")
    detail = event.get("detail", "")

    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🚨【緊急非常参集】基準到達アラート",
                    "weight": "bold",
                    "color": "#ffffff",
                    "size": "sm"
                }
            ],
            "backgroundColor": "#dc2626",
            "paddingAll": "12px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": event.get("title", ""),
                    "weight": "bold",
                    "size": "md",
                    "wrap": True,
                    "color": "#991b1b"
                },
                {
                    "type": "text",
                    "text": reason,
                    "size": "xs",
                    "wrap": True,
                    "color": "#374151",
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "md"
                },
                # 拠点案内
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "spacing": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🏢 参集指定拠点 役割",
                            "weight": "bold",
                            "size": "xs",
                            "color": "#111827"
                        },
                        {
                            "type": "text",
                            "text": "・高輪ビル: 災害対策本部事務局 拠点",
                            "size": "xxs",
                            "color": "#b91c1c",
                            "weight": "bold"
                        },
                        {
                            "type": "text",
                            "text": "・新宿 / 多摩センター: 運用部門 拠点",
                            "size": "xxs",
                            "color": "#1e40af"
                        },
                        {
                            "type": "text",
                            "text": "・ガーデンエアータワー: 情報システム部門 拠点",
                            "size": "xxs",
                            "color": "#065f46"
                        }
                    ]
                },
                {
                    "type": "separator",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "⚠️ 大規模地震時は鉄道全線停止が想定されます。ダッシュボードより徒歩・自転車・バイクの安全参集ルートと危険箇所をご確認ください。",
                    "size": "xxs",
                    "wrap": True,
                    "color": "#d97706",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"発信日時: {now_str}",
                    "size": "xxs",
                    "color": "#9ca3af",
                    "margin": "sm"
                }
            ],
            "paddingAll": "14px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#dc2626",
                    "action": {
                        "type": "uri",
                        "label": "🗺️ 参集ルート・危険確認を開く",
                        "uri": DASHBOARD_URL
                    }
                }
            ],
            "paddingAll": "10px"
        }
    }


def send_line_assembly_notification(config, event):
    """LINE Messaging API によるプッシュ送信"""
    line_cfg = config.get("line", {})
    if not line_cfg.get("enabled", False):
        print("[INFO] LINE通知は無効です (line.enabled=false)。")
        return False

    token = line_cfg.get("channel_access_token", "").strip()
    if not token or token == "YOUR_CHANNEL_ACCESS_TOKEN":
        print("[WARN] LINE Channel Access Token が未設定です。")
        return False

    to_user_id = line_cfg.get("to_user_id", "").strip()
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Authorization": f"Bearer {token}"
    }

    alt_text = f"【緊急非常参集】{event.get('title', '')} - 指定拠点へ参集を開始してください"
    flex_contents = build_assembly_flex_message(event)

    payload = {
        "messages": [
            {
                "type": "flex",
                "altText": alt_text[:100],
                "contents": flex_contents
            }
        ]
    }

    if to_user_id:
        url = "https://api.line.me/v2/bot/message/push"
        payload["to"] = to_user_id
    else:
        url = "https://api.line.me/v2/bot/message/broadcast"

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as res:
            if res.status == 200:
                dest = to_user_id if to_user_id else "友だち全員 (ブロードキャスト)"
                print(f"[SUCCESS] LINE非常参集通知 送信完了 -> {dest}")
                return True
            else:
                print(f"[WARN] LINE送信応答ステータス: HTTP {res.status}")
                return False
    except Exception as e:
        print(f"[ERROR] LINE送信失敗: {e}")
        return False


# =========================================================
# メール 送信ロジック (HTML & Text)
# =========================================================
def send_email_assembly_notification(config, event):
    """Gmail SMTP による HTML/Text メール送信"""
    mail_cfg = config.get("mail", {})
    if not mail_cfg.get("enabled", False):
        print("[INFO] メール通知は無効です (mail.enabled=false)。")
        return False

    username = mail_cfg.get("username")
    password = mail_cfg.get("password")
    from_addr = mail_cfg.get("from_address") or username
    to_addrs = mail_cfg.get("to_addresses", [])
    subject_prefix = mail_cfg.get("subject_prefix", "【緊急非常参集】")

    if not to_addrs or not from_addr or not password:
        print("[WARN] メール設定（宛先、差出人、アプリパスワード）が不足しています。")
        return False

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"{subject_prefix} {event.get('title', '参集基準到達')}"

    # テキスト本文
    body_text = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【KDDI BCP 非常参集基準 到達速報】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
気象庁観測データにおいて、KDDI非常参集基準に合致する災害が検知されました。
対象要員は、直ちに安否報告を行い、事前に定められた担当拠点へ安全に参集を開始してください。

■ 基準到達事由:
{event.get('title')}
{event.get('reason')}

■ 詳細内容:
{event.get('detail')}

■ 発生検知時刻:
{event.get('time', now_str)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 参集対象拠点と組織役割
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. KDDI 高輪ビル 【災害対策本部事務局 拠点】
   住所: 東京都港区高輪3-19-20
   最寄: 品川駅 高輪口 徒歩6分 / 泉岳寺駅 徒歩7分

2. KDDI 新宿ビル 【運用部門 拠点】
   住所: 東京都新宿区西新宿2-3-2
   最寄: 都庁前駅 徒歩3分 / 新宿駅西口 徒歩6分

3. KDDI 多摩センター 【運用部門 拠点】
   住所: 東京都多摩市鶴牧3-5-1
   最寄: 多摩センター駅 徒歩8分

4. KDDI ガーデンエアータワー 【情報システム部門 拠点】
   住所: 東京都千代田区飯田橋3-10-10
   最寄: 飯田橋駅東口 徒歩5分 / 水道橋駅 徒歩4分

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 安全参集ルート＆ハザード確認ダッシュボード
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
大震災時は鉄道の運転見合わせが予測されます。
下記ダッシュボードより、徒歩・自転車・バイクの最適移動手段および経路上危険度をご確認ください。

👉 {DASHBOARD_URL}

※このメールはKDDI BCP自動監視通知システムより自動配信されています。
"""

    # HTML本文
    facilities_html = "".join([
        f"""<tr>
          <td style="padding:10px; border-bottom:1px solid #e5e7eb; font-weight:bold; color:#111827;">{f['name']}</td>
          <td style="padding:10px; border-bottom:1px solid #e5e7eb; color:#991b1b; font-weight:bold;">{f['role']}</td>
          <td style="padding:10px; border-bottom:1px solid #e5e7eb; color:#4b5563; font-size:12px;">{f['address']}<br><span style="color:#6b7280;">最寄: {f['station']}</span></td>
        </tr>""" for f in KDDI_FACILITIES
    ])

    body_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #1f2937; margin: 0; padding: 20px; background-color: #f3f4f6; }}
    .container {{ max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 14px rgba(0,0,0,0.1); border: 1px solid #e5e7eb; }}
    .header {{ background: linear-gradient(135deg, #b91c1c, #dc2626); color: #ffffff; padding: 22px 26px; text-align: left; }}
    .header h1 {{ margin: 0; font-size: 20px; font-weight: 800; letter-spacing: 0.5px; }}
    .content {{ padding: 26px; }}
    .alert-box {{ background-color: #fef2f2; border-left: 5px solid #dc2626; padding: 16px; border-radius: 6px; margin-bottom: 22px; }}
    .alert-title {{ font-size: 17px; font-weight: bold; color: #991b1b; margin-bottom: 6px; }}
    .alert-detail {{ font-size: 14px; color: #374151; }}
    .section-title {{ font-size: 15px; font-weight: bold; color: #111827; margin: 20px 0 10px 0; border-bottom: 2px solid #e5e7eb; padding-bottom: 6px; }}
    .table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
    .table th {{ background-color: #f9fafb; padding: 10px; text-align: left; font-size: 13px; color: #6b7280; border-bottom: 2px solid #e5e7eb; }}
    .btn-container {{ text-align: center; margin: 30px 0 16px 0; }}
    .btn {{ display: inline-block; background-color: #dc2626; color: #ffffff !important; font-weight: bold; font-size: 15px; padding: 14px 28px; text-decoration: none; border-radius: 8px; box-shadow: 0 4px 10px rgba(220,38,38,0.3); }}
    .footer {{ background-color: #f9fafb; padding: 16px; font-size: 12px; color: #6b7280; text-align: center; border-top: 1px solid #e5e7eb; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🚨【緊急非常参集】参集基準 到達速報</h1>
    </div>
    <div class="content">
      <div class="alert-box">
        <div class="alert-title">{event.get('title')}</div>
        <div class="alert-detail">{event.get('reason')}<br><br>{event.get('detail')}</div>
      </div>

      <div class="section-title">🏢 参集対象拠点 ＆ 部門役割一覧</div>
      <table class="table">
        <thead>
          <tr>
            <th>拠点名</th>
            <th>部門役割</th>
            <th>所在地・交通</th>
          </tr>
        </thead>
        <tbody>
          {facilities_html}
        </tbody>
      </table>

      <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:6px; padding:12px; font-size:13px; color:#92400e;">
        ⚠️ <strong>交通遮断警戒:</strong> 激甚地震時は鉄道網の全線停止が予測されます。公共交通機関に依存せず、安全な徒歩・自転車・バイクルートを選択してください。
      </div>

      <div class="btn-container">
        <a class="btn" href="{DASHBOARD_URL}" target="_blank">🗺️ 参集ルート検索 ＆ 危険確認を開く</a>
      </div>
    </div>
    <div class="footer">
      検知時刻: {now_str}<br>
      このメールは KDDI BCP 自動危機管理監視システムにより配信されています。
    </div>
  </div>
</body>
</html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    smtp_server = mail_cfg.get("smtp_server", "smtp.gmail.com")
    smtp_port = mail_cfg.get("smtp_port", 587)
    use_tls = mail_cfg.get("use_tls", True)
    use_ssl = mail_cfg.get("use_ssl", False)

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
            if use_tls:
                server.starttls()

        server.login(username, password)
        server.send_message(msg)
        server.quit()
        print(f"[SUCCESS] 非常参集メール送信完了 -> {', '.join(to_addrs)}")
        return True
    except Exception as e:
        print(f"[ERROR] メール送信失敗: {e}")
        return False


# =========================================================
# 統合実行エントリーポイント
# =========================================================
def check_and_notify_assembly(data, force_notify=False):
    """
    データをもとに参集基準を判定し、未送信ならLINEとメールへ通知する
    """
    is_triggered, event = evaluate_assembly_criteria(data)
    if not is_triggered:
        return False

    history = load_history()
    event_id = event.get("event_id", "")

    if not force_notify and is_already_notified(event_id, history):
        print(f"[INFO] 参集事象 {event_id} は既に通知済みです。スキップします。")
        return False

    print(f"\n========================================================")
    print(f"🚨【非常参集基準 到達検知】 LINE・メール通知を開始します")
    print(f" 事象: {event.get('title')}")
    print(f"========================================================")

    config = load_config()

    line_ok = send_line_assembly_notification(config, event)
    mail_ok = send_email_assembly_notification(config, event)

    # 履歴追加
    history.append({
        "event_id": event_id,
        "type": event.get("type"),
        "title": event.get("title"),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "line_sent": line_ok,
        "mail_sent": mail_ok
    })
    save_history(history)
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BCP非常参集基準 自動検知・通知スクリプト")
    parser.add_argument("--test", action="store_true", help="テスト発令を強制送信（LINE/メール疎通テスト）")
    parser.add_argument("--test-volcano", action="store_true", help="富士山噴火レベル4のテスト発令を強制送信")
    args = parser.parse_args()

    if args.test or args.test_volcano:
        print("=== [テストモード] 非常参集通知の強制テスト配信 ===")
        if args.test_volcano:
            mock_data = {
                "earthquake": {"shindo": "1", "place": "平常"},
                "volcano": {"summary": "気象庁発表: 富士山 噴火警戒レベル4（避難準備）"}
            }
        else:
            mock_data = {
                "earthquake": {
                    "shindo": "6強",
                    "place": "東京都多摩東部",
                    "magnitude": "7.3",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                },
                "volcano": {"summary": "平常"}
            }
        cfg = load_config()
        print(f"LINE有効: {cfg['line']['enabled']}, Mail有効: {cfg['mail']['enabled']}")
        check_and_notify_assembly(mock_data, force_notify=True)
    else:
        # data/bcp_data_all.json を読み込んで評価
        data_path = os.path.join(BASE_DIR, "data", "bcp_data_all.json")
        if os.path.exists(data_path):
            with open(data_path, "r", encoding="utf-8") as f:
                d = json.load(f)
            check_and_notify_assembly(d)
        else:
            print(f"データファイルが見つかりません: {data_path}")
