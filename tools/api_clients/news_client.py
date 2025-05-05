#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import requests
import time
from datetime import datetime, timedelta

logger = logging.getLogger("NewsClient")


class NewsClient:
    """ニュースAPIとの連携クラス"""

    def __init__(self, api_key):
        """初期化"""
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        self.last_request_time = 0
        self.min_request_interval = 1  # 最低1秒間隔を空ける

    def _handle_rate_limit(self):
        """APIレート制限を考慮した待機処理"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)

        self.last_request_time = time.time()

    def search_news(self, query, limit=10, language="ja", days_back=7):
        """ニュース検索"""
        self._phandle_rate_limit()

        # 日付範囲の設定
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")

        params = {
            "q": query,
            "apiKey": self.api_key,
            # "language": language,
            "sortBy": "publishedAt",
            "from": from_date,
            "to": to_date,
            "pageSize": min(limit, 100),  # APIの制限を考慮
        }

        try:
            response = requests.get(f"{self.base_url}/everything", params=params)

            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                logger.info(
                    f"クエリ '{query}' で {len(articles)} 件のニュースを取得しました"
                )
                return articles
            else:
                logger.error(
                    f"ニュース検索エラー: {response.status_code} - {response.text}"
                )
                return []

        except Exception as e:
            logger.error(f"ニュース検索中に例外が発生しました: {e}")
            return []

    def get_top_headlines(self, category=None, country="jp", limit=10):
        """トップヘッドラインを取得"""
        self._handle_rate_limit()

        params = {
            "apiKey": self.api_key,
            "country": country,
            "pageSize": min(limit, 100),
        }

        if category:
            params["category"] = category

        try:
            response = requests.get(f"{self.base_url}/top-headlines", params=params)

            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                logger.info(
                    f"カテゴリ '{category or 'all'}' で {len(articles)} 件のトップヘッドラインを取得しました"
                )
                return articles
            else:
                logger.error(
                    f"トップヘッドライン取得エラー: {response.status_code} - {response.text}"
                )
                return []

        except Exception as e:
            logger.error(f"トップヘッドライン取得中に例外が発生しました: {e}")
            return []
