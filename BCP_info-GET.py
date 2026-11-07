import argparse
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# -------------------------------------------------------------------
# 1. 全国10エリアおよび全一次情報URLマッピング
# -------------------------------------------------------------------

REGION_CONFIG = {
    "北海道": {
        "prefs": ["北海道"],
        "water": ("札幌市水道局", "https://www.city.sapporo.jp/suido/"),
        "gas": ("北海道ガス", "https://www.hokkaidogas.co.jp/"),
        "transit": "https://transit.yahoo.co.jp/diainfo/area/2",
        "highway": ("NEXCO東日本", "https://www.e-nexco.co.jp/")
    },
    "東北": {
        "prefs": ["青森", "岩手", "秋田", "宮城", "山形", "福島"],
        "water": ("仙台市水道局", "https://www.suidou.city.sendai.jp/"),
        "gas": ("仙台市ガス局", "https://www.gas.city.sendai.jp/"),
        "transit": "https://transit.yahoo.co.jp/diainfo/area/3",
        "highway": ("NEXCO東日本", "https://www.e-nexco.co.jp/")
    },
    "北関東": {
        "prefs": ["茨城", "栃木", "群馬", "山梨", "長野"],
        "water": ("東京都水道局", "https://www.waterworks.metro.tokyo.lg.jp/"),
        "gas": ("東京ガス", "https://www.tokyo-gas.co.jp/news/index.html"),
        "transit": "https://transit.yahoo.co.jp/diainfo/area/4",
        "highway": ("NEXCO東日本", "https://www.e-nexco.co.jp/")
    },
    "南関東": {
        "prefs": ["埼玉", "千葉", "東京", "神奈川"],
        "water": ("東京都水道局", "https://www.waterworks.metro.tokyo.lg.jp/"),
        "gas": ("東京ガス", "https://www.tokyo-gas.co.jp/news/index.html"),
        "transit": "https://transit.yahoo.co.jp/diainfo/area/4",
        "highway": ("NEXCO東日本", "https://www.e-nexco.co.jp/")
    },
    "東海": {
        "prefs": ["静岡", "岐阜", "愛知", "三重"],
        "water": ("名古屋市上下水道局", "https://www.water.city.nagoya.jp/"),
        "gas": ("東邦ガス", "https://www.tohogas.co.jp/info/"),
        "transit": "https://transit.yahoo.co.jp/diainfo/area/5",
        "highway": ("NEXCO中日本", "https://www.c-nexco.co.jp/")
    },
    "北陸": {
        "prefs": ["新潟", "富山", "石川", "福井"],
        "water": ("新潟市水道局", "https://www.city.niigata.lg.jp/suidou/"),
        "gas": ("北陸ガス", "https://www.hokurikugas.co.jp/"),
        "transit": "https://transit.yahoo.co.jp/diainfo/area/5",
        "highway": ("NEXCO中日本", "https://www.c-nexco.co.jp/")
    },
    "近畿": {
        "prefs": ["滋賀", "京都", "奈良", "和歌山", "大阪", "兵庫"],
        "water": ("大阪市水道局", "https://www.city.osaka.lg.jp/suido/"),
        "gas": ("大阪ガス", "https://www.osakagas.co.jp/company/press/"),
        "transit": "https://transit.yahoo.co.jp/diainfo/area/6",
        "highway": ("NEXCO西日本", "https://www.w-nexco.co.jp/")
    },
    "中国": {
        "prefs": ["鳥取", "島根", "岡山", "広島", "山口"],
        "water": ("広島市水道局", "https://www.water.city.hiroshima.lg.jp/"),
        "gas": ("広島ガス", "https://www.hiroshima-gas.co.jp/"),
        "transit": "https://transit.yahoo.co.jp/diainfo/area/8",
        "highway": ("NEXCO西日本", "https://www.w-nexco.co.jp/")
    },
    "四国": {
        "prefs": ["徳島", "香川", "愛媛", "高知"],
        "water": ("松山市水道局", "https://www.city.matsuyama.ehime.jp/kurashi/sangyo/suido/"),
        "gas": ("四国ガス", "https://www.shikoku-gas.co.jp/"),
        "transit": "https://transit.yahoo.co.jp/diainfo/area/9",
        "highway": ("NEXCO西日本", "https://www.w-nexco.co.jp/")
    },
    "九州": {
        "prefs": ["福岡", "佐賀", "長崎", "大分", "熊本", "宮崎", "鹿児島"],
        "water": ("福岡市水道局", "https://www.city.fukuoka.lg.jp/mizu/somu/index.html"),
        "gas": ("西部ガス", "https://www.kyugas.co.jp/info/"),
        "transit": "https://transit.yahoo.co.jp/diainfo/area/7",
        "highway": ("NEXCO西日本", "https://www.w-nexco.co.jp/")
    },
    "沖縄": {
        "prefs": ["沖縄"],
        "water": ("沖縄県企業局", "https://www.eb.pref.okinawa.jp/"),
        "gas": ("沖縄ガス", "https://www.okinawagas.co.jp/"),
        "transit": "https://transit.yahoo.co.jp/diainfo/area/7",
        "highway": ("NEXCO西日本", "https://www.w-nexco.co.jp/")
    }
}

# 全エリア共通URL定義
URL_WEATHER_WARN = "https://typhoon.yahoo.co.jp/weather/jp/warn/"
URL_POWER_OUTAGE = "https://typhoon.yahoo.co.jp/weather/poweroutage/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# -------------------------------------------------------------------
# 2. テキスト・ノイズ除去ユーティリティ
# -------------------------------------------------------------------

def fetch_content(url):
    """指定URLからデータ(HTML/XML)を取得"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as res:
            return res.read().decode('utf-8', errors='ignore')
    except Exception:
        return None

def clean_html_to_text(html_content):
    """HTMLからJavaScript/CSS/タグを完全除去してテキストのみを抽出"""
    if not html_content:
        return ""
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_rss(xml_text, target_prefectures=None, max_items=2):
    """RSS/XMLフィードの解析"""
    if not xml_text:
        return []
    results = []
    try:
        root = ET.fromstring(xml_text)
        for item in root.findall('.//item'):
            title = item.findtext('title') or ''
            desc = item.findtext('description') or ''
            full_text = f"{title} {desc}"
            
            clean_title = clean_html_to_text(title)
            if target_prefectures:
                if any(pref in full_text for pref in target_prefectures):
                    results.append(clean_title)
            else:
                results.append(clean_title)
            
            if len(results) >= max_items:
                break
    except Exception:
        pass
    return results

def extract_meaningful_snippets(html_content, keywords, max_items=2):
    """HTMLテキストからノイズを排除してキーワードを含む文章を厳選抽出"""
    if not html_content:
        return []
    
    clean_txt = clean_html_to_text(html_content)
    if not clean_txt:
        return []
    
    exclude_words = ["dataLayer", "var ", "function()", "import", "CSS", "window.", "{", "}", "img.wp-", "has-", "Cookie"]
    sentences = re.split(r'[。！？\n|]', clean_txt)
    results = []

    for sentence in sentences:
        s = sentence.strip()
        if any(ex in s for ex in exclude_words) or len(s) < 6 or len(s) > 180:
            continue
        
        if any(kw in s for kw in keywords):
            if s not in results:
                results.append(s)
            if len(results) >= max_items:
                break

    return results

# -------------------------------------------------------------------
# 3. メイン解析ロジック（全9カテゴリ一元実行）
# -------------------------------------------------------------------

def fetch_all_bcp_info(region_name):
    cfg = REGION_CONFIG.get(region_name)
    if not cfg:
        print(f"エラー: 地域 '{region_name}' の設定が見つかりません。")
        return

    prefs = cfg["prefs"]
    print("=" * 75)
    print(f" 📋 KDDI BCP 総合社会情報 リアルタイム解析 【{region_name}】")
    print(f" 📍 監視対象エリア: {', '.join(prefs)}")
    print("=" * 75)

    # ----------------------------------------------------------------
    # ① 地震・津波・火山・気象・避難
    # ----------------------------------------------------------------
    print("\n【① 地震・津波・火山・気象・避難】")
    
    # 地震 (気象庁全国ポータル)
    eq_url = "https://www.data.jma.go.jp/multi/quake/?lang=jp"
    eq_info = extract_meaningful_snippets(fetch_content(eq_url), ["震度", "地震", "マグニチュード"], max_items=1)
    print(f" ・地震 (気象庁): {eq_info[0] if eq_info else '監視中（特異事項なし）'}")
    
    # 津波 (Yahoo!天気・災害)
    tsunami_url = "https://typhoon.yahoo.co.jp/weather/jp/tsunami/"
    tsunami_info = extract_meaningful_snippets(fetch_content(tsunami_url), ["大津波警報", "津波警報", "津波注意報"], max_items=1)
    print(f" ・津波 (Yahoo!): {tsunami_info[0] if tsunami_info else '現在、津波警報・注意報は発表されていません。'}")
    
    # 火山 (Yahoo!天気・災害)
    volcano_url = "https://typhoon.yahoo.co.jp/weather/jp/volcano/"
    volcano_info = extract_meaningful_snippets(fetch_content(volcano_url), ["噴火警報", "火口周辺規制", "入山規制"], max_items=2)
    print(f" ・火山 (Yahoo!): {' / '.join(volcano_info) if volcano_info else '特筆すべき噴火警報なし'}")

    # 気象警報・注意報 (Yahoo!全国統一ポータル)
    warn_info = extract_meaningful_snippets(fetch_content(URL_WEATHER_WARN), prefs + ["特別警報", "警報", "注意報"], max_items=2)
    print(f" ・気象警報 (Yahoo! - {URL_WEATHER_WARN}): {' / '.join(warn_info) if warn_info else '発表中の特別警報・警報なし'}")

    # 避難情報 (Yahoo!防災速報ポータル)
    evac_url = "https://crisis.yahoo.co.jp/evacuation/"
    evac_info = extract_meaningful_snippets(fetch_content(evac_url), prefs + ["緊急安全確保", "避難指示", "高齢者等避難", "避難所開設"], max_items=2)
    print(f" ・避難情報 (Yahoo!): {' / '.join(evac_info) if evac_info else '発令中の避難指示なし'}")

    # ----------------------------------------------------------------
    # ② 河川（国土交通省 川の防災情報）
    # ----------------------------------------------------------------
    print("\n【② 河川情報】")
    river_url = "https://www.river.go.jp/index"
    river_info = extract_meaningful_snippets(fetch_content(river_url), prefs + ["氾濫危険", "氾濫発生", "氾濫注意", "避難判断", "水位"], max_items=2)
    print(f" ・川の防災情報 (国交省 - {river_url}): {' / '.join(river_info) if river_info else '指定河川での重大な氾濫危険・水害発生なし（正常）'}")

    # ----------------------------------------------------------------
    # ③ 原子力（原子力規制委員会 緊急時情報）
    # ----------------------------------------------------------------
    print("\n【③ 原子力情報】")
    nra_url = "https://kinkyu.nra.go.jp/"
    nra_info = extract_meaningful_snippets(fetch_content(nra_url), ["緊急事態", "警戒態勢", "放射能", "モニタリング", "異常", "事故"], max_items=2)
    print(f" ・原子力緊急時情報 (NRA - {nra_url}): {nra_info[0] if nra_info else '現在、原子力施設における緊急事態・異常は発表されていません（平常）'}")

    # ----------------------------------------------------------------
    # ④ 警察・消防
    # ----------------------------------------------------------------
    print("\n【④ 警察・消防】")
    
    # 消防庁 (全国RSS)
    fdma_xml_url = "https://www.fdma.go.jp/disaster/info/index.xml"
    fdma_news = parse_rss(fetch_content(fdma_xml_url), target_prefectures=prefs, max_items=1)
    if not fdma_news:
        fdma_news = parse_rss(fetch_content(fdma_xml_url), max_items=1)
    print(f" ・消防庁 (RSS): {fdma_news[0] if fdma_news else '直近の重大災害発表なし（平常）'}")

    # 警察庁
    npa_url = "https://www.npa.go.jp/"
    npa_info = extract_meaningful_snippets(fetch_content(npa_url), ["通行止め", "緊急交通路", "災害", "通行規制"], max_items=1)
    print(f" ・警察庁: {npa_info[0] if npa_info else '緊急交通路指定・通行止め規制なし'}")

    # ----------------------------------------------------------------
    # ⑤ 拠点ライフライン (電力・水道・ガス)
    # ----------------------------------------------------------------
    print("\n【⑤ 拠点ライフライン】")
    
    # 電力 (Yahoo!停電情報 全国統一ポータル)
    power_info = extract_meaningful_snippets(fetch_content(URL_POWER_OUTAGE), prefs + ["停電", "軒", "発生"], max_items=1)
    print(f" ・電力 (Yahoo!停電 - {URL_POWER_OUTAGE}): {power_info[0] if power_info else '大規模停電情報なし（平常）'}")
    
    # 水道 (主要拠点水道局)
    water_name, water_url = cfg["water"]
    water_info = extract_meaningful_snippets(fetch_content(water_url), ["断水", "漏水", "緊急", "給水", "派遣"], max_items=1)
    print(f" ・水道 ({water_name} - {water_url}): {water_info[0] if water_info else '大規模断水・給水制限なし（正常）'}")

    # ガス (主要都市ガスポータル)
    gas_name, gas_url = cfg["gas"]
    gas_info = extract_meaningful_snippets(fetch_content(gas_url), ["供給停止", "遮断", "復旧", "緊急", "地震"], max_items=1)
    print(f" ・ガス ({gas_name} - {gas_url}): {gas_info[0] if gas_info else '大規模供給停止なし（供給安定）'}")

    # ----------------------------------------------------------------
    # ⑥ 拠点交通網 (鉄道・高速道路)
    # ----------------------------------------------------------------
    print("\n【⑥ 拠点交通網】")
    
    # 鉄道 (Yahoo!路線情報 エリア別)
    transit_url = cfg["transit"]
    transit_html = fetch_content(transit_url)
    trouble_lines = []
    if transit_html:
        clean_html = re.sub(r'\s+', ' ', transit_html)
        matches = re.findall(r'<a href="/diainfo/detail/\d+/0/">([^<]+)</a>.*?<td[^>]*>(.*?)</td>', clean_html)
        for line, cell_content in matches:
            status_text = clean_html_to_text(cell_content)
            if "平常" not in status_text and status_text:
                trouble_lines.append(f"{line.strip()}: {status_text}")
    
    if trouble_lines:
        print(f" ・鉄道路線 ({transit_url}):")
        for line_err in trouble_lines[:5]:
            print(f"    - {line_err}")
    else:
        print(f" ・鉄道路線 ({transit_url}): 主要路線で全線平常運行中")

    # 高速道路・道路規制
    hw_name, hw_url = cfg["highway"]
    roadway_url = "https://roadway.yahoo.co.jp/"
    road_info = extract_meaningful_snippets(fetch_content(roadway_url), prefs + ["通行止", "通行止め", "通行不能"], max_items=1)
    print(f" ・高速道路 ({hw_name} / Yahoo!道路): {road_info[0] if road_info else '主要高速道路の広域通行止めなし'}")

    # ----------------------------------------------------------------
    # ⑦ 政府・官公庁 (公式緊急RSS)
    # ----------------------------------------------------------------
    print("\n【⑦ 政府・官公庁】")
    
    # 内閣府 防災情報 RSS
    bousai_xml_url = "https://www.bousai.go.jp/news.xml"
    bousai_news = parse_rss(fetch_content(bousai_xml_url), max_items=1)
    print(f" ・内閣府防災 (RSS): {bousai_news[0] if bousai_news else '直近の非常災害発表なし（平常）'}")

    # 厚生労働省 緊急情報 RSS
    mhlw_rdf_url = "https://www.mhlw.go.jp/stf/news.rdf"
    mhlw_news = parse_rss(fetch_content(mhlw_rdf_url), max_items=1)
    print(f" ・厚生労働省 (RSS): {mhlw_news[0] if mhlw_news else '直近の緊急発表なし（平常）'}")

    # ----------------------------------------------------------------
    # ⑧ 通信事業者 (4キャリア障害速報ポータル)
    # ----------------------------------------------------------------
    print("\n【⑧ 通信事業者 (4キャリア)】")
    
    # KDDI (au/UQ/povo) RSS
    kddi_rss = "https://news.kddi.com/important/news/rss/kddi_important_ex.xml"
    kddi_news = parse_rss(fetch_content(kddi_rss), target_prefectures=prefs, max_items=1)
    if not kddi_news:
        kddi_news = parse_rss(fetch_content(kddi_rss), max_items=1)
    print(f" ・KDDI (au/UQ/povo): {kddi_news[0] if kddi_news else '直近の障害発表なし（正常）'}")

    # NTTドコモ RSS
    docomo_rss = "https://www.docomo.ne.jp/info/rss/network.rdf"
    docomo_news = parse_rss(fetch_content(docomo_rss), target_prefectures=prefs, max_items=1)
    if not docomo_news:
        docomo_news = parse_rss(fetch_content(docomo_rss), max_items=1)
    print(f" ・NTTドコモ: {docomo_news[0] if docomo_news else '直近の障害発表なし（正常）'}")

    # ソフトバンク
    sb_url = "https://www.softbank.jp/mobile/info/personal/important/"
    sb_info = extract_meaningful_snippets(fetch_content(sb_url), ["障害", "影響", "不具合", "ご利用しづらい", "停止"], max_items=1)
    print(f" ・ソフトバンク: {sb_info[0] if sb_info else '直近の障害発表なし（正常）'}")

    # 楽天モバイル
    rakuten_url = "https://network.mobile.rakuten.co.jp/information/failure/"
    rakuten_info = extract_meaningful_snippets(fetch_content(rakuten_url), ["障害", "復旧", "影響", "困難", "不具合"], max_items=1)
    print(f" ・楽天モバイル: {rakuten_info[0] if rakuten_info else '直近の障害発表なし（正常）'}")

    # ----------------------------------------------------------------
    # ⑨ SNSリアルタイム急増監視 (Yahoo!リアルタイム検索)
    # ----------------------------------------------------------------
    print("\n【⑨ SNSリアルタイム急増監視】")
    sample_keywords = ["au 障害", "KDDI 障害", "避難所 Wi-Fi"]
    for kw in sample_keywords:
        encoded_kw = urllib.parse.quote(kw)
        realtime_url = f"https://search.yahoo.co.jp/realtime/search?p={encoded_kw}"
        print(f" ・「{kw}」監視URL: {realtime_url}")

    print("\n" + "=" * 75 + "\n")

# -------------------------------------------------------------------
# 4. エントリーポイント
# -------------------------------------------------------------------

def select_region_interactive():
    print("\n--- BCP 監視地域選択 ---")
    keys = list(REGION_CONFIG.keys())
    for idx, name in enumerate(keys, 1):
        print(f" [{str(idx).rjust(2)}] {name}")
    print(" [ 0] 全地域一括取得")
    print("------------------------")
    
    choice = input("地域の番号を選択してください (0-11): ").strip()
    
    if choice == "0":
        for name in keys:
            fetch_all_bcp_info(name)
    elif choice.isdigit() and 1 <= int(choice) <= len(keys):
        fetch_all_bcp_info(keys[int(choice) - 1])
    else:
        print("番号が無効です。デフォルトで「九州」を取得します。")
        fetch_all_bcp_info("九州")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KDDI BCP 一次情報元直結型 自動解析スクリプト")
    parser.add_argument("--region", type=str, help="地域名（例: 九州, 南関東, 北海道 など）")
    args = parser.parse_args()

    if args.region and args.region in REGION_CONFIG:
        fetch_all_bcp_info(args.region)
    else:
        select_region_interactive()