import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# ログレベルを最大に設定
logging.basicConfig(level=logging.DEBUG)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
discord_logger.addHandler(handler)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    # 実行環境の判定
    if os.path.exists('.env'):
        environment = "🏠 ローカル環境"
    else:
        environment = "☁️ Railway環境"

    print(f'{bot.user} でログインしました！')
    print(f'実行環境: {environment}')
    print(f'ボットID: {bot.user.id}')
    print(f'サーバー数: {len(bot.guilds)}')
    for guild in bot.guilds:
        print(f'サーバー: {guild.name} (ID: {guild.id})')
        print(f'メンバー数: {guild.member_count}')
    print('Intents設定:')
    print(f'message_content: {bot.intents.message_content}')
    print(f'guilds: {bot.intents.guilds}')
    print(f'guild_messages: {bot.intents.guild_messages}')

@bot.event
async def on_message(message):
    print(f'[DEBUG] メッセージイベント発生')
    print(f'[DEBUG] 送信者: {message.author} (ID: {message.author.id})')
    print(f'[DEBUG] ボット自身: {bot.user} (ID: {bot.user.id})')
    print(f'[DEBUG] チャンネル: {message.channel} (ID: {message.channel.id})')
    print(f'[DEBUG] メッセージ内容: "{message.content}"')
    print(f'[DEBUG] メッセージタイプ: {message.type}')

    if message.author == bot.user:
        print('[DEBUG] ボット自身のメッセージなのでスキップ')
        return

    # 指定されたチャンネルでのみ反応
    ALLOWED_CHANNEL_ID = 1418467747083587607
    if message.channel.id != ALLOWED_CHANNEL_ID:
        print(f'[DEBUG] 許可されていないチャンネル ({message.channel.id}) からのメッセージなのでスキップ')
        return

    # メンションまたはリプライの場合のみ反応
    is_mentioned = bot.user in message.mentions
    is_reply = message.reference and message.reference.message_id

    print(f'[DEBUG] メンション確認: {is_mentioned}')
    print(f'[DEBUG] リプライ確認: {is_reply}')

    if (is_mentioned or is_reply) and message.content and not message.content.startswith('!'):
        # 実行環境に応じて返信を変える
        if os.path.exists('.env'):
            response = 'こんにちは ハロー！(ローカルから) 🏠'
        else:
            response = 'こんにちは てへっ(Railwayから) ☁️'

        print(f'[DEBUG] 条件一致、{response}と返信します')
        try:
            await message.channel.send(response)
            print('[DEBUG] 返信送信成功')
        except Exception as e:
            print(f'[DEBUG] 返信送信エラー: {e}')
    else:
        print('[DEBUG] 条件不一致、返信しません（メンション/リプライなし）')

    await bot.process_commands(message)

if __name__ == '__main__':
    print('=== Discord Bot 起動中 ===')
    print(f'現在のディレクトリ: {os.getcwd()}')
    print(f'.envファイルの存在: {os.path.exists(".env")}')
    TOKEN = os.getenv('DISCORD_TOKEN')
    print(f'トークンの確認: {TOKEN[:10] if TOKEN else "None"}...')
    if TOKEN:
        print('ボットを起動します...')
        bot.run(TOKEN)
    else:
        print('エラー: DISCORD_TOKENが設定されていません。.envファイルを確認してください。')