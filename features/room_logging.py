"""
ルームログ機能
指定されたチャンネルのメッセージとアクティビティを記録
"""

import os
import datetime
import json
from config import BOT_CONFIG

# 対象ルームIDは設定ファイルから取得
def get_target_room_id():
    from config import BOT_CONFIG
    return BOT_CONFIG.get('target_channel_id', 1418512165165465600)

class RoomLogger:
    def __init__(self, room_id=None):
        if room_id is None:
            room_id = get_target_room_id()
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
    target_id = get_target_room_id()
    if message.channel.id != target_id:
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

async def handle_room_stats_reaction(message, bot):
    """📊リアクションによるルーム統計表示とログファイル送信"""
    from config import REACTION_EMOJIS
    import discord

    try:
        # 処理開始を通知
        await message.add_reaction(REACTION_EMOJIS['processing'])

        # 統計情報を取得
        stats = await get_room_stats()

        if stats:
            # 統計情報を表示
            stats_text = f"**📊 ルーム統計情報:**\n"
            stats_text += f"・メッセージ数: {stats['message_count']}\n"
            stats_text += f"・ユニークユーザー数: {len(stats['unique_users'])}\n"
            stats_text += f"・最終更新: {stats['last_updated'][:19]}\n"

            await message.reply(stats_text)

            # ログファイルをDiscordに送信
            try:
                if os.path.exists(room_logger.log_file):
                    with open(room_logger.log_file, 'rb') as f:
                        discord_file = discord.File(f, filename=f"room_{room_logger.room_id}_log.txt")
                        await message.channel.send("**📁 ルームログファイル:**", file=discord_file)

                if os.path.exists(room_logger.metadata_file):
                    with open(room_logger.metadata_file, 'rb') as f:
                        discord_file = discord.File(f, filename=f"room_{room_logger.room_id}_metadata.json")
                        await message.channel.send("**📁 統計メタデータ:**", file=discord_file)
            except Exception as e:
                print(f"ログファイル送信エラー: {e}")
        else:
            await message.reply("ルーム統計の取得に失敗しました。")

        # 処理完了を通知
        await message.remove_reaction(REACTION_EMOJIS['processing'], bot.user)
        await message.add_reaction(REACTION_EMOJIS['success'])
        return True

    except Exception as e:
        print(f"ルーム統計処理エラー: {str(e)}")
        await message.reply("ルーム統計の処理中にエラーが発生しました。")
        await message.remove_reaction(REACTION_EMOJIS['processing'], bot.user)
        await message.add_reaction(REACTION_EMOJIS['error'])
        return False

async def auto_add_room_stats_reaction(message):
    """特定のキーワードメッセージに自動で📊リアクションを追加"""
    from config import BOT_CONFIG, REACTION_EMOJIS

    # 指定チャンネルのみで動作
    if message.channel.id != BOT_CONFIG.get('target_channel_id'):
        return False

    # 特定のキーワードでルーム統計をトリガー
    trigger_keywords = ['ルーム統計', 'room stats', '統計', 'stats', 'ログ統計', '部屋統計']
    if message.content and any(keyword in message.content.lower() for keyword in trigger_keywords):
        print(f"[DEBUG] 📊リアクション追加: ルーム統計トリガー")
        await message.add_reaction(REACTION_EMOJIS['room_stats'])
        return True
    return False