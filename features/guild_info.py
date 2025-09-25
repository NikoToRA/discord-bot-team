"""
ギルド情報取得機能
サーバー情報とメンバー情報の収集
"""

import discord
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