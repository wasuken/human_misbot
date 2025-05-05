#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
import feedparser
from datetime import datetime, timedelta

logger = logging.getLogger("RSSClient")


class RSSClient:
    """RSSフィードとの連携クラス"""

    def __init__(self):
        """初期化"""
        self.last_request_time = 0
        self.min_request_interval = 1  # 最低1秒間隔を空ける

    def _handle_rate_limit(self):
        """RSSリクエスト間の待機処理"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)

        self.last_request_time = time.time()

    def get_feed_entries(self, feed_url, max_entries=10, days_back=7):
        """RSSフィードからエントリを取得"""
        self._handle_rate_limit()

        try:
            feed = feedparser.parse(feed_url)

            if feed.get("status") != 200:
                logger.error(
                    f"RSSフィード取得エラー: {feed.get('status')} - {feed_url}"
                )
                return []

            # 日付でフィルタリング
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filtered_entries = []

            for entry in feed.entries[:max_entries]:
                # 日付の取得と変換
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    entry_date = datetime(*published[:6])
                    if entry_date > cutoff_date:
                        # エントリ情報の整形
                        filtered_entries.append(
                            {
                                "title": entry.get("title", ""),
                                "link": entry.get("link", ""),
                                "summary": entry.get("summary", ""),
                                "published": entry.get("published", ""),
                            }
                        )
                else:
                    # 日付情報がない場合はとりあえず追加
                    filtered_entries.append(
                        {
                            "title": entry.get("title", ""),
                            "link": entry.get("link", ""),
                            "summary": entry.get("summary", ""),
                            "published": entry.get("published", ""),
                        }
                    )

            logger.info(
                f"フィード '{feed.feed.get('title', feed_url)}' から {len(filtered_entries)} 件のエントリを取得しました"
            )
            return filtered_entries

        except Exception as e:
            logger.error(f"RSSフィード取得中に例外が発生しました: {e} - {feed_url}")
            return []

    def get_tech_feeds(self, feed_urls, max_entries_per_feed=5):
        """技術系RSSフィードの一括取得"""
        all_entries = []

        for url in feed_urls:
            entries = self.get_feed_entries(url, max_entries=max_entries_per_feed)
            all_entries.extend(entries)

        return all_entries
