import discord
from discord.ext import commands
import os
import logging
import aiohttp
import base64
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
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

async def transcribe_image_with_gpt(image_data):
    """ChatGPT APIを使用して画像内のテキストを抽出"""
    try:
        # 画像をbase64エンコード
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }

        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "この画像に含まれているすべてのテキストを正確に読み取って、そのまま文字起こししてください。文字化けしないよう、正確な文字で出力してください。テキスト以外の説明は不要で、文字起こししたテキストのみを返してください。"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.openai.com/v1/chat/completions',
                                   headers=headers,
                                   json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    print(f"OpenAI API エラー: {response.status} - {error_text}")
                    return "画像の文字起こしに失敗しました。"

    except Exception as e:
        print(f"画像文字起こしエラー: {str(e)}")
        return "エラーが発生しました。"

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

@bot.event
async def on_reaction_add(reaction, user):
    """🦀リアクションが押された時の処理"""
    if user.bot:
        return

    # 🦀 絵文字でない場合はスキップ
    if str(reaction.emoji) != '🦀':
        return

    message = reaction.message

    # 画像添付がない場合はスキップ
    if not message.attachments:
        return

    # 画像ファイルかチェック
    image_attachment = None
    for attachment in message.attachments:
        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']):
            image_attachment = attachment
            break

    if not image_attachment:
        return

    try:
        # 処理開始を通知
        await message.add_reaction('⏳')

        # 画像をダウンロード
        image_data = await image_attachment.read()

        # ChatGPT APIで文字起こし
        transcribed_text = await transcribe_image_with_gpt(image_data)

        # 結果を送信（UTF-8で正しく表示されるように）
        if transcribed_text.strip():
            # 長すぎる場合は分割して送信
            if len(transcribed_text) > 1900:
                chunks = [transcribed_text[i:i+1900] for i in range(0, len(transcribed_text), 1900)]
                for i, chunk in enumerate(chunks):
                    await message.reply(f"**📝 文字起こし結果 ({i+1}/{len(chunks)}):**\n```\n{chunk}\n```")
            else:
                await message.reply(f"**📝 文字起こし結果:**\n```\n{transcribed_text}\n```")
        else:
            await message.reply("画像からテキストを検出できませんでした。")

        # 処理完了を通知
        await message.remove_reaction('⏳', bot.user)
        await message.add_reaction('✅')

    except Exception as e:
        print(f"画像処理エラー: {str(e)}")
        await message.reply("画像の処理中にエラーが発生しました。")
        await message.remove_reaction('⏳', bot.user)
        await message.add_reaction('❌')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 画像が添付されたメッセージに自動で🦀をつける
    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']):
                await message.add_reaction('🦀')
                break

    await bot.process_commands(message)

if __name__ == '__main__':
    print('=== Discord 画像文字起こしBot 起動中 ===')
    print(f'現在のディレクトリ: {os.getcwd()}')
    print(f'.envファイルの存在: {os.path.exists(".env")}')
    TOKEN = os.getenv('DISCORD_TOKEN')
    print(f'トークンの確認: {TOKEN[:10] if TOKEN else "None"}...')
    if TOKEN:
        print('ボットを起動します...')
        bot.run(TOKEN)
    else:
        print('エラー: DISCORD_TOKENが設定されていません。.envファイルを確認してください。')