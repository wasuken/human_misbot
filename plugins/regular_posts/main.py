#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import logging
import os
import random
import time
from plugins.base import PluginBase

logger = logging.getLogger("TechBot.RegularPostsPlugin")


class RegularPostsPlugin(PluginBase):
    """定期投稿を行うプラグイン"""

    def __init__(self, bot, config=None):
        """初期化"""
        super().__init__(bot, config)
        self.templates = self._load_templates()
        # 最終投稿時刻を記録
        self.last_post_time = datetime.datetime.now()
        # 次の投稿までの待機時間（秒）
        self.next_post_interval = self._get_random_interval()

    def _get_random_interval(self):
        """次の投稿までのランダムな間隔を取得（1〜10分）"""
        # 60秒（1分）〜600秒（10分）のランダムな秒数
        return random.randint(60, 600)

    def _load_templates(self):
        """投稿テンプレートを読み込む"""
        try:
            # キャラクターの投稿テンプレートを取得
            return self.bot.character_data.get("templates", {})
        except Exception as e:
            logger.error(f"テンプレート読み込みエラー: {e}")
            return {}

    def _generate_daily_schedule(self):
        """一日の投稿スケジュールを生成"""
        schedule = []

        # 活動時間帯
        active_hours = self.config.get("active_hours", [7, 24])

        # 投稿頻度（1日あたりの投稿数）
        post_frequency = self.config.get("post_frequency", 5)

        # 投稿スケジュールを生成（活動時間内でランダム）
        for _ in range(post_frequency):
            hour = random.randint(active_hours[0], active_hours[1])
            minute = random.randint(0, 59)
            schedule.append((hour, minute))

        # 時間順にソート
        return sorted(schedule)

    def _refresh_schedule_if_needed(self, current_time):
        """必要に応じてスケジュールを更新"""
        current_date = current_time.date()

        # 日付が変わった場合、スケジュールを再生成
        if current_date != self.last_post_date:
            self.post_schedules = self._generate_daily_schedule()
            self.last_post_date = current_date
            logger.info(f"新しい日のスケジュールを生成しました: {self.post_schedules}")

    def _format_post_text(self, template_key=None):
        """投稿内容をフォーマット"""
        # キーが指定されない場合はランダムに選択
        if not template_key:
            available_keys = list(self.templates.keys())
            if not available_keys:
                logger.error("テンプレートが存在しません")
                return None

            template_key = random.choice(available_keys)

        # 指定されたキーのテンプレートを取得
        templates = self.templates.get(template_key, [])
        if not templates:
            logger.error(f"テンプレートキー '{template_key}' が存在しません")
            return None

        # テンプレートをランダムに選択
        template = random.choice(templates)

        # 変数を置換
        variables = self.bot.character_data.get("topics", {}).get("variables", {})
        for var_name, var_values in variables.items():
            if f"{{{var_name}}}" in template:
                template = template.replace(
                    f"{{{var_name}}}", random.choice(var_values)
                )

        # 曜日や時間帯に応じた語句の追加
        now = datetime.datetime.now()
        weekday = now.weekday()
        hour = now.hour

        # 曜日に応じた語句
        if weekday == 0:  # 月曜日
            if random.random() < 0.4:
                template = "月曜日か...。" + template
        elif weekday == 4:  # 金曜日
            if random.random() < 0.4:
                template = "やっと金曜日！" + template
        elif weekday in [5, 6]:  # 土日
            if random.random() < 0.3:
                template = "休日だけど" + template

        # 時間帯に応じた語句
        if 5 <= hour < 10:  # 朝
            if random.random() < 0.3:
                template = "おはよう。" + template
        elif 22 <= hour or hour < 5:  # 深夜
            if random.random() < 0.3:
                template = "こんな時間だけど" + template

        # 絵文字をランダムに付加（30%の確率）
        if random.random() < 0.3:
            emojis = ["😊", "🤔", "👍", "✨", "💻", "🚀", "📱", "🔍", "🎮", "⚡", "🤖"]
            template = template + " " + random.choice(emojis)

        return template

    def on_timer(self, current_time):
        """タイマー処理"""
        # 前回の投稿からの経過時間
        elapsed = (current_time - self.last_post_time).total_seconds()

        # 設定した間隔を超えたら投稿
        if elapsed >= self.next_post_interval:
            self._post_scheduled_content()
            # 最終投稿時刻を更新
            self.last_post_time = current_time
            # 次の投稿間隔を再設定
            self.next_post_interval = self._get_random_interval()
            logger.info(f"次の投稿は {self.next_post_interval}秒後に予定")

    def _post_scheduled_content(self):
        """スケジュールに従って投稿"""
        # 投稿内容のフォーマット
        post_text = self._format_post_text()

        if not post_text:
            logger.error("投稿内容の生成に失敗しました")
            return

        # ノート投稿
        result = self.bot.post_note(post_text)

        if result:
            logger.info(f"定期投稿を行いました: {post_text[:30]}...")
        else:
            logger.error("定期投稿に失敗しました")

    def init(self):
        """初期化処理"""
        logger.info("定期投稿プラグインを初期化しています...")

    def shutdown(self):
        """シャットダウン処理"""
        logger.info("定期投稿プラグインをシャットダウンしています...")
