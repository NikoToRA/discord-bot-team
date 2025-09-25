"""
画像文字起こし機能 (🦀リアクション)
ChatGPT Vision APIを使用した画像からのテキスト抽出
"""

import os
import aiohttp
import base64
from config import CHATGPT_CONFIG, REACTION_EMOJIS
from openai import OpenAI

async def transcribe_image_with_gpt(image_data):
    """ChatGPT APIを使用して画像内のテキストを抽出"""
    try:
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        if not OPENAI_API_KEY:
            return "OpenAI APIキーが設定されていません。"

        # OpenAIクライアントを初期化
        client = OpenAI(api_key=OPENAI_API_KEY)

        # 画像をbase64エンコード
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
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
            max_tokens=CHATGPT_CONFIG['max_tokens']
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"画像文字起こしエラー: {str(e)}")
        return "エラーが発生しました。"

async def handle_image_ocr_reaction(message, bot):
    """🦀リアクションによる画像文字起こし処理"""
    # 画像添付がない場合はスキップ
    if not message.attachments:
        return False

    # 画像ファイルかチェック
    image_attachment = None
    for attachment in message.attachments:
        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']):
            image_attachment = attachment
            break

    if not image_attachment:
        return False

    try:
        # 処理開始を通知
        await message.add_reaction(REACTION_EMOJIS['processing'])

        # 画像をダウンロード
        image_data = await image_attachment.read()

        # ChatGPT APIで文字起こし
        transcribed_text = await transcribe_image_with_gpt(image_data)

        # 結果を送信（UTF-8で正しく表示されるように）
        if transcribed_text.strip():
            max_length = CHATGPT_CONFIG['max_message_length']
            # 長すぎる場合は分割して送信
            if len(transcribed_text) > max_length:
                chunks = [transcribed_text[i:i+max_length] for i in range(0, len(transcribed_text), max_length)]
                for i, chunk in enumerate(chunks):
                    await message.reply(f"**📝 文字起こし結果 ({i+1}/{len(chunks)}):**\n```\n{chunk}\n```")
            else:
                await message.reply(f"**📝 文字起こし結果:**\n```\n{transcribed_text}\n```")
        else:
            await message.reply("画像からテキストを検出できませんでした。")

        # 処理完了を通知
        await message.remove_reaction(REACTION_EMOJIS['processing'], bot.user)
        await message.add_reaction(REACTION_EMOJIS['success'])
        return True

    except Exception as e:
        print(f"画像処理エラー: {str(e)}")
        await message.reply("画像の処理中にエラーが発生しました。")
        await message.remove_reaction(REACTION_EMOJIS['processing'], bot.user)
        await message.add_reaction(REACTION_EMOJIS['error'])
        return False

async def auto_add_image_reaction(message):
    """画像が添付されたメッセージに自動で🦀リアクションを追加"""
    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']):
                await message.add_reaction(REACTION_EMOJIS['image_ocr'])
                return True
    return False