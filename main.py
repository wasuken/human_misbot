#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import os
import sys
import time
from core.bot import TechBot
from plugins.loader import PluginLoader

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("data/logs/techbot.log"), logging.StreamHandler()],
)
logger = logging.getLogger("TechBot")


def load_config():
    """設定ファイルを読み込む"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
        sys.exit(1)


def main():
    """メイン実行関数"""
    # 設定ファイル読み込み
    config = load_config()

    # ボットインスタンス作成
    bot = TechBot(config)

    # プラグインのロード
    plugin_loader = PluginLoader(bot)
    plugin_loader.load_all_plugins()

    try:
        # ボット開始
        logger.info("テクノロジー愛好家ボットを起動します...")
        bot.start()

        # メインループ
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("キーボード割り込みを検知しました")
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")
    finally:
        # シャットダウン処理
        logger.info("ボットをシャットダウンしています...")
        bot.shutdown()
        plugin_loader.unload_all_plugins()
        logger.info("正常に終了しました")


if __name__ == "__main__":
    main()
