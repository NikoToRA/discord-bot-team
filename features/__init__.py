"""
Discord Bot Features Package
各機能モジュールの初期化
"""

from .image_ocr import handle_image_ocr_reaction, auto_add_image_reaction
from .voice_transcribe import handle_voice_transcription, auto_add_voice_reaction
from .basic_greeting import handle_basic_greeting
from .chatgpt_text import handle_chatgpt_conversation
from .room_logging import handle_room_logging, get_room_stats
from .guild_info import handle_guild_info_collection, handle_member_collection, get_channel_info
from .chat_logging import handle_chat_logging, collect_all_channels_history

__all__ = [
    'handle_image_ocr_reaction',
    'auto_add_image_reaction',
    'handle_voice_transcription',
    'auto_add_voice_reaction',
    'handle_basic_greeting',
    'handle_chatgpt_conversation',
    'handle_room_logging',
    'get_room_stats',
    'handle_guild_info_collection',
    'handle_member_collection',
    'get_channel_info',
    'handle_chat_logging',
    'collect_all_channels_history'
]