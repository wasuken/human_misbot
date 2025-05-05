#!/bin/bash

.venv/bin/python tools/data_collector.py --config tools/characters_config/tech.json --character tech
.venv/bin/python tools/data_collector.py --config tools/characters_config/creative.json --character creative
.venv/bin/python tools/data_collector.py --config tools/characters_config/otaku.json --character otaku
