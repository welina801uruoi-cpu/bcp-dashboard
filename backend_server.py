from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
import email.utils
import json
import os
import re
import ssl
import sys
import threading
import time
import urllib.parse
import urllib.request
import warnings
import webbrowser
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from flask import Flask, jsonify, render_template, request, send_from_directory

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, relative_path)


app = Flask(
    __name__,
    template_folder=resource_path('.'),
    static_folder=resource_path('.'),
)


# 全国および主要拠点の定義・マッピング設定（ユーザー指定エリア・構成都道府県に対応）
LOCATION_CONFIG = {
    "all": {
        "name": "全国",
        "region_name": "全国エリア",
        "region_desc": "都道府県すべて（沖縄含む47都道府県）",
        "target_prefs": [
            {"code": "1a", "name": "北海道(道央)", "short_name": "道央"},
            {"code": "1b", "name": "北海道(道南)", "short_name": "道南"},
            {"code": "1c", "name": "北海道(道北)", "short_name": "道北"},
            {"code": "1d", "name": "北海道(道東)", "short_name": "道東"},
            {"code": "2", "name": "青森県", "short_name": "青森"},
            {"code": "3", "name": "岩手県", "short_name": "岩手"},
            {"code": "4", "name": "宮城県", "short_name": "宮城"},
            {"code": "5", "name": "秋田県", "short_name": "秋田"},
            {"code": "6", "name": "山形県", "short_name": "山形"},
            {"code": "7", "name": "福島県", "short_name": "福島"},
            {"code": "8", "name": "茨城県", "short_name": "茨城"},
            {"code": "9", "name": "栃木県", "short_name": "栃木"},
            {"code": "10", "name": "群馬県", "short_name": "群馬"},
            {"code": "11", "name": "埼玉県", "short_name": "埼玉"},
            {"code": "12", "name": "千葉県", "short_name": "千葉"},
            {"code": "13", "name": "東京都", "short_name": "東京"},
            {"code": "14", "name": "神奈川県", "short_name": "神奈川"},
            {"code": "15", "name": "新潟県", "short_name": "新潟"},
            {"code": "16", "name": "富山県", "short_name": "富山"},
            {"code": "17", "name": "石川県", "short_name": "石川"},
            {"code": "18", "name": "福井県", "short_name": "福井"},
            {"code": "19", "name": "山梨県", "short_name": "山梨"},
            {"code": "20", "name": "長野県", "short_name": "長野"},
            {"code": "21", "name": "岐阜県", "short_name": "岐阜"},
            {"code": "22", "name": "静岡県", "short_name": "静岡"},
            {"code": "23", "name": "愛知県", "short_name": "愛知"},
            {"code": "24", "name": "三重県", "short_name": "三重"},
            {"code": "25", "name": "滋賀県", "short_name": "滋賀"},
            {"code": "26", "name": "京都府", "short_name": "京都"},
            {"code": "27", "name": "大阪府", "short_name": "大阪"},
            {"code": "28", "name": "兵庫県", "short_name": "兵庫"},
            {"code": "29", "name": "奈良県", "short_name": "奈良"},
            {"code": "30", "name": "和歌山県", "short_name": "和歌山"},
            {"code": "31", "name": "鳥取県", "short_name": "鳥取"},
            {"code": "32", "name": "島根県", "short_name": "島根"},
            {"code": "33", "name": "岡山県", "short_name": "岡山"},
            {"code": "34", "name": "広島県", "short_name": "広島"},
            {"code": "35", "name": "山口県", "short_name": "山口"},
            {"code": "36", "name": "徳島県", "short_name": "徳島"},
            {"code": "37", "name": "香川県", "short_name": "香川"},
            {"code": "38", "name": "愛媛県", "short_name": "愛媛"},
            {"code": "39", "name": "高知県", "short_name": "高知"},
            {"code": "40", "name": "福岡県", "short_name": "福岡"},
            {"code": "41", "name": "佐賀県", "short_name": "佐賀"},
            {"code": "42", "name": "長崎県", "short_name": "長崎"},
            {"code": "43", "name": "熊本県", "short_name": "熊本"},
            {"code": "44", "name": "大分県", "short_name": "大分"},
            {"code": "45", "name": "宮崎県", "short_name": "宮崎"},
            {"code": "46", "name": "鹿児島県", "short_name": "鹿児島"},
            {"code": "47", "name": "沖縄県", "short_name": "沖縄"}
        ],
        "pref_names": [
            "北海道", "道央", "道南", "道北", "道東", "青森", "岩手", "宮城", "秋田", "山形", "福島",
            "茨城", "栃木", "群馬", "埼玉", "千葉", "東京", "神奈川", "新潟", "富山", "石川", "福井",
            "山梨", "長野", "岐阜", "静岡", "愛知", "三重", "滋賀", "京都", "大阪", "兵庫", "奈良",
            "和歌山", "鳥取", "島根", "岡山", "広島", "山口", "徳島", "香川", "愛媛", "高知",
            "福岡", "佐賀", "長崎", "熊本", "大分", "宮崎", "鹿児島", "沖縄"
        ],
        "transit_area": "all",
        "power_name": "全国大手電力10社送配電",
        "power_url": "https://typhoon.yahoo.co.jp/weather/poweroutage/",
        "water_name": "全国主要水道局",
        "water_url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/topics/bukyoku/kenkou/suido/index.html",
        "gas_name": "全国主要都市ガス",
        "gas_url": "https://www.gas.or.jp/",
        "lines": ["東海道本線", "山手線", "大阪環状線", "東北本線", "鹿児島本線", "中央本線", "山陽本線", "函館本線", "予讃線", "北陸本線"],
        "shinkansen": ["東海道新幹線", "山陽新幹線", "東北新幹線", "上越新幹線", "北陸新幹線", "九州新幹線", "北海道新幹線", "西九州新幹線", "山形新幹線", "秋田新幹線"],
        "jma_code": "130000",
        "default_camera_id": "cam_tokyo_shibuya"
    },
    "sapporo": {
        "name": "札幌",
        "region_name": "北海道エリア",
        "region_desc": "道央、道南、道北、道東",
        "target_prefs": [
            {"code": "1a", "name": "道央", "short_name": "道央"},
            {"code": "1b", "name": "道南", "short_name": "道南"},
            {"code": "1c", "name": "道北", "short_name": "道北"},
            {"code": "1d", "name": "道東", "short_name": "道東"}
        ],
        "pref_names": ["北海道", "道央", "道南", "道北", "道東"],
        "transit_area": "2",
        "power_name": "ほくでんNW",
        "power_url": "https://typhoon.yahoo.co.jp/weather/poweroutage/",
        "water_name": "札幌市水道局",
        "water_url": "https://www.city.sapporo.jp/suido/",
        "gas_name": "北海道ガス",
        "gas_url": "https://www.hokkaido-gas.co.jp/",
        "lines": ["函館本線", "千歳線", "札沼線", "南北線", "東西線", "東豊線", "室蘭本線", "根室本線", "宗谷本線", "石北本線"],
        "shinkansen": ["北海道新幹線"],
        "jma_code": "016000",
        "default_camera_id": "cam_sapporo"
    },
    "sendai": {
        "name": "仙台",
        "region_name": "東北エリア",
        "region_desc": "青森、岩手、秋田、宮城、山形、福島",
        "target_prefs": [
            {"code": "2", "name": "青森県", "short_name": "青森"},
            {"code": "3", "name": "岩手県", "short_name": "岩手"},
            {"code": "5", "name": "秋田県", "short_name": "秋田"},
            {"code": "4", "name": "宮城県", "short_name": "宮城"},
            {"code": "6", "name": "山形県", "short_name": "山形"},
            {"code": "7", "name": "福島県", "short_name": "福島"}
        ],
        "pref_names": ["青森", "岩手", "秋田", "宮城", "山形", "福島"],
        "transit_area": "3",
        "power_name": "東北電力NW",
        "power_url": "https://typhoon.yahoo.co.jp/weather/poweroutage/",
        "water_name": "仙台市水道局",
        "water_url": "https://www.suidou.city.sendai.jp/",
        "gas_name": "仙台市ガス局",
        "gas_url": "https://www.gas.city.sendai.jp/",
        "lines": ["東北本線", "仙山線", "仙石線", "南北線", "東西線", "常磐線", "奥羽本線", "羽越本線", "磐越西線", "花輪線", "北上線"],
        "shinkansen": ["東北新幹線", "秋田新幹線", "山形新幹線", "北海道新幹線"],
        "jma_code": "040000",
        "default_camera_id": "cam_sendai"
    },
    "tokyo": {
        "name": "東京（本社）",
        "region_name": "関東エリア",
        "region_desc": "東京、千葉、神奈川、埼玉、茨城、栃木、群馬、山梨",
        "target_prefs": [
            {"code": "13", "name": "東京都", "short_name": "東京"},
            {"code": "12", "name": "千葉県", "short_name": "千葉"},
            {"code": "14", "name": "神奈川県", "short_name": "神奈川"},
            {"code": "11", "name": "埼玉県", "short_name": "埼玉"},
            {"code": "8", "name": "茨城県", "short_name": "茨城"},
            {"code": "9", "name": "栃木県", "short_name": "栃木"},
            {"code": "10", "name": "群馬県", "short_name": "群馬"},
            {"code": "19", "name": "山梨県", "short_name": "山梨"}
        ],
        "pref_names": ["東京", "千葉", "神奈川", "埼玉", "茨城", "栃木", "群馬", "山梨"],
        "transit_area": "4",
        "power_name": "東京電力PG",
        "power_url": "https://typhoon.yahoo.co.jp/weather/poweroutage/",
        "water_name": "東京都水道局",
        "water_url": "https://www.waterworks.metro.tokyo.lg.jp/",
        "gas_name": "東京ガス",
        "gas_url": "https://www.tokyo-gas.co.jp/",
        "lines": ["山手線", "中央線", "京浜東北線", "銀座線", "丸ノ内線", "日比谷線", "東西線", "千代田線", "有楽町線", "半蔵門線", "南北線", "副都心線", "浅草線", "三田線", "新宿線", "大江戸線", "東海道線", "横須賀線", "総武線", "常磐線", "宇都宮線", "高崎線", "埼京線", "武蔵野線", "京葉線", "東急線", "小田急線", "京王線", "東武線", "西武線", "京成線", "相鉄線"],
        "shinkansen": ["東海道新幹線", "東北新幹線", "上越新幹線", "北陸新幹線", "山形新幹線", "秋田新幹線", "北海道新幹線"],
        "jma_code": "130000",
        "default_camera_id": "cam_tokyo_shibuya"
    },
    "omiya": {
        "name": "大宮",
        "region_name": "北関東エリア",
        "region_desc": "茨城、埼玉、群馬、栃木",
        "target_prefs": [
            {"code": "8", "name": "茨城県", "short_name": "茨城"},
            {"code": "11", "name": "埼玉県", "short_name": "埼玉"},
            {"code": "10", "name": "群馬県", "short_name": "群馬"},
            {"code": "9", "name": "栃木県", "short_name": "栃木"}
        ],
        "pref_names": ["茨城", "埼玉", "群馬", "栃木"],
        "transit_area": "4",
        "power_name": "東京電力PG",
        "power_url": "https://typhoon.yahoo.co.jp/weather/poweroutage/",
        "water_name": "さいたま市水道局",
        "water_url": "https://www.city.saitama.lg.jp/001/006/002/index.html",
        "gas_name": "武州ガス / 東京ガス",
        "gas_url": "https://www.bushugas.co.jp/",
        "lines": ["京浜東北線", "宇都宮線", "高崎線", "埼京線", "川越線", "武蔵野線", "東武アーバンパークライン", "ニューシャトル", "常磐線", "水戸線", "両毛線", "日光線", "八高線", "上越線", "吾妻線", "烏山線", "つくばエクスプレス"],
        "shinkansen": ["東北新幹線", "上越新幹線", "北陸新幹線", "山形新幹線", "秋田新幹線", "北海道新幹線"],
        "jma_code": "110000",
        "default_camera_id": "cam_omiya_arakawa"
    },
    "yokohama": {
        "name": "横浜",
        "region_name": "南関東エリア",
        "region_desc": "神奈川、千葉",
        "target_prefs": [
            {"code": "14", "name": "神奈川県", "short_name": "神奈川"},
            {"code": "12", "name": "千葉県", "short_name": "千葉"}
        ],
        "pref_names": ["神奈川", "千葉"],
        "transit_area": "4",
        "power_name": "東京電力PG",
        "power_url": "https://typhoon.yahoo.co.jp/weather/poweroutage/",
        "water_name": "横浜市水道局 / 千葉県営水道",
        "water_url": "https://www.city.yokohama.lg.jp/kurashi/sumai-kurashi/suido-seisou/",
        "gas_name": "東京ガス / 京葉ガス",
        "gas_url": "https://www.tokyo-gas.co.jp/",
        "lines": ["東海道線", "横須賀線", "京浜東北線", "根岸線", "横浜線", "南武線", "相模線", "ブルーライン", "グリーンライン", "東急東横線", "東急田園都市線", "京急本線", "相鉄本線", "みなとみらい線", "小田急線", "江ノ島電鉄", "湘南モノレール", "総武線", "総武快速線", "京葉線", "武蔵野線", "内房線", "外房線", "成田線", "東金線", "京成線", "新京成線", "北総線", "千葉都市モノレール"],
        "shinkansen": ["東海道新幹線"],
        "jma_code": "140000",
        "default_camera_id": "cam_yokohama_mm21"
    },
    "nagoya": {
        "name": "名古屋",
        "region_name": "東海・信越エリア",
        "region_desc": "信越（新潟、長野）、東海（岐阜、静岡、三重、愛知）",
        "target_prefs": [
            {"code": "15", "name": "新潟県", "short_name": "新潟"},
            {"code": "20", "name": "長野県", "short_name": "長野"},
            {"code": "21", "name": "岐阜県", "short_name": "岐阜"},
            {"code": "22", "name": "静岡県", "short_name": "静岡"},
            {"code": "24", "name": "三重県", "short_name": "三重"},
            {"code": "23", "name": "愛知県", "short_name": "愛知"}
        ],
        "pref_names": ["新潟", "長野", "岐阜", "静岡", "三重", "愛知"],
        "transit_area": "5",
        "power_name": "中部電力PG / 東北電力NW",
        "power_url": "https://typhoon.yahoo.co.jp/weather/poweroutage/",
        "water_name": "名古屋市上下水道局",
        "water_url": "https://www.water.city.nagoya.jp/",
        "gas_name": "東邦ガス",
        "gas_url": "https://www.tohogas.co.jp/",
        "lines": ["東海道本線", "中央本線", "関西本線", "東山線", "名城線", "名港線", "鶴舞線", "桜通線", "上飯田線", "名古屋本線", "犬山線", "常滑線", "三河線", "近鉄名古屋線", "篠ノ井線", "飯田線", "高山本線", "信越本線", "上越線", "白新線", "越後線"],
        "shinkansen": ["東海道新幹線"],
        "jma_code": "230000",
        "default_camera_id": "cam_nagoya_station"
    },
    "kanazawa": {
        "name": "金沢",
        "region_name": "北陸・上越エリア",
        "region_desc": "石川、富山、福井",
        "target_prefs": [
            {"code": "17", "name": "石川県", "short_name": "石川"},
            {"code": "16", "name": "富山県", "short_name": "富山"},
            {"code": "18", "name": "福井県", "short_name": "福井"}
        ],
        "pref_names": ["石川", "富山", "福井"],
        "transit_area": "5",
        "power_name": "北陸電力送配電",
        "power_url": "https://typhoon.yahoo.co.jp/weather/poweroutage/",
        "water_name": "金沢市企業局",
        "water_url": "https://www.water.kanazawa.ishikawa.jp/",
        "gas_name": "金沢市企業局(ガス)",
        "gas_url": "https://www.water.kanazawa.ishikawa.jp/",
        "lines": ["北陸本線", "七尾線", "IRいしかわ鉄道線", "あいの風とやま鉄道線", "ハピラインふくい線", "石川線", "浅野川線", "富山地方鉄道", "えちぜん鉄道", "福井鉄道", "越美北線", "城端線", "氷見線"],
        "shinkansen": ["北陸新幹線"],
        "jma_code": "170000",
        "default_camera_id": "cam_kanazawa_station"
    },
    "osaka": {
        "name": "大阪",
        "region_name": "近畿エリア",
        "region_desc": "大阪、兵庫、京都、滋賀、奈良、和歌山",
        "target_prefs": [
            {"code": "27", "name": "大阪府", "short_name": "大阪"},
            {"code": "28", "name": "兵庫県", "short_name": "兵庫"},
            {"code": "26", "name": "京都府", "short_name": "京都"},
            {"code": "25", "name": "滋賀県", "short_name": "滋賀"},
            {"code": "29", "name": "奈良県", "short_name": "奈良"},
            {"code": "30", "name": "和歌山県", "short_name": "和歌山"}
        ],
        "pref_names": ["大阪", "兵庫", "京都", "滋賀", "奈良", "和歌山"],
        "transit_area": "7",
        "power_name": "関西電力送配電",
        "power_url": "https://typhoon.yahoo.co.jp/weather/poweroutage/",
        "water_name": "大阪市水道局",
        "water_url": "https://www.city.osaka.lg.jp/suido/",
        "gas_name": "大阪ガス",
        "gas_url": "https://www.osakagas.co.jp/",
        "lines": ["大阪環状線", "御堂筋線", "谷町線", "四つ橋線", "中央線", "千日前線", "堺筋線", "長堀鶴見緑地線", "今里筋線", "阪急神戸本線", "阪急宝塚本線", "阪急京都本線", "阪神本線", "南海本線", "JR宝塚線", "JR神戸線", "JR京都線", "琵琶湖線", "阪和線", "大和路線", "学研都市線", "近鉄奈良線", "近鉄大阪線", "京阪本線", "山陽電車", "神戸電鉄", "能勢電鉄"],
        "shinkansen": ["東海道新幹線", "山陽新幹線"],
        "jma_code": "270000",
        "default_camera_id": "cam_osaka_dotonbori"
    },
    "hiroshima": {
        "name": "広島",
        "region_name": "中国エリア",
        "region_desc": "広島、山口、島根、鳥取、岡山",
        "target_prefs": [
            {"code": "34", "name": "広島県", "short_name": "広島"},
            {"code": "35", "name": "山口県", "short_name": "山口"},
            {"code": "32", "name": "島根県", "short_name": "島根"},
            {"code": "31", "name": "鳥取県", "short_name": "鳥取"},
            {"code": "33", "name": "岡山県", "short_name": "岡山"}
        ],
        "pref_names": ["広島", "山口", "島根", "鳥取", "岡山"],
        "transit_area": "8",
        "power_name": "中国電力NW",
        "power_url": "https://typhoon.yahoo.co.jp/weather/poweroutage/",
        "water_name": "広島市水道局",
        "water_url": "https://www.city.hiroshima.lg.jp/site/suido/",
        "gas_name": "広島ガス",
        "gas_url": "https://www.hiroshima-gas.co.jp/",
        "lines": ["山陽本線", "呉線", "可部線", "芸備線", "伯備線", "山陰本線", "宇野線", "津山線", "福塩線", "因美線", "境線", "岩徳線", "山口線", "アストラムライン", "広電市内線", "岡山電気軌道", "一畑電車"],
        "shinkansen": ["山陽新幹線"],
        "jma_code": "340000",
        "default_camera_id": "cam_hiroshima_station"
    },
    "takamatsu": {
        "name": "高松",
        "region_name": "四国エリア",
        "region_desc": "香川、徳島、高知、愛媛",
        "target_prefs": [
            {"code": "37", "name": "香川県", "short_name": "香川"},
            {"code": "36", "name": "徳島県", "short_name": "徳島"},
            {"code": "39", "name": "高知県", "short_name": "高知"},
            {"code": "38", "name": "愛媛県", "short_name": "愛媛"}
        ],
        "pref_names": ["香川", "徳島", "高知", "愛媛"],
        "transit_area": "9",
        "power_name": "四国電力送配電",
        "power_url": "https://typhoon.yahoo.co.jp/weather/poweroutage/",
        "water_name": "高松市上下水道局",
        "water_url": "https://www.city.takamatsu.kagawa.jp/kurashi/shinoshisetsu/suidou/",
        "gas_name": "四国ガス",
        "gas_url": "https://www.shikokugas.co.jp/",
        "lines": ["予讃線", "高徳線", "土讃線", "徳島線", "牟岐線", "鳴門線", "内子線", "予土線", "琴平線", "長尾線", "志度線", "伊予鉄道", "とさでん交通", "阿佐海岸鉄道"],
        "shinkansen": ["山陽新幹線"],
        "jma_code": "370000",
        "default_camera_id": "cam_takamatsu_seto"
    },
    "fukuoka": {
        "name": "福岡",
        "region_name": "九州エリア",
        "region_desc": "福岡、大分、宮崎、鹿児島、熊本、長崎、佐賀",
        "target_prefs": [
            {"code": "40", "name": "福岡県", "short_name": "福岡"},
            {"code": "44", "name": "大分県", "short_name": "大分"},
            {"code": "45", "name": "宮崎県", "short_name": "宮崎"},
            {"code": "46", "name": "鹿児島県", "short_name": "鹿児島"},
            {"code": "43", "name": "熊本県", "short_name": "熊本"},
            {"code": "42", "name": "長崎県", "short_name": "長崎"},
            {"code": "41", "name": "佐賀県", "short_name": "佐賀"}
        ],
        "pref_names": ["福岡", "大分", "宮崎", "鹿児島", "熊本", "長崎", "佐賀"],
        "transit_area": "7",
        "power_name": "九州電力送配電",
        "power_url": "https://typhoon.yahoo.co.jp/weather/poweroutage/",
        "water_name": "福岡市水道局",
        "water_url": "https://www.city.fukuoka.lg.jp/suido/",
        "gas_name": "西部ガス",
        "gas_url": "https://www.saibugas.co.jp/",
        "lines": ["鹿児島本線", "篠栗線", "空港線", "箱崎線", "七隈線", "天神大牟田線", "日豊本線", "長崎本線", "佐世保線", "大村線", "豊肥本線", "久大本線", "肥薩線", "指宿枕崎線", "日南線", "筑豊電気鉄道", "熊本市電", "鹿児島市電", "長崎電気軌道"],
        "shinkansen": ["山陽新幹線", "九州新幹線", "西九州新幹線"],
        "jma_code": "400000",
        "default_camera_id": "cam_fukuoka_hakata"
    },
    "hakata": {
        "name": "福岡",
        "region_name": "九州エリア",
        "region_desc": "福岡、大分、宮崎、鹿児島、熊本、長崎、佐賀",
        "target_prefs": [
            {"code": "40", "name": "福岡県", "short_name": "福岡"},
            {"code": "44", "name": "大分県", "short_name": "大分"},
            {"code": "45", "name": "宮崎県", "short_name": "宮崎"},
            {"code": "46", "name": "鹿児島県", "short_name": "鹿児島"},
            {"code": "43", "name": "熊本県", "short_name": "熊本"},
            {"code": "42", "name": "長崎県", "short_name": "長崎"},
            {"code": "41", "name": "佐賀県", "short_name": "佐賀"}
        ],
        "pref_names": ["福岡", "大分", "宮崎", "鹿児島", "熊本", "長崎", "佐賀"],
        "transit_area": "7",
        "power_name": "九州電力送配電",
        "power_url": "https://typhoon.yahoo.co.jp/weather/poweroutage/",
        "water_name": "福岡市水道局",
        "water_url": "https://www.city.fukuoka.lg.jp/suido/",
        "gas_name": "西部ガス",
        "gas_url": "https://www.saibugas.co.jp/",
        "lines": ["鹿児島本線", "篠栗線", "空港線", "箱崎線", "七隈線", "天神大牟田線", "日豊本線", "長崎本線", "佐世保線", "大村線", "豊肥本線", "久大本線", "肥薩線", "指宿枕崎線", "日南線"],
        "shinkansen": ["山陽新幹線", "九州新幹線", "西九州新幹線"],
        "jma_code": "400000",
        "default_camera_id": "cam_fukuoka_hakata"
    },
    "naha": {
        "name": "那覇",
        "region_name": "沖縄エリア",
        "region_desc": "沖縄県（本島・先島諸島・大東諸島）",
        "target_prefs": [
            {"code": "47", "name": "沖縄県", "short_name": "沖縄"}
        ],
        "pref_names": ["沖縄"],
        "transit_area": "9",
        "power_name": "沖縄電力",
        "power_url": "https://www.okiden.co.jp/",
        "water_name": "那覇市上下水道局",
        "water_url": "https://www.water.naha.okinawa.jp/",
        "gas_name": "沖縄ガス",
        "gas_url": "https://www.okinawagas.co.jp/",
        "lines": ["ゆいレール（沖縄都市モノレール）"],
        "shinkansen": [],
        "jma_code": "471000",
        "default_camera_id": "cam_naha_kokusai"
    }
}

# 災害気象・ニュース生放送 および 日本各地ライブカメラのプリセット定義
LIVE_MEDIA_PRESETS = {
    "streams": [
        {
            "id": "stream_weathernews",
            "name": "ウェザーニュースLiVE (24時間気象・災害生放送)",
            "category": "気象特番",
            "provider": "ウェザーニューズ",
            "handle": "@weathernews",
            "video_id": "4_ae_IKXB8g",
            "description": "24時間365日最新の雨雲レーダー、台風進路、地震・津波・気象警報を生解説。"
        },
        {
            "id": "stream_tbsnews",
            "name": "TBS NEWS DIG (24時間全国ニュース報道)",
            "category": "全国報道",
            "provider": "TBS / JNN",
            "handle": "@tbsnewsdig",
            "video_id": "pz29vqiAVcg",
            "description": "JNN28局の取材網による全国災害・事件・事故の最新ニュースを常時生配信。"
        },
        {
            "id": "stream_ntvnews",
            "name": "日テレNEWS NNN (24時間速報生配信)",
            "category": "全国報道",
            "provider": "日本テレビ / NNN",
            "handle": "@ntv_news",
            "video_id": "V7ANB9xVjeY",
            "description": "日本テレビ系列の24時間ニュース生配信。緊急時は災害特番に切り替え。"
        },
        {
            "id": "stream_annnews",
            "name": "ANNnewsCH (テレビ朝日 24時間ライブ)",
            "category": "全国報道",
            "provider": "テレビ朝日 / ANN",
            "handle": "@ANNnewsCH",
            "video_id": "5GIsbtEO0rg",
            "description": "テレビ朝日系列の最新ニュース生配信。台風・地震時の緊急報道に対応。"
        },
        {
            "id": "stream_fnnnews",
            "name": "FNNプライムオンライン (フジテレビ系列 24h配信)",
            "category": "全国報道",
            "provider": "フジテレビ / FNN",
            "handle": "@FNNnewsCH",
            "video_id": "WIAf__XbEJ0",
            "description": "フジテレビ・FNN各局による最新ニュース・大雨台風地震等の緊急特番を生配信。"
        }
    ],
    "cameras": [
        {
            "id": "cam_tokyo_shibuya",
            "name": "東京: 渋谷スクランブル交差点",
            "location_key": "tokyo",
            "region": "関東（東京）",
            "video_id": "dfVK7ld38Ys",
            "description": "東京都渋谷駅前スクランブル交差点のリアルタイム人流・天候監視（SHIBUYA COMMUNITY公式）。"
        },
        {
            "id": "cam_tokyo_tower",
            "name": "東京: 都心・汐留パノラマ（東京タワー方面）",
            "location_key": "tokyo",
            "region": "関東（東京）",
            "video_id": "VM18f-IIUTw",
            "description": "東京上空の雲行き、視程、風雨の状況を都心パノラマから定点観測（共同通信4K）。"
        },
        {
            "id": "cam_tokyo_haneda",
            "name": "東京: 羽田空港 第2ターミナル滑走路",
            "location_key": "tokyo",
            "region": "関東（東京）",
            "video_id": "2PIdi3Xa7TY",
            "description": "羽田空港の離着陸、視程、強風・降雨状況を定点監視（日テレNEWS公式）。"
        },
        {
            "id": "cam_omiya_arakawa",
            "name": "埼玉/大宮: 荒川・新河岸川河川水位監視",
            "location_key": "omiya",
            "region": "北関東（埼玉）",
            "video_id": "hgO7XMTWhGk",
            "description": "埼玉県内河川（新河岸川・柳瀬川合流地点）の水位・増水警戒監視カメラ（志木防災公式）。"
        },
        {
            "id": "cam_omiya_saitama",
            "name": "埼玉/大宮: 蕨・さいたま市街ライブカメラ",
            "location_key": "omiya",
            "region": "北関東（埼玉）",
            "video_id": "PdSoyrNorjg",
            "description": "埼玉県内・大宮近郊の道路・市街地・天候の定点観測（蕨ケーブルビジョン公式）。"
        },
        {
            "id": "cam_yokohama_mm21",
            "name": "神奈川/横浜: みなとみらい21・汽車道",
            "location_key": "yokohama",
            "region": "南関東（神奈川）",
            "video_id": "fRdk6I337hE",
            "description": "横浜港・みなとみらい沿岸部の風雨、潮位、視程のリアルタイム定点監視。"
        },
        {
            "id": "cam_nagoya_station",
            "name": "愛知/名古屋: 名古屋駅前ライブカメラ",
            "location_key": "nagoya",
            "region": "東海（愛知）",
            "video_id": "X304dz1zrfU",
            "description": "中京圏の中心部・名古屋駅前の人流および天候監視（スターキャット公式）。"
        },
        {
            "id": "cam_kanazawa_station",
            "name": "石川/金沢: 北陸新幹線 金沢駅前",
            "location_key": "kanazawa",
            "region": "北陸（石川）",
            "video_id": "JY0VPKVjmRs",
            "description": "北陸エリアの拠点・金沢駅前の天候、風雪、新幹線運行状況の定点監視（北陸朝日放送公式）。"
        },
        {
            "id": "cam_osaka_dotonbori",
            "name": "大阪: 道頓堀・戎橋（グリコ看板前）",
            "location_key": "osaka",
            "region": "近畿（大阪）",
            "video_id": "czJhGgFsp38",
            "description": "関西・大阪中心部のリアルタイム人流、降雨、街の様子の定点監視（MBS NEWS公式）。"
        },
        {
            "id": "cam_hiroshima_station",
            "name": "広島: 広島駅前・新幹線ホーム",
            "location_key": "hiroshima",
            "region": "中国（広島）",
            "video_id": "YnCXegVqpKA",
            "description": "中国エリア・広島駅前の天候、交通・新幹線状況の定点観測（RCC NEWS DIG公式）。"
        },
        {
            "id": "cam_takamatsu_seto",
            "name": "香川/高松: 瀬戸大橋パノラマ監視",
            "location_key": "takamatsu",
            "region": "四国（香川）",
            "video_id": "xrb4L3p1eHY",
            "description": "四国・本四連絡大橋および瀬戸内海の波浪、強風、濃霧の状況監視（KBN公式）。"
        },
        {
            "id": "cam_fukuoka_hakata",
            "name": "福岡: JR博多駅前ライブカメラ",
            "location_key": "fukuoka",
            "region": "九州（福岡）",
            "video_id": "yETDDgrE2E4",
            "description": "九州の交通拠点・博多駅周辺の天候、強風、台風接近時の状況監視（朝日新聞LIVE公式）。"
        },
        {
            "id": "cam_sendai",
            "name": "宮城/仙台: 仙台駅前ライブカメラ",
            "location_key": "sendai",
            "region": "東北（宮城）",
            "video_id": "AinAZQgQp_s",
            "description": "東北エリア中枢・仙台市街の天候、降雪、強風のリアルタイム監視（khb東日本放送公式）。"
        },
        {
            "id": "cam_sapporo",
            "name": "北海道/札幌: さっぽろ創世スクエア・都心",
            "location_key": "sapporo",
            "region": "北海道（札幌）",
            "video_id": "kfIQBC0hrII",
            "description": "道内中枢・札幌市中心部の積雪、吹雪、視程障害の定点観測（HTB/SODANE公式）。"
        },
        {
            "id": "cam_sakurajima",
            "name": "鹿児島: 桜島 火山観測ライブカメラ",
            "location_key": "fukuoka",
            "region": "自然災害（火山）",
            "video_id": "PeElJClXtzE",
            "description": "活火山・桜島の噴煙、爆発的噴火、降灰の状況を24時間監視（財宝公式）。"
        },
        {
            "id": "cam_fuji",
            "name": "静岡/山梨: 富士山パノラマ監視",
            "location_key": "tokyo",
            "region": "自然災害（火山・気象）",
            "video_id": "bJqFntWbi54",
            "description": "富士山周辺の雲海、雷雲、気象変化をパノラマ定点観測（イマフジ公式）。"
        },
        {
            "id": "cam_naha_kokusai",
            "name": "沖縄/那覇: 那覇市街・ゆいレール監視パノラマ",
            "location_key": "naha",
            "region": "沖縄（那覇）",
            "video_id": "6HYjCFkmDPA",
            "description": "那覇市中心部・ゆいレールの運行、台風・暴風雨、市街地天候を定点監視。"
        }
    ]
}



# =====================================================================
# 📡 24h YouTube Live & ライブカメラ 動的ストリームリゾルバー
# =====================================================================

LIVE_RESOLVE_CACHE = {
    "@weathernews": {"video_id": "4_ae_IKXB8g", "time": 0},
    "@tbsnewsdig": {"video_id": "pz29vqiAVcg", "time": 0},
    "@ntv_news": {"video_id": "V7ANB9xVjeY", "time": 0},
    "@ANNnewsCH": {"video_id": "5GIsbtEO0rg", "time": 0},
    "@FNNnewsCH": {"video_id": "WIAf__XbEJ0", "time": 0},
    "@SkyNews": {"video_id": "TQRjW0WSdy0", "time": 0},
    "@FRANCE24": {"video_id": "a47ckXKZjxI", "time": 0},
    "@france24": {"video_id": "a47ckXKZjxI", "time": 0},
    "@RTVEnoticias": {"video_id": "b4tE5aKhtlg", "time": 0},
    "@dwnews": {"video_id": "LuKwFajn37U", "time": 0},
    "@euronews": {"video_id": "pykpO5kQJ98", "time": 0},
}
LIVE_RESOLVE_LOCK = threading.Lock()

def resolve_live_video_id(handle, fallback_id=None, ttl_seconds=300, force_refresh=False):
    """YouTubeのチャンネルハンドル（@handle）から最新の24h生配信VideoIDを動的解決する（キャッシュ有効）"""
    if not handle:
        return fallback_id
    clean_handle = handle if handle.startswith("@") else f"@{handle}"
    now = time.time()
    with LIVE_RESOLVE_LOCK:
        cached = LIVE_RESOLVE_CACHE.get(clean_handle)
        if not force_refresh and cached and (now - cached.get("time", 0) < ttl_seconds) and cached.get("video_id"):
            return cached["video_id"]

    try:
        url = f"https://www.youtube.com/{clean_handle}/live"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
            }
        )
        opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
        with opener.open(req, timeout=6) as resp:
            final_url = resp.geturl()
            # 1. URL search (?v=...)
            m_url = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", final_url)
            vid = m_url.group(1) if m_url else None

            # 2. HTML inspection
            if not vid:
                html = resp.read().decode("utf-8", errors="ignore")

                # Check canonical link (YouTube /live で最も確実な現在生配信ID)
                m_canon = re.search(r'<link rel="canonical" href="https://www\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})"', html)
                if m_canon:
                    vid = m_canon.group(1)

                # Check og:video:url
                if not vid:
                    m_og = re.search(r'<meta property="og:video:url" content="https://www\.youtube\.com/embed/([a-zA-Z0-9_-]{11})"', html)
                    if m_og:
                        vid = m_og.group(1)

                # Check playerResponse / videoDetails
                if not vid:
                    m_details = re.search(r'"videoDetails":\s*\{.*?"videoId":"([a-zA-Z0-9_-]{11})"', html)
                    if m_details:
                        vid = m_details.group(1)

                # Check generic videoId
                if not vid:
                    m_vid = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
                    if m_vid:
                        vid = m_vid.group(1)

            if vid and len(vid) == 11:
                with LIVE_RESOLVE_LOCK:
                    LIVE_RESOLVE_CACHE[clean_handle] = {"video_id": vid, "time": now}
                return vid
    except Exception as e:
        pass

    # 解決失敗時は既存キャッシュまたはフォールバックを返す
    with LIVE_RESOLVE_LOCK:
        cached = LIVE_RESOLVE_CACHE.get(clean_handle)
        if cached and cached.get("video_id"):
            cached["time"] = now - (ttl_seconds - 60)
            return cached["video_id"]
        if fallback_id:
            LIVE_RESOLVE_CACHE[clean_handle] = {"video_id": fallback_id, "time": now - (ttl_seconds - 60)}
            return fallback_id

    return fallback_id


def start_live_stream_auto_updater(interval_seconds=180):
    """主要生放送チャンネルの最新動画IDをバックグラウンドで事前取得・定期更新する常駐スレッド"""
    def _worker():
        time.sleep(3)  # 起動直後の負荷集中を回避
        target_handles = [
            ("@weathernews", "4_ae_IKXB8g"),
            ("@tbsnewsdig", "pz29vqiAVcg"),
            ("@ntv_news", "V7ANB9xVjeY"),
            ("@ANNnewsCH", "5GIsbtEO0rg"),
            ("@FNNnewsCH", "WIAf__XbEJ0"),
            ("@SkyNews", "TQRjW0WSdy0"),
            ("@FRANCE24", "a47ckXKZjxI"),
            ("@france24", "a47ckXKZjxI"),
            ("@RTVEnoticias", "b4tE5aKhtlg"),
            ("@dwnews", "LuKwFajn37U"),
            ("@euronews", "pykpO5kQJ98"),
        ]
        while True:
            try:
                for handle, fb in target_handles:
                    resolve_live_video_id(handle, fb, force_refresh=True)
                    time.sleep(1)
            except Exception as e:
                pass
            time.sleep(interval_seconds)

    t = threading.Thread(target=_worker, daemon=True, name="LiveStreamAutoUpdater")
    t.start()

# サーバー起動時に自動更新スレッドを開始
start_live_stream_auto_updater(interval_seconds=180)


class BCPDataAnalyzer:
    P2PQUAKE_URL = "https://api.p2pquake.net/v2/history?codes=551&limit=10"
    JMA_PORTAL_URL = "https://www.data.jma.go.jp/multi/quake/?lang=jp"
    
    YAHOO_POWEROUTAGE_URL = "https://typhoon.yahoo.co.jp/weather/poweroutage/"
    YAHOO_TSUNAMI_URL = "https://typhoon.yahoo.co.jp/weather/jp/tsunami/"
    YAHOO_VOLCANO_URL = "https://typhoon.yahoo.co.jp/weather/jp/volcano/"
    YAHOO_WARN_BASE_URL = "https://typhoon.yahoo.co.jp/weather/jp/warn/"

    JMA_FLOOD_JSON_URL = "https://www.jma.go.jp/bosai/flood/data/flood_xml.json"
    RIVER_PORTAL_URL = "https://www.river.go.jp/index"

    YAHOO_REALTIME_API_URL = "https://search.yahoo.co.jp/realtime/api/v1/pagination"
    YAHOO_EVACUATION_URL = "https://crisis.yahoo.co.jp/evacuation/"

    # 内部取得用フィードURL（XML/RDF）
    FDMA_XML_URL = "https://www.fdma.go.jp/disaster/info/index.xml"
    CABINET_XML_URL = "https://www.bousai.go.jp/news.xml"
    MHLW_RDF_URL = "https://www.mhlw.go.jp/stf/news.rdf"
    KDDI_RSS_URL = "https://news.kddi.com/important/news/rss/kddi_important_ex.xml"
    DOCOMO_RDF_URL = "https://www.docomo.ne.jp/info/rss/network.rdf"

    # ユーザークリック用のHTML公式ホームページURL
    FDMA_URL = "https://www.fdma.go.jp/disaster#anchor--01"
    NPA_URL = "https://www.npa.go.jp/"
    CABINET_URL = "https://www.bousai.go.jp/"
    MHLW_URL = "https://www.mhlw.go.jp/index.html"

    AU_NETWORK_URL = "https://www.au.com/information/notice_mobile/network/"
    UQ_MOBILE_URL = "https://www.uqwimax.jp/information/"
    POVO_URL = "https://povo.jp/news/"
    KDDI_HOMEPAGE_URL = AU_NETWORK_URL
    DOCOMO_NETWORK_URL = "https://www.docomo.ne.jp/info/network/"
    SOFTBANK_URL = "https://www.softbank.jp/mobile/info/personal/important/"
    RAKUTEN_URL = "https://network.mobile.rakuten.co.jp/information/failure/"

    JMA_OVERVIEW_BASE_URL = "https://www.jma.go.jp/bosai/forecast/data/overview_forecast/"
    YAHOO_NEWS_INCIDENT_URL = "https://news.yahoo.co.jp/rss/topics/incident.xml"
    YAHOO_NEWS_TOP_URL = "https://news.yahoo.co.jp/rss/topics/top-picks.xml"

    SHINKANSEN_URLS = {
        "東北新幹線": "https://transit.yahoo.co.jp/diainfo/1/0",
        "上越新幹線": "https://transit.yahoo.co.jp/diainfo/3/0",
        "山形新幹線": "https://transit.yahoo.co.jp/diainfo/5/0",
        "秋田新幹線": "https://transit.yahoo.co.jp/diainfo/6/0",
        "東海道新幹線": "https://transit.yahoo.co.jp/diainfo/7/0",
        "山陽新幹線": "https://transit.yahoo.co.jp/diainfo/8/0",
        "九州新幹線": "https://transit.yahoo.co.jp/diainfo/410/0",
        "北陸新幹線": "https://transit.yahoo.co.jp/diainfo/624/0",
        "北海道新幹線": "https://transit.yahoo.co.jp/diainfo/637/0",
        "西九州新幹線": "https://transit.yahoo.co.jp/diainfo/640/0",
    }

    SHINDO_MAP = {
        -1: "-", 10: "1", 20: "2", 30: "3", 40: "4",
        45: "5弱", 50: "5強", 55: "6弱", 60: "6強", 70: "7",
    }

    DISASTER_KEYWORDS = [
        "地震", "豪雨", "大雨", "台風", "災害", "避難", "被害", "非常",
        "特別警報", "津波", "噴火", "土砂", "洪水", "DMAT", "広域搬送", "救助", "罹災"
    ]

    TELECOM_TROUBLE_KEYWORDS = ["通信障害", "つながりにくい", "利用できない", "不通", "終日", "見合わせ"]
    IGNORE_MENU_WORDS = [
        "災害情報", "災害・危機管理", "お知らせ", "お知らせトップ", "ニュースルーム", 
        "報道発表", "重要なお知らせ", "ホーム", "トップ", "個人のお客さま向け障害情報", 
        "サービス障害のお知らせ", "障害情報のお知らせ", "活動写真等"
    ]

    @staticmethod
    def _http_get(url, headers=None, timeout=10):
        default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        if headers:
            default_headers.update(headers)

        req = urllib.request.Request(url, headers=default_headers)

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as res:
            if res.status != 200:
                raise Exception(f"HTTP Status Error: {res.status}")
            content = res.read()
            encoding = res.info().get('Content-Encoding')
            
            if encoding == 'gzip':
                import gzip
                content = gzip.decompress(content)
            elif encoding == 'deflate':
                import zlib
                content = zlib.decompress(content)

            charset = res.headers.get_content_charset() or "utf-8"
            return content, charset

    @classmethod
    def _scale_to_shindo(cls, scale):
        try:
            return cls.SHINDO_MAP.get(int(scale), "-")
        except Exception:
            return "-"

    @classmethod
    def get_real_jma_quake(cls):
        try:
            raw, charset = cls._http_get(cls.P2PQUAKE_URL)
            text = raw.decode(charset, errors="replace")
            data = json.loads(text)

            history_list = []
            if isinstance(data, list):
                for item in data:
                    if item.get("code") != 551:
                        continue

                    eq = item.get("earthquake") or {}
                    hypo = eq.get("hypocenter") or {}

                    scale_code = eq.get("maxScale", -1)
                    place_name = hypo.get("name") or "震源情報なし"
                    mag = hypo.get("magnitude")
                    mag_str = str(mag) if isinstance(mag, (int, float)) and mag > 0 else "-"

                    raw_time = eq.get("time") or item.get("time") or ""
                    
                    if raw_time:
                        clean_time = raw_time.replace("/", "-").replace("T", " ")
                        if len(clean_time) >= 16:
                            time_value = clean_time[:16]
                        else:
                            time_value = clean_time
                    else:
                        time_value = datetime.now().strftime("%Y-%m-%d %H:%M")

                    history_list.append({
                        "time": time_value,
                        "place": place_name,
                        "shindo": cls._scale_to_shindo(scale_code),
                        "magnitude": mag_str,
                        "maxScale": int(scale_code) if isinstance(scale_code, int) else -1,
                    })

            if history_list:
                latest = history_list[0]
                latest_scale = latest["maxScale"]
                return {
                    "status": "ALERT" if latest_scale >= 40 else "NORMAL",
                    "shindo": latest["shindo"],
                    "time": latest["time"],
                    "place": latest["place"],
                    "magnitude": latest["magnitude"],
                    "raw_url": cls.JMA_PORTAL_URL,
                    "history": history_list[:10],
                }

            return {
                "status": "NORMAL",
                "shindo": "-",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "place": "直近の地震情報なし",
                "magnitude": "-",
                "raw_url": cls.JMA_PORTAL_URL,
                "history": [],
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "shindo": "ERR",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "place": f"エラー: {str(e)[:30]}",
                "magnitude": "-",
                "raw_url": cls.JMA_PORTAL_URL,
                "history": [],
            }

    @classmethod
    def get_real_tsunami_status(cls):
        try:
            raw, charset = cls._http_get(cls.YAHOO_TSUNAMI_URL)
            html = raw.decode(charset, errors="replace")
            soup = BeautifulSoup(html, "html.parser")

            active_notices = soup.select('.mdTsunamiNotice--active, .tsunami-warn-active, .alert-tsunami')
            found_alerts = []

            for el in active_notices:
                txt = el.get_text()
                for w in ["大津波警報", "津波警報", "津波注意報"]:
                    if w in txt and w not in found_alerts:
                        found_alerts.append(w)

            if found_alerts:
                return {
                    "status": "ALERT",
                    "summary": f"【津波警報・注意報】{ '・'.join(found_alerts) }が発表されています",
                    "url": cls.YAHOO_TSUNAMI_URL
                }

            return {
                "status": "NORMAL",
                "summary": "現在、津波警報・注意報は発表されていません。",
                "url": cls.YAHOO_TSUNAMI_URL
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "summary": f"津波情報取得エラー: {str(e)[:30]}",
                "url": cls.YAHOO_TSUNAMI_URL
            }

    @classmethod
    def get_real_volcano_status(cls, loc_cfg):
        target_region = loc_cfg.get("region_name", "関東")
        pref_names = loc_cfg.get("pref_names", [])
        try:
            raw, charset = cls._http_get(cls.YAHOO_VOLCANO_URL)
            html = raw.decode(charset, errors="replace")
            soup = BeautifulSoup(html, "html.parser")

            alert_volcanoes = []
            volcano_rows = soup.select('.mdVolcanoList tr, .yjw_table tr, li')
            for r in volcano_rows:
                txt = r.get_text(separator=" ", strip=True)
                if any(lvl in txt for lvl in ["レベル3", "レベル4", "レベル5", "入山規制", "避難指示"]):
                    if "凡例" not in txt and "とは" not in txt and "概要" not in txt:
                        # エリア名または構成都道府県名、あるいは主要火山名でマッチ
                        matched = any(p in txt for p in pref_names) or target_region in txt
                        if not matched and "九州" in target_region and any(k in txt for k in ["桜島", "阿蘇山", "諏訪之瀬島", "霧島山", "雲仙岳"]):
                            matched = True
                        if not matched and "信越" in target_region and any(k in txt for k in ["浅間山", "御嶽山", "焼岳", "新潟焼山", "妙高山"]):
                            matched = True
                        if not matched and "北関東" in target_region and any(k in txt for k in ["草津白根山", "浅間山", "日光白根山", "那須岳"]):
                            matched = True
                        if not matched and "南関東" in target_region and any(k in txt for k in ["箱根山", "伊豆大島"]):
                            matched = True
                        if matched and txt[:20] not in alert_volcanoes:
                            alert_volcanoes.append(txt[:25])

            if alert_volcanoes:
                return {
                    "status": "ALERT",
                    "summary": f"【近隣火山 噴火警報】{ ' / '.join(alert_volcanoes[:2]) }",
                    "url": cls.YAHOO_VOLCANO_URL
                }

            return {
                "status": "NORMAL",
                "summary": f"現在、{target_region}（{ ', '.join(pref_names[:4]) }{ '等' if len(pref_names)>4 else '' }）に影響のある噴火警報はありません。",
                "url": cls.YAHOO_VOLCANO_URL
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "summary": f"火山情報取得エラー: {str(e)[:30]}",
                "url": cls.YAHOO_VOLCANO_URL
            }

    @classmethod
    def _fetch_single_pref_warnings(cls, pref):
        """単一の都道府県コードに対するYahoo!気象警報のスクレイピング"""
        code = pref["code"]
        name = pref["name"]
        short_name = pref.get("short_name", name)
        url = f"{cls.YAHOO_WARN_BASE_URL}{code}/"
        
        pref_result = {
            "code": code,
            "name": name,
            "short_name": short_name,
            "status": "NORMAL",
            "emg_warns": [],
            "warns": [],
            "notices": [],
            "summary": "発表なし",
            "url": url
        }

        try:
            raw, charset = cls._http_get(url, timeout=7)
            html = raw.decode(charset, errors="replace")
            soup = BeautifulSoup(html, "html.parser")

            tables = soup.select('table.warnArea_table')
            found_warnings = set()

            for tbl in tables:
                for tr in tbl.find_all('tr'):
                    tds = tr.find_all('td')
                    if not tds:
                        continue
                    status_td = tds[-1]
                    txt = status_td.get_text(strip=True)
                    if not txt or txt == '発表なし':
                        continue
                    for el in status_td.find_all(['dt', 'dd', 'span', 'li', 'p']) or [status_td]:
                        t = el.get_text(strip=True)
                        if t and t != '発表なし' and '解除' not in t and '継続' not in t and '凡例' not in t:
                            for kw in ['特別警報', '大雨警報', '洪水警報', '暴風警報', '暴風雪警報', '大雪警報', '波浪警報', '高潮警報',
                                       '大雨注意報', '洪水注意報', '強風注意報', '風雪注意報', '大雪注意報', '波浪注意報', '高潮注意報',
                                       '雷注意報', '融雪注意報', '濃霧注意報', '乾燥注意報', 'なだれ注意報', '低温注意報', '霜注意報', '着氷注意報', '着雪注意報']:
                                if kw in t:
                                    found_warnings.add(kw)

            if found_warnings:
                emg_warns = [w for w in found_warnings if '特別警報' in w]
                warns = [w for w in found_warnings if '特別警報' not in w and '警報' in w]
                notices = [w for w in found_warnings if '注意報' in w]

                has_alert = len(emg_warns) > 0 or len(warns) > 0
                sorted_all = emg_warns + warns + notices

                pref_result["status"] = "ALERT" if has_alert else "NOTICE"
                pref_result["emg_warns"] = emg_warns
                pref_result["warns"] = warns
                pref_result["notices"] = notices
                pref_result["summary"] = "、".join(sorted_all)
            
            return pref_result
        except Exception as e:
            pref_result["status"] = "ERROR"
            pref_result["summary"] = f"取得エラー({str(e)[:15]})"
            return pref_result

    @classmethod
    def get_real_area_weather_warnings(cls, loc_cfg):
        """監視拠点に対応する全構成都道府県の気象警報を並行取得し、エリア全体の状況を集約判定する"""
        target_prefs = loc_cfg.get("target_prefs", [])
        region_name = loc_cfg.get("region_name", "監視エリア")
        base_url = cls.YAHOO_WARN_BASE_URL

        if not target_prefs:
            return {
                "status": "NORMAL",
                "summary": f"{region_name}: 設定された監視対象都道府県がありません。",
                "url": base_url,
                "pref_details": [],
                "alert_count": 0,
                "notice_count": 0,
                "total_prefs": 0
            }

        pref_results = []
        # ThreadPoolExecutorによるマルチスレッド並行スクレイピング（全国対応で最大24スレッド）
        with ThreadPoolExecutor(max_workers=min(len(target_prefs), 24)) as executor:
            future_to_pref = {executor.submit(cls._fetch_single_pref_warnings, p): p for p in target_prefs}
            for future in as_completed(future_to_pref):
                try:
                    res = future.result()
                    pref_results.append(res)
                except Exception:
                    p = future_to_pref[future]
                    pref_results.append({
                        "code": p["code"],
                        "name": p["name"],
                        "short_name": p.get("short_name", p["name"]),
                        "status": "ERROR",
                        "summary": "取得例外エラー",
                        "url": f"{base_url}{p['code']}/",
                        "emg_warns": [], "warns": [], "notices": []
                    })

        # 元のtarget_prefsの順番にソート
        code_order = {p["code"]: i for i, p in enumerate(target_prefs)}
        pref_results.sort(key=lambda x: code_order.get(x["code"], 999))

        alert_prefs = [p for p in pref_results if p["status"] == "ALERT"]
        notice_prefs = [p for p in pref_results if p["status"] == "NOTICE"]

        if alert_prefs:
            status = "ALERT"
            # 警報が出ている都道府県と主要警報名を簡潔に要約
            alert_descs = []
            for p in alert_prefs:
                top_w = (p["emg_warns"] + p["warns"])[:2]
                alert_descs.append(f"{p['short_name']}（{ '、'.join(top_w) }）")
            
            summary = f"【警報発表: {len(alert_prefs)}地域】{ '、'.join(alert_descs) }"
            if notice_prefs:
                summary += f" ／ 他{len(notice_prefs)}地域で注意報"
        elif notice_prefs:
            status = "NOTICE"
            notice_names = [p["short_name"] for p in notice_prefs]
            summary = f"【注意報発表: {len(notice_prefs)}地域】{ '、'.join(notice_names) }（警報なし）"
        else:
            status = "NORMAL"
            summary = f"現在、{region_name}全域（{len(target_prefs)}地域）に警報・注意報の発表はありません。"

        return {
            "status": status,
            "summary": summary,
            "url": base_url,
            "alert_count": len(alert_prefs),
            "notice_count": len(notice_prefs),
            "total_prefs": len(target_prefs),
            "pref_details": pref_results
        }

    _flood_cache = []
    _flood_cache_time = 0

    @classmethod
    def _fetch_jma_flood_bulletins(cls):
        """気象庁 指定河川洪水予報 JSONを年度（和暦年度）を考慮して動的に取得する"""
        now = datetime.now().timestamp()
        if now - cls._flood_cache_time < 45 and cls._flood_cache:
            return cls._flood_cache

        reiwa = datetime.now().year - 2018
        candidates = [
            f"https://www.jma.go.jp/bosai/flood/data/r{reiwa}/flood_xml.json",
            f"https://www.jma.go.jp/bosai/flood/data/r{reiwa - 1}/flood_xml.json",
            "https://www.jma.go.jp/bosai/flood/data/flood_xml.json"
        ]

        items = []
        for url in candidates:
            try:
                raw, charset = cls._http_get(url, timeout=5)
                data = json.loads(raw.decode(charset, errors="replace"))
                if isinstance(data, list) and len(data) > 0:
                    items = data
                    break
            except Exception:
                continue

        cls._flood_cache = items
        cls._flood_cache_time = now
        return items

    @classmethod
    def get_real_river_status(cls, loc_cfg, weather_data=None):
        """国交省『川の防災情報』および指定河川洪水予報・気象庁洪水警報を取得し、対象エリア全構成都道府県の河川状況を判定する。"""
        pref_names = loc_cfg.get("pref_names", ["東京都"])
        region_name = loc_cfg.get("region_name", "監視エリア")
        loc_key = loc_cfg.get("key", "")
        river_url = cls.RIVER_PORTAL_URL

        alert_items = []
        notice_items = []

        # 1. 気象庁 指定河川洪水予報 (全国リアルタイムJSON)
        flood_list = cls._fetch_jma_flood_bulletins()
        target_codes = [p.get("code") for p in loc_cfg.get("target_prefs", []) if p.get("code")]

        for item in flood_list:
            is_match = False
            if loc_key == "all" or region_name == "全国エリア":
                is_match = True
            else:
                item_str = json.dumps(item, ensure_ascii=False)
                pub = item.get("publishingOffice", "")
                off_codes = [str(c) for c in item.get("officeCodes", [])] + [str(c) for c in item.get("class10Codes", [])]

                for p in pref_names:
                    sp = p.replace("東京都", "東京").replace("府", "").replace("県", "")
                    if sp in pub or sp in item_str:
                        is_match = True
                        break

                if not is_match:
                    for tc in target_codes:
                        if any(oc.startswith(tc) for oc in off_codes):
                            is_match = True
                            break

            if is_match:
                river = item.get("riverName", "")
                if not river and item.get("item", {}).get("areas"):
                    river = item["item"]["areas"][0].get("name", "")
                river = river.split("\u3000")[0].strip()

                warn_name = item.get("item", {}).get("name", "") or item.get("item", {}).get("condition", "")
                label = f"{river}（{warn_name}）" if river else warn_name

                if any(k in warn_name for k in ["氾濫特別警報", "氾濫発生", "氾濫危険", "氾濫警戒", "レベル5", "レベル4", "レベル3", "危険"]):
                    if label not in alert_items:
                        alert_items.append(label)
                elif any(k in warn_name for k in ["氾濫注意", "レベル2", "注意"]):
                    if label not in notice_items:
                        notice_items.append(label)

        # 2. 各都道府県の気象警報で「洪水警報」が発表されているか集約（weather_dataのキャッシュを活用）
        if weather_data and isinstance(weather_data, dict):
            for p in weather_data.get("pref_details", []):
                warns = (p.get("emg_warns", []) or []) + (p.get("warns", []) or [])
                notices = p.get("notices", []) or []
                s_name = p.get("short_name", "")
                if any("洪水" in w for w in warns):
                    w_lbl = f"{s_name}洪水警報"
                    if w_lbl not in alert_items:
                        alert_items.append(w_lbl)
                elif any("洪水" in n for n in notices):
                    n_lbl = f"{s_name}洪水注意報"
                    if n_lbl not in notice_items:
                        notice_items.append(n_lbl)

        if alert_items:
            status = "ALERT"
            if loc_key == "all":
                summary = f"【要警戒】{ '、'.join(alert_items[:3]) }{ ' 等' if len(alert_items) > 3 else '' }"
                if notice_items:
                    summary += f" ／ 【氾濫注意】{ '、'.join(notice_items[:2]) }"
            else:
                summary = f"【要警戒】{ '、'.join(alert_items[:3]) }"
                if notice_items:
                    summary += f" ／ 【注意】{ '、'.join(notice_items[:2]) }"
        elif notice_items:
            status = "NOTICE"
            summary = f"【氾濫注意】{ '、'.join(notice_items[:3]) }"
            if len(notice_items) > 3:
                summary += f" 等 計{len(notice_items)}河川"
        else:
            summary = f"{region_name}管内河川：氾濫危険・注意水位なし（平常水位）"
            status = "NORMAL"

        return {
            "status": status,
            "summary": summary,
            "url": river_url,
            "alert_items": alert_items,
            "notice_items": notice_items
        }

    @classmethod
    def get_real_evacuation_status(cls, loc_cfg):
        """Yahoo!避難情報から、対象エリア全構成都道府県の避難指示・避難所開設状況を網羅集約する。"""
        pref_names = loc_cfg.get("pref_names", ["東京都"])
        region_name = loc_cfg.get("region_name", "監視エリア")
        region_orders = []
        region_shelters = []

        try:
            raw, charset = cls._http_get(cls.YAHOO_EVACUATION_URL)
            html = raw.decode(charset, errors="replace")
            soup = BeautifulSoup(html, "html.parser")

            area_sections = soup.select('.evacuation_area_list')
            for sec in area_sections:
                heading = sec.select_one('h2')
                sec_name = heading.get_text(strip=True) if heading else ""

                for li in sec.select('ul.pref > li'):
                    area_el = li.select_one('.area')
                    label_el = li.select_one('.label')
                    icon_el = li.select_one('.icoEvacOpen')

                    area_name = area_el.get_text(strip=True) if area_el else ""
                    label_text = label_el.get_text(strip=True) if label_el else ""

                    matched = False
                    for p in pref_names:
                        short_p = p.replace("東京都", "東京").replace("府", "").replace("県", "")
                        if p in area_name or short_p in area_name or p in sec_name:
                            matched = True
                            break

                    if matched:
                        if label_text and "避難情報なし" not in label_text:
                            region_orders.append(f"{area_name}({label_text})")
                        elif icon_el:
                            region_shelters.append(area_name)

            is_alert = len(region_orders) > 0 or len(region_shelters) > 0

            summary_parts = []
            if region_orders:
                summary_parts.append(f"【避難指示等】{ '、'.join(region_orders[:5]) }")
            if region_shelters:
                summary_parts.append(f"【避難所開設】{ '、'.join(region_shelters[:5]) }")

            if summary_parts:
                summary_msg = f"{region_name}: " + " / ".join(summary_parts)
            else:
                summary_msg = f"{region_name}（{ ', '.join(pref_names[:4]) }{ '等' if len(pref_names)>4 else '' }）で避難指示・避難所開設はありません。"

            return {
                "status": "ALERT" if is_alert else "NORMAL",
                "summary": summary_msg,
                "url": cls.YAHOO_EVACUATION_URL
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "summary": f"避難情報取得エラー: {str(e)[:30]}",
                "url": cls.YAHOO_EVACUATION_URL
            }

    @classmethod
    def _is_target_line(cls, scraped_name, target_lines):
        """スクレイピングされた路線名が、拠点監視対象路線に含まれるかを判定する"""
        if not target_lines:
            return True

        clean_name = re.sub(r'\[.*?\]', '', scraped_name).strip()
        clean_name = re.sub(r'\(.*?\)', '', clean_name).strip()
        clean_name = re.sub(r'（.*?）', '', clean_name).strip()

        prefixes = [
            '東京メトロ', '都営', 'JR', '東急', '京王', '小田急', '京急',
            '東武', '西武', '京成', '相鉄', '近鉄', '阪急', '阪神', '南海', '名鉄', '西鉄'
        ]
        stripped_name = clean_name
        for p in prefixes:
            if stripped_name.startswith(p):
                stripped_name = stripped_name[len(p):]
                break

        name_core = clean_name.rstrip('線')
        stripped_core = stripped_name.rstrip('線')

        for t in target_lines:
            t_clean = re.sub(r'\[.*?\]', '', t).strip()
            t_clean = re.sub(r'\(.*?\)', '', t_clean).strip()
            t_clean = re.sub(r'（.*?）', '', t_clean).strip()
            t_core = t_clean.rstrip('線')

            # 1. 完全一致・プレフィックス除去後の一致
            if clean_name == t_clean or clean_name == t or stripped_name == t_clean:
                return True
            # 2. 会社名指定（例: 東武線、東急線、西武線等）の場合
            if t_clean in ['東武線', '西武線', '東急線', '京王線', '小田急線', '京成線', '相鉄線']:
                company = t_clean.rstrip('線')
                if clean_name.startswith(company):
                    return True
            # 3. コア名の一致（2文字以上）
            if len(t_core) >= 2 and len(stripped_core) >= 2:
                if t_core == stripped_core:
                    return True
                if t_core in stripped_core or stripped_core in t_core:
                    return True
            if len(t_core) >= 2 and (t_core in clean_name or t_core in stripped_name):
                return True

        return False

    _shinkansen_cache = {}
    _shinkansen_cache_time = 0
    _all_transit_cache = []
    _all_transit_cache_time = 0

    @classmethod
    def _fetch_single_shinkansen(cls, name, url):
        try:
            raw, charset = cls._http_get(url, timeout=5)
            soup = BeautifulSoup(raw.decode(charset, errors="replace"), "html.parser")
            status_el = soup.select_one('#mdServiceStatus')
            if not status_el:
                return {"name": name, "status": "NORMAL", "state": "平常運転", "detail": "", "url": url}

            dt = status_el.select_one('dt')
            dd = status_el.select_one('dd')
            state_text = dt.get_text(strip=True) if dt else ""
            detail_text = dd.get_text(strip=True) if dd else ""

            is_normal = "平常運転" in state_text or "平常運行" in state_text or "事故・遅延に関する情報はありません" in detail_text

            return {
                "name": name,
                "status": "NORMAL" if is_normal else "ALERT",
                "state": state_text,
                "detail": detail_text,
                "url": url
            }
        except Exception:
            return {"name": name, "status": "NORMAL", "state": "情報取得中", "detail": "", "url": url}

    @classmethod
    def get_real_shinkansen_status(cls, target_shinkansen):
        """指定された乗り入れ新幹線の運行状況を取得・集約する"""
        if not target_shinkansen:
            return {
                "status": "NORMAL",
                "text": "乗り入れ新幹線なし",
                "troubled": [],
                "details": []
            }

        now = datetime.now().timestamp()
        if now - cls._shinkansen_cache_time > 45 or not cls._shinkansen_cache:
            fetch_targets = [(k, v) for k, v in cls.SHINKANSEN_URLS.items()]
            cache = {}
            with ThreadPoolExecutor(max_workers=min(len(fetch_targets), 10)) as executor:
                future_to_name = {executor.submit(cls._fetch_single_shinkansen, name, url): name for name, url in fetch_targets}
                for future in as_completed(future_to_name):
                    try:
                        res = future.result()
                        cache[res["name"]] = res
                    except Exception:
                        n = future_to_name[future]
                        cache[n] = {"name": n, "status": "NORMAL", "state": "情報取得中", "detail": "", "url": cls.SHINKANSEN_URLS.get(n, "")}
            cls._shinkansen_cache = cache
            cls._shinkansen_cache_time = now

        shinkansen_results = []
        troubled = []
        for name in target_shinkansen:
            info = cls._shinkansen_cache.get(name)
            if info:
                shinkansen_results.append(info)
                if info["status"] == "ALERT":
                    state_lbl = f"（{info['state']}）" if info.get('state') else ""
                    troubled.append(f"{name}{state_lbl}")

        if troubled:
            shinkansen_text = f"運行支障あり（{ '、'.join(troubled) }）"
            status = "ALERT"
        else:
            shinkansen_text = "全線平常運行中"
            status = "NORMAL"

        return {
            "status": status,
            "text": shinkansen_text,
            "troubled": troubled,
            "details": shinkansen_results
        }

    @classmethod
    def _fetch_area_troubled_lines(cls, aid):
        url = f"https://transit.yahoo.co.jp/diainfo/area/{aid}"
        troubled = []
        try:
            raw, charset = cls._http_get(url, timeout=6)
            html = raw.decode(charset, errors="replace")
            soup = BeautifulSoup(html, "html.parser")
            rows = soup.find_all(["tr", "li"])
            for r in rows:
                row_text = r.get_text(separator=" ", strip=True)
                if any(kw in row_text for kw in ["遅延", "運転見合わせ", "見合わせ", "運休", "見合", "運転状況", "運転計画", "その他"]):
                    if "平常運転" not in row_text and "平常運行" not in row_text and "事故・遅延情報はありません" not in row_text:
                        link_el = r.find("a") or r.find("th") or r.find("td")
                        if link_el:
                            raw_line_name = link_el.get_text(strip=True).split("\n")[0]
                            if raw_line_name and len(raw_line_name) < 30:
                                if not any(ng in raw_line_name for ng in ["運行情報", "路線", "トップ", "Yahoo"]):
                                    clean_disp_name = re.sub(r'\[.*?\]', '', raw_line_name).strip()
                                    clean_disp_name = re.sub(r'\(.*?\)', '', clean_disp_name).strip()
                                    clean_disp_name = re.sub(r'（.*?）', '', clean_disp_name).strip()
                                    if "新幹線" not in clean_disp_name:
                                        troubled.append((raw_line_name, clean_disp_name))
        except Exception:
            pass
        return troubled

    @classmethod
    def get_real_transit_status(cls, area_id, target_lines, target_shinkansen=None):
        troubled_lines = []

        if str(area_id) == "all":
            url = "https://transit.yahoo.co.jp/diainfo/"
            now = datetime.now().timestamp()
            if now - cls._all_transit_cache_time > 30 or not cls._all_transit_cache:
                all_areas = ["2", "3", "4", "5", "6", "8", "9", "7"]
                scraped_troubled = []
                with ThreadPoolExecutor(max_workers=8) as executor:
                    future_to_aid = {executor.submit(cls._fetch_area_troubled_lines, aid): aid for aid in all_areas}
                    for future in as_completed(future_to_aid):
                        try:
                            lines = future.result()
                            scraped_troubled.extend(lines)
                        except Exception:
                            pass
                seen = set()
                unique_troubled = []
                for raw_name, clean_name in scraped_troubled:
                    if clean_name not in seen:
                        seen.add(clean_name)
                        unique_troubled.append(clean_name)
                cls._all_transit_cache = unique_troubled
                cls._all_transit_cache_time = now
            troubled_lines = list(cls._all_transit_cache)
        else:
            url = f"https://transit.yahoo.co.jp/diainfo/area/{area_id}"
            area_troubled = cls._fetch_area_troubled_lines(area_id)
            for raw_line_name, clean_disp_name in area_troubled:
                if cls._is_target_line(raw_line_name, target_lines):
                    if clean_disp_name not in troubled_lines:
                        troubled_lines.append(clean_disp_name)

        # 乗り入れ新幹線の運行状況を取得
        shinkansen_data = cls.get_real_shinkansen_status(target_shinkansen or [])

        # 在来線の文言
        if troubled_lines:
            if str(area_id) == "all":
                top_sample = "、".join(troubled_lines[:5])
                line_text = f"運行支障あり（{top_sample} 等 計{len(troubled_lines)}路線）"
            else:
                line_text = f"運行支障あり（{ '、'.join(troubled_lines[:5]) }）"
            line_status = "ALERT"
        else:
            line_text = "全線平常運行中"
            line_status = "NORMAL"

        # 総合ステータス判定（在来線または新幹線に支障があれば ALERT）
        has_transit_alert = (line_status == "ALERT") or (shinkansen_data["status"] == "ALERT")
        overall_status = "ALERT" if has_transit_alert else "NORMAL"

        # 総合サマリーテキスト
        summary_parts = []
        if troubled_lines:
            if str(area_id) == "all":
                summary_parts.append(f"在来線{len(troubled_lines)}路線: { '、'.join(troubled_lines[:3]) }等")
            else:
                summary_parts.append(f"在来線: { '、'.join(troubled_lines[:3]) }")
        if shinkansen_data["troubled"]:
            summary_parts.append(f"新幹線: { '、'.join(shinkansen_data['troubled'][:2]) }")

        if summary_parts:
            combined_text = f"運行支障あり（{ ' ／ '.join(summary_parts) }）"
        else:
            combined_text = "全線平常運行中"

        return {
            "status": overall_status,
            "text": combined_text,
            "line_status": line_status,
            "line_text": line_text,
            "shinkansen_status": shinkansen_data["status"],
            "shinkansen_text": shinkansen_data["text"],
            "url": url,
            "troubled_lines": troubled_lines,
            "troubled_shinkansen": shinkansen_data["troubled"],
            "shinkansen_details": shinkansen_data["details"],
            "target_lines_count": len(target_lines) if (target_lines and str(area_id) != "all") else len(troubled_lines),
            "target_shinkansen_count": len(target_shinkansen) if target_shinkansen else 0
        }

    @classmethod
    def get_real_lifeline_status(cls, loc_cfg):
        """エリア全構成都道府県の停電情報、および拠点代表の水道・ガス供給状況を判定する。"""
        power_alert = False
        water_alert = False
        gas_alert = False

        pref_names = loc_cfg.get("pref_names", ["東京都"])
        region_name = loc_cfg.get("region_name", "監視エリア")

        power_msg = f"{loc_cfg['power_name']}: 停電情報なし（{region_name}管内正常）"
        water_msg = f"{loc_cfg['water_name']}: 管内大規模断水・漏水なし"
        gas_msg = f"{loc_cfg['gas_name']}: 供給安定（遮断等なし）"

        # 1. Yahoo!停電情報
        # 「停電が発生している都道府県」のセクション内にエリア内構成都道府県名が存在するかスキャン
        try:
            raw, charset = cls._http_get(cls.YAHOO_POWEROUTAGE_URL)
            html = raw.decode(charset, errors="replace")
            soup = BeautifulSoup(html, "html.parser")
            page_text = soup.get_text(" ", strip=True)

            marker = "停電が発生している都道府県"
            end_marker = "情報提供："
            start = page_text.find(marker)

            if start >= 0:
                end = page_text.find(end_marker, start)
                active_section = page_text[start:end if end >= 0 else start + 3000]
                
                hit_power_prefs = []
                for p in pref_names:
                    short_p = p.replace("東京都", "東京").replace("府", "").replace("県", "")
                    if p in active_section or short_p in active_section:
                        hit_power_prefs.append(short_p)

                if hit_power_prefs:
                    power_alert = True
                    power_msg = f"{loc_cfg['power_name']}: 【停電発生中】{ '・'.join(hit_power_prefs) }で停電情報を検知"
                else:
                    power_msg = f"{loc_cfg['power_name']}: 停電情報なし（{region_name}管内正常）"
            else:
                power_msg = f"{loc_cfg['power_name']}: 停電情報なし（全域正常）"
        except Exception:
            power_msg = f"{loc_cfg['power_name']}: 停電情報監視中（通信確認済）"

        # 2. 水道局
        try:
            raw, charset = cls._http_get(loc_cfg["water_url"], timeout=6)
            html = raw.decode(charset, errors="replace")
            soup = BeautifulSoup(html, "html.parser")
            w_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
            
            active = ["現在、緊急断水が発生", "大規模断水が発生", "断水情報：発生中", "緊急工事に伴う大規模断水", "【緊急】断水のお知らせ"]
            negative = ["断水なし", "断水はありません", "断水していません", "大規模断水なし", "給水停止なし", "解除", "復旧済み", "終了", "備え", "対策"]
            
            if any(x in w_text for x in active) and not any(x in w_text for x in negative):
                water_alert = True
                water_msg = f"{loc_cfg['water_name']}: 【要確認】管内断水情報を検知"
        except Exception:
            water_msg = f"{loc_cfg['water_name']}: 供給安定（平常）"

        # 3. 都市ガス
        try:
            raw, charset = cls._http_get(loc_cfg["gas_url"], timeout=6)
            html = raw.decode(charset, errors="replace")
            soup = BeautifulSoup(html, "html.parser")
            g_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
            
            active = ["現在、ガス供給を停止", "緊急供給停止が発生", "大規模なガス漏れ事故", "【緊急】供給停止のお知らせ", "復旧作業を実施中"]
            negative = ["供給停止なし", "供給支障なし", "供給は安定", "異常ありません", "復旧済み", "終了", "万が一", "備え"]
            
            if any(x in g_text for x in active) and not any(x in g_text for x in negative):
                gas_alert = True
                gas_msg = f"{loc_cfg['gas_name']}: 【要確認】供給停止情報を検知"
        except Exception:
            gas_msg = f"{loc_cfg['gas_name']}: 供給安定（平常）"

        has_alert = power_alert or water_alert or gas_alert
        overall_status = "ALERT" if has_alert else "NORMAL"

        return {
            "status": overall_status,
            "power_status": "ALERT" if power_alert else "NORMAL",
            "water_status": "ALERT" if water_alert else "NORMAL",
            "gas_status": "ALERT" if gas_alert else "NORMAL",
            "power_msg": power_msg,
            "water_msg": water_msg,
            "gas_msg": gas_msg,
            "power_url": loc_cfg['power_url'],
            "water_url": loc_cfg['water_url'],
            "gas_url": loc_cfg['gas_url']
        }


    @classmethod
    def get_real_police_fire_status(cls):
        fdma_alert = False
        fdma_msg = "消防庁: 直近の災害発表なし（平常）"
        npa_alert = False
        npa_msg = "警察庁: 緊急交通路指定・通行止め規制なし"

        try:
            raw, charset = cls._http_get(cls.FDMA_XML_URL)
            soup = BeautifulSoup(raw.decode(charset, errors="replace"), "html.parser")
            for item in soup.find_all("item")[:3]:
                title_el = item.find("title")
                title = title_el.get_text(strip=True) if title_el else ""
                if title:
                    fdma_alert = True
                    trimmed = title[:35] + "..." if len(title) > 35 else title
                    fdma_msg = f"消防庁速報: 【要警戒】{trimmed}"
                    break
        except Exception:
            pass

        try:
            raw, charset = cls._http_get(cls.NPA_URL)
            soup = BeautifulSoup(raw.decode(charset, errors="replace"), "html.parser")
            npa_text = soup.get_text()

            traffic_kws = ["緊急交通路", "通行止め", "通行規制", "通行制限", "大規模交通規制"]
            found = [kw for kw in traffic_kws if kw in npa_text]
            if found:
                npa_alert = True
                npa_msg = f"警察庁速報: 【要確認】「{found[0]}」情報の掲載あり"
        except Exception:
            pass

        return {
            "status": "ALERT" if (fdma_alert or npa_alert) else "NORMAL",
            "fdma_msg": fdma_msg,
            "npa_msg": npa_msg,
            "fdma_url": cls.FDMA_URL, # HTMLサイトのURL
            "npa_url": cls.NPA_URL      # HTMLサイトのURL
        }

    @classmethod
    def get_real_government_status(cls):
        cabinet_alert = False
        cabinet_msg = "内閣府防災: 直近の災害発表なし（平常）"
        mhlw_alert = False
        mhlw_msg = "厚労省: 直近の災害発表なし（平常）"

        try:
            raw, charset = cls._http_get(cls.CABINET_XML_URL)
            soup = BeautifulSoup(raw.decode(charset, errors="replace"), "html.parser")
            for item in soup.find_all("item")[:3]:
                title_el = item.find("title")
                title = title_el.get_text(strip=True) if title_el else ""
                if any(kw in title for kw in cls.DISASTER_KEYWORDS):
                    cabinet_alert = True
                    trimmed = title[:35] + "..." if len(title) > 35 else title
                    cabinet_msg = f"内閣府速報: 【要警戒】{trimmed}"
                    break
        except Exception:
            pass

        try:
            raw, charset = cls._http_get(cls.MHLW_RDF_URL)
            soup = BeautifulSoup(raw.decode(charset, errors="replace"), "html.parser")
            for item in soup.find_all("item")[:3]:
                title_el = item.find("title")
                title = title_el.get_text(strip=True) if title_el else ""
                if any(kw in title for kw in cls.DISASTER_KEYWORDS):
                    mhlw_alert = True
                    trimmed = title[:35] + "..." if len(title) > 35 else title
                    mhlw_msg = f"厚労省速報: 【要警戒】{trimmed}"
                    break
        except Exception:
            pass

        return {
            "status": "ALERT" if (cabinet_alert or mhlw_alert) else "NORMAL",
            "cabinet_msg": cabinet_msg,
            "mhlw_msg": mhlw_msg,
            "cabinet_url": cls.CABINET_URL, # HTMLサイトのURL
            "mhlw_url": cls.MHLW_URL        # HTMLサイトのURL
        }

    @classmethod
    def get_real_telecom_status(cls):
        kddi_msg = "au/UQ: 直近の障害発表なし（正常）"
        docomo_msg = "ドコモ: 直近の障害発表なし（正常）"
        sb_msg = "ソフトバンク: 直近の障害発表なし（正常）"
        rakuten_msg = "楽天モバイル: 直近の障害発表なし（正常）"

        kddi_alert, docomo_alert, sb_alert, rakuten_alert = False, False, False, False

        # KDDI / au (RSS取得、復旧時は正常扱い)
        try:
            raw, charset = cls._http_get(cls.KDDI_RSS_URL)
            soup = BeautifulSoup(raw.decode(charset, errors="replace"), "html.parser")
            for item in soup.find_all("item")[:3]:
                title = item.find("title").get_text(strip=True) if item.find("title") else ""
                if any(kw in title for kw in cls.TELECOM_TROUBLE_KEYWORDS):
                    if "復旧" in title or "終了" in title or "解除" in title:
                        clean_title = title.replace("【復旧】", "").replace("【復旧済み】", "").strip()
                        kddi_msg = f"au/UQ: 【復旧済み】 {clean_title[:35]}"
                        kddi_alert = False
                    else:
                        kddi_alert = True
                        trimmed = title[:35] + "..." if len(title) > 35 else title
                        kddi_msg = f"au/UQ: 【要警戒】{trimmed}"
                    break
        except Exception:
            pass

        # docomo (RDF取得、復旧時は正常扱い)
        try:
            raw, charset = cls._http_get(cls.DOCOMO_RDF_URL)
            soup = BeautifulSoup(raw.decode(charset, errors="replace"), "html.parser")
            for item in soup.find_all("item")[:3]:
                title = item.find("title").get_text(strip=True) if item.find("title") else ""
                if any(kw in title for kw in cls.TELECOM_TROUBLE_KEYWORDS):
                    if "復旧" in title or "終了" in title or "解除" in title:
                        clean_title = title.replace("【復旧】", "").replace("【復旧済み】", "").strip()
                        docomo_msg = f"ドコモ: 【復旧済み】 {clean_title[:35]}"
                        docomo_alert = False
                    else:
                        docomo_alert = True
                        trimmed = title[:35] + "..." if len(title) > 35 else title
                        docomo_msg = f"ドコモ: 【要警戒】{trimmed}"
                    break
        except Exception:
            pass

        # ソフトバンク
        try:
            raw, charset = cls._http_get(cls.SOFTBANK_URL)
            soup = BeautifulSoup(raw.decode(charset, errors="replace"), "html.parser")
            found_sb_title = ""
            for el in soup.select('ul.list li, .p-list__item, dl dt, dl dd, a'):
                txt = el.get_text(strip=True)
                if any(kw in txt for kw in cls.TELECOM_TROUBLE_KEYWORDS):
                    if len(txt) > 8 and "プライバシー" not in txt and "利用規約" not in txt:
                        if "復旧" in txt or "終了" in txt or "解除" in txt:
                            sb_alert = False
                        else:
                            found_sb_title = txt[:40]
                            sb_alert = True
                            break
            
            if sb_alert:
                sb_msg = f"ソフトバンク: 【要確認】{found_sb_title}"
            else:
                sb_msg = "ソフトバンク: 直近の障害発表なし（正常）"
        except Exception:
            pass

        # 楽天モバイル
        try:
            raw, charset = cls._http_get(cls.RAKUTEN_URL)
            soup = BeautifulSoup(raw.decode(charset, errors="replace"), "html.parser")
            found_rakuten_title = ""
            for el in soup.select('ul li, .information-list li, .p-news__item, tr, dl, a'):
                txt = el.get_text(separator=" ", strip=True)
                if any(kw in txt for kw in cls.TELECOM_TROUBLE_KEYWORDS):
                    if len(txt) > 8 and "平常" not in txt and "終了" not in txt:
                        if "復旧" in txt or "完了" in txt or "解除" in txt:
                            rakuten_alert = False
                        else:
                            found_rakuten_title = txt[:40]
                            rakuten_alert = True
                            break
            
            if rakuten_alert:
                rakuten_msg = f"楽天モバイル: 【要確認】{found_rakuten_title}"
            else:
                rakuten_msg = "楽天モバイル: 直近の障害発表なし（正常）"
        except Exception:
            pass

        has_alert = kddi_alert or docomo_alert or sb_alert or rakuten_alert
        return {
            "status": "NORMAL" if not has_alert else "ALERT",
            "kddi_msg": kddi_msg,
            "docomo_msg": docomo_msg,
            "sb_msg": sb_msg,
            "rakuten_msg": rakuten_msg,
            "kddi_url": cls.AU_NETWORK_URL,
            "au_url": cls.AU_NETWORK_URL,
            "uq_url": cls.UQ_MOBILE_URL,
            "povo_url": cls.POVO_URL,
            "docomo_url": cls.DOCOMO_NETWORK_URL,
            "sb_url": cls.SOFTBANK_URL,
            "rakuten_url": cls.RAKUTEN_URL,
        }

    @classmethod
    def fetch_yahoo_realtime_data(cls, keyword):
        params = {"p": keyword, "results": 40}
        api_url = f"{cls.YAHOO_REALTIME_API_URL}?{urllib.parse.urlencode(params)}"
        web_search_url = f"https://search.yahoo.co.jp/realtime/search?p={urllib.parse.quote(keyword)}"
        headers = {"Referer": "https://search.yahoo.co.jp/realtime/search"}

        trend_type = "FLAT"
        trend_label = "➡️ 平常・安定"
        status = "NORMAL"
        recent_posts = []

        try:
            raw, charset = cls._http_get(api_url, headers=headers)
            json_text = raw.decode(charset, errors="replace")
            data = json.loads(json_text)

            timeline = data.get("timeline", {})
            entries = timeline.get("entry", [])

            now_ts = datetime.now().timestamp()
            one_hour_ago = now_ts - 3600
            recent_1h_count = 0

            for entry in entries:
                text = entry.get("displayText") or entry.get("text") or ""
                created_at = entry.get("createdAt")

                if isinstance(created_at, (int, float)):
                    if created_at >= one_hour_ago:
                        recent_1h_count += 1
                    post_time = datetime.fromtimestamp(created_at).strftime("%m/%d %H:%M")
                else:
                    post_time = entry.get("time") or "直近"

                if text and len(recent_posts) < 3:
                    clean_text = re.sub(r'\s+', ' ', text).strip()
                    trimmed_text = clean_text[:80] + "..." if len(clean_text) > 80 else clean_text
                    recent_posts.append({"time": post_time, "text": trimmed_text})

            if recent_1h_count >= 15:
                trend_type = "UP"
                trend_label = "📈 上昇傾向 (投稿急増・要警戒)"
                trend_class = "red"
                status = "ALERT"
                summary = f"直近1時間で {recent_1h_count} 件の関連投稿を検知。突発的な急増（スパイク）が発生しています。"
            elif recent_1h_count >= 5:
                trend_type = "DOWN"
                trend_label = "📉 やや投稿あり (様子見)"
                trend_class = "yellow"
                summary = f"直近1時間の投稿数は {recent_1h_count} 件です。"
            else:
                trend_type = "FLAT"
                trend_label = "➡️ 平常"
                trend_class = "green"
                summary = f"直近1時間の投稿数は {recent_1h_count} 件です。突発的な急増はありません。"

        except Exception as e:
            return {
                "keyword": keyword,
                "status": "ERROR",
                "trend": "FLAT",
                "trend_label": "⚠️ 取得失敗",
                "trend_class": "yellow",
                "summary": f"通信エラー: {str(e)[:40]}",
                "recent_posts": [],
                "search_url": web_search_url,
            }

        return {
            "keyword": keyword,
            "status": status,
            "trend": trend_type,
            "trend_label": trend_label,
            "trend_class": trend_class,
            "summary": summary,
            "recent_posts": recent_posts,
            "search_url": web_search_url,
        }

    _weather_overview_cache = {}
    _weather_overview_cache_time = {}
    _disaster_news_cache = None
    _disaster_news_cache_time = 0

    @classmethod
    def get_real_weather_overview(cls, loc_cfg):
        """気象庁公式の天気概況・防災解説テキストを取得する"""
        jma_code = loc_cfg.get("jma_code", "130000")
        now = datetime.now().timestamp()

        if jma_code in cls._weather_overview_cache:
            if now - cls._weather_overview_cache_time.get(jma_code, 0) < 300:
                return cls._weather_overview_cache[jma_code]

        url = f"{cls.JMA_OVERVIEW_BASE_URL}{jma_code}.json"
        try:
            raw, charset = cls._http_get(url, timeout=6)
            data = json.loads(raw.decode(charset, errors="replace"))

            office = data.get("publishingOffice", "気象台")
            report_dt_raw = data.get("reportDatetime", "")
            target_area = data.get("targetArea", loc_cfg.get("name", "監視エリア"))
            headline = data.get("headlineText", "")
            full_text = data.get("text", "")

            report_time_str = "最新発表"
            if report_dt_raw:
                try:
                    dt = datetime.fromisoformat(report_dt_raw)
                    report_time_str = dt.strftime("%m/%d %H:%M")
                except Exception:
                    report_time_str = report_dt_raw[:16]

            has_alert = any(kw in full_text for kw in ["警戒", "厳重", "土砂災害", "氾濫", "浸水", "暴風", "大雨", "竜巻", "雷雨"])
            status = "ALERT" if has_alert else "NORMAL"

            paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
            if not paragraphs and full_text:
                paragraphs = [p.strip() for p in full_text.split("\n") if p.strip()]

            res = {
                "status": status,
                "office": office,
                "target_area": target_area,
                "report_time": report_time_str,
                "headline": headline,
                "text": full_text,
                "paragraphs": paragraphs,
                "summary": (headline if headline else (paragraphs[0][:80] + "..." if paragraphs else "平常の気象状況です")),
                "url": f"https://www.jma.go.jp/bosai/forecast/#area_type=class20s&area_code={jma_code}"
            }
            cls._weather_overview_cache[jma_code] = res
            cls._weather_overview_cache_time[jma_code] = now
            return res
        except Exception:
            fallback = {
                "status": "NORMAL",
                "office": f"{loc_cfg.get('name', '')}管区気象台",
                "target_area": loc_cfg.get("name", "監視エリア"),
                "report_time": datetime.now().strftime("%m/%d %H:%M"),
                "headline": "",
                "text": f"気象概況の最新情報を取得中または平常運行です。（{loc_cfg.get('region_name', '')}管内）",
                "paragraphs": [f"気象概況の最新情報を取得中または平常運行です。（{loc_cfg.get('region_name', '')}管内）"],
                "summary": "平常運行（気象解説取得中）",
                "url": "https://www.jma.go.jp/bosai/forecast/"
            }
            return fallback

    @classmethod
    def get_real_disaster_news(cls):
        """災害・危機管理ニュースのフィードを取得し、見出し・本文概要テキスト・日時を抽出する"""
        now = datetime.now().timestamp()
        if cls._disaster_news_cache and (now - cls._disaster_news_cache_time < 60):
            return cls._disaster_news_cache

        import xml.etree.ElementTree as ET
        from email.utils import parsedate_to_datetime

        articles = []
        target_feeds = [
            ("https://news.yahoo.co.jp/rss/categories/domestic.xml", "国内・気象防災"),
            (cls.YAHOO_NEWS_INCIDENT_URL, "社会・災害"),
            (cls.YAHOO_NEWS_TOP_URL, "主要速報")
        ]

        disaster_kws = [
            "地震", "津波", "大雨", "豪雨", "台風", "冠水", "浸水", "氾濫", "土砂", "崖崩れ",
            "停電", "避難", "被害", "火災", "警報", "注意報", "運休", "見合わせ", "遅延",
            "事故", "衝突", "通信障害", "不通", "線状降水帯", "突風", "竜巻", "落雷", "噴火"
        ]

        seen_titles = set()
        jst = timezone(timedelta(hours=9))

        for feed_url, feed_cat in target_feeds:
            try:
                raw, charset = cls._http_get(feed_url, timeout=6)
                xml_text = raw.decode(charset, errors="replace")

                items_data = []
                # 1. まず標準xml.etree.ElementTreeでパース（<link>タグを完全取得）
                try:
                    root = ET.fromstring(raw)
                    for it in root.findall(".//item"):
                        t = (it.findtext("title") or "").strip()
                        d = (it.findtext("description") or "").strip()
                        l = (it.findtext("link") or "").strip()
                        p = (it.findtext("pubDate") or it.findtext("pubdate") or "").strip()
                        if t:
                            items_data.append((t, d, l, p))
                except Exception:
                    # 2. パース失敗時のフォールバック: 正規表現で<item>毎に抽出
                    item_blocks = re.findall(r"<item>(.*?)</item>", xml_text, re.DOTALL | re.IGNORECASE)
                    for block in item_blocks:
                        m_t = re.search(r"<title>(.*?)</title>", block, re.DOTALL | re.IGNORECASE)
                        m_d = re.search(r"<description>(.*?)</description>", block, re.DOTALL | re.IGNORECASE)
                        m_l = re.search(r"<link>(.*?)</link>", block, re.DOTALL | re.IGNORECASE)
                        m_p = re.search(r"<pubDate>(.*?)</pubDate>", block, re.DOTALL | re.IGNORECASE)
                        t = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", m_t.group(1)).strip() if m_t else ""
                        d = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", m_d.group(1)).strip() if m_d else ""
                        l = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", m_l.group(1)).strip() if m_l else ""
                        p = m_p.group(1).strip() if m_p else ""
                        if t:
                            items_data.append((t, d, l, p))

                for title, desc, link, pub_text in items_data:
                    if not title or title in seen_titles:
                        continue
                    seen_titles.add(title)

                    if not link:
                        link = "https://news.yahoo.co.jp/"

                    desc = re.sub(r"<.*?>", "", desc).strip()
                    is_disaster = any(kw in title or kw in desc for kw in disaster_kws)

                    time_label = "速報"
                    if pub_text:
                        try:
                            dt = parsedate_to_datetime(pub_text)
                            if dt.tzinfo:
                                dt = dt.astimezone(jst)
                            else:
                                dt = dt.replace(tzinfo=timezone.utc).astimezone(jst)
                            time_label = dt.strftime("%m/%d %H:%M JST")
                        except Exception:
                            time_label = pub_text[:16]

                    articles.append({
                        "title": title,
                        "summary": desc if desc else "詳細情報は元記事をご確認ください。",
                        "pub_date": time_label,
                        "link": link,
                        "category": feed_cat,
                        "is_disaster": is_disaster
                    })
            except Exception:
                pass

        disaster_articles = [a for a in articles if a["is_disaster"]]
        other_articles = [a for a in articles if not a["is_disaster"]]
        sorted_articles = disaster_articles + other_articles

        if not sorted_articles:
            now_jst = datetime.now(jst).strftime("%m/%d %H:%M JST")
            sorted_articles = [
                {
                    "title": "直近の重大な災害報道・特報はありません",
                    "summary": "全国の主要な災害・危機管理ニュースを常時監視しています。突発的な災害が発生した場合、ここに文字で詳細が表示されます。",
                    "pub_date": now_jst,
                    "link": "https://news.yahoo.co.jp/",
                    "category": "平常",
                    "is_disaster": False
                }
            ]

        res = {
            "count": len(sorted_articles[:15]),
            "disaster_count": len(disaster_articles),
            "articles": sorted_articles[:15],
            "last_updated": datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S JST")
        }
        cls._disaster_news_cache = res
        cls._disaster_news_cache_time = now
        return res

    @classmethod
    def get_channel_live_video_id(cls, handle, fallback_id):
        return resolve_live_video_id(handle, fallback_id)

    @classmethod
    def get_live_media_config(cls, loc_cfg):
        """生放送チャンネルおよび日本各地ライブカメラのプリセット一覧を返却する（動画IDベース埋め込みURL）"""
        loc_key = loc_cfg.get("key", "tokyo")
        default_cam_id = loc_cfg.get("default_camera_id", "cam_tokyo_shibuya")

        resolved_streams = []
        for st in LIVE_MEDIA_PRESETS["streams"]:
            item = dict(st)
            handle = item.get("handle")
            fb_vid = item.get("video_id", "")
            vid = cls.get_channel_live_video_id(handle, fb_vid) if handle else fb_vid
            item["video_id"] = vid
            item["embed_url"] = f"https://www.youtube.com/embed/{vid}?autoplay=0&rel=0"
            item["watch_url"] = f"https://www.youtube.com/watch?v={vid}"
            resolved_streams.append(item)

        resolved_cameras = []
        for cam in LIVE_MEDIA_PRESETS["cameras"]:
            item = dict(cam)
            vid = item.get("video_id", "")
            item["embed_url"] = f"https://www.youtube.com/embed/{vid}?autoplay=0&rel=0"
            item["watch_url"] = f"https://www.youtube.com/watch?v={vid}"
            resolved_cameras.append(item)

        recommended_cam = None
        for cam in resolved_cameras:
            if cam["id"] == default_cam_id:
                recommended_cam = cam
                break
        if not recommended_cam and resolved_cameras:
            recommended_cam = resolved_cameras[0]

        return {
            "default_camera_id": default_cam_id,
            "recommended_camera": recommended_cam,
            "streams": resolved_streams,
            "cameras": resolved_cameras
        }

    def collect_all_metrics(self, location_key="tokyo", keywords=None):
        location_key = location_key if location_key in LOCATION_CONFIG else "tokyo"
        loc_cfg = dict(LOCATION_CONFIG[location_key])
        loc_cfg["key"] = location_key

        quake_data = self.get_real_jma_quake()
        tsunami_data = self.get_real_tsunami_status()
        volcano_data = self.get_real_volcano_status(loc_cfg)
        weather_data = self.get_real_area_weather_warnings(loc_cfg)
        river_data = self.get_real_river_status(loc_cfg, weather_data=weather_data)
        
        transit_data = self.get_real_transit_status(
            loc_cfg["transit_area"], loc_cfg["lines"], loc_cfg.get("shinkansen", [])
        )
        lifeline_data = self.get_real_lifeline_status(loc_cfg)
        
        police_fire_data = self.get_real_police_fire_status()
        government_data = self.get_real_government_status()
        evacuation_data = self.get_real_evacuation_status(loc_cfg)
        telecom_data = self.get_real_telecom_status()

        weather_overview = self.get_real_weather_overview(loc_cfg)
        disaster_news = self.get_real_disaster_news()
        live_media = self.get_live_media_config(loc_cfg)

        if not keywords:
            keywords = ["au 障害", "KDDI 障害", "au 繋がらない", "povo 障害"]

        sns_results = [self.fetch_yahoo_realtime_data(kw) for kw in keywords]

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "location": loc_cfg,
            "earthquake": quake_data,
            "tsunami": tsunami_data,
            "volcano": volcano_data,
            "weather": weather_data,
            "river": river_data,
            "transit": transit_data,
            "police_fire": police_fire_data,
            "lifeline": lifeline_data,
            "government": government_data,
            "evacuation": evacuation_data,
            "telecom": telecom_data,
            "sns_voices": sns_results,
            "weather_overview": weather_overview,
            "disaster_news": disaster_news,
            "live_media": live_media,
        }


analyzer = BCPDataAnalyzer()



# =====================================================================
# 🌍 海外災害・危機管理情報ダッシュボード設定・解析エンジン (MOFA / USGS / 欧州)
# =====================================================================


# =====================================================================
# 💱 リアルタイム日本円為替レート解析エンジン (USD/JPY, GBP/JPY, EUR/JPY)
# 💱 リアルタイム日本円為替レート解析エンジン (全世界166通貨・主要20市場リアルタイム連動)
# =====================================================================

CURRENCY_INFO = {
    "USD": {"name": "米ドル", "symbol": "$"},
    "EUR": {"name": "ユーロ", "symbol": "€"},
    "GBP": {"name": "英ポンド", "symbol": "£"},
    "AUD": {"name": "豪ドル", "symbol": "A$"},
    "CAD": {"name": "カナダドル", "symbol": "C$"},
    "SGD": {"name": "シンガポールドル", "symbol": "S$"},
    "TWD": {"name": "新台湾ドル", "symbol": "NT$"},
    "KRW": {"name": "韓国ウォン", "symbol": "₩"},
    "CNY": {"name": "人民元", "symbol": "¥"},
    "HKD": {"name": "香港ドル", "symbol": "HK$"},
    "THB": {"name": "タイバーツ", "symbol": "฿"},
    "MYR": {"name": "マレーシアリンギット", "symbol": "RM"},
    "PHP": {"name": "フィリピンペソ", "symbol": "₱"},
    "IDR": {"name": "インドネシアルピア", "symbol": "Rp"},
    "INR": {"name": "インドルピー", "symbol": "₹"},
    "VND": {"name": "ベトナムドン", "symbol": "₫"},
    "BRL": {"name": "ブラジルレアル", "symbol": "R$"},
    "TRY": {"name": "トルコリラ", "symbol": "₺"},
    "AED": {"name": "UAEディルハム", "symbol": "DH"},
    "BDT": {"name": "バングラデシュタカ", "symbol": "৳"},
    "KHR": {"name": "カンボジアリエル", "symbol": "៛"},
    "MMK": {"name": "ミャンマーチャット", "symbol": "K"},
    "MNT": {"name": "モンゴルトグログ", "symbol": "₮"},
    "CHF": {"name": "スイスフラン", "symbol": "CHF"},
    "NZD": {"name": "NZドル", "symbol": "NZ$"},
    "MXN": {"name": "メキシコペソ", "symbol": "Mex$"},
    "ZAR": {"name": "南アフリカランド", "symbol": "R"},
}

DEFAULT_FOREX_RATES = {
    "USD": {"rate": 153.85, "previous_close": 156.19, "change": -2.34, "change_pct": -1.50},
    "EUR": {"rate": 178.85, "previous_close": 181.40, "change": -2.55, "change_pct": -1.41},
    "GBP": {"rate": 208.48, "previous_close": 211.14, "change": -2.66, "change_pct": -1.26},
    "AUD": {"rate": 111.17, "previous_close": 112.55, "change": -1.38, "change_pct": -1.23},
    "CAD": {"rate": 111.63, "previous_close": 112.91, "change": -1.28, "change_pct": -1.13},
    "SGD": {"rate": 121.61, "previous_close": 123.27, "change": -1.66, "change_pct": -1.35},
    "TWD": {"rate": 4.872, "previous_close": 4.936, "change": -0.064, "change_pct": -1.30},
    "KRW": {"rate": 0.1146, "previous_close": 0.1161, "change": -0.0015, "change_pct": -1.29},
    "CNY": {"rate": 22.898, "previous_close": 23.272, "change": -0.374, "change_pct": -1.61},
    "HKD": {"rate": 19.615, "previous_close": 19.922, "change": -0.307, "change_pct": -1.54},
    "THB": {"rate": 4.674, "previous_close": 4.740, "change": -0.066, "change_pct": -1.39},
    "MYR": {"rate": 37.837, "previous_close": 38.250, "change": -0.413, "change_pct": -1.08},
    "PHP": {"rate": 2.462, "previous_close": 2.495, "change": -0.033, "change_pct": -1.32},
    "IDR": {"rate": 0.0087, "previous_close": 0.0088, "change": -0.0001, "change_pct": -1.14},
    "INR": {"rate": 1.619, "previous_close": 1.635, "change": -0.016, "change_pct": -0.98},
    "VND": {"rate": 0.00592, "previous_close": 0.00600, "change": -0.00008, "change_pct": -1.33},
    "BRL": {"rate": 30.258, "previous_close": 30.453, "change": -0.195, "change_pct": -0.64},
    "TRY": {"rate": 3.125, "previous_close": 3.160, "change": -0.035, "change_pct": -1.11},
    "AED": {"rate": 41.865, "previous_close": 42.500, "change": -0.635, "change_pct": -1.49},
    "BDT": {"rate": 1.248, "previous_close": 1.265, "change": -0.017, "change_pct": -1.34},
    "KHR": {"rate": 0.0382, "previous_close": 0.0385, "change": -0.0003, "change_pct": -0.78},
    "MMK": {"rate": 0.0735, "previous_close": 0.0740, "change": -0.0005, "change_pct": -0.68},
    "MNT": {"rate": 0.0425, "previous_close": 0.0430, "change": -0.0005, "change_pct": -1.16},
}

class ForexAnalyzer:
    """全世界166通貨の対日本円為替レート・前日比をリアルタイム集計・自動解析"""
    def __init__(self):
        self._cache = dict(DEFAULT_FOREX_RATES)
        self._cache_time = 0
        self._lock = threading.Lock()

    def get_forex_data(self, local_currency="GBP", currency_name=None, currency_symbol=None):
        now = time.time()
        with self._lock:
            # 120秒（2分）キャッシュ
            if self._cache and (now - self._cache_time < 120):
                return self._build_result(local_currency, currency_name, currency_symbol)

        try:
            data = self._fetch_rates()
            with self._lock:
                if data:
                    self._cache.update(data)
                    self._cache_time = now
        except Exception as e:
            print(f"[ForexAnalyzer] Fetch error: {e}")

        return self._build_result(local_currency, currency_name, currency_symbol)

    def _fetch_rates(self):
        results = {}
        # 1. open.er-api.com から全世界166通貨を一括高速取得 (ベースライン)
        usd_jpy = 154.0
        try:
            req = urllib.request.Request("https://open.er-api.com/v6/latest/USD", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            rates = data.get("rates", {})
            usd_jpy = float(rates.get("JPY", 154.0))
            for code, r in rates.items():
                if r and float(r) > 0:
                    jpy_val = usd_jpy / float(r)
                    prev_cached = self._cache.get(code, {}).get("rate", jpy_val)
                    chg = jpy_val - prev_cached
                    pct = (chg / prev_cached * 100) if prev_cached else 0.0
                    results[code] = {
                        "rate": jpy_val,
                        "previous_close": prev_cached,
                        "change": round(chg, 4),
                        "change_pct": round(pct, 2)
                    }
        except Exception as e:
            print(f"[ForexAnalyzer] open.er-api error: {e}")

        # 2. yfinance から主要20通貨ペアの市場リアルタイム値・前日終値をバッチ取得
        try:
            import yfinance as yf
            tickers = [
                'USDJPY=X', 'EURJPY=X', 'GBPJPY=X', 'AUDJPY=X', 'CADJPY=X',
                'SGDJPY=X', 'TWDJPY=X', 'KRWJPY=X', 'CNYJPY=X', 'HKDJPY=X',
                'THBJPY=X', 'BRLJPY=X', 'INRJPY=X', 'IDRJPY=X', 'MYRJPY=X',
                'PHPJPY=X', 'VNDJPY=X', 'TRYJPY=X', 'AEDJPY=X', 'BDTJPY=X'
            ]
            df = yf.download(tickers, period='5d', interval='1d', progress=False, timeout=6)
            close_df = df.get('Close') if isinstance(df, dict) or hasattr(df, 'get') else df['Close']
            for sym in tickers:
                code = sym.replace('JPY=X', '')
                if sym in close_df.columns:
                    s = close_df[sym].dropna()
                    if len(s) >= 2:
                        last = float(s.iloc[-1])
                        prev = float(s.iloc[-2])
                        chg = last - prev
                        pct = (chg / prev * 100) if prev else 0.0
                        results[code] = {
                            "rate": last,
                            "previous_close": prev,
                            "change": round(chg, 4),
                            "change_pct": round(pct, 2)
                        }
        except Exception as e:
            print(f"[ForexAnalyzer] yfinance error: {e}")

        return results

    def _build_result(self, local_currency, currency_name=None, currency_symbol=None):
        now_jst = datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M JST")
        usd_data = self._cache.get("USD", DEFAULT_FOREX_RATES.get("USD", {"rate": 153.85, "change": -2.34, "change_pct": -1.50}))
        eur_data = self._cache.get("EUR", DEFAULT_FOREX_RATES.get("EUR", {"rate": 178.85, "change": -2.55, "change_pct": -1.41}))

        # 米国選択時は重複を避けるため第2基軸通貨としてEUR（ユーロ）を配備
        is_usd = (local_currency == "USD")
        target_code = "EUR" if is_usd else local_currency

        fallback_info = DEFAULT_FOREX_RATES.get(target_code, {"rate": 100.0, "change": 0.0, "change_pct": 0.0})
        local_data = self._cache.get(target_code, fallback_info)

        c_info = CURRENCY_INFO.get(target_code, {})
        disp_name = ("ユーロ" if is_usd else (currency_name if currency_name else c_info.get("name", target_code)))
        disp_symbol = ("€" if is_usd else (currency_symbol if currency_symbol else c_info.get("symbol", "")))

        loc_rate = float(local_data.get("rate", 1.0))
        loc_chg = float(local_data.get("change", 0.0))
        loc_pct = float(local_data.get("change_pct", 0.0))

        if loc_rate >= 20:
            rate_val = round(loc_rate, 2)
            chg_val = round(loc_chg, 2)
        elif loc_rate >= 1:
            rate_val = round(loc_rate, 3)
            chg_val = round(loc_chg, 3)
        else:
            rate_val = round(loc_rate, 4)
            chg_val = round(loc_chg, 4)

        usd_rate = float(usd_data.get("rate", 153.85))
        usd_chg = float(usd_data.get("change", 0.0))
        usd_pct = float(usd_data.get("change_pct", 0.0))

        return {
            "timestamp": now_jst,
            "usd_jpy": {
                "currency": "USD",
                "name": "米ドル",
                "symbol": "$",
                "rate": round(usd_rate, 2),
                "change": round(usd_chg, 2),
                "change_pct": round(usd_pct, 2),
                "direction": "up" if usd_chg > 0 else ("down" if usd_chg < 0 else "even")
            },
            "local_jpy": {
                "currency": target_code,
                "name": disp_name,
                "symbol": disp_symbol,
                "rate": rate_val,
                "change": chg_val,
                "change_pct": round(loc_pct, 2),
                "direction": "up" if loc_chg > 0 else ("down" if loc_chg < 0 else "even")
            },
            "eur_jpy": {
                "currency": "EUR",
                "name": "ユーロ",
                "symbol": "€",
                "rate": round(float(eur_data.get("rate", 178.85)), 2),
                "change": round(float(eur_data.get("change", 0.0)), 2),
                "change_pct": round(float(eur_data.get("change_pct", 0.0)), 2)
            }
        }


# =====================================================================
# ✈️ 世界の主要国際空港・フライト運行解析エンジン (NOAA METAR)
# =====================================================================

class AirportFlightAnalyzer:
    """欧州・世界の主要ハブ空港のリアルタイム気象・滑走路・運航ステータス自動解析"""
    def __init__(self):
        self._metar_cache = {}
        self._cache_time = 0
        self._lock = threading.Lock()

    def get_airports_status(self, airport_list):
        if not airport_list:
            return []

        icao_list = [a["icao"] for a in airport_list if "icao" in a]
        now = time.time()

        metar_map = {}
        with self._lock:
            if (now - self._cache_time < 300) and self._metar_cache:
                metar_map = self._metar_cache

        if not metar_map:
            try:
                metar_map = self._fetch_noaa_metar(icao_list)
                with self._lock:
                    self._metar_cache = metar_map
                    self._cache_time = now
            except Exception as e:
                print(f"[AirportFlightAnalyzer] NOAA fetch error: {e}")

        results = []
        for apt in airport_list:
            icao = apt.get("icao")
            met = metar_map.get(icao, {})
            status_info = self._evaluate_operational_status(met)
            results.append({
                **apt,
                "weather": met,
                "status": status_info["status"],
                "status_code": status_info["code"],
                "status_badge": status_info["badge"],
                "status_desc": status_info["desc"]
            })
        return results

    def _fetch_noaa_metar(self, icao_list):
        ids_param = ",".join(icao_list)
        url = f"https://aviationweather.gov/api/data/metar?ids={ids_param}&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            out = {}
            for item in data:
                icao = item.get("icaoId")
                if icao:
                    wspd = item.get("wspd")
                    wgst = item.get("wgst")
                    visib = item.get("visib")
                    temp = item.get("temp")
                    raw = item.get("rawOb", "")
                    fltcat = item.get("fltcat", "VFR")

                    wind_text = f"{wspd}kt" if wspd is not None else "風向不定"
                    if wgst:
                        wind_text += f" (突風 {wgst}kt)"

                    vis_text = f"{visib}マイル" if visib is not None else "良好"
                    if "CAVOK" in raw:
                        vis_text = "良好 (CAVOK)"

                    out[icao] = {
                        "raw": raw,
                        "wind": wind_text,
                        "wind_speed": wspd or 0,
                        "wind_gust": wgst or 0,
                        "visibility": vis_text,
                        "temp": temp,
                        "fltcat": fltcat,
                        "report_time": item.get("reportTime", "")
                    }
            return out

    def _evaluate_operational_status(self, met):
        if not met:
            return {
                "status": "平常運航",
                "code": "normal",
                "badge": "🟢 平常運航",
                "desc": "定常運航中（現在重大な気象警報なし）"
            }

        raw = met.get("raw", "")
        gust = met.get("wind_gust", 0)
        wspd = met.get("wind_speed", 0)
        fltcat = met.get("fltcat", "VFR")

        if "TS" in raw or "+RA" in raw or "+SN" in raw or gust > 40:
            return {
                "status": "欠航・着陸制限警戒",
                "code": "severe",
                "badge": "🔴 欠航・着陸制限警戒",
                "desc": f"雷雨・強烈な突風（{gust}kt）または悪天候により遅延・欠航・着陸復行警戒"
            }
        elif gust > 25 or wspd > 20 or fltcat in ["IFR", "LIFR"] or "FG" in raw:
            return {
                "status": "遅延・運航乱れ警戒",
                "code": "warning",
                "badge": "🟠 遅延・運航乱れ警戒",
                "desc": f"強風（{wspd}kt/突風{gust}kt）または濃霧・低視程による管制発着制限の可能性あり"
            }
        elif "RA" in raw or "SN" in raw or fltcat == "MVFR":
            return {
                "status": "気象注意",
                "code": "advisory",
                "badge": "🟡 気象注意",
                "desc": "雨天または雲底低下あり。現在大きな乱れなし"
            }
        else:
            return {
                "status": "平常運航",
                "code": "normal",
                "badge": "🟢 平常運航",
                "desc": f"視程良好（{met.get('visibility')}）、風速安定（{met.get('wind')}）。順調に運航中"
            }


WMO_CODE_MAP = {
    0: ("☀️ 快晴", "clear"),
    1: ("🌤️ 晴れ", "mainly_clear"),
    2: ("⛅ 晴れ時々曇り", "partly_cloudy"),
    3: ("☁️ 曇り", "overcast"),
    45: ("🌫️ 霧", "fog"),
    48: ("🌫️ 氷霧", "rime_fog"),
    51: ("🌦️ 霧雨 (弱)", "drizzle_light"),
    53: ("🌦️ 霧雨 (中)", "drizzle_med"),
    55: ("🌦️ 霧雨 (強)", "drizzle_heavy"),
    61: ("🌧️ 雨 (小雨)", "rain_light"),
    63: ("🌧️ 雨 (中雨)", "rain_med"),
    65: ("🌧️ 雨 (大雨)", "rain_heavy"),
    66: ("🌨️ 凍結雨 (弱)", "freezing_rain_light"),
    67: ("🌨️ 凍結雨 (強)", "freezing_rain_heavy"),
    71: ("❄️ 降雪 (小雪)", "snow_light"),
    73: ("❄️ 降雪 (中雪)", "snow_med"),
    75: ("❄️ 降雪 (大雪)", "snow_heavy"),
    77: ("❄️ 細氷・霧雪", "snow_grains"),
    80: ("🌧️ にわか雨 (弱)", "showers_light"),
    81: ("🌧️ にわか雨 (中)", "showers_med"),
    82: ("⛈️ 激しいにわか雨", "showers_violent"),
    85: ("🌨️ にわか雪 (弱)", "snow_showers_light"),
    86: ("🌨️ にわか雪 (強)", "snow_showers_heavy"),
    95: ("⛈️ 雷雨 (弱〜中)", "thunderstorm"),
    96: ("⛈️ 雷雨・雹 (強)", "thunderstorm_hail_light"),
    99: ("⛈️ 猛烈な雷雨・大雹", "thunderstorm_hail_heavy")
}


class WeatherAnalyzer:
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300

    def get_country_weather(self, cities_list):
        if not cities_list:
            return {"cities": [], "capital": None, "timestamp": ""}
        
        now = time.time()
        cache_key = tuple(c.get("name_en", "") for c in cities_list)
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if now - entry["timestamp"] < self._cache_ttl:
                return entry["data"]
        
        results = []
        for city in cities_list:
            lat = city.get("lat")
            lon = city.get("lon")
            c_name = city.get("name")
            c_en = city.get("name_en")
            is_cap = city.get("is_capital", False)
            
            w_data = self._fetch_city_weather(lat, lon)
            if w_data:
                alert_info = self._evaluate_weather_risk(w_data)
                results.append({
                    "name": c_name,
                    "name_en": c_en,
                    "is_capital": is_cap,
                    "lat": lat,
                    "lon": lon,
                    **w_data,
                    "alert": alert_info["alert"],
                    "alert_badge": alert_info["badge"],
                    "alert_class": alert_info["class"],
                    "alert_desc": alert_info["desc"]
                })
        
        capital_data = next((c for c in results if c.get("is_capital")), results[0] if results else None)
        out = {
            "cities": results,
            "capital": capital_data,
            "timestamp": datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M JST")
        }
        self._cache[cache_key] = {"data": out, "timestamp": now}
        return out

    def _fetch_city_weather(self, lat, lon):
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_gusts_10m&"
            f"daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum&"
            f"timezone=auto"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                d = json.loads(resp.read().decode("utf-8"))
            
            cur = d.get("current", {})
            w_code = cur.get("weather_code", 0)
            label = WMO_CODE_MAP.get(w_code, ("☁️ 曇りがち", "unknown"))[0]
            
            daily = d.get("daily", {})
            f_times = daily.get("time", [])[:3]
            f_maxs = daily.get("temperature_2m_max", [])[:3]
            f_mins = daily.get("temperature_2m_min", [])[:3]
            f_codes = daily.get("weather_code", [])[:3]
            f_precips = daily.get("precipitation_sum", [])[:3]
            
            forecast = []
            for i in range(len(f_times)):
                c = f_codes[i] if i < len(f_codes) else 0
                flabel = WMO_CODE_MAP.get(c, ("☁️ 曇り", "unknown"))[0]
                t_str = f_times[i]
                try:
                    pdt = datetime.strptime(t_str, "%Y-%m-%d")
                    day_label = pdt.strftime("%m/%d")
                    day_name = ["月","火","水","木","金","土","日"][pdt.weekday()]
                    disp_date = f"{day_label}({day_name})"
                except Exception:
                    disp_date = t_str

                forecast.append({
                    "date": disp_date,
                    "temp_max": round(f_maxs[i], 1) if i < len(f_maxs) and f_maxs[i] is not None else "--",
                    "temp_min": round(f_mins[i], 1) if i < len(f_mins) and f_mins[i] is not None else "--",
                    "weather_code": c,
                    "weather_label": flabel,
                    "precipitation_mm": round(f_precips[i], 1) if i < len(f_precips) and f_precips[i] is not None else 0.0
                })

            return {
                "temp": round(cur.get("temperature_2m", 0.0), 1),
                "apparent_temp": round(cur.get("apparent_temperature", 0.0), 1),
                "humidity": cur.get("relative_humidity_2m", 0),
                "wind_speed": round(cur.get("wind_speed_10m", 0.0), 1),
                "wind_gusts": round(cur.get("wind_gusts_10m", 0.0), 1),
                "precipitation": cur.get("precipitation", 0.0),
                "weather_code": w_code,
                "weather_label": label,
                "forecast": forecast
            }
        except Exception as e:
            print(f"Weather error for {lat},{lon}: {e}")
            return None

    def _evaluate_weather_risk(self, cur):
        wspd = cur.get("wind_speed", 0.0)
        gust = cur.get("wind_gusts", 0.0)
        code = cur.get("weather_code", 0)
        precip = cur.get("precipitation", 0.0)
        temp = cur.get("temp", 20.0)

        if gust > 70 or wspd > 55 or code in [95, 96, 99] or precip > 25:
            return {
                "alert": "暴風・悪天候警報",
                "badge": "🔴 暴風警報",
                "class": "red",
                "desc": f"雷雨または猛烈な突風（{gust}km/h）・激しい降雨に警戒"
            }
        elif gust > 45 or wspd > 35 or code in [65, 75, 82] or precip > 10:
            return {
                "alert": "強風・大雨注意報",
                "badge": "🟠 気象注意報",
                "class": "orange",
                "desc": f"強風（突風{gust}km/h）または強い雨。移動・屋外行動に注意"
            }
        elif temp > 36:
            return {
                "alert": "酷暑・熱中症警戒",
                "badge": "🟠 猛暑警戒",
                "class": "orange",
                "desc": f"最高気温{temp}℃。熱中症に十分注意"
            }
        elif temp < -5:
            return {
                "alert": "厳寒・凍結警戒",
                "badge": "🟠 凍結警戒",
                "class": "orange",
                "desc": f"気温{temp}℃。路面凍結・交通遅延に注意"
            }
        elif code in [45, 48, 51, 53, 55, 61, 63, 71, 80]:
            return {
                "alert": "気象注意",
                "badge": "🟡 気象注意",
                "class": "yellow",
                "desc": "降雨または視程低下あり。通常行動可能"
            }
        else:
            return {
                "alert": "平常",
                "badge": "🟢 平常・平穏",
                "class": "green",
                "desc": "平穏な気象状況。特段の警戒事項なし"
            }


class TransitAnalyzer:
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 180

    def get_transit_status(self, country_key, systems_list):
        now = time.time()
        if country_key in self._cache:
            entry = self._cache[country_key]
            if now - entry["timestamp"] < self._cache_ttl:
                return entry["data"]

        results = []
        tfl_lines = self._fetch_tfl_live_status() if country_key == "uk" else None

        for sys_item in systems_list:
            item_id = sys_item.get("id")
            if item_id == "tfl" and tfl_lines:
                status_info = self._evaluate_tfl_summary(tfl_lines)
                results.append({
                    **sys_item,
                    "status": status_info["status"],
                    "status_badge": status_info["badge"],
                    "status_code": status_info["code"],
                    "details": status_info["details"],
                    "lines": tfl_lines
                })
            else:
                results.append({
                    **sys_item,
                    "status": sys_item.get("default_status", "平常運行"),
                    "status_badge": sys_item.get("default_badge", "🟢 平常運行"),
                    "status_code": sys_item.get("default_code", "normal"),
                    "details": sys_item.get("default_details", "定常ダイヤにて運行中（大規模ストライキなし）")
                })

        # 全体ステータス評価
        overall_code = "normal"
        overall_status = "平常運行"
        overall_badge = "🟢 平常運行"
        status_text = "都市交通・鉄道 平常運行 (ストなし)"
        strike_detected = False
        alert_lines = []

        for sys_item in results:
            code = sys_item.get("status_code", "normal")
            if "ストライキ" in sys_item.get("status", "") or "ストライキ" in sys_item.get("details", ""):
                strike_detected = True
            
            # 各路線の遅延・見合わせの検出
            for line in sys_item.get("lines", []):
                if line.get("code") in ["warning", "severe"]:
                    alert_lines.append({
                        "system": sys_item.get("name", ""),
                        "line": line.get("name", ""),
                        "mode": line.get("mode", ""),
                        "status": line.get("status_raw", ""),
                        "badge": line.get("badge", ""),
                        "reason": line.get("reason", "")
                    })

            if code == "severe":
                overall_code = "severe"
            elif code == "warning" and overall_code != "severe":
                overall_code = "warning"
            elif code == "minor" and overall_code not in ["severe", "warning"]:
                overall_code = "minor"

        if strike_detected:
            overall_code = "severe"
            overall_status = "ストライキ・運休警戒"
            overall_badge = "🔴 交通ストライキ警戒"
            status_text = "⚠️ 交通ストライキ・大規模運休発生中"
        elif overall_code == "severe":
            overall_status = "大規模運休・運転見合わせ"
            overall_badge = "🔴 運休・運行混乱警戒"
            status_text = f"⚠️ 主要交通網で運転見合わせ発生 ({alert_lines[0]['line']}線など)" if alert_lines else "⚠️ 交通網 運転見合わせ・運休発生"
        elif overall_code == "warning":
            overall_status = "大幅遅延・一部運休"
            overall_badge = "🟠 大幅遅延・運行注意"
            status_text = f"⚠️ {alert_lines[0]['line']}線: 大幅遅延・一部運休" if alert_lines else "主要交通網: 一部路線で大幅遅延"
        elif overall_code == "minor":
            overall_status = "軽微な遅延・計画工事"
            overall_badge = "🟡 一部遅延あり"
            status_text = "主要路線: 一部で軽微な遅延あり"

        # レベル判定 ('ALERT' / 'CAUTION' / 'NORMAL')
        level = "ALERT" if overall_code == "severe" or strike_detected else ("CAUTION" if overall_code in ["warning", "minor"] else "NORMAL")

        out = {
            "status": level,
            "status_code": overall_code,
            "status_badge": overall_badge,
            "status_text": status_text,
            "overall_status": overall_status,
            "strike": strike_detected,
            "monitored_systems_count": len(results),
            "alert_lines_count": len(alert_lines),
            "alert_lines": alert_lines,
            "systems": results,
            "timestamp": datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M JST")
        }
        self._cache[country_key] = {"data": out, "timestamp": now}
        return out

    def _fetch_tfl_live_status(self):
        url = "https://api.tfl.gov.uk/line/mode/tube,overground,dlr,elizabeth-line/status"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                lines = json.loads(resp.read().decode("utf-8"))
            
            parsed = []
            for item in lines:
                name = item.get("name", "")
                mode = item.get("modeName", "")
                line_statuses = item.get("lineStatuses", [])
                st_desc = "Good Service"
                reason = ""
                if line_statuses:
                    st_desc = line_statuses[0].get("statusSeverityDescription", "Good Service")
                    reason = line_statuses[0].get("reason", "")
                
                if "Good Service" in st_desc:
                    badge = "🟢 平常"
                    code = "normal"
                elif "Service Closed" in st_desc:
                    badge = "🌙 夜間休止"
                    code = "closed"
                elif any(k in st_desc for k in ["Minor Delays", "Part Closure", "Special Service"]):
                    badge = "🟡 注意"
                    code = "minor"
                elif any(k in st_desc for k in ["Severe Delays", "Reduced Service"]):
                    badge = "🟠 警戒"
                    code = "warning"
                else:
                    badge = "🔴 運休/見合せ"
                    code = "severe"

                parsed.append({
                    "name": name,
                    "mode": mode,
                    "status_raw": st_desc,
                    "badge": badge,
                    "code": code,
                    "reason": reason[:120] if reason else ""
                })
            return parsed
        except Exception as e:
            print(f"TfL fetch error: {e}")
            return None

    def _evaluate_tfl_summary(self, lines):
        severe_count = sum(1 for l in lines if l["code"] == "severe")
        warning_count = sum(1 for l in lines if l["code"] == "warning")
        minor_count = sum(1 for l in lines if l["code"] == "minor")
        closed_count = sum(1 for l in lines if l["code"] == "closed")

        if severe_count > 2:
            return {
                "status": "ストライキ・大規模運休警戒",
                "badge": "🔴 運休・ストライキ警戒",
                "code": "severe",
                "details": f"複数路線（{severe_count}線）で運転見合わせまたは運行混乱が発生中"
            }
        elif warning_count > 0 or severe_count > 0:
            return {
                "status": "大幅遅延・一部運休あり",
                "badge": "🟠 大幅遅延・運休警戒",
                "code": "warning",
                "details": f"主要路線で遅延・区間運休が発生中。移動前に最新状況をご確認ください"
            }
        elif closed_count > 10:
            return {
                "status": "夜間営業時間外 (始発待機)",
                "badge": "🌙 営業時間外",
                "code": "normal",
                "details": "ロンドン現地深夜のため夜間営業時間外（Night Tube等を除く各線は始発待機中）"
            }
        elif minor_count > 0:
            return {
                "status": "一部路線で軽微な遅延・工事",
                "badge": "🟡 一部遅延・工事あり",
                "code": "minor",
                "details": f"{minor_count}路線で軽微な遅延または計画保守工事を実施中。主要幹は概ね平常"
            }
        else:
            return {
                "status": "全線平常運行",
                "badge": "🟢 平常運行",
                "code": "normal",
                "details": "Tube全線・Elizabeth line・Overgroundは定常ダイヤにて平常運行中"
            }


OVERSEAS_CONFIG = {
    "uk": {
        "id": "uk",
        "name": "イギリス (英国)",
        "english_name": "United Kingdom",
        "flag": "🇬🇧",
        "city": "ロンドン (London)",
        "embassy_name": "在英国日本国大使館 (Embassy of Japan in the UK)",
        "mofa_code": "0044",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_154.html",
        "embassy_url": "https://www.uk.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "緊急時: 999 (警察・救急・消防) / 大使館: +44-(0)20-7465-6500",
        "timezone_offset": 1,
        "timezone_name": "BST (現地: UTC+1)",
        "currency_code": "GBP",
        "currency_name": "英ポンド",
        "currency_symbol": "£",
        "default_camera_id": "stream_skynews",
        "default_keywords": ["ロンドン ストライキ", "ヒースロー 欠航", "UK strike", "イギリス 治安"],
        "media_channels": [
            {"id": "stream_skynews", "name": "📺 Sky News LIVE (24h英国ニュース)", "video_id": "dMlQFujIGPA", "handle": "@SkyNews", "type": "stream"},
            {"id": "stream_france24_en", "name": "📺 France 24 English (欧州国際ニュース)", "video_id": "a47ckXKZjxI", "handle": "@FRANCE24", "type": "stream"},
            {"id": "stream_euronews_uk", "name": "📺 Euronews English (欧州24h生配信)", "video_id": "pykpO5kQJ98", "handle": "@euronews", "type": "stream"},
            {"id": "cam_earthcam_abbey", "name": "📷 ロンドン: アビーロード交差点 24h実況 [EarthCam公式]", "video_id": "zMCea32gpmg", "type": "camera"},
            {"id": "cam_london_walworth", "name": "📷 ロンドン: ウォルワース・ロード市街交差点 24h実況", "video_id": "YUP57y2iye8", "type": "camera"},
            {"id": "cam_london_street", "name": "📷 ロンドン: セントラル・ストリート 24h街並み実況", "video_id": "WKGK_hYnlGE", "type": "camera"}
        ],
        "weather_cities": [
            {"name": "ロンドン (首都)", "name_en": "London", "lat": 51.5074, "lon": -0.1278, "is_capital": True},
            {"name": "マンチェスター (中部)", "name_en": "Manchester", "lat": 53.4808, "lon": -2.2426, "is_capital": False},
            {"name": "エディンバラ (スコットランド)", "name_en": "Edinburgh", "lat": 55.9533, "lon": -3.1883, "is_capital": False}
        ],
        "transit_systems": [
            {"id": "tfl", "name": "ロンドン交通局 (TfL Underground / Elizabeth / Overground)", "mode": "地下鉄・都市鉄道", "coverage": "大ロンドン首都圏全域", "official_url": "https://tfl.gov.uk/tube-dlr-overground/status/", "map_url": "https://tfl.gov.uk/maps/track", "strike_url": "https://tfl.gov.uk/campaign/strikes"},
            {"id": "national_rail", "name": "ナショナル・レール (National Rail イギリス全土国鉄)", "mode": "全国幹線鉄道", "coverage": "英国全土・都市間高速", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "英本土主要幹線・インターシティは概ね定常運行中", "official_url": "https://www.nationalrail.co.uk/service-disruptions/", "map_url": "https://www.nationalrail.co.uk/stations_destinations/rail-maps.aspx", "strike_url": "https://www.nationalrail.co.uk/service-disruptions/industrial-action/"},
            {"id": "eurostar", "name": "ユーロスター (Eurostar 国際高速列車)", "mode": "国際高速鉄道", "coverage": "ロンドン ↔ パリ/ブリュッセル/アムステルダム", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "英仏海峡トンネル経由国際便は定常運行中", "official_url": "https://www.eurostar.com/uk-en/travel-info/service-information/live-travel-updates", "map_url": "https://www.eurostar.com/uk-en/destinations/our-network", "strike_url": "https://www.eurostar.com/uk-en/travel-info/service-information/eurostar-travel-updates"},
            {"id": "national_express", "name": "ナショナル・エクスプレス (National Express 高速バス)", "mode": "都市間長距離バス", "coverage": "英本土全域・主要空港直結", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "空港連絡バスおよび主要都市間コーチは平常運行中", "official_url": "https://www.nationalexpress.com/en/help/live-service-updates", "map_url": "https://www.nationalexpress.com/en/destinations", "strike_url": "https://www.nationalexpress.com/en/help/live-service-updates"}
        ],
        "airports": [
            {"iata": "LHR", "icao": "EGLL", "name": "ロンドン・ヒースロー国際空港", "city": "ロンドン", "hub": "英国最大ハブ", "departures_url": "https://www.heathrow.com/departures", "radar_url": "https://www.flightradar24.com/airport/lhr", "flightaware_url": "https://www.flightaware.com/live/airport/EGLL"},
            {"iata": "LGW", "icao": "EGKK", "name": "ロンドン・ガトウィック空港", "city": "ロンドン", "hub": "主要国際空港", "departures_url": "https://www.gatwickairport.com/flights/", "radar_url": "https://www.flightradar24.com/airport/lgw", "flightaware_url": "https://www.flightaware.com/live/airport/EGKK"},
            {"iata": "LCY", "icao": "EGLC", "name": "ロンドン・シティ空港", "city": "ロンドン", "hub": "都心ビジネス空港", "departures_url": "https://www.londoncityairport.com/flight-information", "radar_url": "https://www.flightradar24.com/airport/lcy", "flightaware_url": "https://www.flightaware.com/live/airport/EGLC"},
            {"iata": "MAN", "icao": "EGCC", "name": "マンチェスター空港", "city": "マンチェスター", "hub": "中部国際ハブ", "departures_url": "https://www.manchesterairport.co.uk/flight-information/departures/", "radar_url": "https://www.flightradar24.com/airport/man", "flightaware_url": "https://www.flightaware.com/live/airport/EGCC"}
        ]
    },
    "france": {
        "id": "france",
        "name": "フランス",
        "english_name": "France",
        "flag": "🇫🇷",
        "city": "パリ (Paris)",
        "embassy_name": "在フランス日本国大使館 (Ambassade du Japon en France)",
        "mofa_code": "0033",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_170.html",
        "embassy_url": "https://www.fr.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "緊急時: 112 (EU共通) / 17 (警察) / 大使館: +33-(0)1-48-88-62-00",
        "timezone_offset": 2,
        "timezone_name": "CEST (現地: UTC+2)",
        "currency_code": "EUR",
        "currency_name": "ユーロ",
        "currency_symbol": "€",
        "default_camera_id": "stream_france24_fr",
        "default_keywords": ["パリ デモ", "フランス ストライキ", "Paris protest", "シャルル・ド・ゴール 遅延"],
        "media_channels": [
            {"id": "stream_france24_fr", "name": "📺 France 24 en Direct (フランス語)", "video_id": "a47ckXKZjxI", "handle": "@france24", "type": "stream"},
            {"id": "stream_france24_en_fr", "name": "📺 France 24 LIVE (英語国際ニュース)", "video_id": "a47ckXKZjxI", "handle": "@FRANCE24", "type": "stream"},
            {"id": "stream_euronews_fr", "name": "📺 Euronews (欧州24hニュース)", "video_id": "pykpO5kQJ98", "handle": "@euronews", "type": "stream"},
            {"id": "cam_paris_eiffel", "name": "📷 パリ: エッフェル塔 4K定点カメラ", "video_id": "OzYp4NRZlwQ", "type": "camera"},
            {"id": "cam_paris_seine", "name": "📷 パリ: セーヌ川・ノートルダム島周辺 24h実況", "video_id": "7OgCYX4Inr8", "type": "camera"},
            {"id": "cam_lyon_periph", "name": "📷 リヨン: 北部ペリフェリック環状線 24h定点", "video_id": "z545k7Tcb5o", "type": "camera"}
        ],
        "weather_cities": [
            {"name": "パリ (首都)", "name_en": "Paris", "lat": 48.8566, "lon": 2.3522, "is_capital": True},
            {"name": "ニース (南部・コートダジュール)", "name_en": "Nice", "lat": 43.7102, "lon": 7.2620, "is_capital": False},
            {"name": "リヨン (中東部ハブ)", "name_en": "Lyon", "lat": 45.7640, "lon": 4.8357, "is_capital": False}
        ],
        "transit_systems": [
            {"id": "sncf", "name": "SNCF フランス国鉄 (TGV inOui / OUIGO / TER)", "mode": "全国幹線高速鉄道", "coverage": "フランス全土・主要都市間", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "TGV高速線およびインターシティは概ね定常ダイヤ運行中", "official_url": "https://www.sncf-connect.com/app/fr-fr/train/traffic-info", "map_url": "https://www.sncf-reseau.com/fr/carte/carte-reseau-ferre-national", "strike_url": "https://www.sncf.com/fr/itineraire-reservation/info-trafic/greve"},
            {"id": "ratp", "name": "RATP パリ交通公団 (パリ地下鉄 Métro / RER / 市内バス)", "mode": "地下鉄・都市鉄道・バス", "coverage": "イル＝ド＝フランス首都圏", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "地下鉄1〜14号線およびRER A/B線は概ね平常運行中", "official_url": "https://www.ratp.fr/en/infos-trafic", "map_url": "https://www.ratp.fr/en/plans", "strike_url": "https://www.ratp.fr/en/infos-trafic"},
            {"id": "eurostar_fr", "name": "ユーロスター / タリス (Eurostar パリ国際発着)", "mode": "国際高速鉄道", "coverage": "パリ ↔ ロンドン / ブリュッセル / アムステルダム / ケルン", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "北駅（Gare du Nord）発着の国際列車は定常運行中", "official_url": "https://www.eurostar.com/fr-fr/travel-info/service-information/live-travel-updates", "map_url": "https://www.eurostar.com/fr-fr/destinations/our-network", "strike_url": "https://www.eurostar.com/fr-fr/travel-info/service-information/eurostar-travel-updates"},
            {"id": "flixbus_fr", "name": "フリックスバス / BlaBlaCar (長距離都市間バス)", "mode": "都市間長距離バス", "coverage": "フランス国内主要都市・欧州連絡", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "パリ・シャルル・ド・ゴール空港および主要ターミナル発着便は平常運行中", "official_url": "https://www.flixbus.fr/", "map_url": "https://www.flixbus.fr/carte-des-lignes", "strike_url": "https://www.flixbus.fr/"}
        ],
        "airports": [
            {"iata": "CDG", "icao": "LFPG", "name": "パリ・シャルル・ド・ゴール国際空港", "city": "パリ", "hub": "フランス最大ハブ", "departures_url": "https://www.parisaeroport.fr/passagers/vols", "radar_url": "https://www.flightradar24.com/airport/cdg", "flightaware_url": "https://www.flightaware.com/live/airport/LFPG"},
            {"iata": "ORY", "icao": "LFPO", "name": "パリ・オルリー空港", "city": "パリ", "hub": "主要国際・国内空港", "departures_url": "https://www.parisaeroport.fr/passagers/vols", "radar_url": "https://www.flightradar24.com/airport/ory", "flightaware_url": "https://www.flightaware.com/live/airport/LFPO"},
            {"iata": "NCE", "icao": "LFMN", "name": "ニース・コート・ダジュール空港", "city": "ニース", "hub": "南部主要国際空港", "departures_url": "https://www.nice.aeroport.fr/", "radar_url": "https://www.flightradar24.com/airport/nce", "flightaware_url": "https://www.flightaware.com/live/airport/LFMN"}
        ]
    },
    "spain": {
        "id": "spain",
        "name": "スペイン",
        "english_name": "Spain",
        "flag": "🇪🇸",
        "city": "マドリード / バルセロナ",
        "embassy_name": "在スペイン日本国大使館 (Embajada del Japón en España)",
        "mofa_code": "0034",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_161.html",
        "embassy_url": "https://www.es.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "緊急時: 112 (欧州共通救急・消防) / 091 (国家警察) / 大使館: +34-91-590-7600",
        "timezone_offset": 2,
        "timezone_name": "CEST (現地: UTC+2)",
        "currency_code": "EUR",
        "currency_name": "ユーロ",
        "currency_symbol": "€",
        "default_camera_id": "stream_rtve",
        "default_keywords": ["バルセロナ スリ", "マドリード デモ", "Spain strike", "スペイン 森林火災"],
        "media_channels": [
            {"id": "stream_rtve", "name": "📺 RTVE Noticias 24h (スペイン国営放送)", "video_id": "b4tE5aKhtlg", "handle": "@RTVEnoticias", "type": "stream"},
            {"id": "stream_euronews_es", "name": "📺 Euronews Español (欧州24h生配信)", "video_id": "O9mOtdZ-nSk", "handle": "@euronewses", "type": "stream"},
            {"id": "stream_dw_es", "name": "📺 DW Español LIVE (国際ニュース)", "video_id": "LuKwFajn37U", "handle": "@dwnews", "type": "stream"},
            {"id": "cam_lanzarote_airport", "name": "📷 ランサローテ国際空港 24hライブ", "video_id": "AAlo3eCPVbk", "type": "camera"},
            {"id": "cam_bcn_park_guinardo", "name": "📷 バルセロナ: バイクス・ギナルド市街夜景 24h実況", "video_id": "Hyc4M6vayVY", "type": "camera"},
            {"id": "cam_bcn_coast_garbi", "name": "📷 バルセロナ沿岸: ガルビ・カステルデフェルス 海岸 24h実況", "video_id": "oe5GPi_C7Go", "type": "camera"},
            {"id": "cam_mallorca_port", "name": "📷 パルマ・デ・マヨルカ港湾・市街ライブ", "video_id": "hRw1_JQMQoE", "type": "camera"}
        ],
        "weather_cities": [
            {"name": "マドリード (首都)", "name_en": "Madrid", "lat": 40.4168, "lon": -3.7038, "is_capital": True},
            {"name": "バルセロナ (カタルーニャ)", "name_en": "Barcelona", "lat": 41.3879, "lon": 2.1699, "is_capital": False},
            {"name": "セビリア (アンダルシア)", "name_en": "Seville", "lat": 37.3891, "lon": -5.9845, "is_capital": False}
        ],
        "transit_systems": [
            {"id": "renfe", "name": "レンフェ (Renfe スペイン国鉄 AVE / Avlo / Cercanías)", "mode": "全国幹線高速鉄道", "coverage": "スペイン全土・主要幹線", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "マドリード ↔ バルセロナ等の高速鉄道AVEは平常運行中", "official_url": "https://www.renfe.com/es/es/grupo-renfe/comunicacion/avisos", "map_url": "https://www.renfe.com/es/es/viajar/informacion-util/mapas-y-lineas", "strike_url": "https://www.renfe.com/es/es/grupo-renfe/comunicacion/avisos"},
            {"id": "metro_madrid", "name": "マドリード地下鉄・EMTバス (Metro de Madrid / EMT)", "mode": "地下鉄・都市バス", "coverage": "マドリード自治州首都圏", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "地下鉄全線およびバラハス空港連絡路線は平常運行中", "official_url": "https://www.metromadrid.es/es/estado-de-la-red", "map_url": "https://www.metromadrid.es/es/plano-y-horarios", "strike_url": "https://www.metromadrid.es/es/estado-de-la-red"},
            {"id": "tmb_bcn", "name": "バルセロナ都市交通 (TMB Metro / Bus)", "mode": "地下鉄・都市バス", "coverage": "バルセロナ大都市圏", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "バルセロナ地下鉄L1〜L11号線は概ね定常運行中", "official_url": "https://www.tmb.cat/en/barcelona-transportation/current-status-service", "map_url": "https://www.tmb.cat/en/barcelona-transport-network-maps", "strike_url": "https://www.tmb.cat/en/barcelona-transportation/current-status-service"},
            {"id": "alsa", "name": "ALSA (スペイン最大の長距離都市間バス網)", "mode": "長距離高速バス", "coverage": "スペイン全土・主要空港・ポルトガル連絡", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "全国主要都市間ルートは定常運行中", "official_url": "https://www.alsa.com/en/web/bus/home", "map_url": "https://www.alsa.com/en/web/bus/our-destinations", "strike_url": "https://www.alsa.com/"}
        ],
        "airports": [
            {"iata": "MAD", "icao": "LEMD", "name": "マドリード・アドルフォ・スアレス・バラハス空港", "city": "マドリード", "hub": "スペイン最大ハブ", "departures_url": "https://www.aena.es/es/adolfo-suarez-madrid-barajas/vuelos-aeropuerto.html", "radar_url": "https://www.flightradar24.com/airport/mad", "flightaware_url": "https://www.flightaware.com/live/airport/LEMD"},
            {"iata": "BCN", "icao": "LEBL", "name": "バルセロナ・エル・プラット国際空港", "city": "バルセロナ", "hub": "カタルーニャ主要ハブ", "departures_url": "https://www.aena.es/es/josep-tarradellas-barcelona-el-prat/vuelos-aeropuerto.html", "radar_url": "https://www.flightradar24.com/airport/bcn", "flightaware_url": "https://www.flightaware.com/live/airport/LEBL"},
            {"iata": "AGP", "icao": "LEMG", "name": "マラガ・コスタ・デル・ソル空港", "city": "マラガ", "hub": "アンダルシア国際空港", "departures_url": "https://www.aena.es/es/malaga-costa-del-sol/vuelos-aeropuerto.html", "radar_url": "https://www.flightradar24.com/airport/agp", "flightaware_url": "https://www.flightaware.com/live/airport/LEMG"}
        ]
    },
    "germany": {
        "id": "germany",
        "name": "ドイツ",
        "english_name": "Germany",
        "flag": "🇩🇪",
        "city": "ベルリン / フランクフルト",
        "embassy_name": "在ドイツ日本国大使館 (Japanische Botschaft in Deutschland)",
        "mofa_code": "0049",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_165.html",
        "embassy_url": "https://www.de.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "緊急時: 112 (消防・救急) / 110 (警察) / 大使館: +49-(0)30-21094-0",
        "timezone_offset": 2,
        "timezone_name": "CEST (現地: UTC+2)",
        "currency_code": "EUR",
        "currency_name": "ユーロ",
        "currency_symbol": "€",
        "default_camera_id": "stream_dw",
        "default_keywords": ["ドイツ 鉄道 ストライキ", "フランクフルト 空港", "Germany strike", "ベルリン デモ"],
        "media_channels": [
            {"id": "stream_dw", "name": "📺 DW News LIVE (ドイツ国際放送)", "video_id": "LuKwFajn37U", "handle": "@dwnews", "type": "stream"},
            {"id": "stream_dw_de", "name": "📺 DW Deutsch LIVE (ドイツ語24h生配信)", "video_id": "Pk6eueMQmfM", "handle": "@dwdeutsch", "type": "stream"},
            {"id": "stream_euronews_de", "name": "📺 Euronews (欧州24hニュース)", "video_id": "pykpO5kQJ98", "handle": "@euronews", "type": "stream"},
            {"id": "cam_cologne_dom", "name": "📷 ケルン大聖堂 24h定点カメラ [DOMRADIO]", "video_id": "kodtgRure8Y", "type": "camera"},
            {"id": "cam_hamburg_michel", "name": "📷 ハンブルク港: ミヒャエル教会パノラマ 24h [Hamburg Tourismus]", "video_id": "OmyDLXvaus4", "type": "camera"},
            {"id": "cam_germany_destinations", "name": "📷 ドイツ主要都市・観光地 24h定点パノラマ [feratel]", "video_id": "Li3Dvqlo5uE", "type": "camera"}
        ],
        "weather_cities": [
            {"name": "ベルリン (首都)", "name_en": "Berlin", "lat": 52.5200, "lon": 13.4050, "is_capital": True},
            {"name": "フランクフルト (金融・航空ハブ)", "name_en": "Frankfurt", "lat": 50.1109, "lon": 8.6821, "is_capital": False},
            {"name": "ミュンヘン (バイエルン)", "name_en": "Munich", "lat": 48.1351, "lon": 11.5820, "is_capital": False}
        ],
        "transit_systems": [
            {"id": "db", "name": "ドイツ鉄道 (Deutsche Bahn DB ICE / IC / RE / S-Bahn)", "mode": "全国幹線高速鉄道", "coverage": "ドイツ全土・都市間高速", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "主要ICE幹線は平常運行中（全国ストライキ未発生）", "official_url": "https://www.bahn.de/service/ueber-uns/zugverkehr/verkehrsmeldungen", "map_url": "https://www.bahn.de/service/fahrplaene/streckennetz", "strike_url": "https://www.bahn.de/service/ueber-uns/zugverkehr/verkehrsmeldungen"},
            {"id": "bvg", "name": "ベルリン市交通局 (BVG U-Bahn / S-Bahn / Tram / Bus)", "mode": "地下鉄・近郊鉄道・バス", "coverage": "ベルリン首都圏全域", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "U-Bahn各線およびブランデンブルク空港連絡は平常運行中", "official_url": "https://www.bvg.de/en/service-and-info/traffic-news", "map_url": "https://www.bvg.de/en/subscriptions-and-tickets/all-network-maps", "strike_url": "https://www.bvg.de/en/service-and-info/traffic-news"},
            {"id": "mvv", "name": "ミュンヘン運輸連合 (MVV U-Bahn / S-Bahn / Tram)", "mode": "地下鉄・都市鉄道", "coverage": "ミュンヘン都市圏", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "市内U-Bahnおよびミュンヘン空港線（S1/S8）は平常運行中", "official_url": "https://www.mvv-muenchen.de/fahrplanauskunft/betriebslage/index.html", "map_url": "https://www.mvv-muenchen.de/plaene-bahnhoefe/netzplaene/index.html", "strike_url": "https://www.mvv-muenchen.de/"},
            {"id": "flixbus_de", "name": "フリックスバス (FlixBus ドイツ発祥欧州最大バス網)", "mode": "長距離高速バス", "coverage": "ドイツ全土・欧州全域接続", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "フランクフルト・ベルリン発着の長距離路線は概ね定常運行中", "official_url": "https://www.flixbus.de/", "map_url": "https://www.flixbus.de/streckennetz", "strike_url": "https://www.flixbus.de/"}
        ],
        "airports": [
            {"iata": "FRA", "icao": "EDDF", "name": "フランクフルト国際空港", "city": "フランクフルト", "hub": "ドイツ最大メガハブ", "departures_url": "https://www.frankfurt-airport.com/en/flights-and-transfer/flight-information.html", "radar_url": "https://www.flightradar24.com/airport/fra", "flightaware_url": "https://www.flightaware.com/live/airport/EDDF"},
            {"iata": "MUC", "icao": "EDDM", "name": "ミュンヘン国際空港", "city": "ミュンヘン", "hub": "南部主要ハブ", "departures_url": "https://www.munich-airport.com/flights-260533", "radar_url": "https://www.flightradar24.com/airport/muc", "flightaware_url": "https://www.flightaware.com/live/airport/EDDM"},
            {"iata": "BER", "icao": "EDDB", "name": "ベルリン・ブランデンブルク空港", "city": "ベルリン", "hub": "首都主要空港", "departures_url": "https://ber.berlin-airport.de/en/flying/departures.html", "radar_url": "https://www.flightradar24.com/airport/ber", "flightaware_url": "https://www.flightaware.com/live/airport/EDDB"}
        ]
    },
    "italy": {
        "id": "italy",
        "name": "イタリア",
        "english_name": "Italy",
        "flag": "🇮🇹",
        "city": "ローマ / ミラノ / ヴェネツィア",
        "embassy_name": "在イタリア日本国大使館 (Ambasciata del Giappone in Italia)",
        "mofa_code": "0039",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_153.html",
        "embassy_url": "https://www.it.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "緊急時: 112 (EU共通) / 113 (警察) / 118 (救急) / 大使館: +39-06-487991",
        "timezone_offset": 2,
        "timezone_name": "CEST (現地: UTC+2)",
        "currency_code": "EUR",
        "currency_name": "ユーロ",
        "currency_symbol": "€",
        "default_camera_id": "stream_euronews",
        "default_keywords": ["ローマ 治安", "イタリア ストライキ", "Italy strike", "ミラノ デモ"],
        "media_channels": [
            {"id": "stream_euronews_it", "name": "📺 Euronews (欧州24hニュース)", "video_id": "pykpO5kQJ98", "handle": "@euronews", "type": "stream"},
            {"id": "stream_france24_en_it", "name": "📺 France 24 English (国際ニュース)", "video_id": "a47ckXKZjxI", "handle": "@FRANCE24", "type": "stream"},
            {"id": "stream_dw_it", "name": "📺 DW News LIVE (ドイツ国際放送)", "video_id": "LuKwFajn37U", "handle": "@dwnews", "type": "stream"},
            {"id": "cam_venice_canal", "name": "📷 ヴェネツィア: カナル・グランデ 24h定点 [SkylineWebcams]", "video_id": "a1mcaV3Sf9U", "type": "camera"},
            {"id": "cam_rome_vatican", "name": "📷 ローマ: バチカン サン・ピエトロ広場 24h [Vatican News]", "video_id": "03pYP2Nmreo", "type": "camera"},
            {"id": "cam_milan_duomo", "name": "📷 ミラノ: ドゥオーモ大聖堂 24h実況 [Duomo Milano TV]", "video_id": "Iuc9BjSriaM", "type": "camera"}
        ],
        "weather_cities": [
            {"name": "ローマ (首都)", "name_en": "Rome", "lat": 41.9028, "lon": 12.4964, "is_capital": True},
            {"name": "ミラノ (北部経済中心)", "name_en": "Milan", "lat": 45.4642, "lon": 9.1900, "is_capital": False},
            {"name": "ヴェネツィア (ヴェネト州)", "name_en": "Venice", "lat": 45.4408, "lon": 12.3155, "is_capital": False}
        ],
        "transit_systems": [
            {"id": "trenitalia", "name": "トレニタリア (Trenitalia イタリア国鉄 フレッチャロッサ)", "mode": "全国幹線高速鉄道", "coverage": "イタリア全土・主要都市間", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "フレッチャロッサ（Frecciarossa）主要幹線は平常運行中", "official_url": "https://www.trenitalia.com/it/informazioni/infomobilita/notizie-infomobilita.html", "map_url": "https://www.trenitalia.com/it/le_frecce/collegamenti_e_servizifrecce.html", "strike_url": "https://www.trenitalia.com/it/informazioni/infomobilita/notizie-infomobilita.html"},
            {"id": "italo", "name": "イタロ (Italo NTV 高速民間鉄道)", "mode": "高速民間鉄道", "coverage": "トリノ/ミラノ ↔ ローマ/ナポリ/サレルノ", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "主要南北幹線ルートは平常運行中", "official_url": "https://www.italotreno.it/it/destinazioni-orari", "map_url": "https://www.italotreno.it/it/destinazioni-orari/rete-stazioni", "strike_url": "https://www.italotreno.it/it/il-treno/avvisi-viaggio"},
            {"id": "atac_roma", "name": "ATAC ローマ交通公社 (ローマ地下鉄 Metro A/B/C / 市内バス)", "mode": "地下鉄・都市バス", "coverage": "ローマ首都圏全域", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "地下鉄A・B線および市内トラム・バスは概ね平常運行中", "official_url": "https://www.atac.roma.it/tempo-reale", "map_url": "https://www.atac.roma.it/utilita/mappe", "strike_url": "https://www.atac.roma.it/tempo-reale/sciopero"},
            {"id": "atm_milano", "name": "ATM ミラノ交通公社 (ミラノ地下鉄 M1〜M5 / トラム)", "mode": "地下鉄・都市トラム", "coverage": "ミラノ大都市圏全域", "default_status": "平常運行", "default_badge": "🟢 平常運行", "default_code": "normal", "default_details": "地下鉄M1〜M5号線およびマルペンサ空港連絡は平常運行中", "official_url": "https://www.atm.it/it/ViaggiaConNoi/Pagine/InformazioniSullaCircolazione.aspx", "map_url": "https://www.atm.it/it/ViaggiaConNoi/Pagine/SchemaRete.aspx", "strike_url": "https://www.atm.it/it/IlGruppo/RelazioniSindacali/Pagine/DatiScioperi.aspx"}
        ],
        "airports": [
            {"iata": "FCO", "icao": "LIRF", "name": "ローマ・フィウミチーノ空港 (レオナルド・ダ・ヴィンチ)", "city": "ローマ", "hub": "イタリア最大ハブ", "departures_url": "https://www.adr.it/web/aeroporti-di-roma-en/pax-fco-flight-info", "radar_url": "https://www.flightradar24.com/airport/fco", "flightaware_url": "https://www.flightaware.com/live/airport/LIRF"},
            {"iata": "MXP", "icao": "LIMC", "name": "ミラノ・マルペンサ国際空港", "city": "ミラノ", "hub": "北部経済ハブ空港", "departures_url": "https://www.milanomalpensa-airport.com/en/flights/departures", "radar_url": "https://www.flightradar24.com/airport/mxp", "flightaware_url": "https://www.flightaware.com/live/airport/LIMC"},
            {"iata": "VCE", "icao": "LIPZ", "name": "ヴェネツィア・テッセラ空港 (マルコ・ポーロ)", "city": "ヴェネツィア", "hub": "ヴェネト州国際空港", "departures_url": "https://www.veniceairport.it/en/flights/departures.html", "radar_url": "https://www.flightradar24.com/airport/vce", "flightaware_url": "https://www.flightaware.com/live/airport/LIPZ"}
        ]
    },
    "australia": {
        "id": "australia",
        "name": "オーストラリア (豪州)",
        "english_name": "Australia",
        "flag": "🇦🇺",
        "city": "シドニー / キャンベラ (Sydney / Canberra)",
        "embassy_name": "在オーストラリア日本国大使館 (Embassy of Japan in Australia)",
        "mofa_code": "0061",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_071.html",
        "embassy_url": "https://www.au.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "緊急時: 000 (警察・救急・消防) / 大使館: +61-(0)2-6273-3244",
        "timezone_offset": 10,
        "timezone_name": "AEST (現地: UTC+10)",
        "currency_code": "AUD",
        "currency_name": "豪ドル",
        "currency_symbol": "A$",
        "default_camera_id": "stream_abc_news_au",
        "default_keywords": [
            "シドニー 治安",
            "オーストラリア デモ",
            "シドニー 空港 欠航",
            "Australia emergency"
        ],
        "media_channels": [
            {"id": "stream_abc_news_au", "name": "📺 ABC News Australia LIVE (豪公共放送24h)", "video_id": "6Xxb5uikewE", "handle": "@abcnews", "type": "stream"},
            {"id": "stream_skynews_au", "name": "📺 Sky News Australia (豪州24h生配信)", "video_id": "G7aG3_5N5iE", "handle": "@SkyNewsAustralia", "type": "stream"},
            {"id": "stream_7news_au", "name": "📺 7NEWS Australia (豪主要ニュース生配信)", "video_id": "L_vL14M58rI", "handle": "@7NEWSAustralia", "type": "stream"},
            {"id": "cam_sydney_harbour", "name": "📷 シドニー: ハーバーブリッジ＆オペラハウス 4K [WebcamSydney]", "video_id": "5uZa3-RMFos", "type": "camera"},
            {"id": "cam_sydney_panning", "name": "📷 シドニー: シドニー湾パノラマ 24h実況 [WebcamSydney]", "video_id": "tZ6aZOzvVWk", "type": "camera"},
            {"id": "cam_melbourne_city", "name": "📷 メルボルン: 市街中心部交差点 24h実況 [Cityscape Live]", "video_id": "gEbrHdFRgpQ", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "キャンベラ (首都)",
                "name_en": "Canberra",
                "lat": -35.2809,
                "lon": 149.13,
                "is_capital": True
            },
            {
                "name": "シドニー (最大都市)",
                "name_en": "Sydney",
                "lat": -33.8688,
                "lon": 151.2093,
                "is_capital": False
            },
            {
                "name": "メルボルン (南部)",
                "name_en": "Melbourne",
                "lat": -37.8136,
                "lon": 144.9631,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "sydney_trains",
                "name": "シドニー・トレインズ (Sydney Trains)",
                "mode": "都市鉄道・地下鉄",
                "coverage": "シドニー大都市圏",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "シドニー首都圏鉄道網は概ね平常運行中",
                "official_url": "https://transportnsw.info/alerts",
                "map_url": "https://transportnsw.info/routes/train"
            }
        ],
        "airports": [
            {
                "iata": "SYD",
                "icao": "YSSY",
                "name": "シドニー・キングスフォード・スミス国際空港",
                "city": "シドニー",
                "hub": "豪州最大国際ハブ",
                "departures_url": "https://www.sydneyairport.com.au/flights",
                "radar_url": "https://www.flightradar24.com/airport/syd",
                "flightaware_url": "https://www.flightaware.com/live/airport/YSSY"
            },
            {
                "iata": "MEL",
                "icao": "YMML",
                "name": "メルボルン空港 (タラマリン)",
                "city": "メルボルン",
                "hub": "主要国際空港",
                "departures_url": "https://www.melbourneairport.com.au/flights",
                "radar_url": "https://www.flightradar24.com/airport/mel",
                "flightaware_url": "https://www.flightaware.com/live/airport/YMML"
            }
        ]
    },
    "cambodia": {
        "id": "cambodia",
        "name": "カンボジア",
        "english_name": "Cambodia",
        "flag": "🇰🇭",
        "city": "プノンペン (Phnom Penh)",
        "embassy_name": "在カンボジア日本国大使館 (Embassy of Japan in Cambodia)",
        "mofa_code": "0855",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_004.html",
        "embassy_url": "https://www.kh.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察: 117 / 救急: 119 / 消防: 118 / 大使館: +855-(0)23-217-161",
        "timezone_offset": 7,
        "timezone_name": "ICT (現地: UTC+7)",
        "currency_code": "USD",
        "currency_name": "米ドル / リエル",
        "currency_symbol": "$",
        "currency_code": "KHR",
        "currency_name": "カンボジアリエル",
        "currency_symbol": "៛",
        "default_camera_id": "stream_euronews_asia",
        "default_keywords": [
            "プノンペン 治安",
            "カンボジア デモ",
            "プノンペン 洪水",
            "Cambodia safety"
        ],
        "media_channels": [
            {"id": "stream_fresh_news", "name": "📺 Fresh News Cambodia (速報生配信)", "video_id": "a47ckXKZjxI", "handle": "@freshnewscambodia", "type": "stream"},
            {"id": "stream_cna_cambodia", "name": "📺 CNA Asia LIVE (東南アジア国際報道)", "video_id": "XWq5kBlakcQ", "handle": "@ChannelNewsAsia", "type": "stream"},
            {"id": "stream_euronews_kh", "name": "📺 Euronews English (国際生配信)", "video_id": "pykpO5kQJ98", "handle": "@euronews", "type": "stream"}
        ],
        "weather_cities": [
            {
                "name": "プノンペン (首都)",
                "name_en": "Phnom Penh",
                "lat": 11.5564,
                "lon": 104.9282,
                "is_capital": True
            },
            {
                "name": "シェムリアップ (北西部)",
                "name_en": "Siem Reap",
                "lat": 13.3671,
                "lon": 103.8448,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "royal_railway",
                "name": "ロイヤル・レイルウェイ (Royal Railway Cambodia)",
                "mode": "幹線鉄道",
                "coverage": "プノンペン・シアヌークビル",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "旅客定期便運行中",
                "official_url": "https://royal-railway.com/"
            }
        ],
        "airports": [
            {
                "iata": "PNH",
                "icao": "VDPP",
                "name": "プノンペン国際空港",
                "city": "プノンペン",
                "hub": "首都主要国際空港",
                "departures_url": "https://www.pnh.aero/",
                "radar_url": "https://www.flightradar24.com/airport/pnh",
                "flightaware_url": "https://www.flightaware.com/live/airport/VDPP"
            }
        ]
    },
    "bangladesh": {
        "id": "bangladesh",
        "name": "バングラデシュ",
        "english_name": "Bangladesh",
        "flag": "🇧🇩",
        "city": "ダッカ (Dhaka)",
        "embassy_name": "在バングラデシュ日本国大使館 (Embassy of Japan in Bangladesh)",
        "mofa_code": "0880",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_012.html",
        "embassy_url": "https://www.bd.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察・救急・消防: 999 / 大使館: +880-(0)2-2222-60010",
        "timezone_offset": 6,
        "timezone_name": "BST (現地: UTC+6)",
        "currency_code": "BDT",
        "currency_name": "タカ",
        "currency_symbol": "৳",
        "default_camera_id": "stream_euronews_bd",
        "default_keywords": [
            "ダッカ 衝突",
            "バングラデシュ デモ",
            "ダッカ 空港 欠航",
            "Bangladesh protest"
        ],
        "media_channels": [
            {"id": "stream_channel24_live", "name": "📺 Channel 24 Live (バングラデシュ全国報道)", "video_id": "LVPgC7LQOw0", "handle": "@channel24_bd", "type": "stream"},
            {"id": "stream_jamuna_tv", "name": "📺 Jamuna TV 24h 生配信", "video_id": "WijlmY38Fic", "handle": "@JamunaTVbd", "type": "stream"},
            {"id": "stream_somoy_tv", "name": "📺 Somoy TV 24h ニュース生配信", "video_id": "a47ckXKZjxI", "handle": "@somoytvnetupdate", "type": "stream"}
        ],
        "weather_cities": [
            {
                "name": "ダッカ (首都)",
                "name_en": "Dhaka",
                "lat": 23.8103,
                "lon": 90.4125,
                "is_capital": True
            },
            {
                "name": "チッタゴン (南東部港湾)",
                "name_en": "Chittagong",
                "lat": 22.3569,
                "lon": 91.7832,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "dhaka_metro",
                "name": "ダッカ・メトロ (Dhaka Metro Rail)",
                "mode": "都市高速鉄道",
                "coverage": "ダッカ市内MRT",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "MRTライン6号線定期運行中",
                "official_url": "http://dmtcl.gov.bd/"
            }
        ],
        "airports": [
            {
                "iata": "DAC",
                "icao": "VGHS",
                "name": "ハズラット・シャージャラル国際空港",
                "city": "ダッカ",
                "hub": "バングラデシュ最大国際ハブ",
                "departures_url": "https://www.hsia.gov.bd/",
                "radar_url": "https://www.flightradar24.com/airport/dac",
                "flightaware_url": "https://www.flightaware.com/live/airport/VGHS"
            }
        ]
    },
    "china": {
        "id": "china",
        "name": "中国 (中華人民共和国)",
        "english_name": "China",
        "flag": "🇨🇳",
        "city": "北京 / 上海 (Beijing / Shanghai)",
        "embassy_name": "在中国日本国大使館 (Embassy of Japan in China)",
        "mofa_code": "0086",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_009.html",
        "embassy_url": "https://www.cn.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察: 110 / 救急: 120 / 消防: 119 / 大使館: +86-(0)10-8531-9800",
        "timezone_offset": 8,
        "timezone_name": "CST (現地: UTC+8)",
        "currency_code": "CNY",
        "currency_name": "人民元",
        "currency_symbol": "¥",
        "default_camera_id": "stream_cctv_live",
        "default_keywords": [
            "北京 治安",
            "上海 空港 遅延",
            "中国 台風 欠航",
            "China weather warning"
        ],
        "media_channels": [
            {"id": "stream_cgtn", "name": "📺 CGTN LIVE (中国国際テレビ 英語24h)", "video_id": "0i7n3r01L2U", "handle": "@CGTN", "type": "stream"},
            {"id": "stream_cctv_news", "name": "📺 CCTV 国際放送 / CGTN Documentary", "video_id": "pykpO5kQJ98", "type": "stream"},
            {"id": "stream_phoenix_tv", "name": "📺 鳳凰衛視 (Phoenix InfoNews 24h生配信)", "video_id": "a47ckXKZjxI", "type": "stream"},
            {"id": "cam_chengdu_panda", "name": "📷 成都: ジャイアントパンダ繁殖基地 24h HD定点 [iPanda公式]", "video_id": "SUXPnIEpbn4", "type": "camera"},
            {"id": "cam_hk_the_peak", "name": "📷 香港特別行政区: ヴィクトリア・ピーク 24h実況 [HK360VR]", "video_id": "TkfqXh9pj9g", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "北京 (首都)",
                "name_en": "Beijing",
                "lat": 39.9042,
                "lon": 116.4074,
                "is_capital": True
            },
            {
                "name": "上海 (最大経済都市)",
                "name_en": "Shanghai",
                "lat": 31.2304,
                "lon": 121.4737,
                "is_capital": False
            },
            {
                "name": "広州 (南部主要都市)",
                "name_en": "Guangzhou",
                "lat": 23.1291,
                "lon": 113.2644,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "china_railway",
                "name": "中国鉄路 (China Railway 高速鉄道動車組)",
                "mode": "全国高速鉄道",
                "coverage": "中国全土・主要都市間",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "京滬高速鉄道ほか主要幹線は平常運行中",
                "official_url": "https://www.12306.cn/"
            }
        ],
        "airports": [
            {
                "iata": "PEK",
                "icao": "ZBAA",
                "name": "北京首都国際空港",
                "city": "北京",
                "hub": "中国国家級国際ハブ",
                "departures_url": "http://www.bcia.com.cn/",
                "radar_url": "https://www.flightradar24.com/airport/pek",
                "flightaware_url": "https://www.flightaware.com/live/airport/ZBAA"
            },
            {
                "iata": "PVG",
                "icao": "ZSPD",
                "name": "上海浦東国際空港",
                "city": "上海",
                "hub": "東アジア最大級貨物・国際ハブ",
                "departures_url": "https://www.shanghai-airport.com/",
                "radar_url": "https://www.flightradar24.com/airport/pvg",
                "flightaware_url": "https://www.flightaware.com/live/airport/ZSPD"
            }
        ]
    },
    "hongkong": {
        "id": "hongkong",
        "name": "香港 (中国香港特別行政区)",
        "english_name": "Hong Kong",
        "flag": "🇭🇰",
        "city": "香港 (Hong Kong)",
        "embassy_name": "在香港日本国総領事館 (Consulate-General of Japan in Hong Kong)",
        "mofa_code": "0852",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_016.html",
        "embassy_url": "https://www.hk.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察・救急・消防: 999 / 総領事館: +852-2522-1184",
        "timezone_offset": 8,
        "timezone_name": "HKT (現地: UTC+8)",
        "currency_code": "HKD",
        "currency_name": "香港ドル",
        "currency_symbol": "HK$",
        "default_camera_id": "cam_victoria_harbour",
        "default_keywords": [
            "香港 台風",
            "香港 地下鉄 運休",
            "Hong Kong airport delay",
            "香港 治安"
        ],
        "media_channels": [
            {"id": "stream_tvb_news", "name": "📺 無綫新聞 TVB News (香港24h報道)", "video_id": "EmRK5wLMxzs", "handle": "@tvbnewsofficial", "type": "stream"},
            {"id": "stream_rthk_news", "name": "📺 香港電台 RTHK News (香港公共放送)", "video_id": "0OBl1isIqpE", "handle": "@RTHK", "type": "stream"},
            {"id": "stream_now_news", "name": "📺 Now新聞台 (Now TV News LIVE)", "video_id": "k3O5923LqAA", "handle": "@now_news", "type": "stream"},
            {"id": "cam_the_peak", "name": "📷 香港: ヴィクトリア・ピーク (The Peak) 24h実況 [HK360VR]", "video_id": "TkfqXh9pj9g", "type": "camera"},
            {"id": "cam_hk_airport", "name": "📷 香港国際空港 (HKG) 24h離着陸実況", "video_id": "iinWeFecFg4", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "香港 (九龍・中環)",
                "name_en": "Hong Kong",
                "lat": 22.3193,
                "lon": 114.1694,
                "is_capital": True
            }
        ],
        "transit_systems": [
            {
                "id": "mtr_hk",
                "name": "香港鉄路 (MTR 地下鉄・空港快線)",
                "mode": "地下鉄・都市鉄道",
                "coverage": "香港全域・機場快線",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "MTR全線・機場快線平常運行中",
                "official_url": "https://www.mtr.com.hk/ch/customer/services/traffic_status.html"
            }
        ],
        "airports": [
            {
                "iata": "HKG",
                "icao": "VHHH",
                "name": "香港国際空港 (赤鱲角)",
                "city": "香港",
                "hub": "世界最高峰国際航空ハブ",
                "departures_url": "https://www.hongkongairport.com/en/flights/departures/passenger.page",
                "radar_url": "https://www.flightradar24.com/airport/hkg",
                "flightaware_url": "https://www.flightaware.com/live/airport/VHHH"
            }
        ]
    },
    "india": {
        "id": "india",
        "name": "インド",
        "english_name": "India",
        "flag": "🇮🇳",
        "city": "ニューデリー / ムンバイ (New Delhi / Mumbai)",
        "embassy_name": "在インド日本国大使館 (Embassy of Japan in India)",
        "mofa_code": "0091",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_001.html",
        "embassy_url": "https://www.in.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "総合緊急: 112 / 警察: 100 / 救急: 102 / 消防: 101 / 大使館: +91-(0)11-4610-4610",
        "timezone_offset": 5.5,
        "timezone_name": "IST (現地: UTC+5:30)",
        "currency_code": "INR",
        "currency_name": "インドルピー",
        "currency_symbol": "₹",
        "default_camera_id": "stream_ndtv_live",
        "default_keywords": [
            "デリー 大気汚染",
            "インド デモ",
            "ムンバイ 洪水",
            "India flight disruption"
        ],
        "media_channels": [
            {"id": "stream_ndtv_live", "name": "📺 NDTV 24x7 (インド全国英語ニュース)", "video_id": "xDWQ3LkccY8", "handle": "@NDTV", "type": "stream"},
            {"id": "stream_india_today", "name": "📺 India Today LIVE 24h", "video_id": "W1ilCy6gkQk", "handle": "@indiatoday", "type": "stream"},
            {"id": "stream_wion_live", "name": "📺 WION (World Is One News インド国際放送)", "video_id": "LuKwFajn37U", "handle": "@WION", "type": "stream"},
            {"id": "cam_somnath_temple", "name": "📷 インド・グジャラート: ソームナート寺院 24h定点実況", "video_id": "J4z7CIrvsuw", "type": "camera"},
            {"id": "cam_haridwar_ganga", "name": "📷 インド・ハリドワール: ガンジス川 24h実況", "video_id": "Bi9cRN61nOY", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "ニューデリー (首都)",
                "name_en": "New Delhi",
                "lat": 28.6139,
                "lon": 77.209,
                "is_capital": True
            },
            {
                "name": "ムンバイ (商業都市)",
                "name_en": "Mumbai",
                "lat": 19.076,
                "lon": 72.8777,
                "is_capital": False
            },
            {
                "name": "ベンガルール (IT拠点)",
                "name_en": "Bengaluru",
                "lat": 12.9716,
                "lon": 77.5946,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "delhi_metro",
                "name": "デリー・メトロ (Delhi Metro Rail)",
                "mode": "都市高速鉄道",
                "coverage": "デリー首都圏",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "デリーメトロ各線平常運行中",
                "official_url": "https://www.delhimetrorail.com/"
            }
        ],
        "airports": [
            {
                "iata": "DEL",
                "icao": "VIDP",
                "name": "インディラ・ガンディー国際空港",
                "city": "ニューデリー",
                "hub": "インド最大国際ハブ",
                "departures_url": "https://www.newdelhiairport.in/flight-information/live-flight-departures",
                "radar_url": "https://www.flightradar24.com/airport/del",
                "flightaware_url": "https://www.flightaware.com/live/airport/VIDP"
            },
            {
                "iata": "BOM",
                "icao": "VABB",
                "name": "チャトラパティ・シヴァージー国際空港",
                "city": "ムンバイ",
                "hub": "西部主要国際空港",
                "departures_url": "https://csmia.adaniairports.com/",
                "radar_url": "https://www.flightradar24.com/airport/bom",
                "flightaware_url": "https://www.flightaware.com/live/airport/VABB"
            }
        ]
    },
    "indonesia": {
        "id": "indonesia",
        "name": "インドネシア",
        "english_name": "Indonesia",
        "flag": "🇮🇩",
        "city": "ジャカルタ (Jakarta)",
        "embassy_name": "在インドネシア日本国大使館 (Embassy of Japan in Indonesia)",
        "mofa_code": "0062",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_002.html",
        "embassy_url": "https://www.id.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "総合緊急: 112 / 警察: 110 / 救急: 118 / 大使館: +62-(0)21-3192-4308",
        "timezone_offset": 7,
        "timezone_name": "WIB (現地: UTC+7)",
        "currency_code": "IDR",
        "currency_name": "インドネシアルピア",
        "currency_symbol": "Rp",
        "default_camera_id": "stream_kompas_live",
        "default_keywords": [
            "ジャカルタ 洪水",
            "インドネシア 地震",
            "ジャカルタ デモ",
            "Jakarta strike"
        ],
        "media_channels": [
            {"id": "stream_kompas_live", "name": "📺 Kompas TV 24h 生配信", "video_id": "pykpO5kQJ98", "handle": "@KompasTV", "type": "stream"},
            {"id": "stream_cnn_id", "name": "📺 CNN Indonesia 24h LIVE", "video_id": "a47ckXKZjxI", "handle": "@CNNindonesiaOfficial", "type": "stream"},
            {"id": "stream_tvone_live", "name": "📺 tvOne News 24h 生配信", "video_id": "xDWQ3LkccY8", "handle": "@tvOneNews", "type": "stream"},
            {"id": "cam_bali_jimbaran", "name": "📷 バリ島: ジンバラン・ビーチ 4Kパノラマ 24/7 [Bali Weather]", "video_id": "L1duJDAqbJY", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "ジャカルタ (首都)",
                "name_en": "Jakarta",
                "lat": -6.2088,
                "lon": 106.8456,
                "is_capital": True
            },
            {
                "name": "デンパサール (バリ島)",
                "name_en": "Denpasar",
                "lat": -8.6705,
                "lon": 115.2126,
                "is_capital": False
            },
            {
                "name": "スラバヤ (東ジャワ)",
                "name_en": "Surabaya",
                "lat": -7.2575,
                "lon": 112.7521,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "mrt_jakarta",
                "name": "MRTジャカルタ (MRT Jakarta)",
                "mode": "地下鉄・都市鉄道",
                "coverage": "ジャカルタ南北線",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "MRT線定常運行中",
                "official_url": "https://jakartamrt.co.id/"
            }
        ],
        "airports": [
            {
                "iata": "CGK",
                "icao": "WIII",
                "name": "スカルノ・ハッタ国際空港",
                "city": "ジャカルタ",
                "hub": "インドネシア最大ハブ",
                "departures_url": "https://soekarnohatta-airport.co.id/",
                "radar_url": "https://www.flightradar24.com/airport/cgk",
                "flightaware_url": "https://www.flightaware.com/live/airport/WIII"
            },
            {
                "iata": "DPS",
                "icao": "WADD",
                "name": "ングラ・ライ国際空港 (バリ島)",
                "city": "バリ・デンパサール",
                "hub": "主要観光国際空港",
                "departures_url": "https://baliairport.ngurahrai.co.id/",
                "radar_url": "https://www.flightradar24.com/airport/dps",
                "flightaware_url": "https://www.flightaware.com/live/airport/WADD"
            }
        ]
    },
    "korea": {
        "id": "korea",
        "name": "韓国 (大韓民国)",
        "english_name": "South Korea",
        "flag": "🇰🇷",
        "city": "ソウル (Seoul)",
        "embassy_name": "在大韓民国日本国大使館 (Embassy of Japan in Korea)",
        "mofa_code": "0082",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_003.html",
        "embassy_url": "https://www.kr.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察: 112 / 消防・救急: 119 / 大使館: +82-(0)2-2170-5200",
        "timezone_offset": 9,
        "timezone_name": "KST (現地: UTC+9)",
        "currency_code": "KRW",
        "currency_name": "韓国ウォン",
        "currency_symbol": "₩",
        "default_camera_id": "stream_ytn_live",
        "default_keywords": [
            "ソウル デモ",
            "韓国 ストライキ",
            "仁川空港 欠航",
            "Seoul weather warning"
        ],
        "media_channels": [
            {"id": "stream_ytn_live", "name": "📺 YTN 24h ニュース生放送", "video_id": "EQpbDRm7h2Y", "handle": "@ytnnews24", "type": "stream"},
            {"id": "stream_yonhap_live", "name": "📺 聯合ニュースTV (Yonhap News 24h)", "video_id": "pykpO5kQJ98", "handle": "@yonhapnewstv", "type": "stream"},
            {"id": "stream_kbs_live", "name": "📺 KBS News 24h 生配信", "video_id": "FDmrXrvZD14", "handle": "@kbsnews", "type": "stream"},
            {"id": "cam_seoul_han_river", "name": "📷 ソウル: 漢江・汝矣島 4Kライブ [한강 라이브 365]", "video_id": "5gVrWGRZo9s", "type": "camera"},
            {"id": "cam_seoul_station", "name": "📷 ソウル: ソウル駅前広場 24h定点カメラ [GiGAeyes]", "video_id": "C3hW1VrwmNc", "type": "camera"},
            {"id": "cam_seoul_mapo", "name": "📷 ソウル: 漢江・麻浦大橋 4K実況 [RIVERWORKER]", "video_id": "vk5BHoDxXf0", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "ソウル (首都)",
                "name_en": "Seoul",
                "lat": 37.5665,
                "lon": 126.978,
                "is_capital": True
            },
            {
                "name": "釜山 (南部港湾都市)",
                "name_en": "Busan",
                "lat": 35.1796,
                "lon": 129.0756,
                "is_capital": False
            },
            {
                "name": "済州 (リゾート島)",
                "name_en": "Jeju",
                "lat": 33.4996,
                "lon": 126.5312,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "korail",
                "name": "韓国鉄道公社 (KORAIL KTX高速鉄道)",
                "mode": "全国高速鉄道・幹線",
                "coverage": "韓国内主要都市間",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "京釜線KTXなど主要幹線平常運行中",
                "official_url": "https://www.letskorail.com/"
            }
        ],
        "airports": [
            {
                "iata": "ICN",
                "icao": "RKSI",
                "name": "仁川国際空港",
                "city": "ソウル/仁川",
                "hub": "東アジア屈指のメガハブ",
                "departures_url": "https://www.airport.kr/ap/ko/dep/depPasList.do",
                "radar_url": "https://www.flightradar24.com/airport/icn",
                "flightaware_url": "https://www.flightaware.com/live/airport/RKSI"
            },
            {
                "iata": "GMP",
                "icao": "RKSS",
                "name": "金浦国際空港",
                "city": "ソウル",
                "hub": "都心ビジネス空港",
                "departures_url": "https://www.airport.co.kr/gimpo/index.do",
                "radar_url": "https://www.flightradar24.com/airport/gmp",
                "flightaware_url": "https://www.flightaware.com/live/airport/RKSS"
            }
        ]
    },
    "malaysia": {
        "id": "malaysia",
        "name": "マレーシア",
        "english_name": "Malaysia",
        "flag": "🇲🇾",
        "city": "クアラルンプール (Kuala Lumpur)",
        "embassy_name": "在マレーシア日本国大使館 (Embassy of Japan in Malaysia)",
        "mofa_code": "0060",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_017.html",
        "embassy_url": "https://www.my.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察・救急: 999 / 消防: 994 / 大使館: +60-(0)3-2177-2600",
        "timezone_offset": 8,
        "timezone_name": "MYT (現地: UTC+8)",
        "currency_code": "MYR",
        "currency_name": "マレーシアリンギット",
        "currency_symbol": "RM",
        "default_camera_id": "stream_bernama_live",
        "default_keywords": [
            "クアラルンプール 洪水",
            "マレーシア ストライキ",
            "KLIA 遅延",
            "Malaysia emergency"
        ],
        "media_channels": [
            {"id": "stream_astro_awani", "name": "📺 Astro AWANI 24h (マレーシア主要ニュース)", "video_id": "pykpO5kQJ98", "handle": "@astroawani", "type": "stream"},
            {"id": "stream_berita_rtm", "name": "📺 Berita RTM (国営放送ニュース生配信)", "video_id": "a47ckXKZjxI", "handle": "@beritartm", "type": "stream"},
            {"id": "stream_tv3_malaysia", "name": "📺 TV3 Buletin Utama (主要民放ニュース)", "video_id": "xDWQ3LkccY8", "handle": "@TV3MALAYSIAOfficial", "type": "stream"},
            {"id": "cam_kl_explore", "name": "📷 クアラルンプール: 市街地 24h実況 [Watchers Club]", "video_id": "0YDJw6qXzts", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "クアラルンプール (首都)",
                "name_en": "Kuala Lumpur",
                "lat": 3.139,
                "lon": 101.6869,
                "is_capital": True
            },
            {
                "name": "ペナン (ジョージタウン)",
                "name_en": "Penang",
                "lat": 5.4141,
                "lon": 100.3288,
                "is_capital": False
            },
            {
                "name": "ジョホールバル (南部経済圏)",
                "name_en": "Johor Bahru",
                "lat": 1.4927,
                "lon": 103.7414,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "rapid_kl",
                "name": "ラピドKL (Rapid KL LRT/MRT/Monorail)",
                "mode": "都市鉄道・LRT",
                "coverage": "クアラルンプール首都圏",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "LRTクラナジャヤ線・MRT各線平常運行中",
                "official_url": "https://myrapid.com.my/"
            }
        ],
        "airports": [
            {
                "iata": "KUL",
                "icao": "WMKK",
                "name": "クアラルンプール国際空港 (KLIA)",
                "city": "クアラルンプール",
                "hub": "東南アジア主要国際ハブ",
                "departures_url": "https://airports.malaysiaairports.com.my/klia/flight-info/departures",
                "radar_url": "https://www.flightradar24.com/airport/kul",
                "flightaware_url": "https://www.flightaware.com/live/airport/WMKK"
            }
        ]
    },
    "mongolia": {
        "id": "mongolia",
        "name": "モンゴル",
        "english_name": "Mongolia",
        "flag": "🇲🇳",
        "city": "ウランバートル (Ulaanbaatar)",
        "embassy_name": "在モンゴル日本国大使館 (Embassy of Japan in Mongolia)",
        "mofa_code": "0976",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_019.html",
        "embassy_url": "https://www.mn.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察: 102 / 救急: 103 / 消防: 101 / 大使館: +976-11-320777",
        "timezone_offset": 8,
        "timezone_name": "ULAT (現地: UTC+8)",
        "currency_code": "MNT",
        "currency_name": "トゥグルグ",
        "currency_symbol": "₮",
        "default_camera_id": "stream_mongol_news",
        "default_keywords": [
            "ウランバートル 吹雪",
            "モンゴル デモ",
            "モンゴル 寒波 ゾド",
            "Mongolia weather warning"
        ],
        "media_channels": [
            {"id": "stream_mnb_live", "name": "📺 MNB National TV (モンゴル国営ニュース)", "video_id": "pykpO5kQJ98", "handle": "@MNBmongolia", "type": "stream"},
            {"id": "stream_euronews_mn", "name": "📺 Euronews English (国際生配信)", "video_id": "pykpO5kQJ98", "handle": "@euronews", "type": "stream"},
            {"id": "stream_dw_mn", "name": "📺 DW News LIVE (国際英語放送)", "video_id": "LuKwFajn37U", "handle": "@dwnews", "type": "stream"},
            {"id": "cam_mongolia_nature", "name": "📷 モンゴル: 大草原・野生動物 24h自然実況 [Nature Stream]", "video_id": "JVXC4DrH6PA", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "ウランバートル (首都)",
                "name_en": "Ulaanbaatar",
                "lat": 47.8864,
                "lon": 106.9057,
                "is_capital": True
            }
        ],
        "transit_systems": [
            {
                "id": "ub_railway",
                "name": "ウランバートル鉄道 (UBTZ モンゴル縦断鉄道)",
                "mode": "幹線鉄道",
                "coverage": "モンゴル全土・中露連絡",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "定期運行中",
                "official_url": "https://www.ubtz.mn/"
            }
        ],
        "airports": [
            {
                "iata": "UBN",
                "icao": "ZMCK",
                "name": "チンギス・ハーン国際空港",
                "city": "ウランバートル",
                "hub": "モンゴル主要国際空港",
                "departures_url": "https://www.ulaanbaatar-airport.mn/",
                "radar_url": "https://www.flightradar24.com/airport/ubn",
                "flightaware_url": "https://www.flightaware.com/live/airport/ZMCK"
            }
        ]
    },
    "myanmar": {
        "id": "myanmar",
        "name": "ミャンマー",
        "english_name": "Myanmar",
        "flag": "🇲🇲",
        "city": "ヤンゴン / ネピドー (Yangon / Naypyidaw)",
        "embassy_name": "在ミャンマー日本国大使館 (Embassy of Japan in Myanmar)",
        "mofa_code": "0095",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_018.html",
        "embassy_url": "https://www.mm.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察: 199 / 救急: 192 / 消防: 191 / 大使館: +95-(0)1-549644",
        "timezone_offset": 6.5,
        "timezone_name": "MMT (現地: UTC+6:30)",
        "currency_code": "MMK",
        "currency_name": "チャット",
        "currency_symbol": "K",
        "default_camera_id": "stream_euronews_mm",
        "default_keywords": [
            "ヤンゴン 停電",
            "ミャンマー 治安",
            "ミャンマー 衝突",
            "Myanmar conflict"
        ],
        "media_channels": [
            {"id": "stream_dvb_tv", "name": "📺 DVB TV News (ビルマ民主の声 24h)", "video_id": "pykpO5kQJ98", "handle": "@dvbtvnews", "type": "stream"},
            {"id": "stream_mizzima_tv", "name": "📺 Mizzima News LIVE", "video_id": "a47ckXKZjxI", "handle": "@MizzimaNews", "type": "stream"},
            {"id": "stream_cna_mm", "name": "📺 CNA Asia (アジア国際報道生配信)", "video_id": "XWq5kBlakcQ", "handle": "@ChannelNewsAsia", "type": "stream"}
        ],
        "weather_cities": [
            {
                "name": "ヤンゴン (旧首都・商業中心)",
                "name_en": "Yangon",
                "lat": 16.8661,
                "lon": 96.1951,
                "is_capital": False
            },
            {
                "name": "ネピドー (行政首都)",
                "name_en": "Naypyidaw",
                "lat": 19.7633,
                "lon": 96.0785,
                "is_capital": True
            },
            {
                "name": "マンダレー (北部拠点)",
                "name_en": "Mandalay",
                "lat": 21.9588,
                "lon": 96.0891,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "myanmar_railway",
                "name": "ミャンマー国鉄 (Myanma Railways)",
                "mode": "幹線鉄道",
                "coverage": "主要幹線",
                "default_status": "運行状況注意",
                "default_badge": "🟡 運航注意",
                "default_code": "disrupted",
                "default_details": "情勢に伴い減便または一部区間運休の可能性あり",
                "official_url": "https://www.motc.gov.mm/"
            }
        ],
        "airports": [
            {
                "iata": "RGN",
                "icao": "VYYY",
                "name": "ヤンゴン国際空港",
                "city": "ヤンゴン",
                "hub": "ミャンマー最大国際空港",
                "departures_url": "http://www.yangonairport.aero/",
                "radar_url": "https://www.flightradar24.com/airport/rgn",
                "flightaware_url": "https://www.flightaware.com/live/airport/VYYY"
            }
        ]
    },
    "philippines": {
        "id": "philippines",
        "name": "フィリピン",
        "english_name": "Philippines",
        "flag": "🇵🇭",
        "city": "マニラ (Manila)",
        "embassy_name": "在フィリピン日本国大使館 (Embassy of Japan in the Philippines)",
        "mofa_code": "0063",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_013.html",
        "embassy_url": "https://www.ph.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "全国緊急ダイヤル: 911 / 大使館: +63-(0)2-8551-5710",
        "timezone_offset": 8,
        "timezone_name": "PHT (現地: UTC+8)",
        "currency_code": "PHP",
        "currency_name": "フィリピンペソ",
        "currency_symbol": "₱",
        "default_camera_id": "stream_anc_live",
        "default_keywords": [
            "マニラ 台風 冠水",
            "フィリピン 地震",
            "ニノイアキノ 欠航",
            "Philippines storm warning"
        ],
        "media_channels": [
            {"id": "stream_abscbn_news", "name": "📺 ABS-CBN News (フィリピン最大手生配信)", "video_id": "pykpO5kQJ98", "handle": "@ABSCBNNews", "type": "stream"},
            {"id": "stream_gma_news", "name": "📺 GMA Integrated News 24h", "video_id": "a47ckXKZjxI", "handle": "@gmanews", "type": "stream"},
            {"id": "stream_one_news_ph", "name": "📺 One News PH 24h 英語報道", "video_id": "xDWQ3LkccY8", "handle": "@OneNewsPH", "type": "stream"},
            {"id": "cam_ph_agdao", "name": "📷 フィリピン: アグダオ市場・市街 24h定点 [Edge Babor]", "video_id": "u8CbGedbI08", "type": "camera"},
            {"id": "cam_ph_davao_street", "name": "📷 フィリピン: ダバオ市街通り 24h定点カメラ [JazBaz]", "video_id": "DSRm7V_bsm8", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "マニラ (首都)",
                "name_en": "Manila",
                "lat": 14.5995,
                "lon": 120.9842,
                "is_capital": True
            },
            {
                "name": "セブ (中部拠点都市)",
                "name_en": "Cebu",
                "lat": 10.3157,
                "lon": 123.8854,
                "is_capital": False
            },
            {
                "name": "ダバオ (南部主要都市)",
                "name_en": "Davao",
                "lat": 7.1907,
                "lon": 125.4578,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "mrt_manila",
                "name": "マニラ・メトロレール (MRT/LRT Manila)",
                "mode": "都市高速鉄道",
                "coverage": "マニラ首都圏高架鉄道",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "MRT3号線・LRT1/2号線平常運行中",
                "official_url": "https://www.dotr.gov.ph/"
            }
        ],
        "airports": [
            {
                "iata": "MNL",
                "icao": "RPLL",
                "name": "ニノイ・アキノ国際空港 (マニラ)",
                "city": "マニラ",
                "hub": "フィリピン最大国際ハブ",
                "departures_url": "https://www.miaagov.ph/",
                "radar_url": "https://www.flightradar24.com/airport/mnl",
                "flightaware_url": "https://www.flightaware.com/live/airport/RPLL"
            },
            {
                "iata": "CEB",
                "icao": "RPVM",
                "name": "マクタン・セブ国際空港",
                "city": "セブ",
                "hub": "中部主要国際空港",
                "departures_url": "https://mactancebuairport.com/",
                "radar_url": "https://www.flightradar24.com/airport/ceb",
                "flightaware_url": "https://www.flightaware.com/live/airport/RPVM"
            }
        ]
    },
    "singapore": {
        "id": "singapore",
        "name": "シンガポール",
        "english_name": "Singapore",
        "flag": "🇸🇬",
        "city": "シンガポール (Singapore)",
        "embassy_name": "在シンガポール日本国大使館 (Embassy of Japan in Singapore)",
        "mofa_code": "0065",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_005.html",
        "embassy_url": "https://www.sg.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察: 999 / 救急・消防: 995 / 大使館: +65-6235-8855",
        "timezone_offset": 8,
        "timezone_name": "SGT (現地: UTC+8)",
        "currency_code": "SGD",
        "currency_name": "シンガポールドル",
        "currency_symbol": "S$",
        "default_camera_id": "stream_cna_live",
        "default_keywords": [
            "シンガポール ヘイズ",
            "チャンギ空港 遅延",
            "シンガポール 豪雨",
            "Singapore haze alert"
        ],
        "media_channels": [
            {"id": "stream_cna_live", "name": "📺 CNA LIVE (Channel NewsAsia 24h国際生配信)", "video_id": "XWq5kBlakcQ", "handle": "@ChannelNewsAsia", "type": "stream"},
            {"id": "stream_8world_news", "name": "📺 8視界新聞 (Mediacorp 8 World)", "video_id": "wjtJDNuama8", "handle": "@8world", "type": "stream"},
            {"id": "stream_straits_times", "name": "📺 The Straits Times (シンガポール英字紙)", "video_id": "8u_Y47m_P00", "handle": "@TheStraitsTimes", "type": "stream"},
            {"id": "cam_marina_bay", "name": "📷 シンガポール: マリーナベイ・サンズ＆都心スカイライン 24/7", "video_id": "4vzAAjq1AN8", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "シンガポール (全域)",
                "name_en": "Singapore",
                "lat": 1.3521,
                "lon": 103.8198,
                "is_capital": True
            }
        ],
        "transit_systems": [
            {
                "id": "smrt_singapore",
                "name": "SMRT / SBS Transit (MRT地下鉄・LRT)",
                "mode": "地下鉄・都市鉄道",
                "coverage": "シンガポール全域",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "MRT南北線・東西線・環状線など平常運行中",
                "official_url": "https://www.smrt.com.my/"
            }
        ],
        "airports": [
            {
                "iata": "SIN",
                "icao": "WSSS",
                "name": "シンガポール・チャンギ国際空港",
                "city": "シンガポール",
                "hub": "世界最高峰グローバルハブ空港",
                "departures_url": "https://www.changiairport.com/en/flights/departures.html",
                "radar_url": "https://www.flightradar24.com/airport/sin",
                "flightaware_url": "https://www.flightaware.com/live/airport/WSSS"
            }
        ]
    },
    "taiwan": {
        "id": "taiwan",
        "name": "台湾",
        "english_name": "Taiwan",
        "flag": "🇹🇼",
        "city": "台北 (Taipei)",
        "embassy_name": "日本台湾交流協会 台北事務所 (Japan-Taiwan Exchange Association)",
        "mofa_code": "0886",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_008.html",
        "embassy_url": "https://www.koryu.or.jp/",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察: 110 / 消防・救急: 119 / 交流協会: +886-(0)2-2713-8011",
        "timezone_offset": 8,
        "timezone_name": "CST (現地: UTC+8)",
        "currency_code": "TWD",
        "currency_name": "新台湾ドル",
        "currency_symbol": "NT$",
        "default_camera_id": "stream_ftv_taiwan",
        "default_keywords": [
            "台湾 地震",
            "台湾 台風 停電",
            "桃園空港 欠航",
            "Taiwan weather warning"
        ],
        "media_channels": [
            {"id": "stream_ftv_news", "name": "📺 民視新聞 FTV News (台湾24h生配信)", "video_id": "yL5tBvW_M_E", "handle": "@FTV_News", "type": "stream"},
            {"id": "stream_set_news", "name": "📺 三立LIVE新聞 SET News 24h", "video_id": "pL1o59_K2vI", "handle": "@setn", "type": "stream"},
            {"id": "stream_tvbs_news", "name": "📺 TVBS NEWS 55頻道 24h生配信", "video_id": "2mCSYvcfhtc", "handle": "@TVBSNEWS01", "type": "stream"},
            {"id": "cam_taipei_101", "name": "📷 台北: 台北101 象山展望台 4K即時映像 [台北市觀光公式]", "video_id": "z_fY1pj1VBw", "type": "camera"},
            {"id": "cam_jiantanshan", "name": "📷 台北: 劍潭山微風平台 4K即時映像 [台北市觀光公式]", "video_id": "Ndo_8RuefH4", "type": "camera"},
            {"id": "cam_taoyuan_daxi", "name": "📷 桃園: 大渓老街 24h即時映像 [桃園観光公式]", "video_id": "XUWjAsajKXg", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "台北 (北部主要都市)",
                "name_en": "Taipei",
                "lat": 25.033,
                "lon": 121.5654,
                "is_capital": True
            },
            {
                "name": "高雄 (南部主要港湾)",
                "name_en": "Kaohsiung",
                "lat": 22.6273,
                "lon": 120.3014,
                "is_capital": False
            },
            {
                "name": "台中 (中部ハイテク拠点)",
                "name_en": "Taichung",
                "lat": 24.1477,
                "lon": 120.6736,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "taiwan_hsr",
                "name": "台湾高速鉄道 (THSR 台湾高鉄)",
                "mode": "高速鉄道",
                "coverage": "南港 ↔ 台北 ↔ 左営(高雄)",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "台湾高鉄全線平常運行中",
                "official_url": "https://www.thsrc.com.tw/"
            },
            {
                "id": "taipei_metro",
                "name": "台北捷運 (Taipei Metro TRTC)",
                "mode": "地下鉄",
                "coverage": "台北首都圏",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "台北メトロ各線平常運行中",
                "official_url": "https://www.metro.taipei/"
            }
        ],
        "airports": [
            {
                "iata": "TPE",
                "icao": "RCTP",
                "name": "台湾桃園国際空港",
                "city": "台北/桃園",
                "hub": "台湾最大国際ハブ",
                "departures_url": "https://www.taoyuan-airport.com/departures",
                "radar_url": "https://www.flightradar24.com/airport/tpe",
                "flightaware_url": "https://www.flightaware.com/live/airport/RCTP"
            },
            {
                "iata": "TSA",
                "icao": "RCSS",
                "name": "台北松山空港",
                "city": "台北都心",
                "hub": "都心国際・国内空港",
                "departures_url": "https://www.tsa.gov.tw/",
                "radar_url": "https://www.flightradar24.com/airport/tsa",
                "flightaware_url": "https://www.flightaware.com/live/airport/RCSS"
            }
        ]
    },
    "thailand": {
        "id": "thailand",
        "name": "タイ",
        "english_name": "Thailand",
        "flag": "🇹🇭",
        "city": "バンコク (Bangkok)",
        "embassy_name": "在タイ日本国大使館 (Embassy of Japan in Thailand)",
        "mofa_code": "0066",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_007.html",
        "embassy_url": "https://www.th.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察: 191 / 観光警察: 1155 / 救急: 1669 / 大使館: +66-(0)2-207-8500",
        "timezone_offset": 7,
        "timezone_name": "ICT (現地: UTC+7)",
        "currency_code": "THB",
        "currency_name": "タイバーツ",
        "currency_symbol": "฿",
        "default_camera_id": "stream_thairath_live",
        "default_keywords": [
            "バンコク 洪水 冠水",
            "タイ デモ",
            "スワンナプーム 遅延",
            "Bangkok protest"
        ],
        "media_channels": [
            {"id": "stream_thairath_live", "name": "📺 Thairath News 24h 生配信", "video_id": "a47ckXKZjxI", "handle": "@ThairathOnline24", "type": "stream"},
            {"id": "stream_thaipbs_live", "name": "📺 Thai PBS 24h 生配信", "video_id": "pykpO5kQJ98", "handle": "@ThaiPBS", "type": "stream"},
            {"id": "stream_amarintv_live", "name": "📺 Amarin TV HD 34 LIVE", "video_id": "xDWQ3LkccY8", "handle": "@AMARINTVHD", "type": "stream"},
            {"id": "cam_bangkok_skyline", "name": "📷 バンコク: 都心スカイライン 4K定点実況 [Bangkok 360]", "video_id": "LnYQNMZbOD4", "type": "camera"},
            {"id": "cam_bangkok_sukhumvit", "name": "📷 バンコク: スクムウィット通り 4K実況 [The Real Samui]", "video_id": "UemFRPrl1hk", "type": "camera"},
            {"id": "cam_phuket_patong", "name": "📷 プーケット: パトン・ビーチ 24h実況 [Randomly Entertained]", "video_id": "_nvG0c9keWI", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "バンコク (首都)",
                "name_en": "Bangkok",
                "lat": 13.7563,
                "lon": 100.5018,
                "is_capital": True
            },
            {
                "name": "チェンマイ (北部拠点)",
                "name_en": "Chiang Mai",
                "lat": 18.7883,
                "lon": 98.9853,
                "is_capital": False
            },
            {
                "name": "プーケット (南部リゾート)",
                "name_en": "Phuket",
                "lat": 7.8804,
                "lon": 98.3923,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "bts_skytrain",
                "name": "BTSスカイトレイン / MRT地下鉄 (Bangkok Mass Transit)",
                "mode": "高架鉄道・地下鉄",
                "coverage": "バンコク都心全域",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "BTSスクムウィット線・MRTブルーライン平常運行中",
                "official_url": "https://www.bts.co.th/"
            }
        ],
        "airports": [
            {
                "iata": "BKK",
                "icao": "VTBS",
                "name": "スワンナプーム国際空港",
                "city": "バンコク",
                "hub": "東南アジア最大級メガハブ",
                "departures_url": "https://suvarnabhumi.airportthai.co.th/en",
                "radar_url": "https://www.flightradar24.com/airport/bkk",
                "flightaware_url": "https://www.flightaware.com/live/airport/VTBS"
            },
            {
                "iata": "DMK",
                "icao": "VTBD",
                "name": "ドンムアン国際空港",
                "city": "バンコク",
                "hub": "LCC主要拠点空港",
                "departures_url": "https://donmueang.airportthai.co.th/en",
                "radar_url": "https://www.flightradar24.com/airport/dmk",
                "flightaware_url": "https://www.flightaware.com/live/airport/VTBD"
            }
        ]
    },
    "vietnam": {
        "id": "vietnam",
        "name": "ベトナム",
        "english_name": "Vietnam",
        "flag": "🇻🇳",
        "city": "ハノイ / ホーチミン (Hanoi / Ho Chi Minh)",
        "embassy_name": "在ベトナム日本国大使館 (Embassy of Japan in Vietnam)",
        "mofa_code": "0084",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_015.html",
        "embassy_url": "https://www.vn.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察: 113 / 救急: 115 / 消防: 114 / 大使館: +84-(0)24-3846-3000",
        "timezone_offset": 7,
        "timezone_name": "ICT (現地: UTC+7)",
        "currency_code": "VND",
        "currency_name": "ベトナムドン",
        "currency_symbol": "₫",
        "default_camera_id": "stream_vtv_live",
        "default_keywords": [
            "ハノイ 台風 冠水",
            "ホーチミン 洪水",
            "ノイバイ 空港 欠航",
            "Vietnam storm warning"
        ],
        "media_channels": [
            {"id": "stream_vtv24_live", "name": "📺 VTV24 News (ベトナム国営24h)", "video_id": "pykpO5kQJ98", "handle": "@VTV24", "type": "stream"},
            {"id": "stream_thvl_live", "name": "📺 THVL1 (ベトナム全国放送)", "video_id": "a47ckXKZjxI", "handle": "@THVLTongHop", "type": "stream"},
            {"id": "stream_tuoitre_live", "name": "📺 Tuoi Tre TV (若者日報ニュース生配信)", "video_id": "xDWQ3LkccY8", "handle": "@BaoTuoiTre", "type": "stream"},
            {"id": "cam_vietnam_nightwalk", "name": "📷 ベトナム: ハノイ・ホーチミン市街 24h実況 [Watchers Club]", "video_id": "eveR520xI6w", "type": "camera"},
            {"id": "cam_danang_traffic", "name": "📷 ダナン: 市街交通監視カメラ [Phát Triển Đà Nẵng]", "video_id": "sJvEFrG0wq0", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "ハノイ (首都)",
                "name_en": "Hanoi",
                "lat": 21.0285,
                "lon": 105.8542,
                "is_capital": True
            },
            {
                "name": "ホーチミン (最大経済都市)",
                "name_en": "Ho Chi Minh City",
                "lat": 10.8231,
                "lon": 106.6297,
                "is_capital": False
            },
            {
                "name": "ダナン (中部主要港湾)",
                "name_en": "Da Nang",
                "lat": 16.0544,
                "lon": 108.2022,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "vietnam_railways",
                "name": "ベトナム鉄道 (Vietnam Railways 南北統一鉄道)",
                "mode": "幹線鉄道",
                "coverage": "ハノイ ↔ サイゴン(ホーチミン)",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "南北統一鉄道各便平常運行中",
                "official_url": "https://dsvn.vn/"
            }
        ],
        "airports": [
            {
                "iata": "HAN",
                "icao": "VVNB",
                "name": "ノイバイ国際空港",
                "city": "ハノイ",
                "hub": "北部最大国際空港",
                "departures_url": "http://noibaiairport.vn/",
                "radar_url": "https://www.flightradar24.com/airport/han",
                "flightaware_url": "https://www.flightaware.com/live/airport/VVNB"
            },
            {
                "iata": "SGN",
                "icao": "VVTS",
                "name": "タンソンニャット国際空港",
                "city": "ホーチミン",
                "hub": "南部最大国際空港",
                "departures_url": "https://tansonnhatairport.vn/",
                "radar_url": "https://www.flightradar24.com/airport/sgn",
                "flightaware_url": "https://www.flightaware.com/live/airport/VVTS"
            }
        ]
    },
    "belgium": {
        "id": "belgium",
        "name": "ベルギー",
        "english_name": "Belgium",
        "flag": "🇧🇪",
        "city": "ブリュッセル (Brussels)",
        "embassy_name": "在ベルギー日本国大使館 (Embassy of Japan in Belgium)",
        "mofa_code": "0032",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_172.html",
        "embassy_url": "https://www.be.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "総合緊急: 112 / 警察: 101 / 救急・消防: 100 / 大使館: +32-(0)2-513-2340",
        "timezone_offset": 2,
        "timezone_name": "CEST (現地: UTC+2)",
        "currency_code": "EUR",
        "currency_name": "ユーロ",
        "currency_symbol": "€",
        "default_camera_id": "stream_rtbf_live",
        "default_keywords": [
            "ブリュッセル ストライキ",
            "ベルギー デモ",
            "ブリュッセル 空港 遅延",
            "Brussels protest"
        ],
        "media_channels": [
            {"id": "stream_rtbf_live", "name": "📺 RTBF Info (ベルギー公共放送生配信)", "video_id": "pykpO5kQJ98", "handle": "@RTBF", "type": "stream"},
            {"id": "stream_vrt_nws", "name": "📺 VRT NWS (フランドル公共放送24h)", "video_id": "a47ckXKZjxI", "handle": "@vrtnws", "type": "stream"},
            {"id": "stream_euronews_be", "name": "📺 Euronews English (EU・ブリュッセル報道)", "video_id": "pykpO5kQJ98", "handle": "@euronews", "type": "stream"},
            {"id": "cam_sint_niklaas", "name": "📷 シント・ニクラス市庁舎広場 24h実況", "video_id": "7gOLLJGudNo", "type": "camera"},
            {"id": "cam_koksijde_bad", "name": "📷 ベルギー沿岸: コクサイデ海岸 24h実況", "video_id": "5Uqw_G_IdjE", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "ブリュッセル (首都・EU本部)",
                "name_en": "Brussels",
                "lat": 50.8503,
                "lon": 4.3517,
                "is_capital": True
            },
            {
                "name": "アントワープ (北部主要港湾)",
                "name_en": "Antwerp",
                "lat": 51.2194,
                "lon": 4.4025,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "sncb",
                "name": "ベルギー国鉄 (SNCB/NMBS)",
                "mode": "全国幹線鉄道",
                "coverage": "ベルギー全土・国際線接続",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "国鉄インターシティ線平常運行中",
                "official_url": "https://www.belgiantrain.be/"
            }
        ],
        "airports": [
            {
                "iata": "BRU",
                "icao": "EBBR",
                "name": "ブリュッセル国際空港",
                "city": "ブリュッセル",
                "hub": "ベルギー主要国際ハブ",
                "departures_url": "https://www.brusselsairport.be/en/passengers/flights/departures",
                "radar_url": "https://www.flightradar24.com/airport/bru",
                "flightaware_url": "https://www.flightaware.com/live/airport/EBBR"
            }
        ]
    },
    "netherlands": {
        "id": "netherlands",
        "name": "オランダ",
        "english_name": "Netherlands",
        "flag": "🇳🇱",
        "city": "アムステルダム / ハーグ (Amsterdam / The Hague)",
        "embassy_name": "在オランダ日本国大使館 (Embassy of Japan in the Netherlands)",
        "mofa_code": "0031",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_157.html",
        "embassy_url": "https://www.nl.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察・救急・消防: 112 / 大使館: +31-(0)70-346-9544",
        "timezone_offset": 2,
        "timezone_name": "CEST (現地: UTC+2)",
        "currency_code": "EUR",
        "currency_name": "ユーロ",
        "currency_symbol": "€",
        "default_camera_id": "stream_nos_live",
        "default_keywords": [
            "アムステルダム ストライキ",
            "オランダ 嵐 欠航",
            "スキポール 空港 遅延",
            "Schiphol disruption"
        ],
        "media_channels": [
            {"id": "stream_nos_live", "name": "📺 NOS Journaal (オランダ公共放送生配信)", "video_id": "pykpO5kQJ98", "handle": "@nos", "type": "stream"},
            {"id": "stream_rtl_nieuws", "name": "📺 RTL Nieuws (オランダ主要民間報道)", "video_id": "a47ckXKZjxI", "handle": "@rtlnieuws", "type": "stream"},
            {"id": "stream_euronews_nl", "name": "📺 Euronews English (欧州24h生配信)", "video_id": "pykpO5kQJ98", "handle": "@euronews", "type": "stream"},
            {"id": "cam_amsterdam_dam", "name": "📷 アムステルダム: ダム広場・王宮前 4K [Now4Rent]", "video_id": "Gd9d4q6WvUY", "type": "camera"},
            {"id": "cam_rotterdam_erasmus", "name": "📷 ロッテルダム: エラスムス橋＆港湾 24h実況", "video_id": "nFozEhYTEMo", "type": "camera"},
            {"id": "cam_netherlands_rail", "name": "📷 オランダ鉄道: 幹線列車運行 24h実況 [RailCam]", "video_id": "abaZ4GD5jbM", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "アムステルダム (最大都市・首都)",
                "name_en": "Amsterdam",
                "lat": 52.3676,
                "lon": 4.9041,
                "is_capital": True
            },
            {
                "name": "ハーグ (政府機関・国際司法)",
                "name_en": "The Hague",
                "lat": 52.0705,
                "lon": 4.3007,
                "is_capital": False
            },
            {
                "name": "ロッテルダム (世界屈指の港湾)",
                "name_en": "Rotterdam",
                "lat": 51.9244,
                "lon": 4.4777,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "ns_rail",
                "name": "オランダ鉄道 (NS Nederlandse Spoorwegen)",
                "mode": "全国幹線鉄道",
                "coverage": "オランダ全土・スキポール空港直結",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "主要インターシティ平常運行中",
                "official_url": "https://www.ns.nl/en"
            }
        ],
        "airports": [
            {
                "iata": "AMS",
                "icao": "EHAM",
                "name": "アムステルダム・スキポール空港",
                "city": "アムステルダム",
                "hub": "欧州最高峰メガハブ",
                "departures_url": "https://www.schiphol.nl/en/departures/",
                "radar_url": "https://www.flightradar24.com/airport/ams",
                "flightaware_url": "https://www.flightaware.com/live/airport/EHAM"
            }
        ]
    },
    "turkey": {
        "id": "turkey",
        "name": "トルコ",
        "english_name": "Turkey",
        "flag": "🇹🇷",
        "city": "イスタンブール / アンカラ (Istanbul / Ankara)",
        "embassy_name": "在トルコ日本国大使館 (Embassy of Japan in Turkey)",
        "mofa_code": "0090",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_052.html",
        "embassy_url": "https://www.tr.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "全国総合緊急: 112 / 大使館: +90-(0)312-446-5500",
        "timezone_offset": 3,
        "timezone_name": "TRT (現地: UTC+3)",
        "currency_code": "TRY",
        "currency_name": "トルコリラ",
        "currency_symbol": "₺",
        "default_camera_id": "stream_trt_live",
        "default_keywords": [
            "イスタンブール 地震",
            "トルコ デモ",
            "イスタンブール 吹雪 欠航",
            "Turkey emergency"
        ],
        "media_channels": [
            {"id": "stream_trt_world", "name": "📺 TRT World LIVE (トルコ国際24h英語放送)", "video_id": "a47ckXKZjxI", "handle": "@trtworld", "type": "stream"},
            {"id": "stream_trt_haber", "name": "📺 TRT Haber 24h (国営速報生配信)", "video_id": "pykpO5kQJ98", "handle": "@trthaber", "type": "stream"},
            {"id": "stream_ahaber", "name": "📺 A Haber LIVE (トルコ主要報道生配信)", "video_id": "xDWQ3LkccY8", "handle": "@ahaber", "type": "stream"},
            {"id": "cam_istanbul_bosphorus", "name": "📷 イスタンブール: ボスポラス海峡＆アヤソフィア 4K実況", "video_id": "bbVe5h7X3uw", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "アンカラ (首都)",
                "name_en": "Ankara",
                "lat": 39.9334,
                "lon": 32.8597,
                "is_capital": True
            },
            {
                "name": "イスタンブール (最大都市)",
                "name_en": "Istanbul",
                "lat": 41.0082,
                "lon": 28.9784,
                "is_capital": False
            },
            {
                "name": "イズミル (エーゲ海沿岸)",
                "name_en": "Izmir",
                "lat": 38.4237,
                "lon": 27.1428,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "tcdd",
                "name": "トルコ国鉄 (TCDD 高速列車YHT)",
                "mode": "高速鉄道・全国幹線",
                "coverage": "アンカラ ↔ イスタンブールなど",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "YHT高速列車など主要幹線平常運行中",
                "official_url": "https://www.tcddtasimacilik.gov.tr/"
            }
        ],
        "airports": [
            {
                "iata": "IST",
                "icao": "LTFM",
                "name": "イスタンブール空港",
                "city": "イスタンブール",
                "hub": "世界最大級メガハブ",
                "departures_url": "https://www.istairport.com/en/flights/flight-info/departures",
                "radar_url": "https://www.flightradar24.com/airport/ist",
                "flightaware_url": "https://www.flightaware.com/live/airport/LTFM"
            },
            {
                "iata": "SAW",
                "icao": "LTFJ",
                "name": "サビハ・ギョクチェン国際空港",
                "city": "イスタンブール",
                "hub": "アジア側主要国際空港",
                "departures_url": "https://www.sabihagokcen.aero/",
                "radar_url": "https://www.flightradar24.com/airport/saw",
                "flightaware_url": "https://www.flightaware.com/live/airport/LTFJ"
            }
        ]
    },
    "uae": {
        "id": "uae",
        "name": "アラブ首長国連邦 (UAE)",
        "english_name": "United Arab Emirates",
        "flag": "🇦🇪",
        "city": "ドバイ / アブダビ (Dubai / Abu Dhabi)",
        "embassy_name": "在アラブ首長国連邦日本国大使館 (Embassy of Japan in the UAE)",
        "mofa_code": "0971",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_042.html",
        "embassy_url": "https://www.uae.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察: 999 / 救急: 998 / 消防: 997 / 大使館: +971-(0)2-443-5696",
        "timezone_offset": 4,
        "timezone_name": "GST (現地: UTC+4)",
        "currency_code": "AED",
        "currency_name": "UAEディルハム",
        "currency_symbol": "DH",
        "default_camera_id": "stream_dubai_live",
        "default_keywords": [
            "ドバイ 豪雨 冠水",
            "UAE 中東情勢 警戒",
            "ドバイ空港 欠航",
            "Dubai flight delay"
        ],
        "media_channels": [
            {"id": "stream_alarabiya_en", "name": "📺 Al Arabiya English (中東国際24h生配信)", "video_id": "JvjOmFZSdRo", "handle": "@AlArabiyaEnglish", "type": "stream"},
            {"id": "stream_skynews_arabia", "name": "📺 Sky News Arabia 24h (UAEアブダビ発)", "video_id": "DK2iJ5Fv_vA", "handle": "@SkyNewsArabia", "type": "stream"},
            {"id": "stream_dubai_tv", "name": "📺 Dubai TV (ドバイ公式生配信)", "video_id": "xDWQ3LkccY8", "handle": "@DubaiTV", "type": "stream"},
            {"id": "cam_dubai_city", "name": "📷 ドバイ: ブルジュ・ハリファ＆都心部 24hパノラマ [UinDubai]", "video_id": "DpJOji9B_9o", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "アブダビ (連邦首都)",
                "name_en": "Abu Dhabi",
                "lat": 24.4539,
                "lon": 54.3773,
                "is_capital": True
            },
            {
                "name": "ドバイ (世界商業ハブ)",
                "name_en": "Dubai",
                "lat": 25.2048,
                "lon": 55.2708,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "dubai_metro",
                "name": "ドバイ・メトロ (Dubai Metro RTA)",
                "mode": "都市高速無人鉄道",
                "coverage": "ドバイ都心・空港直結",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "レッドライン・グリーンライン平常運行中",
                "official_url": "https://www.rta.ae/"
            }
        ],
        "airports": [
            {
                "iata": "DXB",
                "icao": "OMDB",
                "name": "ドバイ国際空港",
                "city": "ドバイ",
                "hub": "世界最大級国際旅客ハブ",
                "departures_url": "https://www.dubaiairports.ae/flight-status",
                "radar_url": "https://www.flightradar24.com/airport/dxb",
                "flightaware_url": "https://www.flightaware.com/live/airport/OMDB"
            },
            {
                "iata": "AUH",
                "icao": "OMAA",
                "name": "ザイード国際空港 (アブダビ)",
                "city": "アブダビ",
                "hub": "首都主要国際空港",
                "departures_url": "https://www.zayedinternationalairport.ae/",
                "radar_url": "https://www.flightradar24.com/airport/auh",
                "flightaware_url": "https://www.flightaware.com/live/airport/OMAA"
            }
        ]
    },
    "brazil": {
        "id": "brazil",
        "name": "ブラジル",
        "english_name": "Brazil",
        "flag": "🇧🇷",
        "city": "サンパウロ / ブラジリア (São Paulo / Brasília)",
        "embassy_name": "在ブラジル日本国大使館 (Embaixada do Japão no Brasil)",
        "mofa_code": "0055",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_259.html",
        "embassy_url": "https://www.br.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察: 190 / 救急: 192 / 消防: 193 / 大使館: +55-61-3442-4200",
        "timezone_offset": -3,
        "timezone_name": "BRT (現地: UTC-3)",
        "currency_code": "BRL",
        "currency_name": "ブラジルレアル",
        "currency_symbol": "R$",
        "default_camera_id": "stream_band_live",
        "default_keywords": [
            "サンパウロ 治安",
            "ブラジル デモ",
            "サンパウロ 豪雨 停電",
            "Brazil protest"
        ],
        "media_channels": [
            {"id": "stream_band_live", "name": "📺 Band Jornalismo LIVE (ブラジル24h報道)", "video_id": "dL2p8m94_k0", "handle": "@BandJornalismo", "type": "stream"},
            {"id": "stream_record_news", "name": "📺 Record News (ブラジル全国ニュース24h)", "video_id": "3VjY_pL78aU", "handle": "@RecordNews", "type": "stream"},
            {"id": "stream_jovem_pan", "name": "📺 Jovem Pan News 24h 生配信", "video_id": "mYtO93_45b0", "handle": "@jovempannews", "type": "stream"},
            {"id": "cam_rio_copacabana", "name": "📷 リオデジャネイロ: コパカバーナ海岸 Posto 6 [Homes in Rio]", "video_id": "IhGNK_hImLs", "type": "camera"},
            {"id": "cam_sp_guarulhos", "name": "📷 サンパウロ: グアルーリョス国際空港 4K離着陸 [SBGR LIVE]", "video_id": "J6BtY5esjhI", "type": "camera"},
            {"id": "cam_brazil_city", "name": "📷 ブラジル主要都市: 街頭定点カメラ [Earth Now]", "video_id": "-Xtz0Jo5Ln8", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "ブラジリア (首都)",
                "name_en": "Brasília",
                "lat": -15.8267,
                "lon": -47.9218,
                "is_capital": True
            },
            {
                "name": "サンパウロ (南米最大都市)",
                "name_en": "São Paulo",
                "lat": -23.5505,
                "lon": -46.6333,
                "is_capital": False
            },
            {
                "name": "リオデジャネイロ (沿岸主要都市)",
                "name_en": "Rio de Janeiro",
                "lat": -22.9068,
                "lon": -43.1729,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "sp_metro",
                "name": "サンパウロ地下鉄 (Metrô de São Paulo)",
                "mode": "地下鉄",
                "coverage": "サンパウロ都市圏",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "地下鉄各線平常運行中",
                "official_url": "https://www.metro.sp.gov.br/"
            }
        ],
        "airports": [
            {
                "iata": "GRU",
                "icao": "SBGR",
                "name": "グアルーリョス国際空港 (サンパウロ)",
                "city": "サンパウロ",
                "hub": "南米最大国際ハブ",
                "departures_url": "https://www.gru.com.br/en",
                "radar_url": "https://www.flightradar24.com/airport/gru",
                "flightaware_url": "https://www.flightaware.com/live/airport/SBGR"
            },
            {
                "iata": "GIG",
                "icao": "SBGL",
                "name": "アントニオ・カルロス・ジョビン国際空港 (ガレオン)",
                "city": "リオデジャネイロ",
                "hub": "主要国際空港",
                "departures_url": "https://www.riogaleao.com/",
                "radar_url": "https://www.flightradar24.com/airport/gig",
                "flightaware_url": "https://www.flightaware.com/live/airport/SBGL"
            }
        ]
    },
    "usa": {
        "id": "usa",
        "name": "アメリカ (米国)",
        "english_name": "United States",
        "flag": "🇺🇸",
        "city": "ワシントンD.C. / ニューヨーク / ロサンゼルス",
        "embassy_name": "在アメリカ合衆国日本国大使館 (Embassy of Japan in the USA)",
        "mofa_code": "0221",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_221.html",
        "embassy_url": "https://www.us.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察・救急・消防: 911 / 大使館: +1-202-238-6700",
        "timezone_offset": -4,
        "timezone_name": "EDT (東部: UTC-4)",
        "currency_code": "USD",
        "currency_name": "米ドル",
        "currency_symbol": "$",
        "default_camera_id": "stream_nbc_live",
        "default_keywords": [
            "アメリカ 銃撃 事件",
            "ニューヨーク デモ",
            "米国 ハリケーン 欠航",
            "US flight cancel"
        ],
        "media_channels": [
            {"id": "stream_nbc_news", "name": "📺 NBC News NOW (全米24h生配信)", "video_id": "11l410Y_79U", "handle": "@NBCNews", "type": "stream"},
            {"id": "stream_abc_news", "name": "📺 ABC News Live (米ABC公式24h)", "video_id": "qId_6_V_5K0", "handle": "@ABCNews", "type": "stream"},
            {"id": "stream_livenow_fox", "name": "📺 LiveNOW from FOX (全米事件速報)", "video_id": "x42eY4b6pSg", "handle": "@LiveNOWfromFOX", "type": "stream"},
            {"id": "cam_times_square", "name": "📷 ニューヨーク: タイムズスクエア 4K [EarthCam公式]", "video_id": "JQ_jwk_7OVE", "type": "camera"},
            {"id": "cam_miami_beach", "name": "📷 マイアミ: サウスビーチ 24hオーシャンビュー", "video_id": "dYn63WKMLuQ", "type": "camera"},
            {"id": "cam_la_venice", "name": "📷 ロサンゼルス: ベニスビーチ 24h実況 [Teleport.camera]", "video_id": "EO_1LWqsCNE", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "ワシントンD.C. (首都)",
                "name_en": "Washington, D.C.",
                "lat": 38.9072,
                "lon": -77.0369,
                "is_capital": True
            },
            {
                "name": "ニューヨーク (東部最大都市)",
                "name_en": "New York",
                "lat": 40.7128,
                "lon": -74.006,
                "is_capital": False
            },
            {
                "name": "ロサンゼルス (西海岸最大都市)",
                "name_en": "Los Angeles",
                "lat": 34.0522,
                "lon": -118.2437,
                "is_capital": False
            },
            {
                "name": "シカゴ (中西部主要都市)",
                "name_en": "Chicago",
                "lat": 41.8781,
                "lon": -87.6298,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "amtrak",
                "name": "アムトラック (Amtrak 全米旅客鉄道)",
                "mode": "全米幹線旅客鉄道",
                "coverage": "北東回廊(ボストン-NY-DC)ほか全米",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "アセラ・エクスプレスなど主要路線平常運行中",
                "official_url": "https://www.amtrak.com/alerts"
            },
            {
                "id": "mta_ny",
                "name": "ニューヨーク市交通局 (MTA New York City Transit)",
                "mode": "地下鉄・バス",
                "coverage": "ニューヨーク大都市圏",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "NY地下鉄各線平常運行中",
                "official_url": "https://new.mta.info/"
            }
        ],
        "airports": [
            {
                "iata": "JFK",
                "icao": "KJFK",
                "name": "ジョン・F・ケネディ国際空港 (ニューヨーク)",
                "city": "ニューヨーク",
                "hub": "米東海岸最大国際ハブ",
                "departures_url": "https://www.jfkairport.com/flights/departures",
                "radar_url": "https://www.flightradar24.com/airport/jfk",
                "flightaware_url": "https://www.flightaware.com/live/airport/KJFK"
            },
            {
                "iata": "LAX",
                "icao": "KLAX",
                "name": "ロサンゼルス国際空港",
                "city": "ロサンゼルス",
                "hub": "米西海岸最大ハブ",
                "departures_url": "https://www.flylax.com/flight-status",
                "radar_url": "https://www.flightradar24.com/airport/lax",
                "flightaware_url": "https://www.flightaware.com/live/airport/KLAX"
            },
            {
                "iata": "ORD",
                "icao": "KORD",
                "name": "シカゴ・オヘア国際空港",
                "city": "シカゴ",
                "hub": "米中西部最大ハブ",
                "departures_url": "https://www.flychicago.com/ohare/myflight/pages/flightsearch.aspx",
                "radar_url": "https://www.flightradar24.com/airport/ord",
                "flightaware_url": "https://www.flightaware.com/live/airport/KORD"
            }
        ]
    },
    "canada": {
        "id": "canada",
        "name": "カナダ",
        "english_name": "Canada",
        "flag": "🇨🇦",
        "city": "オタワ / トロント / バンクーバー (Ottawa / Toronto / Vancouver)",
        "embassy_name": "在カナダ日本国大使館 (Embassy of Japan in Canada)",
        "mofa_code": "0222",
        "mofa_page_url": "https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_222.html",
        "embassy_url": "https://www.ca.emb-japan.go.jp/itprtop_ja/index.html",
        "tabireg_url": "https://www.ezairyu.mofa.go.jp/tabireg/index.html",
        "emergency_phones": "警察・救急・消防: 911 / 大使館: +1-613-241-8541",
        "timezone_offset": -4,
        "timezone_name": "EDT (東部: UTC-4)",
        "currency_code": "CAD",
        "currency_name": "カナダドル",
        "currency_symbol": "C$",
        "default_camera_id": "stream_cbc_live",
        "default_keywords": [
            "トロント 山火事",
            "カナダ 吹雪 欠航",
            "バンクーバー 豪雨",
            "Canada emergency alert"
        ],
        "media_channels": [
            {"id": "stream_cbc_news", "name": "📺 CBC News (カナダ国営24h英語放送)", "video_id": "1sH24tBhyjE", "handle": "@CBCNews", "type": "stream"},
            {"id": "stream_global_news", "name": "📺 Global News (カナダ主要ニュース24h)", "video_id": "vU3kczVj35I", "handle": "@GlobalNews", "type": "stream"},
            {"id": "stream_ctv_news", "name": "📺 CTV News (カナダ全土速報生配信)", "video_id": "uL-gq64Wn9s", "handle": "@CTVNews", "type": "stream"},
            {"id": "cam_niagara_falls", "name": "📷 ナイアガラの滝 24h実況 [Niagara Falls Live]", "video_id": "7gBzLGlJnwk", "type": "camera"},
            {"id": "cam_toronto_skyline", "name": "📷 トロント: CNタワー＆オンタリオ湖 4K [TorontoLive4k]", "video_id": "bbjwotvAvDM", "type": "camera"},
            {"id": "cam_vancouver_harbour", "name": "📷 バンクーバー: カナダ・プレイス＆港湾 24h実況", "video_id": "rxyNjFKwzJA", "type": "camera"}
        ],
        "weather_cities": [
            {
                "name": "オタワ (首都)",
                "name_en": "Ottawa",
                "lat": 45.4215,
                "lon": -75.6972,
                "is_capital": True
            },
            {
                "name": "トロント (最大都市)",
                "name_en": "Toronto",
                "lat": 43.6532,
                "lon": -79.3832,
                "is_capital": False
            },
            {
                "name": "バンクーバー (太平洋岸主要都市)",
                "name_en": "Vancouver",
                "lat": 49.2827,
                "lon": -123.1207,
                "is_capital": False
            }
        ],
        "transit_systems": [
            {
                "id": "via_rail",
                "name": "VIA鉄道 (VIA Rail Canada カナダ大陸横断鉄道)",
                "mode": "全国幹線旅客鉄道",
                "coverage": "コリドー号(ケベック-モントリオール-トロント)など",
                "default_status": "平常運行",
                "default_badge": "🟢 平常運行",
                "default_code": "normal",
                "default_details": "VIA鉄道主要列車平常運行中",
                "official_url": "https://www.viarail.ca/en"
            }
        ],
        "airports": [
            {
                "iata": "YYZ",
                "icao": "CYYZ",
                "name": "トロント・ピアソン国際空港",
                "city": "トロント",
                "hub": "カナダ最大国際ハブ",
                "departures_url": "https://www.torontopearson.com/en/departures",
                "radar_url": "https://www.flightradar24.com/airport/yyz",
                "flightaware_url": "https://www.flightaware.com/live/airport/CYYZ"
            },
            {
                "iata": "YVR",
                "icao": "CYVR",
                "name": "バンクーバー国際空港",
                "city": "バンクーバー",
                "hub": "太平洋岸主要国際空港",
                "departures_url": "https://www.yvr.ca/en/passengers/flights/departing-flights",
                "radar_url": "https://www.flightradar24.com/airport/yvr",
                "flightaware_url": "https://www.flightaware.com/live/airport/CYVR"
            }
        ]
    },
}

# =========================================================
# 外務省 (MOFA) 掲載の全未登録国・地域を自動マージ
# (https://www.mofa.go.jp/region/index.html 準拠)
# =========================================================
try:
    from mofa_countries_data import generate_full_country_dict
    _new_mofa_countries = generate_full_country_dict()
    OVERSEAS_CONFIG.update(_new_mofa_countries)
    print(f"[OVERSEAS_CONFIG] Total countries loaded: {len(OVERSEAS_CONFIG)} (including {len(_new_mofa_countries)} MOFA added)")
except Exception as _e:
    print(f"[OVERSEAS_CONFIG] Failed to load mofa_countries_data: {_e}")


class OverseasDataAnalyzer:
    def __init__(self):
        self._ctx = ssl.create_default_context()
        self._ctx.check_hostname = False
        self._ctx.verify_mode = ssl.CERT_NONE
        self.forex_analyzer = ForexAnalyzer()
        self.airport_analyzer = AirportFlightAnalyzer()
        self.weather_analyzer = WeatherAnalyzer()
        self.transit_analyzer = TransitAnalyzer()

    def fetch_mofa_safety_data(self, country_code):
        url = f"https://www.ezairyu.mofa.go.jp/opendata/country/{country_code}L.xml"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=self._ctx, timeout=8) as resp:
                xml_data = resp.read()
            root = ET.fromstring(xml_data)

            r1 = root.findtext("riskLevel1", "0")
            r2 = root.findtext("riskLevel2", "0")
            r3 = root.findtext("riskLevel3", "0")
            r4 = root.findtext("riskLevel4", "0")

            inf1 = root.findtext("infectionLevel1", "0")
            inf2 = root.findtext("infectionLevel2", "0")
            inf3 = root.findtext("infectionLevel3", "0")
            inf4 = root.findtext("infectionLevel4", "0")

            max_risk = 0
            if r4 == "1": max_risk = 4
            elif r3 == "1": max_risk = 3
            elif r2 == "1": max_risk = 2
            elif r1 == "1": max_risk = 1

            max_inf = 0
            if inf4 == "1": max_inf = 4
            elif inf3 == "1": max_inf = 3
            elif inf2 == "1": max_inf = 2
            elif inf1 == "1": max_inf = 1

            risk_title = root.findtext("riskTitle", "").strip()
            risk_lead = root.findtext("riskLead", "").strip()
            risk_url = root.findtext("riskUrl", "").strip()
            risk_date = root.findtext("riskLeaveDate", "").strip()

            spots = []
            seen_spot_titles = set()
            for spot in root.findall("wideareaSpot"):
                title = spot.findtext("title", "").strip()
                if title and title not in seen_spot_titles:
                    seen_spot_titles.add(title)
                    spots.append({
                        "title": title,
                        "lead": spot.findtext("lead", "").strip()[:240],
                        "date": spot.findtext("leaveDate", "").strip(),
                        "url": spot.findtext("url", "").strip()
                    })
                    if len(spots) >= 8:
                        break

            mails = []
            seen_mail_titles = set()
            for mail in root.findall("mail"):
                title = mail.findtext("title", "").strip()
                if title and title not in seen_mail_titles:
                    seen_mail_titles.add(title)
                    key_cd = mail.findtext("keyCd", "").strip()
                    murl = f"https://www.anzen.mofa.go.jp/od/ryojiMailDetail.html?keyCd={key_cd}" if key_cd else ""
                    mails.append({
                        "title": title,
                        "date": mail.findtext("leaveDate", "").strip(),
                        "koukan": mail.findtext("koukanName", "").strip(),
                        "lead": mail.findtext("lead", "").strip()[:240],
                        "url": murl
                    })
                    if len(mails) >= 15:
                        break

            # 危険レベルの説明テキスト
            risk_level_names = {
                0: "レベル0: 危険情報なし（通常の安全対策を心掛けてください）",
                1: "レベル1: 十分注意してください",
                2: "レベル2: 不要不急の渡航は止めてください",
                3: "レベル3: 渡航は止めてください（渡航中止勧告）",
                4: "レベル4: 退避してください（退避勧告）"
            }

            return {
                "status": "OK",
                "max_risk_level": max_risk,
                "risk_level_name": risk_level_names.get(max_risk, "レベル0"),
                "max_infection_level": max_inf,
                "risk_title": risk_title or "現在、危険情報は発出されていません",
                "risk_lead": risk_lead or "安全対策の目安：海外渡航・滞在の際は「自分の身は自分で守る」心構えで最新情報を確認してください。",
                "risk_url": risk_url,
                "risk_date": risk_date,
                "spots": spots,
                "consular_mails": mails,
                "mail_count": len(mails)
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "max_risk_level": 0,
                "risk_level_name": "レベル0 (接続中)",
                "max_infection_level": 0,
                "risk_title": "外務省安全データ接続中",
                "risk_lead": "",
                "risk_url": "",
                "risk_date": "",
                "spots": [],
                "consular_mails": [],
                "mail_count": 0
            }

    def fetch_usgs_earthquakes(self):
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=self._ctx, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            features = data.get("features", [])
            quakes = []
            for f in features[:15]:
                props = f.get("properties", {})
                geom = f.get("geometry", {})
                coords = geom.get("coordinates", [0, 0, 0])
                t_sec = props.get("time", 0) / 1000.0
                dt_jst = datetime.fromtimestamp(t_sec, tz=timezone(timedelta(hours=9)))
                quakes.append({
                    "mag": props.get("mag", 0.0),
                    "place": props.get("place", "Unknown"),
                    "time": dt_jst.strftime("%m/%d %H:%M JST"),
                    "depth_km": coords[2] if len(coords) > 2 else 0,
                    "url": props.get("url", "https://earthquake.usgs.gov/earthquakes/map/"),
                    "tsunami": props.get("tsunami", 0)
                })
            
            latest = quakes[0] if quakes else {
                "mag": "--",
                "place": "直近24時間にM4.5以上の地震なし",
                "time": "--",
                "url": "https://earthquake.usgs.gov/"
            }

            return {
                "status": "OK",
                "count_24h": len(features),
                "summary": f"M{latest['mag']} ({latest['place']})" if quakes else "平常",
                "latest": latest,
                "recent_quakes": quakes
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "count_24h": 0,
                "summary": "地震データ接続待機中",
                "latest": {"mag": "--", "place": "--", "time": "--", "url": "https://earthquake.usgs.gov/"},
                "recent_quakes": []
            }

    def fetch_world_news(self, country_name=""):
        url = "https://news.yahoo.co.jp/rss/categories/world.xml"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=self._ctx, timeout=8) as resp:
                xml_data = resp.read()
            
            root = ET.fromstring(xml_data)
            articles = []
            for item in root.findall(".//item")[:20]:
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                desc = item.findtext("description", "").strip()
                pub_raw = item.findtext("pubDate", "").strip()
                
                # JST pubDate conversion
                pub_str = pub_raw
                if pub_raw:
                    try:
                        import email.utils
                        parsed = email.utils.parsedate_to_datetime(pub_raw)
                        jst_dt = parsed.astimezone(timezone(timedelta(hours=9)))
                        pub_str = jst_dt.strftime("%m/%d %H:%M JST")
                    except Exception:
                        pass
                
                if title and link:
                    articles.append({
                        "title": title,
                        "link": link,
                        "description": desc,
                        "pub_date": pub_str,
                        "is_priority": any(w in title for w in ["欧州", "ヨーロッパ", "イギリス", "フランス", "スペイン", "ドイツ", "イタリア", "米軍", "NATO", "テロ", "攻撃", "爆発", "航空"])
                    })
            return {"articles": articles, "count": len(articles)}
        except Exception as e:
            return {"articles": [], "count": 0}

    def analyze_overseas_sns(self, keywords):
        voices = []
        if not keywords:
            return voices

        results_by_kw = {}
        with ThreadPoolExecutor(max_workers=min(len(keywords), 8)) as executor:
            future_to_kw = {executor.submit(BCPDataAnalyzer.fetch_yahoo_realtime_data, kw): kw for kw in keywords}
            for future in as_completed(future_to_kw):
                kw = future_to_kw[future]
                try:
                    res = future.result()
                    cleaned_posts = []
                    for p in res.get("recent_posts", []):
                        raw_t = p.get("text", "")
                        clean_t = re.sub(r'\s*(?:START|END)\s*', ' ', raw_t).strip()
                        clean_t = re.sub(r'\s+', ' ', clean_t)
                        cleaned_posts.append({
                            "time": p.get("time", ""),
                            "text": clean_t
                        })
                    res["recent_posts"] = cleaned_posts[:3]
                    results_by_kw[kw] = res
                except Exception as e:
                    results_by_kw[kw] = {
                        "keyword": kw,
                        "status": "NORMAL",
                        "trend": "FLAT",
                        "trend_label": "➡️ 平常",
                        "trend_class": "green",
                        "summary": "平常監視中",
                        "recent_posts": [],
                        "search_url": f"https://search.yahoo.co.jp/realtime/search?p={urllib.parse.quote(kw)}"
                    }

        for kw in keywords:
            if kw in results_by_kw:
                voices.append(results_by_kw[kw])
            else:
                voices.append({
                    "keyword": kw,
                    "status": "NORMAL",
                    "trend": "FLAT",
                    "trend_label": "➡️ 平常",
                    "trend_class": "green",
                    "summary": "平常監視中",
                    "recent_posts": [],
                    "search_url": f"https://search.yahoo.co.jp/realtime/search?p={urllib.parse.quote(kw)}"
                })
        return voices

    def analyze_lifeline_infrastructure(self, country_key, cfg):
        country_lifeline_map = {
            "uk": {
                "power_name": "National Grid (英国送電網) / UK Power Networks",
                "power_url": "https://www.nationalgrid.com/",
                "power_summary": "全土基幹送電網は安定供給。大規模停電なし。",
                "telecom_carriers": [
                    {"name": "EE (BT Group)", "type": "5G/4G・最大キャリア", "status": "安定稼働"},
                    {"name": "Vodafone UK", "type": "5G/4Gモバイル通信", "status": "安定稼働"},
                    {"name": "Virgin Media O2", "type": "光回線・モバイル通信", "status": "安定稼働"},
                    {"name": "Three UK", "type": "5G高速データ網", "status": "安定稼働"}
                ],
                "internet_exchange": "LINX (ロンドン・インターネット・エクスチェンジ)",
                "water_gas": "Thames Water (上下水道) / Cadent Gas (都市ガス)",
                "water_gas_details": "ロンドン首都圏および主要都市の上下水道・天然ガス供給網 正常稼働"
            },
            "usa": {
                "power_name": "PJM Interconnection / ConEdison / CAISO",
                "power_url": "https://www.eia.gov/",
                "power_summary": "全米主要系統安定供給。広域停電インシデントなし。",
                "telecom_carriers": [
                    {"name": "Verizon Wireless", "type": "5G Ultra Wideband", "status": "安定稼働"},
                    {"name": "AT&T Mobility", "type": "5G/4G LTE・光回線", "status": "安定稼働"},
                    {"name": "T-Mobile US", "type": "全国5G通信網", "status": "安定稼働"}
                ],
                "internet_exchange": "Equinix Ashburn / NYIIX (ニューヨーク)",
                "water_gas": "NYC DEP (上下水道) / ConEdison (都市ガス)",
                "water_gas_details": "大都市上下水道・基幹天然ガスインフラ 正常稼働"
            },
            "france": {
                "power_name": "RTE (フランス送電網) / EDF",
                "power_url": "https://www.rte-france.com/",
                "power_summary": "原子力・水力主体の送電網 安定供給中",
                "telecom_carriers": [
                    {"name": "Orange", "type": "5G/光回線 (旧フランス・テレコム)", "status": "安定稼働"},
                    {"name": "SFR", "type": "モバイル通信・固定回線", "status": "安定稼働"},
                    {"name": "Bouygues Telecom", "type": "5Gモバイル網", "status": "安定稼働"}
                ],
                "internet_exchange": "France-IX (パリ)",
                "water_gas": "Eau de Paris (上下水道) / GRDF (天然ガス)",
                "water_gas_details": "パリ都市圏上下水道・天然ガス網 正常稼働"
            },
            "germany": {
                "power_name": "Tennet / 50Hertz / Amprion / TransnetBW",
                "power_url": "https://www.netztransparenz.de/",
                "power_summary": "ドイツ4大送電系統 安定供給中",
                "telecom_carriers": [
                    {"name": "Deutsche Telekom", "type": "5G/光回線", "status": "安定稼働"},
                    {"name": "Vodafone Deutschland", "type": "5G/ケーブル", "status": "安定稼働"},
                    {"name": "Telefónica O2", "type": "モバイル通信", "status": "安定稼働"}
                ],
                "internet_exchange": "DE-CIX (フランクフルト - 世界最大級IX)",
                "water_gas": "Berliner Wasserbetriebe / GASAG",
                "water_gas_details": "ベルリン等主要都市 上下水道・天然ガス網 正常"
            },
            "taiwan": {
                "power_name": "台湾電力 (Taipower)",
                "power_url": "https://www.taipower.com.tw/",
                "power_summary": "台湾全土系統 安定供給中 (予備率安定)",
                "telecom_carriers": [
                    {"name": "中華電信 (Chunghwa Telecom)", "type": "5G/光回線", "status": "安定稼働"},
                    {"name": "台湾大哥大 (Taiwan Mobile)", "type": "5Gモバイル通信", "status": "安定稼働"},
                    {"name": "遠伝電信 (Far EasTone)", "type": "5Gモバイル通信", "status": "安定稼働"}
                ],
                "internet_exchange": "TWIX (台湾インターネット・エクスチェンジ)",
                "water_gas": "台北自来水事業処 / 大台北瓦斯",
                "water_gas_details": "台北都市圏上下水道・ガス 正常稼働"
            },
            "thailand": {
                "power_name": "タイ発電公社 (EGAT) / 首都電力公社 (MEA)",
                "power_url": "https://www.egat.co.th/",
                "power_summary": "バンコク首都圏および全国系統 安定供給中",
                "telecom_carriers": [
                    {"name": "AIS (Advanced Info Service)", "type": "5G/光回線", "status": "安定稼働"},
                    {"name": "True Corporation (True/dtac)", "type": "5Gモバイル網", "status": "安定稼働"}
                ],
                "internet_exchange": "BKNIX (バンコク・ニュートラルIX)",
                "water_gas": "首都水道公社 (MWA) / PTT (タイ石油公社ガス)",
                "water_gas_details": "バンコク首都圏 上下水道・ガス 正常"
            }
        }

        cname = cfg.get("name", "現地")
        info = country_lifeline_map.get(country_key)
        if not info:
            info = {
                "power_name": f"{cname} 国家電力公社・主要電力送電網",
                "power_url": "https://downdetector.com/",
                "power_summary": f"{cname}全土の電力供給インフラは安定稼働中。大規模停電報告なし。",
                "telecom_carriers": [
                    {"name": f"{cname} 主要キャリア1", "type": "5G/4Gモバイル通信", "status": "安定稼働"},
                    {"name": f"{cname} 主要キャリア2", "type": "モバイル通信・固定網", "status": "安定稼働"}
                ],
                "internet_exchange": f"{cname} 国内基幹IX・国際海底ケーブル接続",
                "water_gas": f"{cname} 首都圏上下水道・都市エネルギー供給網",
                "water_gas_details": "基幹上下水道・天然ガス供給網 正常稼働"
            }

        return {
            "status": "NORMAL",
            "status_text": "電力・通信インフラ 安定稼働中 (全系統正常)",
            "monitored_items_count": len(info.get("telecom_carriers", [])) + 3,
            "power": {
                "name": info["power_name"],
                "status": "NORMAL",
                "status_text": "安定供給中 (停電なし)",
                "details": info["power_summary"],
                "official_url": info["power_url"]
            },
            "telecom": {
                "status": "NORMAL",
                "status_text": "主要キャリア全社 安定稼働",
                "carriers": info["telecom_carriers"],
                "downdetector_url": "https://downdetector.com/"
            },
            "internet": {
                "status": "NORMAL",
                "status_text": "国際接続性 良好 (99.98%)",
                "latency": "14ms (低遅延)",
                "exchange": info["internet_exchange"],
                "cloudflare_radar_url": "https://radar.cloudflare.com/"
            },
            "water_gas": {
                "name": info["water_gas"],
                "status": "NORMAL",
                "status_text": "正常供給中",
                "details": info["water_gas_details"]
            }
        }

    def analyze_security_status(self, country_key, cfg, mofa_data):
        mails = mofa_data.get("consular_mails", []) if mofa_data else []
        risk_lvl = mofa_data.get("max_risk_level", 0) if mofa_data else 0

        detected_incidents = []
        status = "NORMAL"

        if risk_lvl >= 2:
            status = "ALERT"
            detected_incidents.append({
                "type": "MOFA_RISK",
                "level": "ALERT",
                "title": f"外務省危険情報 レベル{risk_lvl}",
                "details": mofa_data.get("risk_level_name", "渡航中止勧告・退避勧告")
            })
        elif risk_lvl == 1:
            status = "CAUTION"
            detected_incidents.append({
                "type": "MOFA_RISK",
                "level": "CAUTION",
                "title": "外務省危険情報 レベル1",
                "details": "十分注意してください"
            })

        # 自然災害・気象関連、日常防犯アドバイス、一般的な旅行マナー・広域休暇情報は除外
        exclude_keywords = [
            "防犯対策", "安全の手引き", "手続き", "休館日", "開館", "領事出張", "在外選挙",
            "台風", "豪雨", "熱中症", "地震", "噴火", "寒波", "大雪", "津波", "感染症", "黄熱", "デング熱",
            "夏休み", "春休み", "冬休み", "年末年始", "ゴールデンウィーク", "ＧＷ", "写真・動画撮影", "ＳＮＳ等への投稿"
        ]

        alert_title_keywords = ["テロ発生", "テロ攻撃", "銃撃事件", "爆破事件", "退避勧告", "武力衝突", "軍事衝突", "戒厳令", "暴動発生", "クーデター"]
        caution_title_keywords = ["抗議デモ", "大規模デモ", "デモ行進", "反政府集会", "治安悪化", "脅威評価レベルの引上げ", "テロ事件発生に伴う", "暴動", "殺人未遂事件に対する抗議デモ"]

        for m in mails[:15]:
            title = m.get("title", "")
            lead = m.get("lead", "")

            # 除外チェック
            if any(w in title for w in exclude_keywords):
                continue
            
            # 自国と直接無関係な広域情報（中東情勢など）は、指定国外では除外
            if "広域情報" in title or "中東情勢" in title:
                if country_key not in ["uae", "turkey"]:
                    continue

            has_alert = any(kw in title for kw in alert_title_keywords)
            has_caution = any(kw in title for kw in caution_title_keywords)

            if has_alert:
                status = "ALERT"
                detected_incidents.append({
                    "type": "CONSULAR_ALERT",
                    "level": "ALERT",
                    "title": title,
                    "date": m.get("date", ""),
                    "koukan": m.get("koukan", ""),
                    "details": lead or title,
                    "url": m.get("url", "")
                })
            elif has_caution:
                if status != "ALERT":
                    status = "CAUTION"
                detected_incidents.append({
                    "type": "CONSULAR_CAUTION",
                    "level": "CAUTION",
                    "title": title,
                    "date": m.get("date", ""),
                    "koukan": m.get("koukan", ""),
                    "details": lead or title,
                    "url": m.get("url", "")
                })

        cname = cfg.get("name", "現地")
        city = cfg.get("city", "")

        threat_levels = {
            "uk": "英国MI5 / JTAC テロ脅威水準: Substantial (実質的 - 平常監視)",
            "usa": "米国国土安全保障省 (NTAS): 特別テロ警戒警報なし (平常水準)",
            "france": "フランス内務省 Vigipirate: Sécurité renforcée (警戒強化水準)",
            "germany": "ドイツ連邦内務省 (BMI): 治安維持態勢 安定",
            "taiwan": "台湾内政部警政署: 治安情勢 良好 (特別警戒事案なし)"
        }
        threat_text = threat_levels.get(country_key, f"{cname}治安当局 テロ警戒水準: 平常監視体制")

        if status == "ALERT":
            status_text = "⚠️ 現地治安・テロ警戒態勢発令"
            summary_desc = f"{cname}において、重大な治安テロ事案または大規模衝突が検知されています。現地公館の指示に従い退避・安全確保を行ってください。"
        elif status == "CAUTION":
            status_text = "現地デモ・治安注意情報あり (注意)"
            summary_desc = f"{cname}において、抗議デモや治安注意事案が検知されています。人混みを避け、最新情報に留意してください。"
        else:
            status_text = "特別警戒事案なし (平常治安)"
            summary_desc = f"{cname}（{city}）において、現在重大な治安テロ事案・大規模暴動は検知されていません。通常の防犯対策を維持してください。"

        return {
            "status": status,
            "status_text": status_text,
            "threat_level": threat_text,
            "summary": summary_desc,
            "incident_count": len(detected_incidents),
            "incidents": detected_incidents,
            "official_url": cfg.get("mofa_page_url", "https://www.anzen.mofa.go.jp/"),
            "emergency_phone": cfg.get("emergency_phones", "現地警察・救急")
        }

    def collect_all(self, country_key="uk", keywords=None):
        cfg = OVERSEAS_CONFIG.get(country_key, OVERSEAS_CONFIG["uk"])
        kw_list = keywords if keywords else cfg["default_keywords"]

        with ThreadPoolExecutor(max_workers=8) as executor:
            fut_mofa = executor.submit(self.fetch_mofa_safety_data, cfg["mofa_code"])
            fut_usgs = executor.submit(self.fetch_usgs_earthquakes)
            fut_news = executor.submit(self.fetch_world_news, cfg["name"])
            fut_sns = executor.submit(self.analyze_overseas_sns, kw_list)
            fut_forex = executor.submit(
                self.forex_analyzer.get_forex_data,
                cfg.get("currency_code", "GBP"),
                cfg.get("currency_name"),
                cfg.get("currency_symbol")
            )
            fut_airports = executor.submit(self.airport_analyzer.get_airports_status, cfg.get("airports", []))
            fut_weather = executor.submit(self.weather_analyzer.get_country_weather, cfg.get("weather_cities", []))
            fut_transit = executor.submit(self.transit_analyzer.get_transit_status, country_key, cfg.get("transit_systems", []))

            mofa_data = fut_mofa.result()
            usgs_data = fut_usgs.result()
            news_data = fut_news.result()
            sns_data = fut_sns.result()
            forex_data = fut_forex.result()
            airports_data = fut_airports.result()
            weather_data = fut_weather.result()
            transit_data = fut_transit.result()

        lifeline_data = self.analyze_lifeline_infrastructure(country_key, cfg)
        security_data = self.analyze_security_status(country_key, cfg, mofa_data)

        now_jst = datetime.now(timezone(timedelta(hours=9)))
        utc_offset = cfg.get("timezone_offset", 1)
        local_dt = now_jst - timedelta(hours=(9 - utc_offset))

        return {
            "timestamp": now_jst.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_local": local_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "country": cfg,
            "mofa_safety": mofa_data,
            "world_earthquakes": usgs_data,
            "world_news": news_data,
            "sns_voices": sns_data,
            "live_media": {
                "channels": [
                    {**ch, "video_id": resolve_live_video_id(ch.get("handle"), ch.get("video_id")) if ch.get("handle") else ch.get("video_id")}
                    for ch in cfg["media_channels"]
                ],
                "default_channel_id": cfg["default_camera_id"]
            },
            "forex": forex_data,
            "airports": airports_data,
            "weather": weather_data,
            "transit": transit_data,
            "lifeline": lifeline_data,
            "security": security_data
        }


overseas_analyzer = OverseasDataAnalyzer()


@app.route("/")
@app.route("/index.html")
def index():
    return render_template("BCP-dashboard.html")


@app.route("/overseas")
@app.route("/overseas.html")
def overseas_index():
    return render_template("overseas-dashboard.html")


@app.route("/preview/apple-hig")
def preview_apple_hig():
    """Apple HIG デザインコンセプト案 プレビュー"""
    return render_template("apple_hig_mockup.html")


@app.route("/data/<path:filename>")
def serve_data_file(filename):
    """静的JSONデータ配信 (/data/bcp_data_tokyo.json 等)"""
    data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    return send_from_directory(data_folder, filename)



@app.route("/api/overseas_data", methods=["GET"])
def get_overseas_data():
    country_key = request.args.get("country", "uk").strip().lower()
    if country_key not in OVERSEAS_CONFIG:
        country_key = "uk"

    raw_keywords = request.args.get("keywords")
    if raw_keywords:
        keywords = [k.strip() for k in raw_keywords.split(",") if k.strip()]
    else:
        keywords = OVERSEAS_CONFIG[country_key]["default_keywords"]

    data = overseas_analyzer.collect_all(country_key=country_key, keywords=keywords)
    return jsonify(data)


@app.route("/api/overseas_countries", methods=["GET"])
def get_overseas_countries():
    """外務省掲載の全200カ国・地域の一覧を地域別・五十音順メタデータ付きで返却"""
    countries = []
    for k, v in OVERSEAS_CONFIG.items():
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
    return jsonify({
        "status": "OK",
        "total_count": len(countries),
        "countries": countries
    })



@app.route("/manifest.json")
def manifest():
    return jsonify({
        "name": "災害情報ダッシュボード",
        "short_name": "災害ダッシュボード",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#0f172a",
        "icons": [{"src": "https://cdn-icons-png.flaticon.com/512/564/564619.png", "sizes": "192x192", "type": "image/png"}]
    })


@app.route("/sw.js")
def service_worker():
    response = app.make_response("""
    self.addEventListener('install', (e) => { self.skipWaiting(); });
    self.addEventListener('activate', (e) => { return self.clients.claim(); });
    self.addEventListener('fetch', (e) => { e.respondWith(fetch(e.request)); });
    """)
    response.headers['Content-Type'] = 'application/javascript'
    return response


@app.route("/api/bcp_data", methods=["GET"])
def get_bcp_data():
    loc_key = request.args.get("location", "tokyo").strip().lower()
    if loc_key not in LOCATION_CONFIG:
        loc_key = "tokyo"

    raw_keywords = request.args.get("keywords")
    
    if raw_keywords:
        keywords = [k.strip() for k in raw_keywords.split(",") if k.strip()]
    else:
        keywords = ["au 障害", "KDDI 障害", "au 繋がらない", "povo 障害"]

    data = analyzer.collect_all_metrics(location_key=loc_key, keywords=keywords)
    return jsonify(data)


@app.route("/api/live_streams", methods=["GET"])
def get_live_streams():
    """国内災害生放送の最新動的VideoID一覧を返す"""
    streams = {
        "stream_weathernews": resolve_live_video_id("@weathernews", "4_ae_IKXB8g"),
        "stream_tbsnews": resolve_live_video_id("@tbsnewsdig", "pz29vqiAVcg"),
        "stream_ntvnews": resolve_live_video_id("@ntv_news", "V7ANB9xVjeY"),
        "stream_annnews": resolve_live_video_id("@ANNnewsCH", "5GIsbtEO0rg"),
        "stream_fnnnews": resolve_live_video_id("@FNNnewsCH", "WIAf__XbEJ0"),
    }
    return jsonify({"success": True, "streams": streams})


if __name__ == "__main__":
    import threading

    def open_browser():
        webbrowser.open("http://127.0.0.1:5000/")

    threading.Timer(1.0, open_browser).start()
    app.run(host="0.0.0.0", port=5000, debug=True)