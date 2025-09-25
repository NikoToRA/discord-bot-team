"""
音声文字起こし機能
音声ファイルをChatGPT Whisper APIで文字起こし
"""

import os
import tempfile
from openai import OpenAI
from config import REACTION_EMOJIS

async def transcribe_audio_with_whisper(audio_data, filename):
    """Whisper APIを使用して音声をテキストに変換"""
    temp_file_path = None
    try:
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        if not OPENAI_API_KEY:
            return "OpenAI APIキーが設定されていません。"

        # OpenAIクライアントを初期化
        client = OpenAI(api_key=OPENAI_API_KEY)

        # 一時ファイルとして保存
        file_ext = os.path.splitext(filename)[1] if filename else '.mp3'
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        # Whisper APIで文字起こし
        with open(temp_file_path, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
                language="ja",
                prompt="以下は日本語の音声です。正確に文字起こしをしてください。句読点も適切に付けてください。"
            )

        return transcription.strip()

    except Exception as e:
        print(f"音声文字起こしエラー: {str(e)}")
        return "エラーが発生しました。"
    finally:
        # 一時ファイルを削除
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                print(f"一時ファイル削除エラー: {e}")

async def handle_voice_transcription(message, bot):
    """音声ファイルの文字起こし処理"""
    # 音声添付がない場合はスキップ
    if not message.attachments:
        return False

    # 音声ファイルかチェック
    audio_attachment = None
    for attachment in message.attachments:
        if any(attachment.filename.lower().endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']):
            audio_attachment = attachment
            break

    if not audio_attachment:
        return False

    try:
        # 処理開始を通知
        await message.add_reaction(REACTION_EMOJIS['processing'])

        # 音声をダウンロード
        audio_data = await audio_attachment.read()

        # Whisper APIで文字起こし
        transcribed_text = await transcribe_audio_with_whisper(audio_data, audio_attachment.filename)

        # 結果を送信
        if transcribed_text.strip():
            await message.reply(f"**🎤 音声文字起こし結果:**\n```\n{transcribed_text}\n```")
        else:
            await message.reply("音声からテキストを認識できませんでした。")

        # 処理完了を通知
        await message.remove_reaction(REACTION_EMOJIS['processing'], bot.user)
        await message.add_reaction(REACTION_EMOJIS['success'])
        return True

    except Exception as e:
        print(f"音声処理エラー: {str(e)}")
        await message.reply("音声の処理中にエラーが発生しました。")
        await message.remove_reaction(REACTION_EMOJIS['processing'], bot.user)
        await message.add_reaction(REACTION_EMOJIS['error'])
        return False

async def auto_add_voice_reaction(message):
    """音声ファイルが添付されたメッセージに自動で🎤リアクションを追加"""
    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']):
                await message.add_reaction(REACTION_EMOJIS['voice_transcribe'])
                return True
    return False