import json
import backend_server

app = backend_server.app
client = app.test_client()

print("=== Flask API 11拠点全網羅テスト ===")
locations = ['sapporo', 'sendai', 'tokyo', 'omiya', 'yokohama', 'nagoya', 'kanazawa', 'osaka', 'hiroshima', 'takamatsu', 'fukuoka']

for loc in locations:
    res = client.get(f'/api/bcp_data?location={loc}')
    assert res.status_code == 200, f"Failed on {loc}: {res.status_code}"
    data = json.loads(res.data)
    loc_info = data['location']
    w = data['weather']
    r = data['river']
    lf = data['lifeline']
    ev = data['evacuation']
    assert 'weather_overview' in data, f"Missing weather_overview in {loc}"
    assert 'disaster_news' in data, f"Missing disaster_news in {loc}"
    assert 'live_media' in data, f"Missing live_media in {loc}"

    wo = data['weather_overview']
    dn = data['disaster_news']
    lm = data['live_media']

    print(f"[{loc_info['name']}] 監視エリア: {loc_info['region_name']} ({loc_info['region_desc']})")
    print(f"  - 気象: {w['status']} ({w['summary']}) [構成地域数: {w['total_prefs']}]")
    print(f"  - 天気概況: [{wo['office']}] {wo['summary'][:40]}...")
    print(f"  - 災害ニュース: {dn['count']}件取得 (災害特報: {dn['disaster_count']}件)")
    print(f"  - ライブカメラ: 推奨=[{lm['recommended_camera']['name']}] (生放送{len(lm['streams'])}ch / カメラ{len(lm['cameras'])}台)")
    print(f"  - 河川: {r['status']} ({r['summary']})")
    print(f"  - 停電: {lf['power_status']} ({lf['power_msg']})")
    print(f"  - 避難: {ev['status']} ({ev['summary']})")
    print(f"  - 交通: {data['transit']['text']}")
    print("-" * 70)

print("ALL 11 LOCATIONS TEST PASSED WITH ALL NEW FEATURES!")

