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

    # 🦀 画像文字起こし機能
    if FEATURES['chatgpt_image_ocr'] and emoji_str == REACTION_EMOJIS['image_ocr']:
        await handle_image_ocr_reaction(message, bot)

    # 🎤 音声文字起こし機能
    if FEATURES['chatgpt_voice'] and emoji_str == REACTION_EMOJIS['voice_transcribe']:
        await handle_voice_transcription(message, bot)

@bot.event
async def on_message(message):
    """メッセージ受信時の処理"""
    if message.author == bot.user:
        return

    # デバッグログ出力
    if FEATURES['debug_logging']:
        print(f'[DEBUG] メッセージ: {message.author} -> "{message.content[:50]}..."')

    # 自動リアクション追加
    reaction_added = False

    # 画像に自動で🦀リアクション
    if FEATURES['chatgpt_image_ocr']:
        if await auto_add_image_reaction(message):
            reaction_added = True

    # 音声に自動で🎤リアクション
    if FEATURES['chatgpt_voice']:
        if await auto_add_voice_reaction(message):
            reaction_added = True

    # メッセージ処理（リアクション追加済みの場合は基本挨拶をスキップ）
    if not reaction_added:
        # ChatGPTテキスト会話機能
        if FEATURES['chatgpt_text']:
            if await handle_chatgpt_conversation(message):
                await bot.process_commands(message)
                return

        # 基本的な挨拶機能
        if FEATURES['basic_greeting']:
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