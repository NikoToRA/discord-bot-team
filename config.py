"""
Discord Bot Configuration
機能のON/OFF制御とボット設定
"""

# 機能のON/OFF設定 - テキスト会話追加
FEATURES = {
    'basic_greeting': False,        # 無効
    'chatgpt_text': True,           # 有効化
    'chatgpt_voice': True,          # 有効化
    'chatgpt_image_ocr': True,      # 有効
    'room_logging': True,           # 有効化
    'guild_info': False,            # 無効
    'chat_logging': True,           # 有効化
    'member_collection': False,     # 無効
    'debug_logging': True,          # デバッグ有効
}

# リアクション絵文字設定
REACTION_EMOJIS = {
    'image_ocr': '🦀',             # 画像文字起こし
    'voice_transcribe': '🎤',      # 音声文字起こし
    'chat_collect': '📜',          # チャット履歴収集
    'room_stats': '📊',            # ルーム統計表示
    'processing': '⏳',            # 処理中
    'success': '✅',               # 成功
    'error': '❌',                 # エラー
}

# ChatGPT設定
CHATGPT_CONFIG = {
    'vision_model': 'gpt-4o',
    'text_model': 'gpt-4',
    'max_tokens': 1000,
    'max_message_length': 1900,
}

# ボット設定
BOT_CONFIG = {
    'command_prefix': '!',
    'debug_level': 'DEBUG',         # デバッグレベル最大
    'intents_reactions': True,
    'intents_voice_states': True,
    'target_channel_id': 1418512165165465600,  # 対象チャンネル指定
}