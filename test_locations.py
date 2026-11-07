import backend_server

analyzer = backend_server.BCPDataAnalyzer()
print("=== 11拠点 エリア気象警報取得テスト ===")
for key in ['sapporo', 'sendai', 'tokyo', 'omiya', 'yokohama', 'nagoya', 'kanazawa', 'osaka', 'hiroshima', 'takamatsu', 'fukuoka']:
    cfg = backend_server.LOCATION_CONFIG[key]
    w = analyzer.get_real_area_weather_warnings(cfg)
    print(f"[{cfg['name']}] {cfg['region_name']} ({cfg['region_desc']}):")
    print(f"  Status: {w['status']} | Prefs: {w['total_prefs']}")
    print(f"  Summary: {w['summary']}")
    print(f"  Details: {[p['short_name'] + ':' + p['status'] for p in w['pref_details']]}")
    print("-" * 60)

