"""
チャットログ収集機能
全チャンネルのメッセージ履歴を収集
"""

import os
import json
import datetime
from config import BOT_CONFIG

class ChatLogger:
    def __init__(self):
        self.log_dir = "chat_logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def save_chat_log(self, channel, messages_data):
        """チャットログをJSONファイルに保存"""
        try:
            log_filename = f"{channel.guild.name}_{channel.name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            log_filename = log_filename.replace("/", "_").replace(" ", "_")  # ファイル名を安全にする
            log_path = os.path.join(self.log_dir, log_filename)

            log_data = {
                'guild_name': channel.guild.name,
                'guild_id': channel.guild.id,
                'channel_name': channel.name,
                'channel_id': channel.id,
                'collected_at': datetime.datetime.now().isoformat(),
                'message_count': len(messages_data),
                'messages': messages_data
            }

            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

            print(f"チャットログ保存完了: {log_filename} ({len(messages_data)}件)")
            return log_path

        except Exception as e:
            print(f"チャットログ保存エラー: {e}")
            return None

    async def collect_channel_history(self, channel, limit=100):
        """チャンネルの履歴を収集"""
        try:
            messages_data = []

            async for message in channel.history(limit=limit):
                message_data = {
                    'id': message.id,
                    'author_name': message.author.name,
                    'author_id': message.author.id,
                    'content': message.content,
                    'timestamp': message.created_at.isoformat(),
                    'edited_at': message.edited_at.isoformat() if message.edited_at else None,
                    'attachments': [att.url for att in message.attachments],
                    'embeds_count': len(message.embeds),
                    'reactions_count': len(message.reactions)
                }
                messages_data.append(message_data)

            return messages_data

        except Exception as e:
            print(f"履歴収集エラー ({channel.name}): {e}")
            return []

# グローバルロガーインスタンス
chat_logger = ChatLogger()

async def handle_chat_logging(message):
    """リアルタイムチャットログ処理"""
    if message.author.bot:
        return False

    try:
        # 簡易ログファイルにリアルタイム記録
        daily_log_file = os.path.join(
            chat_logger.log_dir,
            f"daily_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
        )

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message.guild.name}#{message.channel.name} {message.author.name}: {message.content}\n"

        with open(daily_log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        if BOT_CONFIG.get('debug_level') == 'DEBUG':
            print(f"チャットログ記録: {message.guild.name}#{message.channel.name}")

        return True

    except Exception as e:
        print(f"チャットログ処理エラー: {e}")
        return False

async def collect_all_channels_history(bot, guild):
    """ギルドの全チャンネル履歴を収集"""
    try:
        collected_count = 0

        for channel in guild.text_channels:
            try:
                # 権限確認
                if not channel.permissions_for(guild.me).read_message_history:
                    continue

                messages_data = await chat_logger.collect_channel_history(channel, limit=50)
                if messages_data:
                    chat_logger.save_chat_log(channel, messages_data)
                    collected_count += 1

            except Exception as e:
                print(f"チャンネル処理エラー ({channel.name}): {e}")

        print(f"全チャンネル履歴収集完了: {collected_count}チャンネル")
        return collected_count

    except Exception as e:
        print(f"全履歴収集エラー: {e}")
        return 0

async def handle_chat_collection_reaction(message, bot):
    """📜リアクションによるチャット履歴収集処理"""
    from config import REACTION_EMOJIS

    try:
        # 処理開始を通知
        await message.add_reaction(REACTION_EMOJIS['processing'])

        # ギルドの全チャンネル履歴を収集
        collected_count = await collect_all_channels_history(bot, message.guild)

        # 結果を送信
        if collected_count > 0:
            await message.reply(f"**📜 チャット履歴収集完了:**\n`{collected_count}チャンネル`の履歴を収集し、JSONファイルとして保存しました。")
        else:
            await message.reply("チャット履歴の収集に失敗しました。権限を確認してください。")

        # 処理完了を通知
        await message.remove_reaction(REACTION_EMOJIS['processing'], bot.user)
        await message.add_reaction(REACTION_EMOJIS['success'])
        return True

    except Exception as e:
        print(f"チャット収集処理エラー: {str(e)}")
        await message.reply("チャット履歴収集中にエラーが発生しました。")
        await message.remove_reaction(REACTION_EMOJIS['processing'], bot.user)
        await message.add_reaction(REACTION_EMOJIS['error'])
        return False

async def auto_add_chat_collect_reaction(message):
    """特定のキーワードメッセージに自動で📜リアクションを追加"""
    from config import BOT_CONFIG, REACTION_EMOJIS

    # 指定チャンネルのみで動作
    if message.channel.id != BOT_CONFIG.get('target_channel_id'):
        return False

    # 特定のキーワードでチャット収集をトリガー
    trigger_keywords = ['チャット収集', 'ログ収集', 'chat collect', 'collect', '履歴収集', 'history']
    if message.content and any(keyword in message.content.lower() for keyword in trigger_keywords):
        print(f"[DEBUG] 📜リアクション追加: チャット収集トリガー")
        await message.add_reaction(REACTION_EMOJIS['chat_collect'])
        return True
    return False