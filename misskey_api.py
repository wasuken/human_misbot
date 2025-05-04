#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import requests
import websocket
import threading
import time

logger = logging.getLogger("TechBot.MisskeyAPI")

class MisskeyAPI:
    """Misskey API連携クラス"""
    
    def __init__(self, instance_url, access_token):
        """初期化"""
        self.instance_url = instance_url.rstrip('/')
        self.access_token = access_token
        self.ws = None
        self.ws_connected = False
        
    def api_request(self, endpoint, data=None):
        """APIリクエスト送信"""
        if data is None:
            data = {}
            
        # トークンを追加
        data['i'] = self.access_token
        
        url = f"{self.instance_url}/api/{endpoint}"
        
        try:
            response = requests.post(
                url, 
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API呼び出しエラー: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"API呼び出し中に例外が発生しました: {e}")
            return None
    
    def connect_websocket(self, on_message_callback):
        """WebSocket接続を開始"""
        # 既存接続をクローズ
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
                
        self.ws_connected = False
        
        # 新しい接続を作成
        ws_url = f"{self.instance_url.replace('http', 'ws')}/streaming"
        
        def on_open(ws):
            logger.info("WebSocket接続が確立されました")
            self.ws_connected = True
            
            # ストリーミング接続開始
            connect_data = {
                'type': 'connect',
                'body': {
                    'channel': 'main',
                    'id': 'main',
                    'params': {'i': self.access_token}
                }
            }
            ws.send(json.dumps(connect_data))
            
            # ホームタイムライン購読
            timeline_data = {
                'type': 'connect',
                'body': {
                    'channel': 'homeTimeline',
                    'id': 'homeTimeline',
                    'params': {'i': self.access_token}
                }
            }
            ws.send(json.dumps(timeline_data))
            
            # メンション購読
            mention_data = {
                'type': 'connect',
                'body': {
                    'channel': 'mention',
                    'id': 'mention',
                    'params': {'i': self.access_token}
                }
            }
            ws.send(json.dumps(mention_data))
            
        def on_message(ws, message):
            try:
                data = json.loads(message)
                # メッセージデータの前処理
                if data.get('type') == 'channel' and data.get('body'):
                    body = data.get('body')
                    channel = body.get('channel')
                    
                    if channel == 'homeTimeline':
                        # ホームタイムラインのメッセージ
                        on_message_callback({
                            'type': 'note',
                            'data': body.get('body')
                        })
                    elif channel == 'mention':
                        # メンションのメッセージ
                        on_message_callback({
                            'type': 'mention',
                            'data': body.get('body')
                        })
            except Exception as e:
                logger.error(f"WebSocketメッセージ処理中に例外が発生しました: {e}")
                
        def on_error(ws, error):
            logger.error(f"WebSocketエラー: {error}")
            self.ws_connected = False
            
        def on_close(ws, close_status_code, close_msg):
            logger.info(f"WebSocket接続が閉じられました: {close_status_code}, {close_msg}")
            self.ws_connected = False
            
        def run_websocket(*args):
            while True:
                try:
                    self.ws = websocket.WebSocketApp(
                        ws_url,
                        on_open=on_open,
                        on_message=on_message,
                        on_error=on_error,
                        on_close=on_close
                    )
                    self.ws.run_forever()
                    
                    # 接続が切れた場合、再接続
                    logger.info("WebSocket接続が切断されました。5秒後に再接続します...")
                    time.sleep(5)
                except Exception as e:
                    logger.error(f"WebSocket実行中に例外が発生しました: {e}")
                    time.sleep(30)
        
        # 別スレッドでWebSocketを実行
        thread = threading.Thread(target=run_websocket)
        thread.daemon = True
        thread.start()
    
    def close(self):
        """接続を閉じる"""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None
        self.ws_connected = False
    
    def post_note(self, text, visibility="public", reply_id=None, files=None):
        """ノートを投稿"""
        data = {
            'text': text,
            'visibility': visibility
        }
        
        if reply_id:
            data['replyId'] = reply_id
            
        if files:
            data['fileIds'] = files
            
        return self.api_request('notes/create', data)
    
    def add_reaction(self, note_id, reaction):
        """リアクションを追加"""
        data = {
            'noteId': note_id,
            'reaction': reaction
        }
        
        return self.api_request('notes/reactions/create', data)
    
    def update_profile(self, name=None, description=None, avatar_url=None):
        """プロフィールを更新"""
        data = {}
        
        if name:
            data['name'] = name
            
        if description:
            data['description'] = description
            
        if avatar_url:
            # 画像のアップロード
            pass  # 実装が必要
            
        return self.api_request('i/update', data)
    
    def get_trend_hashtags(self):
        """トレンドのハッシュタグを取得"""
        return self.api_request('hashtags/trend')
    
    def search_notes(self, query, limit=20):
        """ノートを検索"""
        data = {
            'query': query,
            'limit': limit
        }
        
        return self.api_request('notes/search', data)
