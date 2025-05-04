#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import re
from plugins.base import PluginBase

logger = logging.getLogger("TechBot.ReactionsPlugin")

class ReactionsPlugin(PluginBase):
    """自動リアクションを行うプラグイン"""
    
    def __init__(self, bot, config=None):
        """初期化"""
        super().__init__(bot, config)
        self.tech_keywords = self.config.get('tech_keywords', [
            "プログラミング", "コード", "開発", "エンジニア", "AI", "機械学習", 
            "アプリ", "サーバー", "クラウド", "JavaScript", "Python", "TypeScript",
            "フレームワーク", "デプロイ", "API", "フロントエンド", "バックエンド"
        ])
        self.tech_reactions = self.config.get('tech_reactions', [
            "👍", "🚀", "💻", "✨", "🤖", "⚡", "🔥", "🎉"
        ])
        self.general_reactions = self.config.get('general_reactions', [
            "👍", "😊", "✨", "🙌", "👀"
        ])
        self.reaction_probability = self.config.get('reaction_probability', 0.4)
        self.tech_reaction_probability = self.config.get('tech_reaction_probability', 0.7)
    
    def on_note(self, note):
        """ノート受信時の処理"""
        if not note or not note.get('data'):
            return
            
        note_data = note.get('data')
        
        # 自分自身の投稿には反応しない
        if note_data.get('user', {}).get('username') == self.bot.config.get('username'):
            return
            
        # テキストがない場合はスキップ
        if not note_data.get('text'):
            return
            
        text = note_data.get('text')
        note_id = note_data.get('id')
        
        # テキストにキーワードが含まれるか確認
        is_tech_related = any(keyword in text for keyword in self.tech_keywords)
        
        # リアクションするかどうかの確率計算
        react_probability = self.tech_reaction_probability if is_tech_related else self.reaction_probability
        
        if random.random() < react_probability:
            # リアクション対象の場合
            if is_tech_related:
                reaction = random.choice(self.tech_reactions)
            else:
                reaction = random.choice(self.general_reactions)
                
            # リアクション送信
            result = self.bot.add_reaction(note_id, reaction)
            
            if result:
                logger.info(f"リアクションしました: {note_id} - {reaction}")
            else:
                logger.error(f"リアクション失敗: {note_id}")
                
    def on_mention(self, message):
        """メンション受信時の処理"""
        if not message or not message.get('data'):
            return
            
        message_data = message.get('data')
        note_id = message_data.get('id')
        
        # メンションには高確率でリアクション
        if random.random() < 0.8:
            reaction = random.choice(self.tech_reactions + self.general_reactions)
            result = self.bot.add_reaction(note_id, reaction)
            
            if result:
                logger.info(f"メンションにリアクションしました: {note_id} - {reaction}")
    
    def init(self):
        """初期化処理"""
        logger.info("リアクションプラグインを初期化しています...")
    
    def shutdown(self):
        """シャットダウン処理"""
        logger.info("リアクションプラグインをシャットダウンしています...")
