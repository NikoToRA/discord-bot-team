"""
基本的な挨拶機能
メッセージに対する簡単な返答
"""

import os

async def handle_basic_greeting(message):
    """基本的な挨拶応答"""
    if not message.content or message.content.startswith('!'):
        return False

    # 実行環境に応じて返信を変える
    if os.path.exists('.env'):
        response = 'こんにちは ハロー！(ローカルから) 🏠'
    else:
        response = 'こんにちは てへっ(Railwayから) ☁️'

    try:
        await message.channel.send(response)
        return True
    except Exception as e:
        print(f'挨拶返信エラー: {e}')
        return False