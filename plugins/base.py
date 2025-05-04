#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import os

logger = logging.getLogger("TechBot.PluginBase")

class PluginBase:
    """プラグイン基底クラス"""
    
    def __init__(self, bot, config=None):
        """初期化"""
        self.bot = bot
        self.name = self.__class__.__name__
        self.config = config or {}
        self.data_dir = os.path.join('plugins', self.__module__.split('.')[-2])
        
        # 設定ファイルの読み込み
        config_file = os.path.join(self.data_dir, 'config.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.config.update(json.load(f))
            except Exception as e:
                logger.error(f"プラグイン '{self.name}' の設定ファイル読み込みに失敗しました: {e}")
        
        logger.info(f"プラグイン '{self.name}' が初期化されました")
    
    def init(self):
        """初期化処理（オーバーライド用）"""
        pass
    
    def on_message(self, message):
        """メッセージ受信時の処理（オーバーライド用）"""
        pass
    
    def on_mention(self, message):
        """メンション受信時の処理（オーバーライド用）"""
        pass
    
    def on_note(self, note):
        """ノート受信時の処理（オーバーライド用）"""
        pass
    
    def on_timer(self, current_time):
        """定期的な処理（オーバーライド用）"""
        pass
    
    def shutdown(self):
        """シャットダウン処理（オーバーライド用）"""
        pass
