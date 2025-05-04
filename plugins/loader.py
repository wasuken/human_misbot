#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib
import json
import logging
import os
import sys

logger = logging.getLogger("TechBot.PluginLoader")


class PluginLoader:
    """プラグインローダークラス"""

    def __init__(self, bot):
        """初期化"""
        self.bot = bot
        self.plugins = {}

        # プラグインディレクトリをパスに追加
        plugin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if plugin_dir not in sys.path:
            sys.path.append(plugin_dir)

    def load_all_plugins(self):
        """全プラグインをロード"""
        # ボット設定から有効なプラグインリストを取得
        enabled_plugins = self.bot.config.get("enabled_plugins", [])

        # プラグインディレクトリをスキャン
        plugin_dir = os.path.join(os.path.dirname(__file__))
        for item in os.listdir(plugin_dir):
            item_path = os.path.join(plugin_dir, item)

            # ディレクトリでかつmain.pyが存在する場合のみ
            if os.path.isdir(item_path) and os.path.exists(
                os.path.join(item_path, "main.py")
            ):
                if enabled_plugins and item not in enabled_plugins:
                    logger.info(
                        f"プラグイン '{item}' は有効化されていないためスキップします"
                    )
                    continue

                # プラグインをロード
                self.load_plugin(item)

    def load_plugin(self, plugin_name):
        """個別プラグインをロード"""
        if plugin_name in self.plugins:
            logger.warning(f"プラグイン '{plugin_name}' は既にロードされています")
            return False

        try:
            # プラグインモジュールをインポート
            module_path = f"plugins.{plugin_name}.main"
            module = importlib.import_module(module_path)

            # プラグインクラスを取得
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and attr_name.endswith("Plugin"):
                    plugin_class = attr
                    break

            if not plugin_class:
                logger.error(
                    f"プラグイン '{plugin_name}' にプラグインクラスが見つかりません"
                )
                return False

            # プラグインインスタンスを作成
            plugin = plugin_class(self.bot)

            # ボットに登録
            self.bot.register_plugin(plugin)

            # 登録済みプラグインリストに追加
            self.plugins[plugin_name] = plugin

            logger.info(f"プラグイン '{plugin_name}' が正常にロードされました")
            return True

        except Exception as e:
            logger.error(
                f"プラグイン '{plugin_name}' のロード中にエラーが発生しました: {e}"
            )
            return False

    def unload_plugin(self, plugin_name):
        """プラグインをアンロード"""
        if plugin_name not in self.plugins:
            logger.warning(f"プラグイン '{plugin_name}' はロードされていません")
            return False

        plugin = self.plugins[plugin_name]

        try:
            # シャットダウン処理
            plugin.shutdown()

            # ボットから登録解除
            self.bot.unregister_plugin(plugin)

            # 登録済みプラグインリストから削除
            del self.plugins[plugin_name]

            logger.info(f"プラグイン '{plugin_name}' が正常にアンロードされました")
            return True

        except Exception as e:
            logger.error(
                f"プラグイン '{plugin_name}' のアンロード中にエラーが発生しました: {e}"
            )
            return False

    def unload_all_plugins(self):
        """全プラグインをアンロード"""
        plugin_names = list(self.plugins.keys())
        for plugin_name in plugin_names:
            self.unload_plugin(plugin_name)
