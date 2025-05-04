#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import logging
import threading
import time
import random
from .misskey_api import MisskeyAPI

logger = logging.getLogger("TechBot.Core")

class TechBot:
    """テクノロジー愛好家ボットのコアクラス"""
    
    def __init__(self, config):
        """初期化"""
        self.config = config
        self.api = MisskeyAPI(
            instance_url=config['instance_url'],
            access_token=config['access_token']
        )
        self.running = False
        self.plugins = []
        self.character_data = self._load_character_data()
        self.timer_thread = None
        self.ws_thread = None
        
    def _load_character_data(self):
        """キャラクターデータを読み込む"""
        character_data = {}
        try:
            # プロフィール情報
            with open('data/character/profile.json', 'r', encoding='utf-8') as f:
                character_data['profile'] = json.load(f)
                
            # 話題データ
            with open('data/character/topics.json', 'r', encoding='utf-8') as f:
                character_data['topics'] = json.load(f)
                
            # 投稿テンプレート
            with open('data/character/templates.json', 'r', encoding='utf-8') as f:
                character_data['templates'] = json.load(f)
                
            logger.info("キャラクターデータの読み込みが完了しました")
            return character_data
            
        except Exception as e:
            logger.error(f"キャラクターデータの読み込みに失敗しました: {e}")
            return {}
            
    def register_plugin(self, plugin):
        """プラグインを登録"""
        self.plugins.append(plugin)
        logger.info(f"プラグイン '{plugin.name}' を登録しました")
        
    def unregister_plugin(self, plugin):
        """プラグインの登録解除"""
        if plugin in self.plugins:
            self.plugins.remove(plugin)
            logger.info(f"プラグイン '{plugin.name}' の登録を解除しました")
            
    def start(self):
        """ボットを開始"""
        if self.running:
            return
            
        self.running = True
        
        # 各プラグインの初期化
        for plugin in self.plugins:
            try:
                plugin.init()
            except Exception as e:
                logger.error(f"プラグイン '{plugin.name}' の初期化中にエラーが発生しました: {e}")
        
        # タイマースレッド開始
        self.timer_thread = threading.Thread(target=self._timer_loop)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
        # WebSocketスレッド開始
        self.ws_thread = threading.Thread(target=self._websocket_loop)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        # プロフィール更新
        self._update_profile()
        
        logger.info("ボットが正常に開始されました")
        
    def shutdown(self):
        """ボットを停止"""
        if not self.running:
            return
            
        self.running = False
        
        # 各プラグインのシャットダウン
        for plugin in self.plugins:
            try:
                plugin.shutdown()
            except Exception as e:
                logger.error(f"プラグイン '{plugin.name}' のシャットダウン中にエラーが発生しました: {e}")
        
        # API接続を閉じる
        self.api.close()
        
        logger.info("ボットが正常に停止しました")
        
    def _timer_loop(self):
        """タイマーループ処理"""
        last_minute = -1
        
        while self.running:
            now = datetime.datetime.now()
            
            # 1分ごとに処理
            if now.minute != last_minute:
                last_minute = now.minute
                
                # 各プラグインのタイマー処理を呼び出し
                for plugin in self.plugins:
                    try:
                        plugin.on_timer(now)
                    except Exception as e:
                        logger.error(f"プラグイン '{plugin.name}' のタイマー処理中にエラーが発生しました: {e}")
            
            time.sleep(1)
            
    def _websocket_loop(self):
        """WebSocketループ処理"""
        while self.running:
            try:
                # WebSocket接続を開始
                self.api.connect_websocket(self._on_websocket_message)
                
                # 切断された場合、再接続までスリープ
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"WebSocket接続中にエラーが発生しました: {e}")
                time.sleep(30)  # エラー時は長めに待機
    
    def _on_websocket_message(self, message):
        """WebSocketからのメッセージ処理"""
        if not message or not isinstance(message, dict):
            return
            
        # メッセージのタイプに基づく処理
        msg_type = message.get('type')
        
        if msg_type == 'mention':
            # メンション
            for plugin in self.plugins:
                try:
                    plugin.on_mention(message)
                except Exception as e:
                    logger.error(f"プラグイン '{plugin.name}' のメンション処理中にエラーが発生しました: {e}")
                    
        elif msg_type == 'note':
            # ノート
            for plugin in self.plugins:
                try:
                    plugin.on_note(message)
                except Exception as e:
                    logger.error(f"プラグイン '{plugin.name}' のノート処理中にエラーが発生しました: {e}")
                    
        elif msg_type == 'message':
            # メッセージ
            for plugin in self.plugins:
                try:
                    plugin.on_message(message)
                except Exception as e:
                    logger.error(f"プラグイン '{plugin.name}' のメッセージ処理中にエラーが発生しました: {e}")
    
    def _update_profile(self):
        """プロフィールを更新"""
        try:
            profile = self.character_data.get('profile', {})
            if profile:
                self.api.update_profile(
                    name=profile.get('name'),
                    description=profile.get('description'),
                    avatar_url=profile.get('avatar_url')
                )
                logger.info("プロフィールを更新しました")
        except Exception as e:
            logger.error(f"プロフィール更新中にエラーが発生しました: {e}")
    
    def post_note(self, text, visibility="public", reply_id=None, files=None):
        """ノートを投稿"""
        try:
            # 自然さを出すための遅延 (0-3秒)
            time.sleep(random.uniform(0, 3))
            
            # 時々の誤字脱字を入れる (10%の確率)
            if random.random() < 0.1:
                text = self._add_typo(text)
                
            # 投稿
            result = self.api.post_note(
                text=text,
                visibility=visibility,
                reply_id=reply_id,
                files=files
            )
            
            return result
            
        except Exception as e:
            logger.error(f"ノート投稿中にエラーが発生しました: {e}")
            return None
    
    def reply_to_note(self, note, text, visibility="public", files=None):
        """ノートに返信"""
        if not note or not note.get('id'):
            return None
            
        return self.post_note(
            text=text,
            visibility=visibility,
            reply_id=note.get('id'),
            files=files
        )
    
    def add_reaction(self, note_id, reaction):
        """リアクションを追加"""
        try:
            # 自然さを出すための遅延 (1-5秒)
            time.sleep(random.uniform(1, 5))
            
            result = self.api.add_reaction(note_id, reaction)
            return result
            
        except Exception as e:
            logger.error(f"リアクション追加中にエラーが発生しました: {e}")
            return None
    
    def _add_typo(self, text):
        """簡単な誤字脱字を追加する"""
        if not text or len(text) < 5:
            return text
            
        # 文字の入れ替え、欠落、重複などのパターン
        pos = random.randint(0, len(text) - 2)
        typo_type = random.randint(0, 2)
        
        if typo_type == 0:  # 文字入れ替え
            return text[:pos] + text[pos+1] + text[pos] + text[pos+2:]
        elif typo_type == 1:  # 文字欠落
            return text[:pos] + text[pos+1:]
        else:  # 文字重複
            return text[:pos] + text[pos] + text[pos:]
