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

intents = discord.Intents.all()
# リアクションイベント用の明示的な設定を追加
intents.reactions = True
intents.guild_reactions = True
# または個別に設定する場合:
# intents = discord.Intents.default()
# intents.message_content = True
# intents.guilds = True
# intents.guild_messages = True
# intents.reactions = True
# intents.guild_reactions = True
# intents.members = True

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
    print(f'reactions: {bot.intents.reactions}')
    print(f'guild_reactions: {bot.intents.guild_reactions}')

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

    # メンション、リプライ、または通常のメッセージで反応
    is_mentioned = bot.user in message.mentions
    is_reply = message.reference and message.reference.message_id
    has_content = bool(message.content.strip())

    print(f'[DEBUG] メンション確認: {is_mentioned}')
    print(f'[DEBUG] リプライ確認: {is_reply}')
    print(f'[DEBUG] メッセージ内容あり: {has_content}')

    if has_content and not message.content.startswith('!'):
        # メッセージをオウム返しする
        original_message = message.content

        # メンションを除去してクリーンなメッセージを取得
        clean_message = original_message
        for mention in message.mentions:
            clean_message = clean_message.replace(f'<@{mention.id}>', '').strip()

        # 実行環境の情報を追加
        if os.path.exists('.env'):
            response = f'{clean_message} (ローカルから) 🏠'
        else:
            response = f'{clean_message} (Railwayから) ☁️'

        print(f'[DEBUG] 条件一致、オウム返し: {response}')
        try:
            await message.channel.send(response)
            print('[DEBUG] 返信送信成功')
        except Exception as e:
            print(f'[DEBUG] 返信送信エラー: {e}')
    else:
        print('[DEBUG] 条件不一致、返信しません（メッセージ内容なしまたはコマンド）')

    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    print(f'[DEBUG] リアクションイベント発生')
    print(f'[DEBUG] リアクション絵文字: {reaction.emoji}')
    print(f'[DEBUG] リアクションしたユーザー: {user} (ID: {user.id})')
    print(f'[DEBUG] メッセージチャンネル: {reaction.message.channel} (ID: {reaction.message.channel.id})')
    print(f'[DEBUG] メッセージ内容: "{reaction.message.content}"')

    # ボット自身のリアクションは無視
    if user == bot.user:
        print('[DEBUG] ボット自身のリアクションなのでスキップ')
        return

    # 指定されたチャンネルでのみ反応
    ALLOWED_CHANNEL_ID = 1418467747083587607
    if reaction.message.channel.id != ALLOWED_CHANNEL_ID:
        print(f'[DEBUG] 許可されていないチャンネル ({reaction.message.channel.id}) からのリアクションなのでスキップ')
        return

    # グッドマーク（👍）リアクションに反応
    if str(reaction.emoji) == '👍':
        # 実行環境に応じて返信を変える
        if os.path.exists('.env'):
            response = 'グッドマークが押されたよ！ (ローカルから) 🏠'
        else:
            response = 'グッドマークが押されたよ！ (Railwayから) ☁️'

        print(f'[DEBUG] グッドマーク検知、{response}と返信します')
        try:
            await reaction.message.channel.send(response)
            print('[DEBUG] リアクション返信送信成功')
        except Exception as e:
            print(f'[DEBUG] リアクション返信送信エラー: {e}')
    else:
        print(f'[DEBUG] グッドマーク以外のリアクション ({reaction.emoji}) なので無視')

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