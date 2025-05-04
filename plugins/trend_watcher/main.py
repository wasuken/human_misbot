#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import logging
import os
import random
import time
from plugins.base import PluginBase

logger = logging.getLogger("TechBot.TrendWatcherPlugin")

class TrendWatcherPlugin(PluginBase):
    """トレンドを監視して反応するプラグイン"""
    
    def __init__(self, bot, config=None):
        """初期化"""
        super().__init__(bot, config)
        self.last_trend_check = datetime.datetime.now() - datetime.timedelta(hours=1)
        self.trend_check_interval = self.config.get('trend_check_interval', 3600)  # デフォルト1時間
        self.tech_keywords = self.config.get('tech_keywords', [
            "プログラミング", "コード", "開発", "エンジニア", "AI", "機械学習", 
            "アプリ", "サーバー", "クラウド", "javascript", "python", "typescript",
            "フレームワーク", "デプロイ", "api", "フロントエンド", "バックエンド"
        ])
        
    def on_timer(self, current_time):
        """タイマー処理"""
        # トレンドチェックの時間か確認
        elapsed = (current_time - self.last_trend_check).total_seconds()
        
        if elapsed >= self.trend_check_interval:
            self._check_trends()
            self.last_trend_check = current_time
            
    def _check_trends(self):
        """トレンドを確認し、関連があれば投稿"""
        try:
            # トレンドハッシュタグを取得
            trends = self.bot.api.get_trend_hashtags()
            
            if not trends:
                logger.warning("トレンドハッシュタグの取得に失敗しました")
                return
                
            # 技術関連のトレンドを抽出
            tech_trends = []
            for trend in trends:
                tag = trend.get('tag', '').lower()
                if any(keyword.lower() in tag for keyword in self.tech_keywords):
                    tech_trends.append(trend)
            
            # 技術関連のトレンドがあれば投稿
            if tech_trends and random.random() < 0.7:  # 70%の確率で投稿
                self._post_about_trend(random.choice(tech_trends))
                
        except Exception as e:
            logger.error(f"トレンドチェック中にエラーが発生しました: {e}")
    
    def _post_about_trend(self, trend):
        """トレンドについての投稿"""
        tag = trend.get('tag', '')
        
        # 投稿テンプレート
        templates = [
            f"「#{tag}」がトレンドに入ってる。気になるな...",
            f"みんな #{tag} について話してるみたい。これは要チェックだ！",
            f"#{tag} の話題が熱いらしい。自分も調べてみるか。",
            f"最近 #{tag} が注目されてるみたい。興味深いトピックだね。",
            f"#{tag} について調べてみたけど、なかなか面白そう。"
        ]
        
        # ランダムにテンプレートを選択
        post_text = random.choice(templates)
        
        # 投稿
        result = self.bot.post_note(post_text)
        
        if result:
            logger.info(f"トレンドについて投稿しました: {post_text}")
        else:
            logger.error(f"トレンド投稿に失敗しました: {post_text}")
    
    def init(self):
        """初期化処理"""
        logger.info("トレンド監視プラグインを初期化しています...")
    
    def shutdown(self):
        """シャットダウン処理"""
        logger.info("トレンド監視プラグインをシャットダウンしています...")
