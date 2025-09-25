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

        # APIキーをクリーンアップ（改行や空白を除去）
        OPENAI_API_KEY = OPENAI_API_KEY.strip().replace('\n', '').replace(' ', '')
        print(f"[DEBUG] OpenAI APIキー長: {len(OPENAI_API_KEY)}")

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

    print(f"[DEBUG] ChatGPT処理開始: チャンネルID={message.channel.id}, メッセージ='{message.content}'")

    # コマンドまたは空のメッセージはスキップ
    if not message.content or message.content.startswith('!'):
        print(f"[DEBUG] 空のメッセージまたはコマンドのためスキップ")
        return False

    # 指定チャンネルのみで動作
    target_id = BOT_CONFIG.get('target_channel_id')
    print(f"[DEBUG] ターゲットチャンネル: {target_id}, 現在チャンネル: {message.channel.id}")
    if message.channel.id != target_id:
        print(f"[DEBUG] チャンネルID不一致のためスキップ")
        return False

    # 特定のキーワードでChatGPT応答をトリガー（テスト用に拡張）
    trigger_keywords = ['chatgpt', 'gpt', '質問', 'おしえて', '教えて', '会話', '話', 'ai']
    content_lower = message.content.lower()
    print(f"[DEBUG] キーワード検索: '{content_lower}' in {trigger_keywords}")
    if not any(keyword in content_lower for keyword in trigger_keywords):
        print(f"[DEBUG] トリガーキーワード未検出のためスキップ")
        return False

    print(f"[DEBUG] ChatGPTテキスト会話トリガー成功: {message.content}")

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