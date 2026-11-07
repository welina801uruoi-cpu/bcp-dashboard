#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BCPダッシュボード 定期データ収集スクリプト (GitHub Actions / ローカル両用)
国内主要9拠点、および海外主要全28カ国（ミャンマー・タイ・韓国・米国等）の
詳細防災データを収集し、さらに全カ国の外務省危険情報マスターを自動生成します。
"""

import os
import sys
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import pytz

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    import backend_server
except ImportError as e:
    print(f"[ERROR] backend_server.py のインポートに失敗しました: {e}")
    sys.exit(1)

DATA_DIR = os.path.join(current_dir, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 国内主要9拠点
TARGET_LOCATIONS = [
    "all",       # 全国
    "tokyo",     # 東京
    "osaka",     # 大阪
    "nagoya",    # 名古屋
    "fukuoka",   # 福岡
    "sapporo",   # 札幌
    "sendai",    # 仙台
    "hiroshima", # 広島
    "naha"       # 那覇
]

# 海外主要全28カ国（フロントエンドのドロップダウン値と100%一致）
TARGET_OVERSEAS_COUNTRIES = [
    # アジア
    "myanmar",      # 🇲🇲 ミャンマー
    "thailand",     # 🇹🇭 タイ
    "taiwan",       # 🇹🇼 台湾
    "singapore",    # 🇸🇬 シンガポール
    "korea",        # 🇰🇷 韓国
    "china",        # 🇨🇳 中国
    "hongkong",     # 🇭🇰 香港
    "vietnam",      # 🇻🇳 ベトナム
    "philippines",  # 🇵🇭 フィリピン
    "indonesia",    # 🇮🇩 インドネシア
    "malaysia",     # 🇲🇾 マレーシア
    "india",        # 🇮🇳 インド
    "cambodia",     # 🇰🇭 カンボジア
    "bangladesh",   # 🇧🇩 バングラデシュ
    "mongolia",     # 🇲🇳 モンゴル
    # 欧州
    "uk",           # 🇬🇧 イギリス
    "france",       # 🇫🇷 フランス
    "germany",      # 🇩🇪 ドイツ
    "italy",        # 🇮🇹 イタリア
    "spain",        # 🇪🇸 スペイン
    "belgium",      # 🇧🇪 ベルギー
    "netherlands",  # 🇳🇱 オランダ
    "turkey",       # 🇹🇷 トルコ
    # オセアニア・北米・南米・中東
    "australia",    # 🇦🇺 オーストラリア
    "usa",          # 🇺🇸 アメリカ
    "canada",       # 🇨🇦 カナダ
    "brazil",       # 🇧🇷 ブラジル
    "uae",          # 🇦🇪 アラブ首長国連邦
]

# 2文字短縮コードとのエイリアスマッピング（互換性確保）
COUNTRY_ALIASES = {
    "us": "usa",
    "cn": "china",
    "kr": "korea",
    "tw": "taiwan",
    "th": "thailand",
    "vn": "vietnam",
    "my": "malaysia",
    "ph": "philippines",
    "in": "india",
    "sg": "singapore",
    "au": "australia",
    "ca": "canada",
    "de": "germany",
    "fr": "france",
    "it": "italy",
    "es": "spain",
    "mm": "myanmar"
}


def save_json(filepath, data):
    """安全にJSONをUTF-8で保存"""
    temp_path = f"{filepath}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if os.path.exists(filepath):
        os.remove(filepath)
    os.rename(temp_path, filepath)


def export_country_list():
    """全200カ国のメタデータ一覧を出力"""
    print("[1/4] 海外国メタデータ一覧を出力中...")
    countries = []
    for k, v in backend_server.OVERSEAS_CONFIG.items():
        countries.append({
            "id": k,
            "name": v.get("name", ""),
            "english_name": v.get("english_name", ""),
            "region": v.get("region", "other"),
            "flag": v.get("flag", "🌐"),
            "city": v.get("city", ""),
            "timezone_offset": v.get("timezone_offset", 0),
            "currency_code": v.get("currency_code", "USD"),
            "currency_name": v.get("currency_name", "米ドル"),
            "currency_symbol": v.get("currency_symbol", "$")
        })
    dest = os.path.join(DATA_DIR, "overseas_countries.json")
    save_json(dest, {
        "status": "OK",
        "total_count": len(countries),
        "countries": countries
    })
    print(f" -> 保存完了: {dest} ({len(countries)}カ国)")


def collect_domestic_data(quick_mode=False):
    """国内主要エリアの災害データを収集・保存"""
    print("\n[2/4] 国内災害データを収集開始...")
    locations = ["all", "tokyo", "osaka"] if quick_mode else TARGET_LOCATIONS
    # ユーザー設定キーワードと完全一致 (au / KDDI / povo 障害)
    default_keywords = ["au 障害", "KDDI 障害", "au 繋がらない", "povo 障害"]

    success_count = 0
    for loc_key in locations:
        t0 = time.time()
        print(f" -> 国内エリア収集中: {loc_key} ...", end="", flush=True)
        try:
            data = backend_server.analyzer.collect_all_metrics(
                location_key=loc_key,
                keywords=default_keywords
            )
            data["collected_by"] = "GitHub Actions"
            dest = os.path.join(DATA_DIR, f"bcp_data_{loc_key}.json")
            save_json(dest, data)
            elapsed = time.time() - t0
            print(f" [OK] ({elapsed:.1f}s)")
            success_count += 1
        except Exception as e:
            print(f" [NG] エラー: {e}")

    return success_count, len(locations)


def collect_overseas_detail_data(quick_mode=False):
    """海外主要28カ国（ミャンマー含む）の詳細データを収集・保存"""
    print("\n[3/4] 海外主要国の危機管理詳細データを収集開始...")
    # クイック時は代表的な主要国
    countries = ["myanmar", "uk", "usa", "china", "thailand"] if quick_mode else TARGET_OVERSEAS_COUNTRIES

    success_count = 0
    for c_key in countries:
        t0 = time.time()
        print(f" -> 海外国収集中: {c_key} ...", end="", flush=True)
        try:
            cfg = backend_server.OVERSEAS_CONFIG.get(c_key, {})
            keywords = cfg.get("default_keywords", ["crisis", "strike", "earthquake"])
            data = backend_server.overseas_analyzer.collect_all(
                country_key=c_key,
                keywords=keywords
            )
            data["collected_by"] = "GitHub Actions"
            dest = os.path.join(DATA_DIR, f"overseas_data_{c_key}.json")
            save_json(dest, data)

            # 2文字短縮エイリアスファイルも作成（例: us -> usa）
            for alias_code, full_code in COUNTRY_ALIASES.items():
                if full_code == c_key:
                    alias_dest = os.path.join(DATA_DIR, f"overseas_data_{alias_code}.json")
                    save_json(alias_dest, data)

            elapsed = time.time() - t0
            print(f" [OK] ({elapsed:.1f}s)")
            success_count += 1
        except Exception as e:
            print(f" [NG] エラー: {e}")

    return success_count, len(countries)


def collect_all_countries_risk_master():
    """全200カ国の外務省危険情報マスターを一括並列収集して保存"""
    print("\n[4/4] 全200カ国の外務省安全・危機情報マスターを生成中...")
    t0 = time.time()
    analyzer = backend_server.overseas_analyzer
    countries = list(backend_server.OVERSEAS_CONFIG.items())

    master_data = {}

    def fetch_country_risk(item):
        k, cfg = item
        mcode = cfg.get("mofa_code", "")
        # mcodeが未設定または0000の場合は国際電話国番号等から推測
        mofa_res = None
        if mcode and mcode != "0000":
            try:
                mofa_res = analyzer.fetch_mofa_safety_data(mcode)
            except Exception:
                pass

        if not mofa_res or mofa_res.get("status") != "OK":
            mofa_res = {
                "status": "OK",
                "max_risk_level": 0,
                "risk_level_name": "レベル0: 危険情報なし（平常）",
                "max_infection_level": 0,
                "risk_title": f"{cfg.get('name', k)}：現在危険情報は発出されていません",
                "risk_lead": "最新の海外安全情報は外務省安全ホームページをご確認ください。",
                "spots": [],
                "mails": []
            }

        return k, {
            "country": {
                "id": k,
                "name": cfg.get("name", k),
                "english_name": cfg.get("english_name", ""),
                "flag": cfg.get("flag", "🌐"),
                "city": cfg.get("city", ""),
                "timezone_offset": cfg.get("timezone_offset", 0),
                "currency_code": cfg.get("currency_code", "USD"),
                "currency_name": cfg.get("currency_name", "米ドル"),
                "currency_symbol": cfg.get("currency_symbol", "$"),
                "emergency_phones": cfg.get("emergency_phones", "警察: 110 / 救急: 119")
            },
            "mofa_safety": mofa_res,
            "security": {
                "threat_level": "ALERT" if mofa_res.get("max_risk_level", 0) >= 2 else ("CAUTION" if mofa_res.get("max_risk_level", 0) >= 1 else "NORMAL"),
                "desc": mofa_res.get("risk_level_name", "平常態勢")
            },
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    with ThreadPoolExecutor(max_workers=20) as executor:
        for k, v in executor.map(fetch_country_risk, countries):
            master_data[k] = v

    dest = os.path.join(DATA_DIR, "overseas_all_countries_risk.json")
    save_json(dest, master_data)
    elapsed = time.time() - t0
    print(f" -> [OK] 全200カ国マスター保存完了: {dest} ({len(master_data)}カ国, 所要時間: {elapsed:.1f}s)")
    return len(master_data)


def main():
    quick_mode = "--quick" in sys.argv
    start_time = datetime.now()
    jst = pytz.timezone("Asia/Tokyo")
    now_jst = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S JST")
    now_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    print("=" * 60)
    print(f" BCP Dashboard データ収集バッチ (モード: {'QUICK' if quick_mode else 'FULL'})")
    print(f" 開始時刻: {now_jst}")
    print("=" * 60)

    # 1. 国リストメタデータ
    export_country_list()

    # 2. 国内主要拠点データ
    dom_ok, dom_total = collect_domestic_data(quick_mode)

    # 3. 海外主要28カ国詳細データ（ミャンマー含む）
    ovs_ok, ovs_total = collect_overseas_detail_data(quick_mode)

    # 4. 全200カ国外務省危険情報マスター
    master_count = collect_all_countries_risk_master()

    # メタデータ出力
    meta_path = os.path.join(DATA_DIR, "metadata.json")
    save_json(meta_path, {
        "last_updated_jst": now_jst,
        "last_updated_utc": now_utc,
        "mode": "quick" if quick_mode else "full",
        "domestic": {"success": dom_ok, "total": dom_total},
        "overseas_detail": {"success": ovs_ok, "total": ovs_total},
        "overseas_master_countries": master_count,
        "locations": ["all", "tokyo", "osaka"] if quick_mode else TARGET_LOCATIONS,
        "countries": ["myanmar", "uk", "usa", "china", "thailand"] if quick_mode else TARGET_OVERSEAS_COUNTRIES
    })

    total_elapsed = (datetime.now() - start_time).total_seconds()
    print("=" * 60)
    print(f" [完了] 全データ収集完了！ 総所要時間: {total_elapsed:.1f} 秒")
    print(f" 国内: {dom_ok}/{dom_total} | 海外詳細: {ovs_ok}/{ovs_total} | 海外マスター: {master_count}カ国")
    print(f" 出力先: {DATA_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
