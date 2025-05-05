# 1時間ごとに技術系キャラクター向けにデータ収集（例）
0 */1 * * * cd /path/to/project && python tools/data_collector.py --config tools/config.json --character tech >> data/logs/collector_tech.log 2>&1

# 2時間ごとにクリエイティブ系キャラクター向けにデータ収集（例）
0 */2 * * * cd /path/to/project && python tools/data_collector.py --config tools/config.json --character creative >> data/logs/collector_creative.log 2>&1

# 3時間ごとにオタク系キャラクター向けにデータ収集（例）
0 */3 * * * cd /path/to/project && python tools/data_collector.py --config tools/config.json --character otaku >> data/logs/collector_otaku.log 2>&1
