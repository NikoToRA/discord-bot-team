"""
Discord Bot Main File
統合された機能を持つメインボット

使用方法:
python main_bot.py

設定変更:
config.py で各機能のON/OFF制御
"""

import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv

# 設定とフィーチャーをインポート
from config import FEATURES, REACTION_EMOJIS, BOT_CONFIG
from features.image_ocr import handle_image_ocr_reaction, auto_add_image_reaction
from features.voice_transcribe import handle_voice_transcription, auto_add_voice_reaction
from features.basic_greeting import handle_basic_greeting
from features.chatgpt_text import handle_chatgpt_conversation
from features.room_logging import handle_room_logging, get_room_stats, handle_room_stats_reaction, auto_add_room_stats_reaction
from features.guild_info import handle_guild_info_collection, handle_member_collection, get_channel_info, handle_guild_info_reaction, auto_add_guild_info_reaction
from features.chat_logging import handle_chat_logging, collect_all_channels_history, handle_chat_collection_reaction, auto_add_chat_collect_reaction

# 環境変数を読み込み
load_dotenv()

# ログ設定
if BOT_CONFIG['debug_level'] == 'DEBUG':
    logging.basicConfig(level=logging.DEBUG)
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    discord_logger.addHandler(handler)
else:
    logging.basicConfig(level=getattr(logging, BOT_CONFIG['debug_level']))

# Discord Intents設定
intents = discord.Intents.default()
intents.message_content = True
if BOT_CONFIG['intents_reactions']:
    intents.reactions = True
if BOT_CONFIG['intents_voice_states']:
    intents.voice_states = True

# ボットを初期化
bot = commands.Bot(command_prefix=BOT_CONFIG['command_prefix'], intents=intents)

@bot.event
async def on_ready():
    """ボット起動時の処理"""
    # 実行環境の判定
    if os.path.exists('.env'):
        environment = "🏠 ローカル環境"
    else:
        environment = "☁️ Railway環境"

    print('='*50)
    print('🤖 Discord統合ボット起動完了！')
    print(f'ボット名: {bot.user}')
    print(f'実行環境: {environment}')
    print(f'ボットID: {bot.user.id}')
    print(f'サーバー数: {len(bot.guilds)}')

    for guild in bot.guilds:
        print(f'  └ サーバー: {guild.name} (ID: {guild.id}, メンバー: {guild.member_count})')

    print('\n🔧 有効な機能:')
    for feature_name, enabled in FEATURES.items():
        status = "✅" if enabled else "❌"
        print(f'  {status} {feature_name}')

    print(f'\n🎯 リアクション設定:')
    for key, emoji in REACTION_EMOJIS.items():
        print(f'  {emoji} {key}')

    print('='*50)

@bot.event
async def on_reaction_add(reaction, user):
    """リアクション追加時の処理"""
    if user.bot:
        return

    message = reaction.message
    emoji_str = str(reaction.emoji)

    # 指定チャンネルのみで動作
    if message.channel.id != BOT_CONFIG.get('target_channel_id'):
        print(f"[DEBUG] リアクション対象外チャンネル: {message.channel.id}")
        return

    print(f"[DEBUG] リアクション検知: {emoji_str} by {user.name} in {message.channel.name}")

    # 🦀 画像文字起こし機能
    if FEATURES['chatgpt_image_ocr'] and emoji_str == REACTION_EMOJIS['image_ocr']:
        print(f"[DEBUG] 🦀画像文字起こし開始")
        await handle_image_ocr_reaction(message, bot)

    # 🎤 音声文字起こし機能
    if FEATURES['chatgpt_voice'] and emoji_str == REACTION_EMOJIS['voice_transcribe']:
        print(f"[DEBUG] 🎤音声文字起こし開始")
        await handle_voice_transcription(message, bot)

    # 📜 チャット履歴収集機能
    if FEATURES['chat_logging'] and emoji_str == REACTION_EMOJIS['chat_collect']:
        print(f"[DEBUG] 📜チャット履歴収集開始")
        await handle_chat_collection_reaction(message, bot)

    # 📊 ルーム統計表示機能
    if FEATURES['room_logging'] and emoji_str == REACTION_EMOJIS['room_stats']:
        print(f"[DEBUG] 📊ルーム統計表示開始")
        await handle_room_stats_reaction(message, bot)

    # 🏛️ ギルド情報収集機能
    if FEATURES['guild_info'] and emoji_str == REACTION_EMOJIS['guild_info']:
        print(f"[DEBUG] 🏛️ギルド情報収集開始")
        await handle_guild_info_reaction(message, bot)

@bot.event
async def on_message(message):
    """メッセージ受信時の処理"""
    if message.author == bot.user:
        return

    # 指定チャンネルのみで処理
    if message.channel.id != BOT_CONFIG.get('target_channel_id'):
        return

    # デバッグログ出力
    if FEATURES['debug_logging']:
        print(f'[DEBUG] 対象チャンネルメッセージ: {message.author} -> "{message.content[:50]}..." in {message.channel.name}')

    # 自動リアクション追加
    reaction_added = False

    # 画像に自動で🦀リアクション
    if FEATURES['chatgpt_image_ocr']:
        if await auto_add_image_reaction(message):
            reaction_added = True
            print(f'[DEBUG] 🦀リアクション追加完了')

    # 音声に自動で🎤リアクション
    if FEATURES['chatgpt_voice']:
        if await auto_add_voice_reaction(message):
            reaction_added = True

    # チャット収集キーワードに自動で📜リアクション
    if FEATURES['chat_logging']:
        if await auto_add_chat_collect_reaction(message):
            reaction_added = True
            print(f'[DEBUG] 📜リアクション追加完了')

    # ルーム統計キーワードに自動で📊リアクション
    if FEATURES['room_logging']:
        if await auto_add_room_stats_reaction(message):
            reaction_added = True
            print(f'[DEBUG] 📊リアクション追加完了')

    # ギルド情報キーワードに自動で🏛️リアクション
    if FEATURES['guild_info']:
        if await auto_add_guild_info_reaction(message):
            reaction_added = True
            print(f'[DEBUG] 🏛️リアクション追加完了')

    # ログ機能処理
    # ルームログ機能
    if FEATURES['room_logging']:
        await handle_room_logging(message)

    # チャットログ機能
    if FEATURES['chat_logging']:
        await handle_chat_logging(message)

    # メッセージ処理
    # ChatGPTテキスト会話機能
    if FEATURES['chatgpt_text']:
        if await handle_chatgpt_conversation(message):
            await bot.process_commands(message)
            return

    # 基本的な挨拶機能（リアクション追加されていない場合のみ）
    if FEATURES['basic_greeting'] and not reaction_added:
        await handle_basic_greeting(message)

    await bot.process_commands(message)

@bot.command(name='features')
async def show_features(ctx):
    """有効な機能一覧を表示"""
    embed = discord.Embed(title="🤖 ボット機能一覧", color=0x00ff00)

    for feature_name, enabled in FEATURES.items():
        status = "✅ 有効" if enabled else "❌ 無効"
        embed.add_field(name=feature_name, value=status, inline=True)

    await ctx.send(embed=embed)

@bot.command(name='help_reactions')
async def show_reactions(ctx):
    """リアクション一覧を表示"""
    embed = discord.Embed(title="🎯 リアクション一覧", color=0x0099ff)

    descriptions = {
        'image_ocr': '画像の文字起こし',
        'voice_transcribe': '音声の文字起こし',
        'processing': '処理中',
        'success': '成功',
        'error': 'エラー'
    }

    for key, emoji in REACTION_EMOJIS.items():
        desc = descriptions.get(key, key)
        embed.add_field(name=f"{emoji} {key}", value=desc, inline=True)

    await ctx.send(embed=embed)

@bot.command(name='room_stats')
async def show_room_stats(ctx):
    """ルーム統計を表示"""
    if not FEATURES['room_logging']:
        await ctx.send("❌ ルームログ機能が無効です。")
        return

    stats = await get_room_stats()
    if stats:
        embed = discord.Embed(title="📊 ルーム統計", color=0x00ff00)
        embed.add_field(name="メッセージ数", value=stats['message_count'], inline=True)
        embed.add_field(name="ユニークユーザー数", value=len(stats['unique_users']), inline=True)
        embed.add_field(name="最終更新", value=stats['last_updated'][:19], inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ 統計データの取得に失敗しました。")

@bot.command(name='collect_guild_info')
async def collect_guild_info_command(ctx):
    """ギルド情報を収集"""
    if not FEATURES['guild_info']:
        await ctx.send("❌ ギルド情報機能が無効です。")
        return

    try:
        guild = ctx.guild
        guild_info = await handle_guild_info_collection(bot, guild)
        members_info = await handle_member_collection(guild)
        channels_info = await get_channel_info(guild)

        embed = discord.Embed(title="🏛️ ギルド情報収集完了", color=0x00ff00)
        embed.add_field(name="サーバー名", value=guild.name, inline=True)
        embed.add_field(name="メンバー数", value=guild.member_count, inline=True)
        embed.add_field(name="収集メンバー数", value=len(members_info), inline=True)
        embed.add_field(name="チャンネル数", value=len(channels_info), inline=True)
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ ギルド情報収集エラー: {e}")

@bot.command(name='collect_chat_history')
async def collect_chat_history_command(ctx):
    """チャット履歴を収集"""
    if not FEATURES['chat_logging']:
        await ctx.send("❌ チャットログ機能が無効です。")
        return

    try:
        count = await collect_all_channels_history(bot, ctx.guild)
        await ctx.send(f"✅ チャット履歴収集完了: {count}チャンネル")
    except Exception as e:
        await ctx.send(f"❌ チャット履歴収集エラー: {e}")

def main():
    """メイン実行関数"""
    print('🚀 Discord統合ボットを起動中...')
    print(f'現在のディレクトリ: {os.getcwd()}')
    print(f'.envファイルの存在: {os.path.exists(".env")}')

    TOKEN = os.getenv('DISCORD_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # 必要な環境変数をチェック
    missing_vars = []
    if not TOKEN:
        missing_vars.append('DISCORD_TOKEN')
    if not OPENAI_API_KEY:
        missing_vars.append('OPENAI_API_KEY')

    if missing_vars:
        print(f'❌ 環境変数が不足しています: {", ".join(missing_vars)}')
        print('.envファイルを確認してください。')
        return

    print(f'✅ Discord Token確認済み: {TOKEN[:10]}...')
    print(f'✅ OpenAI API Key確認済み: {OPENAI_API_KEY[:10]}...')

    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f'❌ ボット起動エラー: {e}')

if __name__ == '__main__':
    main()