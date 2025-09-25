"""
ギルド情報取得機能
サーバー情報とメンバー情報の収集
"""

import discord
import json
import os
from datetime import datetime

async def handle_guild_info_collection(bot, guild):
    """ギルド情報収集のメイン関数"""
    try:
        guild_info = {
            'id': guild.id,
            'name': guild.name,
            'description': guild.description,
            'member_count': guild.member_count,
            'created_at': guild.created_at.isoformat(),
            'owner_id': guild.owner_id,
            'verification_level': str(guild.verification_level),
            'collected_at': datetime.now().isoformat()
        }

        print(f"ギルド情報収集完了: {guild.name} ({guild.member_count}人)")
        return guild_info

    except Exception as e:
        print(f"ギルド情報収集エラー: {e}")
        return None

async def handle_member_collection(guild):
    """ギルドメンバー情報の収集"""
    try:
        members_info = []

        # 最初の100人のメンバー情報を収集（大きなサーバーでの負荷軽減）
        member_count = 0
        async for member in guild.fetch_members(limit=100):
            member_info = {
                'id': member.id,
                'name': member.name,
                'discriminator': member.discriminator,
                'display_name': member.display_name,
                'joined_at': member.joined_at.isoformat() if member.joined_at else None,
                'created_at': member.created_at.isoformat(),
                'is_bot': member.bot,
                'roles_count': len(member.roles)
            }
            members_info.append(member_info)
            member_count += 1

        print(f"メンバー情報収集完了: {member_count}人")
        return members_info

    except Exception as e:
        print(f"メンバー情報収集エラー: {e}")
        return []

async def get_channel_info(guild):
    """チャンネル情報の取得"""
    try:
        channels_info = []

        for channel in guild.channels:
            channel_info = {
                'id': channel.id,
                'name': channel.name,
                'type': str(channel.type),
                'created_at': channel.created_at.isoformat(),
                'position': channel.position
            }

            # テキストチャンネルの場合は追加情報
            if isinstance(channel, discord.TextChannel):
                channel_info.update({
                    'topic': channel.topic,
                    'slowmode_delay': channel.slowmode_delay,
                    'is_news': channel.is_news()
                })

            channels_info.append(channel_info)

        print(f"チャンネル情報収集完了: {len(channels_info)}個")
        return channels_info

    except Exception as e:
        print(f"チャンネル情報収集エラー: {e}")
        return []

async def handle_guild_info_reaction(message, bot):
    """🏛️リアクションによるギルド情報収集処理"""
    from config import REACTION_EMOJIS

    try:
        # 処理開始を通知
        await message.add_reaction(REACTION_EMOJIS['processing'])

        guild = message.guild

        # ギルド情報収集
        guild_info = await handle_guild_info_collection(bot, guild)
        members_info = await handle_member_collection(guild)
        channels_info = await get_channel_info(guild)

        if guild_info:
            # 結果を表示
            summary_text = f"**🏛️ ギルド情報収集完了:**\n"
            summary_text += f"・サーバー名: {guild.name}\n"
            summary_text += f"・メンバー数: {guild.member_count}\n"
            summary_text += f"・収集メンバー数: {len(members_info)}\n"
            summary_text += f"・チャンネル数: {len(channels_info)}\n"

            await message.reply(summary_text)

            # データをファイルに保存して送信
            try:
                # ディレクトリ作成
                guild_info_dir = "guild_info"
                if not os.path.exists(guild_info_dir):
                    os.makedirs(guild_info_dir)

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                # ギルド情報ファイル
                guild_file = os.path.join(guild_info_dir, f"guild_{guild.id}_{timestamp}.json")
                with open(guild_file, 'w', encoding='utf-8') as f:
                    json.dump(guild_info, f, indent=2, ensure_ascii=False)

                # メンバー情報ファイル
                members_file = os.path.join(guild_info_dir, f"members_{guild.id}_{timestamp}.json")
                with open(members_file, 'w', encoding='utf-8') as f:
                    json.dump(members_info, f, indent=2, ensure_ascii=False)

                # チャンネル情報ファイル
                channels_file = os.path.join(guild_info_dir, f"channels_{guild.id}_{timestamp}.json")
                with open(channels_file, 'w', encoding='utf-8') as f:
                    json.dump(channels_info, f, indent=2, ensure_ascii=False)

                # ファイルをDiscordに送信
                files_to_send = [
                    (guild_file, "ギルド基本情報"),
                    (members_file, "メンバー情報"),
                    (channels_file, "チャンネル情報")
                ]

                for file_path, description in files_to_send:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            discord_file = discord.File(f, filename=os.path.basename(file_path))
                            await message.channel.send(f"**📁 {description}:**", file=discord_file)

            except Exception as e:
                print(f"ギルド情報ファイル送信エラー: {e}")

        else:
            await message.reply("ギルド情報の収集に失敗しました。")

        # 処理完了を通知
        await message.remove_reaction(REACTION_EMOJIS['processing'], bot.user)
        await message.add_reaction(REACTION_EMOJIS['success'])
        return True

    except Exception as e:
        print(f"ギルド情報処理エラー: {str(e)}")
        await message.reply("ギルド情報収集中にエラーが発生しました。")
        await message.remove_reaction(REACTION_EMOJIS['processing'], bot.user)
        await message.add_reaction(REACTION_EMOJIS['error'])
        return False

async def auto_add_guild_info_reaction(message):
    """特定のキーワードメッセージに自動で🏛️リアクションを追加"""
    from config import BOT_CONFIG, REACTION_EMOJIS

    # 指定チャンネルのみで動作
    if message.channel.id != BOT_CONFIG.get('target_channel_id'):
        return False

    # 特定のキーワードでギルド情報をトリガー
    trigger_keywords = ['ギルド情報', 'guild info', 'サーバー情報', 'server info', 'メンバー情報', 'member info']
    if message.content and any(keyword in message.content.lower() for keyword in trigger_keywords):
        print(f"[DEBUG] 🏛️リアクション追加: ギルド情報トリガー")
        await message.add_reaction(REACTION_EMOJIS['guild_info'])
        return True
    return False