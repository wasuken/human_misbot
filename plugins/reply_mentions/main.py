#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import re
from plugins.base import PluginBase

logger = logging.getLogger("TechBot.ReplyMentionsPlugin")

class ReplyMentionsPlugin(PluginBase):
    """メンションに返信するプラグイン"""
    
    def __init__(self, bot, config=None):
        """初期化"""
        super().__init__(bot, config)
        self.responses = self._load_responses()
        
    def _load_responses(self):
        """返信用のレスポンスを読み込む"""
        # キャラクターデータから応答テンプレートを取得
        return self.bot.character_data.get('topics', {}).get('responses', {})
    
    def _find_matching_response(self, text):
        """テキストに合致する応答を見つける"""
        if not text:
            return None
            
        # キーワードマッチングで応答を選択
        for keyword, responses in self.responses.items():
            if keyword in text:
                return random.choice(responses)
                
        # デフォルト応答
        default_responses = self.responses.get('default', [
            "なるほど！それは興味深いね。",
            "ありがとう、参考になるよ！",
            "そうなんだ、知らなかった。",
            "なるほど、考えさせられるね。"
        ])
        
        return random.choice(default_responses)
    
    def _format_response(self, text, mention_username):
        """応答をフォーマット"""
        # 変数を置換
        variables = self.bot.character_data.get('topics', {}).get('variables', {})
        for var_name, var_values in variables.items():
            if f"{{{var_name}}}" in text:
                text = text.replace(f"{{{var_name}}}", random.choice(var_values))
        
        # 名前を含める（たまに）
        if random.random() < 0.3 and mention_username:
            text = f"@{mention_username} {text}"
            
        return text
    
    def on_mention(self, message):
        """メンション受信時の処理"""
        if not message or not message.get('data'):
            return
            
        message_data = message.get('data')
        text = message_data.get('text', '')
        note_id = message_data.get('id')
        
        # メンション部分を除去
        text = re.sub(r'@\w+', '', text).strip()
        
        # ユーザー名を取得
        username = message_data.get('user', {}).get('username')
        
        # 応答を選択
        response = self._find_matching_response(text)
        
        if response:
            # 応答をフォーマット
            formatted_response = self._format_response(response, username)
            
            # 少し遅延を入れる（自然さのため）
            import time
            time.sleep(random.uniform(2, 5))
            
            # 返信を送信
            result = self.bot.reply_to_note(message_data, formatted_response)
            
            if result:
                logger.info(f"メンションに返信しました: {note_id} - {formatted_response[:30]}...")
            else:
                logger.error(f"メンション返信に失敗しました: {note_id}")
    
    def init(self):
        """初期化処理"""
        logger.info("メンション返信プラグインを初期化しています...")
    
    def shutdown(self):
        """シャットダウン処理"""
        logger.info("メンション返信プラグインをシャットダウンしています...")
