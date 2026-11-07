#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BCPダッシュボード 定期データ収集スクリプト (GitHub Actions / ローカル両用)
PCが起動していなくても、GitHub Actionsで定期実行（cron）されて
最新の防災・危機管理データをJSONとして data/ ディレクトリに出力します。
"""

import os
import sys
import json
import time
from datetime import datetime
import pytz

# カレントディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    import backend_server
except ImportError as e:
    print(f"[ERROR] backend_server.py のインポートに失敗しました: {e}")
    sys.exit(1)

# 出力先ディレクトリ
DATA_DIR = os.path.join(current_dir, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 収集対象エリア（主要拠点・全地方中枢都市を網羅）
TARGET_LOCATIONS = [
    "all",       # 全国
    "tokyo",     # 東京 (関東)
    "osaka",     # 大阪 (近畿)
    "nagoya",    # 名古屋 (東海)
    "fukuoka",   # 福岡 (九州)
    "sapporo",   # 札幌 (北海道)
    "sendai",    # 仙台 (東北)
    "hiroshima", # 広島 (中国)
    "naha"       # 那覇 (沖縄)
]

# 収集対象国（主要渡航先・出張先・サプライチェーン拠点）
TARGET_COUNTRIES = [
    "uk",        # イギリス
    "us",        # アメリカ
    "cn",        # 中国
    "kr",        # 韓国
    "tw",        # 台湾
    "fr",        # フランス
    "de",        # ドイツ
    "it",        # イタリア
    "au",        # オーストラリア
    "sg",        # シンガポール
    "th",        # タイ
    "vn",        # ベトナム
    "my",        # マレーシア
    "ph",        # フィリピン
    "in",        # インド
    "ca"         # カナダ
]


def save_json(filepath, data):
    """安全にJSONをUTF-8で保存（一時ファイル経由のアトミック書き込み）"""
    temp_path = f"{filepath}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if os.path.exists(filepath):
        os.remove(filepath)
    os.rename(temp_path, filepath)


def export_country_list():
    """全200カ国のメタデータ一覧をJSON出力"""
    print("[1/3] 海外国メタデータ一覧を出力中...")
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
    print("\n[2/3] 国内災害データを収集開始...")
    locations = ["all", "tokyo", "osaka"] if quick_mode else TARGET_LOCATIONS
    default_keywords = ["au 障害", "KDDI 障害", "通信 障害", "新幹線 遅延"]

    success_count = 0
    for loc_key in locations:
        t0 = time.time()
        print(f" -> 国内エリア収集中: {loc_key} ...", end="", flush=True)
        try:
            data = backend_server.analyzer.collect_all_metrics(
                location_key=loc_key,
                keywords=default_keywords
            )
            # クラウド収集フラグを付与
            data["collected_by"] = "GitHub Actions"
            dest = os.path.join(DATA_DIR, f"bcp_data_{loc_key}.json")
            save_json(dest, data)
            elapsed = time.time() - t0
            print(f" [OK] ({elapsed:.1f}s)")
            success_count += 1
        except Exception as e:
            print(f" [NG] エラー: {e}")

    return success_count, len(locations)


def collect_overseas_data(quick_mode=False):
    """海外主要国の危機管理データを収集・保存"""
    print("\n[3/3] 海外危機管理データを収集開始...")
    countries = ["uk", "us", "cn"] if quick_mode else TARGET_COUNTRIES

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
            elapsed = time.time() - t0
            print(f" [OK] ({elapsed:.1f}s)")
            success_count += 1
        except Exception as e:
            print(f" [NG] エラー: {e}")

    return success_count, len(countries)


def main():
    quick_mode = "--quick" in sys.argv
    start_time = datetime.now()
    jst = pytz.timezone("Asia/Tokyo")
    now_jst = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S JST")
    now_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    print("=" * 60)
    print(f" BCP Dashboard 定期データ収集バッチ (モード: {'QUICK' if quick_mode else 'FULL'})")
    print(f" 開始時刻: {now_jst}")
    print("=" * 60)

    # 1. 国リストメタデータ
    export_country_list()

    # 2. 国内データ収集
    dom_ok, dom_total = collect_domestic_data(quick_mode)

    # 3. 海外データ収集
    ovs_ok, ovs_total = collect_overseas_data(quick_mode)

    # メタデータ出力
    meta_path = os.path.join(DATA_DIR, "metadata.json")
    save_json(meta_path, {
        "last_updated_jst": now_jst,
        "last_updated_utc": now_utc,
        "mode": "quick" if quick_mode else "full",
        "domestic": {"success": dom_ok, "total": dom_total},
        "overseas": {"success": ovs_ok, "total": ovs_total},
        "locations": ["all", "tokyo", "osaka"] if quick_mode else TARGET_LOCATIONS,
        "countries": ["uk", "us", "cn"] if quick_mode else TARGET_COUNTRIES
    })

    total_elapsed = (datetime.now() - start_time).total_seconds()
    print("=" * 60)
    print(f" [完了] 全データ収集完了！ 所要時間: {total_elapsed:.1f} 秒")
    print(f" 国内: {dom_ok}/{dom_total} 成功 | 海外: {ovs_ok}/{ovs_total} 成功")
    print(f" 出力先: {DATA_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
