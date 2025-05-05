#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import logging
import os
import random
import time
from plugins.base import PluginBase

logger = logging.getLogger("TechBot.AdaptiveContentPlugin")


class AdaptiveContentPlugin(PluginBase):
    """学習データを活用して投稿内容を適応的に生成するプラグイン"""

    def __init__(self, bot, config=None):
        """初期化"""
        super().__init__(bot, config)
        self.learning_data_dir = self.config.get("learning_data_dir", "data/learning")
        self.character_type = self.config.get("character_type", "tech")
        self.learning_data_path = os.path.join(
            self.learning_data_dir, self.character_type, "learned_data.json"
        )

        # 学習データ
        self.learned_data = {}

        # 最終データ読み込み時刻
        self.last_data_load_time = 0
        # データの更新間隔（秒）
        self.data_reload_interval = self.config.get(
            "data_reload_interval", 3600
        )  # デフォルト1時間

        # 適応的な投稿を行う確率（0.0-1.0）
        self.adaptive_post_probability = self.config.get(
            "adaptive_post_probability", 0.3
        )

        # 最終適応的投稿時刻
        self.last_adaptive_post_time = datetime.datetime.now()
        # 適応的投稿の間隔（秒）
        self.adaptive_post_interval = self.config.get(
            "adaptive_post_interval", 3600 * 6
        )  # デフォルト6時間

        # 初回データロード
        self._load_learned_data()

    def _load_learned_data(self):
        """学習データを読み込む"""
        current_time = time.time()

        # 一定時間が経過していない場合はリロードしない
        if (
            current_time - self.last_data_load_time < self.data_reload_interval
            and self.learned_data
        ):
            return

        logger.info("学習データを読み込みます")

        # 学習データの読み込み
        try:
            if os.path.exists(self.learning_data_path):
                with open(self.learning_data_path, "r", encoding="utf-8") as f:
                    self.learned_data = json.load(f)
                logger.info("学習データを読み込みました")
            else:
                logger.warning(
                    f"学習データファイルが見つかりません: {self.learning_data_path}"
                )
        except Exception as e:
            logger.error(f"学習データの読み込みに失敗しました: {e}")

        # 最終読み込み時刻を更新
        self.last_data_load_time = current_time

    def _should_post_adaptive_content(self):
        """適応的な投稿を行うべきかを判断"""
        # データがない場合は投稿しない
        if not self.learned_data:
            return False

        # 一定の確率で投稿するかを決定
        if random.random() > self.adaptive_post_probability:
            return False

        # 前回の適応的投稿からの経過時間をチェック
        now = datetime.datetime.now()
        elapsed = (now - self.last_adaptive_post_time).total_seconds()

        return elapsed >= self.adaptive_post_interval

    def _generate_adaptive_post(self):
        """適応的な投稿内容を生成"""
        # トピックデータからテンプレートを選択
        templates = self.bot.character_data.get("templates", {})

        # 投稿カテゴリをランダムに選択
        available_categories = list(templates.keys())
        if not available_categories:
            logger.error("投稿カテゴリが見つかりません")
            return None

        selected_category = random.choice(available_categories)

        # 選択したカテゴリのテンプレートをランダム選択
        category_templates = templates.get(selected_category, [])
        if not category_templates:
            logger.error(
                f"カテゴリ '{selected_category}' のテンプレートが見つかりません"
            )
            return None

        template = random.choice(category_templates)

        # 変数の置換
        variables = self.bot.character_data.get("topics", {}).get("variables", {})

        # 学習した新しいトピックがあれば置き換える
        learned_topics = self.learned_data.get("topics", {})
        for topic_name, topics in learned_topics.items():
            if topics and topic_name in variables:
                # トピックを学習データのものに置き換える（最大5つ）
                num_to_add = min(len(topics), 5)
                if num_to_add > 0:
                    # ランダムに選んで先頭に追加
                    selected_topics = random.sample(topics, num_to_add)
                    variables[topic_name] = (
                        selected_topics + variables[topic_name][:-num_to_add]
                    )

        # テンプレート内の変数を置換
        for var_name, var_values in variables.items():
            if f"{{{var_name}}}" in template and var_values:
                template = template.replace(
                    f"{{{var_name}}}", random.choice(var_values)
                )

        # 学習データからハッシュタグを追加（確率で）
        if self.learned_data.get("hashtags") and random.random() < 0.2:
            hashtag = random.choice(self.learned_data["hashtags"])
            template = f"{template} #{hashtag}"

        return template

    def on_timer(self, current_time):
        """タイマー処理"""
        # 学習データの再読み込み
        self._load_learned_data()

        # 適応的な投稿を行うべきか判断
        if self._should_post_adaptive_content():
            # 適応的な投稿内容を生成
            post_text = self._generate_adaptive_post()

            if post_text:
                # 投稿
                result = self.bot.post_note(post_text)

                if result:
                    logger.info(f"適応的な投稿を行いました: {post_text[:30]}...")
                    # 最終投稿時刻を更新
                    self.last_adaptive_post_time = current_time
                else:
                    logger.error("適応的な投稿に失敗しました")

    def init(self):
        """初期化処理"""
        logger.info("適応的コンテンツプラグインを初期化しています...")
        self._load_learned_data()

    def shutdown(self):
        """シャットダウン処理"""
        logger.info("適応的コンテンツプラグインをシャットダウンしています...")
