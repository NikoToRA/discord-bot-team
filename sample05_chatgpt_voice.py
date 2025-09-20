import discord
from discord.ext import commands
import os
import asyncio
import logging
import aiohttp
import tempfile
from dotenv import load_dotenv
from openai import OpenAI
import datetime

# ログ設定を強化
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('voice_bot_debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 全てのDiscordイベントをログ出力
logging.getLogger('discord').setLevel(logging.DEBUG)
logging.getLogger('discord.gateway').setLevel(logging.DEBUG)
logging.getLogger('discord.client').setLevel(logging.DEBUG)

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)
bot_logger = logging.getLogger('voice_bot')

load_dotenv()

# 音声文字起こしDiscordボット
intents = discord.Intents.all()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
intents.guild_reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 対象チャンネルID
TARGET_CHANNEL_ID = 1418512165165465600

# OpenAI クライアント初期化
client = None
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        print(f'[SETUP] OpenAI APIクライアント初期化完了')
        bot_logger.info(f'OpenAI APIクライアント初期化完了 - キー: {OPENAI_API_KEY[:10]}...')
    except Exception as e:
        print(f'[ERROR] OpenAI APIクライアント初期化失敗: {e}')
        bot_logger.error(f'OpenAI APIクライアント初期化失敗: {e}', exc_info=True)
else:
    print('[WARNING] OPENAI_API_KEYが設定されていません')
    bot_logger.warning('OPENAI_API_KEYが設定されていません')

# 対応する音声ファイル形式
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg']

# 音声処理のためのリアクション
TRANSCRIBE_EMOJI = '🔄'

class VoiceTranscriber:
    def __init__(self, openai_client):
        self.client = openai_client
        self.processing_messages = set()  # 処理中のメッセージIDを追跡
        self.transcription_history = []  # 文字起こし履歴

    async def download_audio_file(self, attachment):
        """音声ファイルをダウンロード"""
        try:
            bot_logger.info(f'音声ファイルダウンロード開始: {attachment.filename} ({attachment.size} bytes)')

            # ファイルサイズチェック (25MB制限)
            if attachment.size > 25 * 1024 * 1024:
                bot_logger.warning(f'ファイルサイズ制限超過: {attachment.size} bytes')
                return None, "❌ ファイルサイズが25MBを超えています。"

            # 一時ファイル作成
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(attachment.filename)[1]) as temp_file:
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as response:
                        if response.status == 200:
                            content = await response.read()
                            temp_file.write(content)
                            bot_logger.info(f'ファイルダウンロード完了: {temp_file.name}')
                            return temp_file.name, None
                        else:
                            bot_logger.error(f'ファイルダウンロード失敗: HTTP {response.status}')
                            return None, f"❌ ファイルのダウンロードに失敗しました。(HTTP {response.status})"

        except Exception as e:
            bot_logger.error(f'ファイルダウンロードエラー: {e}', exc_info=True)
            return None, f"❌ ファイルダウンロード中にエラーが発生しました: {str(e)}"

    async def transcribe_audio(self, file_path, original_filename):
        """音声ファイルを文字起こし"""
        try:
            bot_logger.info(f'文字起こし開始: {file_path}')

            with open(file_path, 'rb') as audio_file:
                # GPT-4oを使用した高品質な文字起こし
                transcription = self.client.audio.transcriptions.create(
                    model="gpt-4o-transcribe",  # 最新の高品質モデル
                    file=audio_file,
                    response_format="text",
                    language="ja",  # 日本語を明示的に指定
                    prompt="以下は日本語の音声です。正確に文字起こしをしてください。句読点も適切に付けてください。"  # 日本語用プロンプト
                )

                transcribed_text = transcription.strip()
                bot_logger.info(f'文字起こし完了: {len(transcribed_text)} 文字')

                # 履歴に保存
                self.transcription_history.append({
                    "filename": original_filename,
                    "text": transcribed_text,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "text_length": len(transcribed_text)
                })

                # 履歴が20件を超えたら古いものを削除
                if len(self.transcription_history) > 20:
                    self.transcription_history = self.transcription_history[-20:]

                return transcribed_text, None

        except Exception as e:
            bot_logger.error(f'文字起こしエラー: {e}', exc_info=True)
            return None, f"❌ 文字起こし中にエラーが発生しました: {str(e)}"
        finally:
            # 一時ファイルを削除
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    bot_logger.debug(f'一時ファイル削除: {file_path}')
            except Exception as e:
                bot_logger.warning(f'一時ファイル削除失敗: {e}')

    def is_audio_file(self, filename):
        """音声ファイルかどうかを判定"""
        if not filename:
            return False

        file_ext = os.path.splitext(filename.lower())[1]
        return file_ext in SUPPORTED_AUDIO_FORMATS

    def get_stats(self):
        """統計情報を取得"""
        total_transcriptions = len(self.transcription_history)
        recent_transcriptions = [
            h for h in self.transcription_history
            if (datetime.datetime.now() - datetime.datetime.fromisoformat(h['timestamp'])).seconds < 3600
        ]

        total_text_length = sum(h.get('text_length', 0) for h in self.transcription_history)

        return {
            "total_transcriptions": total_transcriptions,
            "recent_transcriptions": len(recent_transcriptions),
            "total_text_length": total_text_length,
            "processing_count": len(self.processing_messages)
        }

# 音声文字起こし初期化
voice_transcriber = VoiceTranscriber(client) if client else None

@bot.event
async def on_ready():
    print(f'{bot.user} でログイン完了！')
    print('音声文字起こしボットが起動しました')
    print(f'対象チャンネル: {TARGET_CHANNEL_ID}')
    print(f'OpenAI API: {"✅ 設定済み" if client else "❌ 未設定"}')
    print(f'対応音声形式: {", ".join(SUPPORTED_AUDIO_FORMATS)}')
    bot_logger.info(f'ボット起動完了 - ユーザー: {bot.user}')

    # サーバー情報表示
    for guild in bot.guilds:
        print(f'サーバー: {guild.name} (ID: {guild.id})')
        bot_logger.info(f'接続サーバー: {guild.name} (ID: {guild.id})')
        target_channel = bot.get_channel(TARGET_CHANNEL_ID)
        if target_channel and target_channel.guild == guild:
            print(f'  ✅ 対象チャンネル発見: {target_channel.name}')
            bot_logger.info(f'対象チャンネル発見: {target_channel.name} (ID: {TARGET_CHANNEL_ID})')
        else:
            print(f'  ❓ 対象チャンネル未発見')
            bot_logger.warning(f'対象チャンネル未発見: ID {TARGET_CHANNEL_ID}')

    # 権限チェック
    if target_channel:
        permissions = target_channel.permissions_for(guild.me)
        print(f'  📝 権限チェック:')
        print(f'    - メッセージ読み取り: {permissions.read_messages}')
        print(f'    - メッセージ送信: {permissions.send_messages}')
        print(f'    - リアクション追加: {permissions.add_reactions}')
        print(f'    - リアクション閲覧: {permissions.read_message_history}')
        bot_logger.info(f'権限 - 読み取り:{permissions.read_messages}, 送信:{permissions.send_messages}, リアクション:{permissions.add_reactions}')

@bot.event
async def on_message(message):
    """音声ファイル付きメッセージを検出"""
    print(f'[MESSAGE] メッセージ検出: チャンネル {message.channel.id}, 送信者: {message.author}')
    bot_logger.debug(f'メッセージイベント - チャンネル: {message.channel.id}, 送信者: {message.author}')

    # ボット自身のメッセージは無視
    if message.author == bot.user:
        print(f'[MESSAGE] ボット自身のメッセージなのでスキップ')
        return

    # 対象チャンネル以外は無視
    if message.channel.id != TARGET_CHANNEL_ID:
        print(f'[MESSAGE] 対象外チャンネル ({message.channel.id}) なのでスキップ')
        return

    print(f'[MESSAGE] 対象チャンネルでのメッセージ - 添付ファイル数: {len(message.attachments)}')

    # 音声ファイルが添付されているかチェック
    audio_attachments = []
    for attachment in message.attachments:
        if voice_transcriber and voice_transcriber.is_audio_file(attachment.filename):
            audio_attachments.append(attachment)

    if audio_attachments:
        bot_logger.info(f'音声ファイル検出: {len(audio_attachments)}件 - ユーザー: {message.author}')

        # 案内メッセージを送信
        embed = discord.Embed(
            title="🎵 音声ファイルを検出しました",
            description=f"文字起こしを開始するには {TRANSCRIBE_EMOJI} リアクションを押してください",
            color=0x00aaff
        )

        for attachment in audio_attachments:
            embed.add_field(
                name="📁 ファイル名",
                value=f"`{attachment.filename}`",
                inline=False
            )
            embed.add_field(
                name="📏 ファイルサイズ",
                value=f"{attachment.size / 1024:.1f} KB",
                inline=True
            )

        embed.add_field(
            name="🔧 使用モデル",
            value="GPT-4o Transcribe",
            inline=True
        )
        embed.add_field(
            name="🌐 対応言語",
            value="日本語最適化",
            inline=True
        )

        guide_message = await message.reply(embed=embed)

        # 自動でリアクションを追加
        await guide_message.add_reaction(TRANSCRIBE_EMOJI)

    # コマンドも処理
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    """リアクション追加時の処理"""
    print(f'[REACTION] リアクション検出: {reaction.emoji} by {user} on {reaction.message.id}')
    print(f'[REACTION] チャンネル: {reaction.message.channel.id}, 絵文字タイプ: {type(reaction.emoji)}')
    bot_logger.info(f'リアクション追加: {reaction.emoji} by {user} on {reaction.message.id} in channel {reaction.message.channel.id}')

    # 全ての処理ステップをログ出力
    try:
        # ボット自身のリアクションは無視
        if user == bot.user:
            print(f'[REACTION] ボット自身のリアクションなのでスキップ')
            bot_logger.debug('ボット自身のリアクションなのでスキップ')
            return

        # 対象チャンネル以外は無視
        if reaction.message.channel.id != TARGET_CHANNEL_ID:
            print(f'[REACTION] 対象外チャンネル ({reaction.message.channel.id}) なのでスキップ')
            bot_logger.debug(f'対象外チャンネル ({reaction.message.channel.id}) なのでスキップ')
            return

        # 文字起こしリアクションかチェック
        print(f'[REACTION] リアクション絵文字チェック: "{str(reaction.emoji)}" vs "{TRANSCRIBE_EMOJI}"')
        if str(reaction.emoji) != TRANSCRIBE_EMOJI:
            print(f'[REACTION] 対象外リアクション ({str(reaction.emoji)}) なのでスキップ')
            bot_logger.debug(f'対象外リアクション ({str(reaction.emoji)}) なのでスキップ')
            return

        print(f'[REACTION] 🔄リアクション検出！処理開始')

        # 音声文字起こし機能が無効な場合
        if not voice_transcriber:
            await reaction.message.reply("❌ 音声文字起こし機能が利用できません。OPENAI_API_KEYを設定してください。")
            return

        # 既に処理中の場合
        if reaction.message.id in voice_transcriber.processing_messages:
            await reaction.message.reply("⏳ この音声ファイルは既に処理中です。少しお待ちください。")
            return

        # 元のメッセージ（音声ファイルが添付されたメッセージ）を取得
        original_message = None

        # リアクションされたメッセージが返信の場合、元メッセージを取得
        if reaction.message.reference and reaction.message.reference.message_id:
            try:
                original_message = await reaction.message.channel.fetch_message(reaction.message.reference.message_id)
            except discord.NotFound:
                await reaction.message.reply("❌ 元のメッセージが見つかりません。")
                return
        else:
            original_message = reaction.message

        # 音声ファイルをチェック
        audio_attachments = []
        for attachment in original_message.attachments:
            if voice_transcriber.is_audio_file(attachment.filename):
                audio_attachments.append(attachment)

        if not audio_attachments:
            await reaction.message.reply("❌ 音声ファイルが見つかりません。対応形式: " + ", ".join(SUPPORTED_AUDIO_FORMATS))
            return

        # 処理開始
        voice_transcriber.processing_messages.add(reaction.message.id)

        bot_logger.info(f'音声文字起こし処理開始: {len(audio_attachments)}件 - ユーザー: {user}')

        # 処理開始メッセージ
        processing_embed = discord.Embed(
            title="🔄 文字起こし処理中...",
            description="音声ファイルを分析しています。しばらくお待ちください。",
            color=0xffaa00
        )
        processing_message = await reaction.message.reply(embed=processing_embed)

        # 各音声ファイルを処理
        for i, attachment in enumerate(audio_attachments):
            try:
                # ファイルダウンロード
                temp_file_path, error = await voice_transcriber.download_audio_file(attachment)
                if error:
                    await processing_message.edit(content=error, embed=None)
                    continue

                # 進行状況更新
                progress_embed = discord.Embed(
                    title="🔄 文字起こし中...",
                    description=f"ファイル {i+1}/{len(audio_attachments)}: `{attachment.filename}`",
                    color=0xffaa00
                )
                await processing_message.edit(embed=progress_embed)

                # 文字起こし実行
                transcribed_text, error = await voice_transcriber.transcribe_audio(temp_file_path, attachment.filename)
                if error:
                    await processing_message.edit(content=error, embed=None)
                    continue

                # 結果を投稿
                result_embed = discord.Embed(
                    title="✅ 文字起こし完了",
                    color=0x00ff00
                )
                result_embed.add_field(name="📁 ファイル名", value=f"`{attachment.filename}`", inline=False)
                result_embed.add_field(name="📝 文字数", value=f"{len(transcribed_text)} 文字", inline=True)
                result_embed.add_field(name="🤖 使用モデル", value="GPT-4o Transcribe", inline=True)
                result_embed.add_field(name="⏰ 処理時間", value=f"{datetime.datetime.now().strftime('%H:%M:%S')}", inline=True)

                # 文字起こし結果（長い場合は分割）
                if len(transcribed_text) <= 4000:
                    result_embed.add_field(name="📋 文字起こし結果", value=f"```\n{transcribed_text}\n```", inline=False)
                    await processing_message.edit(embed=result_embed)
                else:
                    # 長いテキストは分割して送信
                    result_embed.add_field(name="📋 文字起こし結果", value="長いテキストのため、以下に分割して表示します。", inline=False)
                    await processing_message.edit(embed=result_embed)

                    # テキストを分割して送信
                    chunks = [transcribed_text[i:i+1900] for i in range(0, len(transcribed_text), 1900)]
                    for j, chunk in enumerate(chunks):
                        chunk_embed = discord.Embed(
                            title=f"📄 文字起こし結果 ({j+1}/{len(chunks)})",
                            description=f"```\n{chunk}\n```",
                            color=0x00ff00
                        )
                        await reaction.message.channel.send(embed=chunk_embed)

                        # 分割送信の間に短い間隔を空ける
                        if j < len(chunks) - 1:
                            await asyncio.sleep(1)

            except Exception as e:
                bot_logger.error(f'音声ファイル処理エラー ({attachment.filename}): {e}', exc_info=True)
                error_embed = discord.Embed(
                    title="❌ 処理エラー",
                    description=f"ファイル `{attachment.filename}` の処理中にエラーが発生しました。",
                    color=0xff0000
                )
                await processing_message.edit(embed=error_embed)

    except Exception as e:
        print(f'[ERROR] リアクション処理中にエラー: {e}')
        bot_logger.error(f'リアクション処理エラー: {e}', exc_info=True)
        try:
            await reaction.message.reply(f"❌ リアクション処理中にエラーが発生しました: {str(e)}")
        except:
            pass
    finally:
        # 処理完了
        if voice_transcriber and reaction.message.id in voice_transcriber.processing_messages:
            voice_transcriber.processing_messages.discard(reaction.message.id)
        bot_logger.info(f'音声文字起こし処理完了 - ユーザー: {user}')

@bot.command(name='voiceinfo')
async def voice_info(ctx):
    """音声文字起こし機能の情報を表示"""
    embed = discord.Embed(
        title="🎵 音声文字起こし機能",
        description="OpenAI GPT-4oを使用した高品質な音声文字起こし",
        color=0x00aaff
    )

    embed.add_field(name="🎯 対象チャンネル", value=f"<#{TARGET_CHANNEL_ID}>", inline=False)
    embed.add_field(name="🔧 使用方法", value=f"音声ファイルを投稿 → {TRANSCRIBE_EMOJI} リアクション", inline=False)
    embed.add_field(name="🤖 使用モデル", value="GPT-4o Transcribe", inline=True)
    embed.add_field(name="🌐 対応言語", value="日本語（最適化済み）", inline=True)
    embed.add_field(name="📁 対応形式", value=", ".join(SUPPORTED_AUDIO_FORMATS), inline=False)
    embed.add_field(name="📏 ファイル制限", value="25MB以下", inline=True)

    # 統計情報
    if voice_transcriber:
        stats = voice_transcriber.get_stats()
        embed.add_field(name="📊 利用統計",
                       value=f"総処理数: {stats['total_transcriptions']}\n直近1時間: {stats['recent_transcriptions']}\n処理中: {stats['processing_count']}",
                       inline=True)
        embed.add_field(name="✅ API状態", value="正常動作中", inline=True)
    else:
        embed.add_field(name="❌ API状態", value="未設定", inline=True)

    embed.add_field(name="⚠️ 注意事項",
                   value="• 処理には時間がかかる場合があります\n• API利用料が発生します\n• 音質により精度が変わります",
                   inline=False)

    await ctx.send(embed=embed)

@bot.command(name='voiceclear')
async def voice_clear(ctx):
    """音声文字起こし履歴をクリア"""
    if ctx.channel.id != TARGET_CHANNEL_ID:
        await ctx.send("❌ このコマンドは対象チャンネルでのみ使用できます。")
        return

    if not voice_transcriber:
        await ctx.send("❌ 音声文字起こし機能が利用できません。")
        return

    old_count = len(voice_transcriber.transcription_history)
    voice_transcriber.transcription_history = []

    embed = discord.Embed(
        title="🧹 履歴クリア完了",
        description=f"音声文字起こし履歴を削除しました",
        color=0x00ff00
    )
    embed.add_field(name="削除した履歴数", value=f"{old_count}件", inline=True)

    await ctx.send(embed=embed)

if __name__ == '__main__':
    # 環境変数チェック
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    print('=== 音声文字起こしDiscordボット起動中 ===')
    print(f'対象チャンネル: {TARGET_CHANNEL_ID}')
    print(f'Discord Token: {"✅ 設定済み" if DISCORD_TOKEN else "❌ 未設定"}')
    print(f'OpenAI API Key: {"✅ 設定済み" if OPENAI_API_KEY else "❌ 未設定"}')
    print(f'対応音声形式: {", ".join(SUPPORTED_AUDIO_FORMATS)}')

    if not DISCORD_TOKEN:
        print('❌ DISCORD_TOKENが設定されていません。')
        print('📝 手順:')
        print('   1. .envファイルを作成または確認')
        print('   2. DISCORD_TOKEN=your_token_here を設定')
        exit(1)

    if not OPENAI_API_KEY or OPENAI_API_KEY == 'your_openai_api_key_here':
        print('⚠️  OPENAI_API_KEYが未設定です。')
        print('📝 手順:')
        print('   1. https://platform.openai.com/ でAPIキーを取得')
        print('   2. .envファイルに OPENAI_API_KEY=sk-your-key-here を設定')
        print('   3. 音声文字起こし機能は無効になります。')
        print('🔄 現在は音声文字起こし機能無効でボットを起動します...')

    print('✅ 設定確認完了。ボットを起動します...')
    bot.run(DISCORD_TOKEN)