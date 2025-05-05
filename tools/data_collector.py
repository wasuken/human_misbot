#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import datetime
import json
import logging
import os
import random
import re
import time
from api_clients.news_client import NewsClient
from api_clients.rss_client import RSSClient

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("data/logs/collector.log"), logging.StreamHandler()],
)
logger = logging.getLogger("DataCollector")


class DataCollector:
    """外部データを収集して学習するクラス"""

    def __init__(self, config_path, output_dir):
        """初期化"""
        self.config_path = config_path
        self.output_dir = output_dir
        self.config = self._load_config()
        self.character_type = self.config.get("character_type", "tech")

        # 出力ディレクトリの作成
        os.makedirs(self.output_dir, exist_ok=True)

        # ニュースAPIクライアント
        self.news_api = None
        if self.config.get("news_api", {}).get("enabled", False):
            self.news_api = NewsClient(self.config["news_api"]["api_key"])

        # RSSフィードクライアント
        self.rss_client = None
        if self.config.get("rss_feeds", {}).get("enabled", False):
            self.rss_client = RSSClient()

        # 学習データストア
        self.learned_data = {
            "topics": {},
            "hashtags": [],
            "updated_at": datetime.datetime.now().isoformat(),
        }

        # 既存のデータがあれば読み込む
        self._load_existing_data()

    def _load_config(self):
        """設定ファイルを読み込む"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
            return {}

    def _load_existing_data(self):
        """既存の学習データがあれば読み込む"""
        data_path = os.path.join(self.output_dir, "learned_data.json")
        if os.path.exists(data_path):
            try:
                with open(data_path, "r", encoding="utf-8") as f:
                    self.learned_data = json.load(f)
                logger.info("既存の学習データを読み込みました")
            except Exception as e:
                logger.error(f"既存の学習データの読み込みに失敗しました: {e}")

    def collect_news_data(self):
        """ニュースAPIからデータを収集"""
        if not self.news_api:
            logger.warning("ニュースAPIが設定されていません")
            return

        logger.info("ニュースからデータ収集を開始します")

        try:
            # キャラクタータイプに基づいて検索キーワードを選択
            keywords = self.config.get("news_api", {}).get("queries", [])
            if not keywords:
                logger.warning(
                    f"キャラクタータイプ '{self.character_type}' の検索キーワードが設定されていません"
                )
                return

            # 各キーワードで検索
            all_articles = []
            for keyword in keywords:
                articles = self.news_api.search_news(keyword, limit=10)
                all_articles.extend(articles)
                time.sleep(1)  # APIレート制限を考慮

            # 収集したニュースデータを処理
            self._process_news_articles(all_articles)

            logger.info("ニュースからのデータ収集が完了しました")
        except Exception as e:
            logger.error(f"ニュースからのデータ収集に失敗しました: {e}")

    def collect_rss_data(self):
        """RSSフィードからデータを収集"""
        if not self.rss_client:
            logger.warning("RSSクライアントが設定されていません")
            return

        logger.info("RSSフィードからデータ収集を開始します")

        try:
            feed_urls = self.config.get("rss_feeds", {}).get("feeds", [])
            if not feed_urls:
                logger.warning(
                    f"キャラクタータイプ '{self.character_type}' のRSSフィードが設定されていません"
                )
                return

            # 各フィードからデータを収集
            all_entries = []
            for feed_url in feed_urls:
                entries = self.rss_client.get_feed_entries(feed_url)
                all_entries.extend(entries)

            # 収集したRSSエントリを処理
            self._process_rss_entries(all_entries)

            logger.info("RSSフィードからのデータ収集が完了しました")
        except Exception as e:
            logger.error(f"RSSフィードからのデータ収集に失敗しました: {e}")

    def _process_news_articles(self, articles):
        """ニュース記事を処理して学習データに変換"""
        if not articles:
            return

        topics = {}

        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            if not title:
                continue

            # カテゴリごとの処理
            if self.character_type == "tech":
                self._categorize_tech_news(title, description, topics)
            elif self.character_type == "creative":
                self._categorize_creative_news(title, description, topics)
            elif self.character_type == "otaku":
                self._categorize_otaku_news(title, description, topics)

        # 学習データに追加
        for category, items in topics.items():
            if category not in self.learned_data["topics"]:
                self.learned_data["topics"][category] = []

            # 重複を避けながら追加
            existing_items = set(self.learned_data["topics"][category])
            for item in items:
                if item not in existing_items:
                    self.learned_data["topics"][category].append(item)

            # カテゴリごとの最大数を制限
            max_items = self.config.get("max_category_items", 20)
            if len(self.learned_data["topics"][category]) > max_items:
                self.learned_data["topics"][category] = self.learned_data["topics"][
                    category
                ][-max_items:]

    def _process_rss_entries(self, entries):
        """RSSエントリを処理して学習データに変換"""
        if not entries:
            return

        topics = {}

        for entry in entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            if not title:
                continue

            # カテゴリごとの処理（ニュース記事と同様）
            if self.character_type == "tech":
                self._categorize_tech_news(title, summary, topics)
            elif self.character_type == "creative":
                self._categorize_creative_news(title, summary, topics)
            elif self.character_type == "otaku":
                self._categorize_otaku_news(title, summary, topics)

        # 学習データに追加（ニュース記事と同様）
        for category, items in topics.items():
            if category not in self.learned_data["topics"]:
                self.learned_data["topics"][category] = []

            existing_items = set(self.learned_data["topics"][category])
            for item in items:
                if item not in existing_items:
                    self.learned_data["topics"][category].append(item)

            max_items = self.config.get("max_category_items", 20)
            if len(self.learned_data["topics"][category]) > max_items:
                self.learned_data["topics"][category] = self.learned_data["topics"][
                    category
                ][-max_items:]

    def _categorize_tech_news(self, title, description, topics):
        """技術ニュースをカテゴリ分け"""
        text = f"{title} {description}"

        # 技術カテゴリと対応するキーワード
        categories = {
            "tech_news": [
                "AI",
                "人工知能",
                "機械学習",
                "クラウド",
                "サーバー",
                "量子",
                "ブロックチェーン",
            ],
            "programming_language": [
                "Python",
                "JavaScript",
                "TypeScript",
                "Rust",
                "Go",
                "Java",
                "C#",
            ],
            "gadget": [
                "iPhone",
                "Android",
                "スマートフォン",
                "タブレット",
                "デバイス",
                "ガジェット",
            ],
        }

        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    # タイトルを整形してトピックに追加
                    topics.setdefault(category, []).append(
                        self._format_news_topic(title)
                    )
                    break

    def _categorize_creative_news(self, title, description, topics):
        """クリエイティブ関連ニュースをカテゴリ分け"""
        text = f"{title} {description}"

        categories = {
            "design_news": [
                "デザイン",
                "UI",
                "UX",
                "グラフィック",
                "クリエイティブ",
                "アート",
            ],
            "creative_tool": [
                "Figma",
                "Adobe",
                "Photoshop",
                "Illustrator",
                "デザインツール",
            ],
            "inspiration_source": [
                "展示",
                "美術館",
                "ギャラリー",
                "アート展",
                "デザイナー",
            ],
        }

        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    topics.setdefault(category, []).append(
                        self._format_news_topic(title)
                    )
                    break

    def _categorize_otaku_news(self, title, description, topics):
        """オタク関連ニュースをカテゴリ分け"""
        text = f"{title} {description}"

        categories = {
            "anime_title": ["アニメ", "声優", "漫画", "ゲーム", "コミック", "ラノベ"],
            "infra_tool": [
                "AWS",
                "Azure",
                "クラウド",
                "インフラ",
                "サーバー",
                "ネットワーク",
            ],
            "anime_character": ["キャラクター", "フィギュア", "グッズ", "コレクション"],
        }

        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    topics.setdefault(category, []).append(
                        self._format_news_topic(title)
                    )
                    break

    def _format_news_topic(self, title):
        """ニュースタイトルをトピック用に整形"""
        # 不要な文字や記号を削除
        title = re.sub(r"[\[\]「」『』【】（）\(\)]", "", title)

        # 長すぎるタイトルは短縮
        if len(title) > 30:
            title = title[:27] + "..."

        return title

    def save_learned_data(self):
        """学習データを保存"""
        try:
            # 更新日時を設定
            self.learned_data["updated_at"] = datetime.datetime.now().isoformat()

            # JSONファイルとして保存
            output_path = os.path.join(self.output_dir, "learned_data.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(self.learned_data, f, ensure_ascii=False, indent=2)

            logger.info(f"学習データを保存しました: {output_path}")

            # 既存のキャラクターデータを必要に応じて更新
            self._update_character_templates()

            return True
        except Exception as e:
            logger.error(f"学習データの保存に失敗しました: {e}")
            return False

    def _update_character_templates(self):
        """必要に応じてキャラクターテンプレートを更新"""
        # ここでは特に何もしない（学習データを直接利用する方式）
        pass

    def run(self):
        """データ収集と学習の実行"""
        logger.info("データ収集と学習プロセスを開始します")

        # ニュースからデータ収集
        if self.config.get("collect_news", True):
            self.collect_news_data()

        # RSSフィードからデータ収集
        if self.config.get("collect_rss", True):
            self.collect_rss_data()

        # データ保存
        result = self.save_learned_data()

        logger.info("データ収集と学習プロセスが完了しました")
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="データ収集と学習スクリプト")
    parser.add_argument(
        "--config", default="tools/config.json", help="設定ファイルパス"
    )
    parser.add_argument("--output", default="data/learning", help="出力ディレクトリ")
    parser.add_argument(
        "--character",
        default="tech",
        choices=["tech", "creative", "otaku"],
        help="キャラクタータイプ",
    )

    args = parser.parse_args()

    # 設定ファイルを読み込み、キャラクタータイプを上書き
    config = {}
    try:
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)
        config["character_type"] = args.character
    except Exception as e:
        logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
        config = {"character_type": args.character}

    # 出力ディレクトリをキャラクター別に設定
    output_dir = os.path.join(args.output, args.character)

    # データコレクターを実行
    collector = DataCollector(args.config, output_dir)
    collector.run()
