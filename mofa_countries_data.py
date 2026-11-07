# -*- coding: utf-8 -*-
"""
MOFA (外務省) 国・地域一覧データ定義モジュール
https://www.mofa.go.jp/region/index.html に掲載されている全世界の国・地域を網羅。
すでに登録済みの28カ国を除いた全未登録国・地域を定義します。
"""

# 既に登録済みの国キー (28カ国)
ALREADY_REGISTERED_KEYS = {
    'uk', 'france', 'spain', 'germany', 'italy', 'australia', 'cambodia', 
    'bangladesh', 'china', 'hongkong', 'india', 'indonesia', 'korea', 
    'malaysia', 'mongolia', 'myanmar', 'philippines', 'singapore', 
    'taiwan', 'thailand', 'vietnam', 'belgium', 'netherlands', 'turkey', 
    'uae', 'brazil', 'usa', 'canada'
}

# 地域定義 (外務省の7地域区分)
REGIONS = {
    "asia": {"name": "アジア", "icon": "🌏"},
    "oceania": {"name": "大洋州", "icon": "🏝️"},
    "north_america": {"name": "北米", "icon": "🗽"},
    "latin_america": {"name": "中南米", "icon": "🌎"},
    "europe": {"name": "欧州", "icon": "🏰"},
    "middle_east": {"name": "中東", "icon": "🕌"},
    "africa": {"name": "アフリカ", "icon": "🌍"}
}

# 外務省掲載の全未登録国・地域マスターリスト
# (国名, 英語名, キー, 地域, 国旗, 首都/主要都市, UTCオフセット, TZ名, 緯度, 経度, 通貨コード, 通貨名, 通貨記号, 警察/救急)
ALL_MOFA_COUNTRIES_RAW = [
    # ==================== 1. アジア (Asia) ====================
    ("スリランカ", "Sri Lanka", "srilanka", "asia", "🇱🇰", "コロンボ", 5.5, "SLST (UTC+5.5)", 6.9271, 79.8612, "LKR", "スリランカ・ルピー", "Rs", "119 / 110"),
    ("ネパール", "Nepal", "nepal", "asia", "🇳🇵", "カトマンズ", 5.75, "NPT (UTC+5.75)", 27.7172, 85.3240, "NPR", "ネパール・ルピー", "रू", "100 / 102"),
    ("パキスタン", "Pakistan", "pakistan", "asia", "🇵🇰", "イスラマバード", 5.0, "PKT (UTC+5)", 33.6844, 73.0479, "PKR", "パキスタン・ルピー", "Rs", "15 / 1122"),
    ("東ティモール", "Timor-Leste", "timor_leste", "asia", "🇹🇱", "ディリ", 9.0, "TLT (UTC+9)", -8.5569, 125.5603, "USD", "米ドル", "$", "112 / 110"),
    ("ブータン", "Bhutan", "bhutan", "asia", "🇧🇹", "ティンプー", 6.0, "BTT (UTC+6)", 27.4728, 89.6393, "BTN", "ニュルタム", "Nu.", "113 / 112"),
    ("ブルネイ", "Brunei", "brunei", "asia", "🇧🇳", "バンダルスリブガワン", 8.0, "BNT (UTC+8)", 4.9031, 114.9398, "BND", "ブルネイ・ドル", "B$", "993 / 991"),
    ("モルディブ", "Maldives", "maldives", "asia", "🇲🇻", "マレ", 5.0, "MVT (UTC+5)", 4.1755, 73.5093, "MVR", "ルフィヤ", "Rf", "119 / 102"),
    ("ラオス", "Lao PDR", "laos", "asia", "🇱🇦", "ビエンチャン", 7.0, "ICT (UTC+7)", 17.9757, 102.6331, "LAK", "キープ", "₭", "1191 / 1195"),
    ("北朝鮮", "North Korea", "north_korea", "asia", "🇰🇵", "平壌", 9.0, "KST (UTC+9)", 39.0392, 125.7625, "KPW", "北朝鮮ウォン", "₩", "110 / 119"),
    ("マカオ", "Macau", "macau", "asia", "🇲🇴", "マカオ", 8.0, "MST (UTC+8)", 22.1987, 113.5439, "MOP", "パタカ", "MOP$", "999 / 993"),

    # ==================== 2. 大洋州 (Oceania) ====================
    ("ニュージーランド", "New Zealand", "new_zealand", "oceania", "🇳🇿", "ウェリントン", 12.0, "NZST (UTC+12)", -41.2865, 174.7762, "NZD", "NZドル", "NZ$", "111"),
    ("フィジー", "Fiji", "fiji", "oceania", "🇫🇯", "スバ", 12.0, "FJT (UTC+12)", -18.1248, 178.4501, "FJD", "フィジー・ドル", "FJ$", "917 / 911"),
    ("パプアニューギニア", "Papua New Guinea", "papua_new_guinea", "oceania", "🇵🇬", "ポートモレスビー", 10.0, "PGT (UTC+10)", -9.4438, 147.1803, "PGK", "キナ", "K", "111 / 112"),
    ("サモア", "Samoa", "samoa", "oceania", "🇼🇸", "アピア", 13.0, "WST (UTC+13)", -13.8333, -171.7667, "WST", "タラ", "WS$", "995 / 996"),
    ("ソロモン諸島", "Solomon Islands", "solomon_islands", "oceania", "🇸🇧", "ホニアラ", 11.0, "SBT (UTC+11)", -9.4456, 159.9729, "SBD", "ソロモン諸島・ドル", "SI$", "999"),
    ("バヌアツ", "Vanuatu", "vanuatu", "oceania", "🇻🇺", "ポートビラ", 11.0, "VUT (UTC+11)", -17.7333, 168.3273, "VUV", "バツ", "VT", "112 / 115"),
    ("トンガ", "Tonga", "tonga", "oceania", "🇹🇴", "ヌクアロファ", 13.0, "TOT (UTC+13)", -21.1790, -175.1982, "TOP", "パアンガ", "T$", "911 / 933"),
    ("パラオ", "Palau", "palau", "oceania", "🇵🇼", "マルキョク", 9.0, "PWT (UTC+9)", 7.5004, 134.6243, "USD", "米ドル", "$", "911"),
    ("ミクロネシア連邦", "Micronesia", "micronesia", "oceania", "🇫🇲", "パリキール", 11.0, "PONT (UTC+11)", 6.9248, 158.1611, "USD", "米ドル", "$", "911"),
    ("マーシャル諸島", "Marshall Islands", "marshall_islands", "oceania", "🇲🇭", "マジュロ", 12.0, "MHT (UTC+12)", 7.1315, 171.1845, "USD", "米ドル", "$", "911"),
    ("キリバス", "Kiribati", "kiribati", "oceania", "🇰🇮", "タラワ", 12.0, "GILT (UTC+12)", 1.3291, 172.9790, "AUD", "豪ドル", "A$", "992 / 994"),
    ("ツバル", "Tuvalu", "tuvalu", "oceania", "🇹🇻", "フナフティ", 12.0, "TVT (UTC+12)", -8.5211, 179.1962, "AUD", "豪ドル", "A$", "911"),
    ("ナウル", "Nauru", "nauru", "oceania", "🇳🇷", "ヤレン", 12.0, "NRT (UTC+12)", -0.5477, 166.9209, "AUD", "豪ドル", "A$", "110 / 111"),
    ("クック諸島", "Cook Islands", "cook_islands", "oceania", "🇨🇰", "アバルア", -10.0, "CKT (UTC-10)", -21.2070, -159.7710, "NZD", "NZドル", "NZ$", "999"),
    ("ニウエ", "Niue", "niue", "oceania", "🇳🇺", "アロフィ", -11.0, "NUT (UTC-11)", -19.0560, -169.9210, "NZD", "NZドル", "NZ$", "999"),

    # ==================== 4. 中南米 (Latin America and the Caribbean) ====================
    ("メキシコ", "Mexico", "mexico", "latin_america", "🇲🇽", "メキシコシティ", -6.0, "CST (UTC-6)", 19.4326, -99.1332, "MXN", "メキシコ・ペソ", "Mex$", "911"),
    ("アルゼンチン", "Argentina", "argentina", "latin_america", "🇦🇷", "ブエノスアイレス", -3.0, "ART (UTC-3)", -34.6037, -58.3816, "ARS", "アルゼンチン・ペソ", "$", "911 / 107"),
    ("チリ", "Chile", "chile", "latin_america", "🇨🇱", "サンティアゴ", -4.0, "CLT (UTC-4)", -33.4489, -70.6693, "CLP", "チリ・ペソ", "$", "133 / 131"),
    ("コロンビア", "Colombia", "colombia", "latin_america", "🇨🇴", "ボゴタ", -5.0, "COT (UTC-5)", 4.7110, -74.0721, "COP", "コロンビア・ペソ", "$", "123"),
    ("ペルー", "Peru", "peru", "latin_america", "🇵🇪", "リマ", -5.0, "PET (UTC-5)", -12.0464, -77.0428, "PEN", "ソル", "S/.", "105 / 106"),
    ("ウルグアイ", "Uruguay", "uruguay", "latin_america", "🇺🇾", "モンテビデオ", -3.0, "UYT (UTC-3)", -34.9011, -56.1645, "UYU", "ウルグアイ・ペソ", "$U", "911 / 105"),
    ("パラグアイ", "Paraguay", "paraguay", "latin_america", "🇵🇾", "アスンシオン", -4.0, "PYT (UTC-4)", -25.2637, -57.5759, "PYG", "グアラニー", "₲", "911"),
    ("ボリビア", "Bolivia", "bolivia", "latin_america", "🇧🇴", "ラパス", -4.0, "BOT (UTC-4)", -16.5000, -68.1500, "BOB", "ボリビアーノ", "Bs.", "110 / 118"),
    ("エクアドル", "Ecuador", "ecuador", "latin_america", "🇪🇨", "キト", -5.0, "ECT (UTC-5)", -0.1807, -78.4678, "USD", "米ドル", "$", "911"),
    ("ベネズエラ", "Venezuela", "venezuela", "latin_america", "🇻🇪", "カラカス", -4.0, "VET (UTC-4)", 10.4806, -66.9036, "VES", "ボリバル", "Bs.S", "911 / 171"),
    ("パナマ", "Panama", "panama", "latin_america", "🇵🇦", "パナマシティ", -5.0, "EST (UTC-5)", 8.9824, -79.5199, "PAB", "バルボア / USD", "B/.", "911 / 104"),
    ("コスタリカ", "Costa Rica", "costa_rica", "latin_america", "🇨🇷", "サンホセ", -6.0, "CST (UTC-6)", 9.9281, -84.0907, "CRC", "コスタリカ・コロン", "₡", "911"),
    ("グアテマラ", "Guatemala", "guatemala", "latin_america", "🇬🇹", "グアテマラシティ", -6.0, "CST (UTC-6)", 14.6349, -90.5069, "GTQ", "ケツァル", "Q", "110 / 123"),
    ("エルサルバドル", "El Salvador", "el_salvador", "latin_america", "🇸🇻", "サンサルバドル", -6.0, "CST (UTC-6)", 13.6929, -89.2182, "USD", "米ドル", "$", "911"),
    ("ホンジュラス", "Honduras", "honduras", "latin_america", "🇭🇳", "テグシガルパ", -6.0, "CST (UTC-6)", 14.0723, -87.1921, "HNL", "レンピラ", "L", "911"),
    ("ニカラグア", "Nicaragua", "nicaragua", "latin_america", "🇳🇮", "マナグア", -6.0, "CST (UTC-6)", 12.1150, -86.2362, "NIO", "コルドバ", "C$", "118 / 128"),
    ("キューバ", "Cuba", "cuba", "latin_america", "🇨🇺", "ハバナ", -5.0, "CST (UTC-5)", 23.1136, -82.3666, "CUP", "キューバ・ペソ", "$", "106 / 104"),
    ("ドミニカ共和国", "Dominican Republic", "dominican_republic", "latin_america", "🇩🇴", "サントドミンゴ", -4.0, "AST (UTC-4)", 18.4861, -69.9312, "DOP", "ドミニカ・ペソ", "RD$", "911"),
    ("ジャマイカ", "Jamaica", "jamaica", "latin_america", "🇯🇲", "キングストン", -5.0, "EST (UTC-5)", 18.0179, -76.8099, "JMD", "ジャマイカ・ドル", "J$", "119 / 110"),
    ("トリニダード・トバゴ", "Trinidad and Tobago", "trinidad_and_tobago", "latin_america", "🇹🇹", "ポートオブスペイン", -4.0, "AST (UTC-4)", 10.6549, -61.5019, "TTD", "TTドル", "TT$", "999 / 811"),
    ("バハマ", "Bahamas", "bahamas", "latin_america", "🇧🇸", "ナッソー", -5.0, "EST (UTC-5)", 25.0480, -77.3554, "BSD", "バハマ・ドル", "B$", "919 / 911"),
    ("バルバドス", "Barbados", "barbados", "latin_america", "🇧🇧", "ブリッジタウン", -4.0, "AST (UTC-4)", 13.1939, -59.5432, "BBD", "バルバドス・ドル", "Bds$", "211 / 511"),
    ("ハイチ", "Haiti", "haiti", "latin_america", "🇭🇹", "ポルトープランス", -5.0, "EST (UTC-5)", 18.5944, -72.3074, "HTG", "グールド", "G", "114 / 118"),
    ("ベリーズ", "Belize", "belize", "latin_america", "🇧🇿", "ベルモパン", -6.0, "CST (UTC-6)", 17.2510, -88.7590, "BZD", "ベリーズ・ドル", "BZ$", "911 / 90"),
    ("ガイアナ", "Guyana", "guyana", "latin_america", "🇬🇾", "ジョージタウン", -4.0, "GYT (UTC-4)", 6.8013, -58.1551, "GYD", "ガイアナ・ドル", "G$", "911 / 913"),
    ("スリナム", "Suriname", "suriname", "latin_america", "🇸🇷", "パラマリボ", -3.0, "SRT (UTC-3)", 5.8520, -55.2038, "SRD", "スリナム・ドル", "Sr$", "115 / 112"),
    ("アンティグア・バーブーダ", "Antigua and Barbuda", "antigua_and_barbuda", "latin_america", "🇦🇬", "セントジョンズ", -4.0, "AST (UTC-4)", 17.1274, -61.8468, "XCD", "東カリブ・ドル", "EC$", "911 / 999"),
    ("グレナダ", "Grenada", "grenada", "latin_america", "🇬🇩", "セントジョージズ", -4.0, "AST (UTC-4)", 12.0561, -61.7488, "XCD", "東カリブ・ドル", "EC$", "911"),
    ("セントクリストファー・ネービス", "Saint Kitts and Nevis", "saint_kitts_and_nevis", "latin_america", "🇰🇳", "バセテール", -4.0, "AST (UTC-4)", 17.3026, -62.7177, "XCD", "東カリブ・ドル", "EC$", "911"),
    ("セントビンセント及びグレナディーン諸島", "Saint Vincent and the Grenadines", "saint_vincent", "latin_america", "🇻🇨", "キングスタウン", -4.0, "AST (UTC-4)", 13.1600, -61.2248, "XCD", "東カリブ・ドル", "EC$", "911 / 999"),
    ("セントルシア", "Saint Lucia", "saint_lucia", "latin_america", "🇱🇨", "カストリーズ", -4.0, "AST (UTC-4)", 14.0101, -60.9875, "XCD", "東カリブ・ドル", "EC$", "911 / 999"),
    ("ドミニカ国", "Dominica", "dominica", "latin_america", "🇩🇲", "ロゾー", -4.0, "AST (UTC-4)", 15.3092, -61.3794, "XCD", "東カリブ・ドル", "EC$", "999"),

    # ==================== 5. 欧州 (Europe) ====================
    ("オーストリア", "Austria", "austria", "europe", "🇦🇹", "ウィーン", 1.0, "CET (UTC+1)", 48.2082, 16.3738, "EUR", "ユーロ", "€", "112 / 133"),
    ("スイス", "Switzerland", "switzerland", "europe", "🇨🇭", "ベルン", 1.0, "CET (UTC+1)", 46.9480, 7.4474, "CHF", "スイス・フラン", "CHF", "112 / 117"),
    ("スウェーデン", "Sweden", "sweden", "europe", "🇸🇪", "ストックホルム", 1.0, "CET (UTC+1)", 59.3293, 18.0686, "SEK", "スウェーデン・クローナ", "kr", "112"),
    ("ノルウェー", "Norway", "norway", "europe", "🇳🇴", "オスロ", 1.0, "CET (UTC+1)", 59.9139, 10.7522, "NOK", "ノルウェー・クローネ", "kr", "112 / 113"),
    ("デンマーク", "Denmark", "denmark", "europe", "🇩🇰", "コペンハーゲン", 1.0, "CET (UTC+1)", 55.6761, 12.5683, "DKK", "デンマーク・クローネ", "kr.", "112"),
    ("フィンランド", "Finland", "finland", "europe", "🇫🇮", "ヘルシンキ", 2.0, "EET (UTC+2)", 60.1699, 24.9384, "EUR", "ユーロ", "€", "112"),
    ("アイルランド", "Ireland", "ireland", "europe", "🇮🇪", "ダブリン", 0.0, "GMT (UTC+0)", 53.3498, -6.2603, "EUR", "ユーロ", "€", "112 / 999"),
    ("ポルトガル", "Portugal", "portugal", "europe", "🇵🇹", "リスボン", 0.0, "WET (UTC+0)", 38.7223, -9.1393, "EUR", "ユーロ", "€", "112"),
    ("ギリシャ", "Greece", "greece", "europe", "🇬🇷", "アテネ", 2.0, "EET (UTC+2)", 37.9838, 23.7275, "EUR", "ユーロ", "€", "112 / 100"),
    ("ポーランド", "Poland", "poland", "europe", "🇵🇱", "ワルシャワ", 1.0, "CET (UTC+1)", 52.2297, 21.0122, "PLN", "ズウォティ", "zł", "112 / 997"),
    ("チェコ", "Czech Republic", "czech_republic", "europe", "🇨🇿", "プラハ", 1.0, "CET (UTC+1)", 50.0755, 14.4378, "CZK", "チェコ・コルナ", "Kč", "112 / 158"),
    ("ハンガリー", "Hungary", "hungary", "europe", "🇭🇺", "ブダペスト", 1.0, "CET (UTC+1)", 47.4979, 19.0402, "HUF", "フォリント", "Ft", "112 / 107"),
    ("ルーマニア", "Romania", "romania", "europe", "🇷🇴", "ブカレスト", 2.0, "EET (UTC+2)", 44.4268, 26.1025, "RON", "レイ", "lei", "112"),
    ("ブルガリア", "Bulgaria", "bulgaria", "europe", "🇧🇬", "ソフィア", 2.0, "EET (UTC+2)", 42.6977, 23.3219, "BGN", "レフ", "лв", "112"),
    ("クロアチア", "Croatia", "croatia", "europe", "🇭🇷", "ザグレブ", 1.0, "CET (UTC+1)", 45.8150, 15.9819, "EUR", "ユーロ", "€", "112"),
    ("スロバキア", "Slovakia", "slovakia", "europe", "🇸🇰", "ブラチスラバ", 1.0, "CET (UTC+1)", 48.1486, 17.1077, "EUR", "ユーロ", "€", "112 / 158"),
    ("スロベニア", "Slovenia", "slovenia", "europe", "🇸🇮", "リュブリャナ", 1.0, "CET (UTC+1)", 46.0569, 14.5058, "EUR", "ユーロ", "€", "112 / 113"),
    ("エストニア", "Estonia", "estonia", "europe", "🇪🇪", "タリン", 2.0, "EET (UTC+2)", 59.4370, 24.7536, "EUR", "ユーロ", "€", "112"),
    ("ラトビア", "Latvia", "latvia", "europe", "🇱🇻", "リガ", 2.0, "EET (UTC+2)", 56.9496, 24.1052, "EUR", "ユーロ", "€", "112"),
    ("リトアニア", "Lithuania", "lithuania", "europe", "🇱🇹", "ヴィリニュス", 2.0, "EET (UTC+2)", 54.6872, 25.2797, "EUR", "ユーロ", "€", "112"),
    ("アイスランド", "Iceland", "iceland", "europe", "🇮🇸", "レイキャビク", 0.0, "GMT (UTC+0)", 64.1466, -21.9426, "ISK", "アイスランド・クローナ", "kr", "112"),
    ("ルクセンブルク", "Luxembourg", "luxembourg", "europe", "🇱🇺", "ルクセンブルク", 1.0, "CET (UTC+1)", 49.6116, 6.1319, "EUR", "ユーロ", "€", "112 / 113"),
    ("マルタ", "Malta", "malta", "europe", "🇲🇹", "バレッタ", 1.0, "CET (UTC+1)", 35.8989, 14.5146, "EUR", "ユーロ", "€", "112"),
    ("キプロス", "Cyprus", "cyprus", "europe", "🇨🇾", "ニコシア", 2.0, "EET (UTC+2)", 35.1856, 33.3823, "EUR", "ユーロ", "€", "112"),
    ("セルビア", "Serbia", "serbia", "europe", "🇷🇸", "ベオグラード", 1.0, "CET (UTC+1)", 44.7866, 20.4489, "RSD", "ディナール", "дин.", "192 / 194"),
    ("ボスニア・ヘルツェゴビナ", "Bosnia and Herzegovina", "bosnia", "europe", "🇧🇦", "サラエボ", 1.0, "CET (UTC+1)", 43.8563, 18.4131, "BAM", "兌換マルク", "KM", "122 / 124"),
    ("アルバニア", "Albania", "albania", "europe", "🇦🇱", "ティラナ", 1.0, "CET (UTC+1)", 41.3275, 19.8187, "ALL", "レク", "L", "112 / 129"),
    ("北マケドニア", "North Macedonia", "north_macedonia", "europe", "🇲🇰", "スコピエ", 1.0, "CET (UTC+1)", 41.9981, 21.4254, "MKD", "デナル", "ден", "112 / 192"),
    ("モンテネグロ", "Montenegro", "montenegro", "europe", "🇲🇪", "ポドゴリツァ", 1.0, "CET (UTC+1)", 42.4304, 19.2594, "EUR", "ユーロ", "€", "112 / 122"),
    ("コソボ", "Kosovo", "kosovo", "europe", "🇽🇰", "プリシュティナ", 1.0, "CET (UTC+1)", 42.6629, 21.1655, "EUR", "ユーロ", "€", "112 / 192"),
    ("ウクライナ", "Ukraine", "ukraine", "europe", "🇺🇦", "キーウ", 2.0, "EET (UTC+2)", 50.4501, 30.5234, "UAH", "フリヴニャ", "₴", "112 / 102"),
    ("ベラルーシ", "Belarus", "belarus", "europe", "🇧🇾", "ミンスク", 3.0, "MSK (UTC+3)", 53.9045, 27.5615, "BYN", "ベラルーシ・ルーブル", "Br", "102 / 103"),
    ("モルドバ", "Moldova", "moldova", "europe", "🇲🇩", "キシナウ", 2.0, "EET (UTC+2)", 47.0105, 28.8638, "MDL", "モルドバ・レウ", "L", "112"),
    ("ロシア", "Russia", "russia", "europe", "🇷🇺", "モスクワ", 3.0, "MSK (UTC+3)", 55.7558, 37.6173, "RUB", "ロシア・ルーブル", "₽", "112 / 102"),
    ("アンドラ", "Andorra", "andorra", "europe", "🇦🇩", "アンドララベリャ", 1.0, "CET (UTC+1)", 42.5063, 1.5218, "EUR", "ユーロ", "€", "112 / 110"),
    ("モナコ", "Monaco", "monaco", "europe", "🇲🇨", "モナコ", 1.0, "CET (UTC+1)", 43.7384, 7.4246, "EUR", "ユーロ", "€", "112 / 17"),
    ("サンマリノ", "San Marino", "san_marino", "europe", "🇸🇲", "サンマリノ", 1.0, "CET (UTC+1)", 43.9424, 12.4578, "EUR", "ユーロ", "€", "112 / 113"),
    ("バチカン", "Vatican", "vatican", "europe", "🇻🇦", "バチカン", 1.0, "CET (UTC+1)", 41.9029, 12.4534, "EUR", "ユーロ", "€", "112"),
    ("リヒテンシュタイン", "Liechtenstein", "liechtenstein", "europe", "🇱🇮", "ファドゥーツ", 1.0, "CET (UTC+1)", 47.1410, 9.5209, "CHF", "スイス・フラン", "CHF", "112 / 117"),
    ("カザフスタン", "Kazakhstan", "kazakhstan", "europe", "🇰🇿", "アスタナ", 5.0, "KZT (UTC+5)", 51.1694, 71.4491, "KZT", "テンゲ", "₸", "112 / 102"),
    ("ウズベキスタン", "Uzbekistan", "uzbekistan", "europe", "🇺🇿", "タシュケント", 5.0, "UZT (UTC+5)", 41.2995, 69.2401, "UZS", "スム", "so'm", "102 / 103"),
    ("キルギス", "Kyrgyz Republic", "kyrgyzstan", "europe", "🇰🇬", "ビシュケク", 6.0, "KGT (UTC+6)", 42.8746, 74.5698, "KGS", "ソム", "с", "102 / 103"),
    ("タジキスタン", "Tajikistan", "tajikistan", "europe", "🇹🇯", "ドゥシャンベ", 5.0, "TJT (UTC+5)", 38.5598, 68.7870, "TJS", "ソモニ", "ЅМ", "102 / 103"),
    ("トルクメニスタン", "Turkmenistan", "turkmenistan", "europe", "🇹🇲", "アシガバート", 5.0, "TMT (UTC+5)", 37.9601, 58.3261, "TMT", "マナト", "T", "02 / 03"),
    ("アゼルバイジャン", "Azerbaijan", "azerbaijan", "europe", "🇦🇿", "バクー", 4.0, "AZT (UTC+4)", 40.4093, 49.8671, "AZN", "マナト", "₼", "102 / 103"),
    ("アルメニア", "Armenia", "armenia", "europe", "🇦🇲", "エレバン", 4.0, "AMT (UTC+4)", 40.1792, 44.4991, "AMD", "ドラム", "֏", "102 / 103"),
    ("ジョージア", "Georgia", "georgia", "europe", "🇬🇪", "トビリシ", 4.0, "GET (UTC+4)", 41.7151, 44.8271, "GEL", "ラリ", "₾", "112"),

    # ==================== 6. 中東 (Middle East) ====================
    ("サウジアラビア", "Saudi Arabia", "saudi_arabia", "middle_east", "🇸🇦", "リヤド", 3.0, "AST (UTC+3)", 24.7136, 46.6753, "SAR", "サウジ・リヤル", "SR", "999 / 997"),
    ("カタール", "Qatar", "qatar", "middle_east", "🇶🇦", "ドーハ", 3.0, "AST (UTC+3)", 25.2854, 51.5310, "QAR", "カタール・リヤル", "QR", "999"),
    ("クウェート", "Kuwait", "kuwait", "middle_east", "🇰🇼", "クウェート", 3.0, "AST (UTC+3)", 29.3759, 47.9774, "KWD", "クウェート・ディナール", "KD", "112"),
    ("バーレーン", "Bahrain", "bahrain", "middle_east", "🇧🇭", "マナマ", 3.0, "AST (UTC+3)", 26.2285, 50.5860, "BHD", "バーレーン・ディナール", "BD", "999"),
    ("オマーン", "Oman", "oman", "middle_east", "🇴🇲", "マスカット", 4.0, "GST (UTC+4)", 23.5859, 58.4059, "OMR", "オマーン・リアル", "RO", "9999"),
    ("イスラエル", "Israel", "israel", "middle_east", "🇮🇱", "エルサレム / テルアビブ", 2.0, "IST (UTC+2)", 31.7683, 35.2137, "ILS", "新シェケル", "₪", "100 / 101"),
    ("ヨルダン", "Jordan", "jordan", "middle_east", "🇯🇴", "アンマン", 3.0, "AST (UTC+3)", 31.9454, 35.9284, "JOD", "ヨルダン・ディナール", "JD", "911"),
    ("レバノン", "Lebanon", "lebanon", "middle_east", "🇱🇧", "ベイルート", 2.0, "EET (UTC+2)", 33.8938, 35.5018, "LBP", "レバノン・ポンド", "LL", "112 / 140"),
    ("イラク", "Iraq", "iraq", "middle_east", "🇮🇶", "バグダッド", 3.0, "AST (UTC+3)", 33.3152, 44.3661, "IQD", "イラク・ディナール", "ID", "104 / 122"),
    ("イラン", "Iran", "iran", "middle_east", "🇮🇷", "テヘラン", 3.5, "IRST (UTC+3.5)", 35.6892, 51.3890, "IRR", "イラン・リアル", "Rl", "110 / 115"),
    ("イエメン", "Yemen", "yemen", "middle_east", "🇾🇪", "サナア", 3.0, "AST (UTC+3)", 15.3694, 44.1910, "YER", "イエメン・リアル", "YR", "199 / 191"),
    ("シリア", "Syria", "syria", "middle_east", "🇸🇾", "ダマスカス", 3.0, "AST (UTC+3)", 33.5138, 36.2765, "SYP", "シリア・ポンド", "LS", "112 / 110"),
    ("アフガニスタン", "Afghanistan", "afghanistan", "middle_east", "🇦🇫", "カブール", 4.5, "AFT (UTC+4.5)", 34.5553, 69.2075, "AFN", "アフガニ", "Af", "119 / 102"),
    ("パレスチナ", "Palestine", "palestine", "middle_east", "🇵🇸", "ラマッラー", 2.0, "EET (UTC+2)", 31.9038, 35.2034, "ILS", "新シェケル / JOD", "₪", "100 / 101"),

    # ==================== 7. アフリカ (Africa) ====================
    ("エジプト", "Egypt", "egypt", "africa", "🇪🇬", "カイロ", 2.0, "EET (UTC+2)", 30.0444, 31.2357, "EGP", "エジプト・ポンド", "E£", "122 / 123"),
    ("南アフリカ", "South Africa", "south_africa", "africa", "🇿🇦", "プレトリア / ヨハネスブルグ", 2.0, "SAST (UTC+2)", -25.7479, 28.2293, "ZAR", "ランド", "R", "10111 / 10177"),
    ("ナイジェリア", "Nigeria", "nigeria", "africa", "🇳🇬", "アブジャ / ラゴス", 1.0, "WAT (UTC+1)", 9.0765, 7.3986, "NGN", "ナイラ", "₦", "112 / 199"),
    ("ケニア", "Kenya", "kenya", "africa", "🇰🇪", "ナイロビ", 3.0, "EAT (UTC+3)", -1.2921, 36.8219, "KES", "ケニア・シリング", "KSh", "999 / 112"),
    ("モロッコ", "Morocco", "morocco", "africa", "🇲🇦", "ラバト / カサブランカ", 1.0, "WEST (UTC+1)", 34.0209, -6.8416, "MAD", "モロッコ・ディルハム", "DH", "19 / 15"),
    ("アルジェリア", "Algeria", "algeria", "africa", "🇩🇿", "アルジェ", 1.0, "CET (UTC+1)", 36.7538, 3.0588, "DZD", "ディナール", "DA", "17 / 14"),
    ("チュニジア", "Tunisia", "tunisia", "africa", "🇹🇳", "チュニス", 1.0, "CET (UTC+1)", 36.8065, 10.1815, "TND", "ディナール", "DT", "197 / 190"),
    ("エチオピア", "Ethiopia", "ethiopia", "africa", "🇪🇹", "アディスアベバ", 3.0, "EAT (UTC+3)", 9.0320, 38.7469, "ETB", "ブル", "Br", "991 / 907"),
    ("ガーナ", "Ghana", "ghana", "africa", "🇬🇭", "アクラ", 0.0, "GMT (UTC+0)", 5.6037, -0.1870, "GHS", "セディ", "GH₵", "191 / 193"),
    ("タンザニア", "Tanzania", "tanzania", "africa", "🇹🇿", "ドドマ / ダルエスサラーム", 3.0, "EAT (UTC+3)", -6.1630, 35.7516, "TZS", "タンザニア・シリング", "TSh", "112 / 114"),
    ("ウガンダ", "Uganda", "uganda", "africa", "🇺🇬", "カンパラ", 3.0, "EAT (UTC+3)", 0.3476, 32.5825, "UGX", "ウガンダ・シリング", "USh", "999 / 112"),
    ("コートジボワール", "Cote d'Ivoire", "cote_divoire", "africa", "🇨🇮", "ヤムスクロ / アビジャン", 0.0, "GMT (UTC+0)", 6.8276, -5.2893, "XOF", "CFAフラン", "CFA", "111 / 185"),
    ("セネガル", "Senegal", "senegal", "africa", "🇸🇳", "ダカール", 0.0, "GMT (UTC+0)", 14.7167, -17.4677, "XOF", "CFAフラン", "CFA", "17 / 18"),
    ("アンゴラ", "Angola", "angola", "africa", "🇦🇴", "ルアンダ", 1.0, "WAT (UTC+1)", -8.8390, 13.2894, "AOA", "クワンザ", "Kz", "113 / 112"),
    ("ザンビア", "Zambia", "zambia", "africa", "🇿🇲", "ルサカ", 2.0, "CAT (UTC+2)", -15.3875, 28.3228, "ZMW", "ザンビア・クワチャ", "ZK", "999 / 991"),
    ("ジンバブエ", "Zimbabwe", "zimbabwe", "africa", "🇿🇼", "ハラレ", 2.0, "CAT (UTC+2)", -17.8252, 31.0335, "USD", "米ドル / ZiG", "$", "999 / 994"),
    ("ルワンダ", "Rwanda", "rwanda", "africa", "🇷🇼", "キガリ", 2.0, "CAT (UTC+2)", -1.9706, 30.1044, "RWF", "ルワンダ・フラン", "FRw", "112 / 912"),
    ("モザンビーク", "Mozambique", "mozambique", "africa", "🇲🇿", "マプト", 2.0, "CAT (UTC+2)", -25.9692, 32.5732, "MZN", "メティカル", "MT", "119 / 117"),
    ("マダガスカル", "Madagascar", "madagascar", "africa", "🇲🇬", "アンタナナリボ", 3.0, "EAT (UTC+3)", -18.8792, 47.5079, "MGA", "アリアリ", "Ar", "117 / 118"),
    ("モーリシャス", "Mauritius", "mauritius", "africa", "🇲🇺", "ポートルイス", 4.0, "MUT (UTC+4)", -20.1609, 57.5012, "MUR", "モーリシャス・ルピー", "₨", "999 / 114"),
    ("ボツワナ", "Botswana", "botswana", "africa", "🇧🇼", "ハボローネ", 2.0, "CAT (UTC+2)", -24.6282, 25.9231, "BWP", "プラ", "P", "999 / 997"),
    ("ナミビア", "Namibia", "namibia", "africa", "🇳🇦", "ウィントフック", 2.0, "CAT (UTC+2)", -22.5609, 17.0658, "NAD", "ナミビア・ドル", "N$", "10111 / 211111"),
    ("ガボン", "Gabon", "gabon", "africa", "🇬🇦", "リーブルビル", 1.0, "WAT (UTC+1)", 0.4162, 9.4673, "XAF", "中央アフリカCFAフラン", "FCFA", "1730 / 1300"),
    ("カメルーン", "Cameroon", "cameroon", "africa", "🇨🇲", "ヤウンデ", 1.0, "WAT (UTC+1)", 3.8480, 11.5021, "XAF", "中央アフリカCFAフラン", "FCFA", "117 / 119"),
    ("コンゴ民主共和国", "DR Congo", "dr_congo", "africa", "🇨🇩", "キンシャサ", 1.0, "WAT (UTC+1)", -4.4419, 15.2663, "CDF", "コンゴ・フラン", "FC", "112 / 118"),
    ("コンゴ共和国", "Republic of the Congo", "congo", "africa", "🇨🇬", "ブラザビル", 1.0, "WAT (UTC+1)", -4.2634, 15.2429, "XAF", "中央アフリカCFAフラン", "FCFA", "117 / 118"),
    ("スーダン", "Sudan", "sudan", "africa", "🇸🇩", "ハルツーム", 2.0, "CAT (UTC+2)", 15.5007, 32.5599, "SDG", "スーダン・ポンド", "SDG", "999"),
    ("南スーダン", "South Sudan", "south_sudan", "africa", "🇸🇸", "ジュバ", 2.0, "CAT (UTC+2)", 4.8594, 31.5713, "SSP", "南スーダン・ポンド", "£", "777 / 999"),
    ("リビア", "Libya", "libya", "africa", "🇱🇾", "トリポリ", 2.0, "EET (UTC+2)", 32.8872, 13.1913, "LYD", "リビア・ディナール", "LD", "1515 / 193"),
    ("マリ", "Mali", "mali", "africa", "🇲🇱", "バマコ", 0.0, "GMT (UTC+0)", 12.6392, -8.0029, "XOF", "CFAフラン", "CFA", "17 / 18"),
    ("ブルキナファソ", "Burkina Faso", "burkina_faso", "africa", "🇧🇫", "ワガドゥグー", 0.0, "GMT (UTC+0)", 12.3714, -1.5197, "XOF", "CFAフラン", "CFA", "17 / 18"),
    ("ニジェール", "Niger", "niger", "africa", "🇳🇪", "ニアメ", 1.0, "WAT (UTC+1)", 13.5116, 2.1254, "XOF", "CFAフラン", "CFA", "17 / 18"),
    ("チャド", "Chad", "chad", "africa", "🇹🇩", "ヌジャメナ", 1.0, "WAT (UTC+1)", 12.1348, 15.0557, "XAF", "中央アフリカCFAフラン", "FCFA", "17 / 18"),
    ("ギニア", "Guinea", "guinea", "africa", "🇬🇳", "コナクリ", 0.0, "GMT (UTC+0)", 9.6412, -13.5784, "GNF", "ギニア・フラン", "FG", "117 / 18"),
    ("ベナン", "Benin", "benin", "africa", "🇧🇯", "ポルトノボ", 1.0, "WAT (UTC+1)", 6.4969, 2.6289, "XOF", "CFAフラン", "CFA", "117 / 118"),
    ("トーゴ", "Togo", "togo", "africa", "🇹🇬", "ロメ", 0.0, "GMT (UTC+0)", 6.1375, 1.2125, "XOF", "CFAフラン", "CFA", "117 / 118"),
    ("シエラレオネ", "Sierra Leone", "sierra_leone", "africa", "🇸🇱", "フリータウン", 0.0, "GMT (UTC+0)", 8.4844, -13.2344, "SLE", "レオン", "Le", "019 / 999"),
    ("リベリア", "Liberia", "liberia", "africa", "🇱🇷", "モンロビア", 0.0, "GMT (UTC+0)", 6.3156, -10.8074, "LRD", "リベリア・ドル", "L$", "911"),
    ("モーリタニア", "Mauritania", "mauritania", "africa", "🇲🇷", "ヌアクショット", 0.0, "GMT (UTC+0)", 18.0735, -15.9582, "MRU", "ウギア", "UM", "117 / 101"),
    ("マラウイ", "Malawi", "malawi", "africa", "🇲🇼", "リロングウェ", 2.0, "CAT (UTC+2)", -13.9626, 33.7741, "MWK", "クワチャ", "MK", "997 / 998"),
    ("ソマリア", "Somalia", "somalia", "africa", "🇸🇴", "モガディシュ", 3.0, "EAT (UTC+3)", 2.0469, 45.3182, "SOS", "ソマリア・シリング", "Ssh", "888 / 999"),
    ("エリトリア", "Eritrea", "eritrea", "africa", "🇪🇷", "アスマラ", 3.0, "EAT (UTC+3)", 15.3229, 38.9251, "ERN", "ナクファ", "Nfk", "113 / 114"),
    ("ジブチ", "Djibouti", "djibouti", "africa", "🇩🇯", "ジブチ", 3.0, "EAT (UTC+3)", 11.8251, 42.5903, "DJF", "ジブチ・フラン", "Fdj", "17 / 18"),
    ("中央アフリカ", "Central African Republic", "central_african_republic", "africa", "🇨🇫", "バンギ", 1.0, "WAT (UTC+1)", 4.3947, 18.5582, "XAF", "中央アフリカCFAフラン", "FCFA", "117 / 118"),
    ("赤道ギニア", "Equatorial Guinea", "equatorial_guinea", "africa", "🇬🇶", "マラボ", 1.0, "WAT (UTC+1)", 3.7504, 8.7371, "XAF", "中央アフリカCFAフラン", "FCFA", "114 / 115"),
    ("ブルンジ", "Burundi", "burundi", "africa", "🇧🇮", "ギテガ", 2.0, "CAT (UTC+2)", -3.4273, 29.9246, "BIF", "ブルンジ・フラン", "FBu", "117 / 112"),
    ("エスワティニ", "Eswatini", "eswatini", "africa", "🇸🇿", "ムババーネ", 2.0, "SAST (UTC+2)", -26.3055, 31.1367, "SZL", "リランゲニ", "L", "999 / 977"),
    ("レソト", "Lesotho", "lesotho", "africa", "🇱🇸", "マセル", 2.0, "SAST (UTC+2)", -29.3151, 27.4869, "LSL", "ロティ", "M", "123 / 121"),
    ("コモロ", "Comoros", "comoros", "africa", "🇰🇲", "モロニ", 3.0, "EAT (UTC+3)", -11.7172, 43.2473, "KMF", "コモロ・フラン", "CF", "17 / 18"),
    ("カーボベルデ", "Cabo Verde", "cabo_verde", "africa", "🇨🇻", "プライア", -1.0, "CVT (UTC-1)", 14.9330, -23.5133, "CVE", "カーボベルデ・エスクード", "$", "132 / 130"),
    ("ガンビア", "Gambia", "gambia", "africa", "🇬🇲", "バンジュール", 0.0, "GMT (UTC+0)", 13.4549, -16.5790, "GMD", "ダラシ", "D", "117 / 116"),
    ("ギニアビサウ", "Guinea-Bissau", "guinea_bissau", "africa", "🇬🇼", "ビサウ", 0.0, "GMT (UTC+0)", 11.8632, -15.5977, "XOF", "CFAフラン", "CFA", "117 / 119"),
    ("サントメ・プリンシペ", "Sao Tome and Principe", "sao_tome_and_principe", "africa", "🇸🇹", "サントメ", 0.0, "GMT (UTC+0)", 0.3365, 6.7273, "STN", "ドブラ", "Db", "222222 / 112"),
    ("セーシェル", "Seychelles", "seychelles", "africa", "🇸🇨", "ビクトリア", 4.0, "SCT (UTC+4)", -4.6191, 55.4513, "SCR", "セーシェル・ルピー", "SR", "999 / 151")
]

def generate_full_country_dict():
    """
    外務省掲載の未登録国を全て OVERSEAS_CONFIG 形式の辞書に変換して返します。
    """
    country_dict = {}
    for (name, en_name, key, region, flag, city, offset, tz_name, lat, lon, curr_code, curr_name, curr_symbol, emergency) in ALL_MOFA_COUNTRIES_RAW:
        if key in ALREADY_REGISTERED_KEYS:
            continue
        
        country_dict[key] = {
            "id": key,
            "name": name,
            "english_name": en_name,
            "region": region,
            "flag": flag,
            "city": f"{city} ({en_name})",
            "embassy_name": f"在{name}日本国大使館 (Embassy of Japan in {en_name})",
            "mofa_code": "0000",
            "mofa_page_url": f"https://www.anzen.mofa.go.jp/",
            "embassy_url": f"https://www.anzen.mofa.go.jp/",
            "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
            "emergency_phones": f"緊急時: {emergency} (警察/救急) / 大使館",
            "timezone_offset": offset,
            "timezone_name": tz_name,
            "lat": lat,
            "lon": lon,
            "currency_code": curr_code,
            "currency_name": curr_name,
            "currency_symbol": curr_symbol,
            "default_camera_id": "stream_skynews",
            "default_keywords": [f"{city} 暴動", f"{name} デモ", f"{name} 治安", f"{en_name} strike"],
            "media_channels": [
                {"id": "stream_global_news", "name": "📺 国際24hニュース (Sky News / DW)", "video_id": "dMlQFujIGPA", "type": "stream"},
                {"id": "cam_global_city", "name": f"📷 {city} 周辺・主要都市カメラ", "video_id": "OzYp4NRZlwQ", "type": "camera"}
            ],
            "weather_cities": [
                {"name": f"{city} (首都)", "name_en": city, "lat": lat, "lon": lon, "is_capital": True}
            ],
            "transit_systems": [
                {"id": f"transit_{key}", "name": f"{name} 国鉄・都市交通網", "mode": "全国鉄道・都市交通", "coverage": f"{name}全域・{city}", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": f"{name}主要交通機関は定常運行中"}
            ],
            "airports": [
                {"iata": curr_code[:3], "icao": "XXXX", "name": f"{city} 国際空港", "city": city, "hub": f"{name}主要ハブ"}
            ]
        }
    return country_dict

if __name__ == "__main__":
    new_countries = generate_full_country_dict()
    print(f"Newly defined countries count: {len(new_countries)}")
    print(f"Total countries with registered: {len(new_countries) + len(ALREADY_REGISTERED_KEYS)}")
    for r_k, r_info in REGIONS.items():
        count = sum(1 for c in new_countries.values() if c['region'] == r_k)
        print(f"  {r_info['icon']} {r_info['name']}: {count}カ国 (新規追加)")
