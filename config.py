"""
Discord Bot Configuration
機能のON/OFF制御とボット設定
"""

# 機能のON/OFF設定
FEATURES = {
    'basic_greeting': False,        # 基本的な挨拶機能（競合するため無効）
    'chatgpt_text': True,           # ChatGPT テキスト会話
    'chatgpt_voice': True,          # ChatGPT 音声文字起こし
    'chatgpt_image_ocr': True,      # ChatGPT 画像文字起こし (🦀)
    'room_logging': True,           # ルームログ機能
    'guild_info': True,             # ギルド情報取得
    'chat_logging': True,           # チャットログ収集
    'member_collection': True,      # ルームメンバー収集
    'debug_logging': True,          # デバッグログ
}

# リアクション絵文字設定
REACTION_EMOJIS = {
    'image_ocr': '🦀',             # 画像文字起こし
    'voice_transcribe': '🎤',      # 音声文字起こし
    'processing': '⏳',            # 処理中
    'success': '✅',               # 成功
    'error': '❌',                 # エラー
}

# ChatGPT設定
CHATGPT_CONFIG = {
    'vision_model': 'gpt-4-vision-preview',
    'text_model': 'gpt-4',
    'max_tokens': 1000,
    'max_message_length': 1900,
}

# ボット設定
BOT_CONFIG = {
    'command_prefix': '!',
    'debug_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'intents_reactions': True,
    'intents_voice_states': True,
}