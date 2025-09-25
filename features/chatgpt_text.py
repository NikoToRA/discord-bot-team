"""
ChatGPTテキスト会話機能
テキストメッセージに対するChatGPT応答
"""

import os
from openai import OpenAI
from config import CHATGPT_CONFIG

async def get_chatgpt_response(user_message):
    """ChatGPT APIでテキスト応答を取得"""
    try:
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        if not OPENAI_API_KEY:
            return "OpenAI APIキーが設定されていません。"

        # OpenAIクライアントを初期化
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model=CHATGPT_CONFIG['text_model'],
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            max_tokens=CHATGPT_CONFIG['max_tokens']
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"ChatGPTテキスト応答エラー: {str(e)}")
        return "エラーが発生しました。"

async def handle_chatgpt_conversation(message):
    """ChatGPTとのテキスト会話処理"""
    from config import BOT_CONFIG

    # コマンドまたは空のメッセージはスキップ
    if not message.content or message.content.startswith('!'):
        return False

    # 指定チャンネルのみで動作
    if message.channel.id != BOT_CONFIG.get('target_channel_id'):
        return False

    # 特定のキーワードでChatGPT応答をトリガー（テスト用に拡張）
    trigger_keywords = ['chatgpt', 'gpt', '質問', 'おしえて', '教えて', '会話', '話', 'ai']
    if not any(keyword in message.content.lower() for keyword in trigger_keywords):
        return False

    print(f"[DEBUG] ChatGPTテキスト会話トリガー: {message.content}")

    try:
        # ChatGPT応答を取得
        response_text = await get_chatgpt_response(message.content)

        # 長すぎる場合は分割して送信
        max_length = CHATGPT_CONFIG['max_message_length']
        if len(response_text) > max_length:
            chunks = [response_text[i:i+max_length] for i in range(0, len(response_text), max_length)]
            for i, chunk in enumerate(chunks):
                await message.reply(f"**🤖 ChatGPT応答 ({i+1}/{len(chunks)}):**\n{chunk}")
        else:
            await message.reply(f"**🤖 ChatGPT応答:**\n{response_text}")

        return True

    except Exception as e:
        print(f"ChatGPT会話処理エラー: {str(e)}")
        await message.reply("ChatGPTとの会話でエラーが発生しました。")
        return False