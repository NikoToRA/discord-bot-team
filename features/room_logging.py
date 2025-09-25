"""
ルームログ機能
指定されたチャンネルのメッセージとアクティビティを記録
"""

import os
import datetime
import json
from config import BOT_CONFIG

# 対象ルームID（設定可能）
TARGET_ROOM_ID = 1418511738046779393

class RoomLogger:
    def __init__(self, room_id=TARGET_ROOM_ID):
        self.room_id = room_id
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.log_file = os.path.join(self.log_dir, f"room_{room_id}_log.txt")
        self.metadata_file = os.path.join(self.log_dir, f"room_{room_id}_metadata.json")
        self.ensure_log_files()

    def ensure_log_files(self):
        """ログファイルの存在確認と初期化"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Room {self.room_id} Log Started at {datetime.datetime.now()} ===\n")

        if not os.path.exists(self.metadata_file):
            initial_metadata = {
                "room_id": self.room_id,
                "created_at": datetime.datetime.now().isoformat(),
                "last_updated": datetime.datetime.now().isoformat(),
                "message_count": 0,
                "unique_users": []
            }
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(initial_metadata, f, indent=2, ensure_ascii=False)

    def log_message(self, message):
        """メッセージをログファイルに記録"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"[{timestamp}] {message.author.name}#{message.author.discriminator}: {message.content}\n"

            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)

            # メタデータ更新
            self.update_metadata(message.author)

        except Exception as e:
            print(f"ログ記録エラー: {e}")

    def update_metadata(self, author):
        """メタデータファイルを更新"""
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # ユーザー情報を更新
            user_info = f"{author.name}#{author.discriminator}"
            if user_info not in metadata["unique_users"]:
                metadata["unique_users"].append(user_info)

            metadata["message_count"] += 1
            metadata["last_updated"] = datetime.datetime.now().isoformat()

            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"メタデータ更新エラー: {e}")

# グローバルロガーインスタンス
room_logger = RoomLogger()

async def handle_room_logging(message):
    """ルームログ処理のメイン関数"""
    if message.channel.id != TARGET_ROOM_ID:
        return False

    try:
        room_logger.log_message(message)
        if BOT_CONFIG.get('debug_level') == 'DEBUG':
            print(f"ルームログ記録: {message.author.name} in {message.channel.name}")
        return True
    except Exception as e:
        print(f"ルームログ処理エラー: {e}")
        return False

async def get_room_stats():
    """ルームの統計情報を取得"""
    try:
        with open(room_logger.metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return metadata
    except Exception as e:
        print(f"統計取得エラー: {e}")
        return None