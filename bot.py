import discord
from discord.ext import commands, tasks
import os
import logging
import datetime
import asyncio
import json
import csv
from dotenv import load_dotenv

load_dotenv()

# ログレベルを最大に設定
logging.basicConfig(level=logging.DEBUG)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
discord_logger.addHandler(handler)

intents = discord.Intents.all()
# リアクションイベント用の明示的な設定を追加
intents.reactions = True
intents.guild_reactions = True
# または個別に設定する場合:
# intents = discord.Intents.default()
# intents.message_content = True
# intents.guilds = True
# intents.guild_messages = True
# intents.reactions = True
# intents.guild_reactions = True
# intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ログ収集クラス
class RoomLogCollector:
    def __init__(self, bot):
        self.bot = bot
        self.is_collecting = False
        
    async def collect_all_messages(self, channel):
        """チャンネルのすべてのメッセージを収集"""
        print(f'[LOG] {channel.name}のログ収集を開始します...')
        
        all_messages = []
        total_collected = 0
        
        try:
            # チャンネルの履歴を遡って取得
            async for message in channel.history(limit=None, oldest_first=True):
                # メッセージ情報を構造化
                message_data = {
                    'timestamp': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'author': str(message.author),
                    'author_id': message.author.id,
                    'content': message.content,
                    'message_id': message.id,
                    'attachments': [att.url for att in message.attachments],
                    'reactions': [f"{reaction.emoji}({reaction.count})" for reaction in message.reactions]
                }
                all_messages.append(message_data)
                total_collected += 1
                
                # 100件ごとに2秒スリープ
                if total_collected % 100 == 0:
                    print(f'[LOG] {total_collected}件取得完了。2秒休憩中...')
                    await asyncio.sleep(2)
                    
        except Exception as e:
            print(f'[ERROR] メッセージ収集中にエラー: {e}')
            
        print(f'[LOG] 収集完了！総メッセージ数: {total_collected}件')
        return all_messages
    
    def save_to_file(self, messages, channel_name):
        """メッセージをテキストファイルに保存"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{channel_name}_log_{timestamp}.txt"
        # 現在のディレクトリに保存
        filepath = os.path.join(os.getcwd(), filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== {channel_name} チャンネルログ ===\n")
                f.write(f"収集日時: {datetime.datetime.now().strftime('%Y年%m月%d日 %H時%M分%S秒')}\n")
                f.write(f"総メッセージ数: {len(messages)}件\n")
                f.write("=" * 50 + "\n\n")
                
                for msg in messages:
                    f.write(f"[{msg['timestamp']}] {msg['author']}\n")
                    if msg['content']:
                        f.write(f"内容: {msg['content']}\n")
                    if msg['attachments']:
                        f.write(f"添付ファイル: {', '.join(msg['attachments'])}\n")
                    if msg['reactions']:
                        f.write(f"リアクション: {', '.join(msg['reactions'])}\n")
                    f.write(f"メッセージID: {msg['message_id']}\n")
                    f.write("-" * 30 + "\n\n")
                    
            print(f'[LOG] ファイル保存完了: {filepath}')
            return filepath
            
        except Exception as e:
            print(f'[ERROR] ファイル保存中にエラー: {e}')
            return None

# ログコレクター初期化
log_collector = RoomLogCollector(bot)

# リアルタイムルームログクラス
class RealtimeRoomLogger:
    def __init__(self, room_id):
        self.room_id = room_id
        self.log_dir = os.getcwd()  # Railwayでは/app
        self.log_file = os.path.join(self.log_dir, f"realtime_room_{room_id}_log.txt")
        self.metadata_file = os.path.join(self.log_dir, f"realtime_room_{room_id}_metadata.json")
        self.ensure_log_files()
        
    def ensure_log_files(self):
        """ログファイルとメタデータファイルの存在確認・作成"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Room {self.room_id} リアルタイムログ ===\n")
                f.write(f"ログ開始: {datetime.datetime.now().strftime('%Y年%m月%d日 %H時%M分%S秒')}\n")
                f.write("=" * 60 + "\n\n")
                
        if not os.path.exists(self.metadata_file):
            metadata = {
                "room_id": self.room_id,
                "log_start_time": datetime.datetime.now().isoformat(),
                "message_count": 0,
                "last_updated": datetime.datetime.now().isoformat()
            }
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def append_message(self, message):
        """新しいメッセージをログファイルに追記"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {message.author}\n")
                
                if message.content:
                    f.write(f"内容: {message.content}\n")
                if message.attachments:
                    attachments = [att.url for att in message.attachments]
                    f.write(f"添付ファイル: {', '.join(attachments)}\n")
                if message.reactions:
                    reactions = [f"{reaction.emoji}({reaction.count})" for reaction in message.reactions]
                    f.write(f"リアクション: {', '.join(reactions)}\n")
                    
                f.write(f"メッセージID: {message.id}\n")
                f.write("-" * 40 + "\n\n")
                
            self.update_metadata()
            print(f'[REALTIME] メッセージをリアルタイムログに追記: {message.author} - {message.content[:50]}...')
            
        except Exception as e:
            print(f'[ERROR] リアルタイムログ追記中にエラー: {e}')
    
    def update_metadata(self):
        """メタデータファイルの更新"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {
                    "room_id": self.room_id,
                    "log_start_time": datetime.datetime.now().isoformat(),
                    "message_count": 0
                }
                
            metadata["message_count"] += 1
            metadata["last_updated"] = datetime.datetime.now().isoformat()
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f'[ERROR] リアルタイムメタデータ更新中にエラー: {e}')
    
    def get_log_info(self):
        """ログファイルの統計情報を取得"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    
                file_size = os.path.getsize(self.log_file) if os.path.exists(self.log_file) else 0
                file_size_mb = file_size / (1024 * 1024)
                
                return {
                    "message_count": metadata.get("message_count", 0),
                    "log_start_time": metadata.get("log_start_time"),
                    "last_updated": metadata.get("last_updated"),
                    "file_size": file_size,
                    "file_size_mb": file_size_mb,
                    "file_path": self.log_file
                }
            else:
                return None
                
        except Exception as e:
            print(f'[ERROR] リアルタイムログ情報取得中にエラー: {e}')
            return None

# room1用リアルタイムロガー初期化
REALTIME_TARGET_ROOM = 1418511738046779393
realtime_logger = RealtimeRoomLogger(REALTIME_TARGET_ROOM)

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
        print(f'アクセス可能なチャンネル数: {len(guild.text_channels)}')
        print('チャンネル一覧:')
        for channel in guild.text_channels:
            print(f'  - {channel.name} (ID: {channel.id})')
            # すべてのチャンネルで機能が利用可能
            print(f'    ✅ 利用可能（メッセージ・リアクション・ログ収集）')
    print('Intents設定:')
    print(f'message_content: {bot.intents.message_content}')
    print(f'guilds: {bot.intents.guilds}')
    print(f'guild_messages: {bot.intents.guild_messages}')
    print(f'reactions: {bot.intents.reactions}')
    print(f'guild_reactions: {bot.intents.guild_reactions}')
    
    # 定期投稿タスクを開始（現在停止中）
    # if not periodic_greeting.is_running():
    #     periodic_greeting.start()
    #     print('[DEBUG] 定期投稿タスクを開始しました')
    print('[DEBUG] 定期投稿タスクは停止中です')

# 定期投稿タスク（10秒ごと）
@tasks.loop(seconds=10)
async def periodic_greeting():
    """10秒ごとに指定チャンネルに「おはようございます」を投稿"""
    GREETING_CHANNEL_ID = 1418511738046779393
    channel = bot.get_channel(GREETING_CHANNEL_ID)
    
    if channel:
        # 実行環境に応じてメッセージを変える
        if os.path.exists('.env'):
            message = 'おはようございます (ローカルから) 🏠'
        else:
            message = 'おはようございます (Railwayから) ☁️'
        
        try:
            await channel.send(message)
            print(f'[DEBUG] 定期投稿成功: {message}')
        except Exception as e:
            print(f'[DEBUG] 定期投稿エラー: {e}')
    else:
        print(f'[DEBUG] チャンネル {GREETING_CHANNEL_ID} が見つかりません')

@periodic_greeting.before_loop
async def before_periodic_greeting():
    """定期投稿開始前にボットの準備を待つ"""
    await bot.wait_until_ready()

@bot.event
async def on_message(message):
    print(f'[DEBUG] メッセージイベント発生')
    print(f'[DEBUG] 送信者: {message.author} (ID: {message.author.id})')
    print(f'[DEBUG] ボット自身: {bot.user} (ID: {bot.user.id})')
    print(f'[DEBUG] チャンネル: {message.channel} (ID: {message.channel.id})')
    print(f'[DEBUG] メッセージ内容: "{message.content}"')
    print(f'[DEBUG] メッセージタイプ: {message.type}')

    if message.author == bot.user:
        print('[DEBUG] ボット自身のメッセージなのでスキップ')
        return

    # すべてのチャンネルで反応（制限なし）
    print(f'[DEBUG] チャンネル {message.channel.name} (ID: {message.channel.id}) でメッセージ処理')
    
    # リアルタイムログ記録（room1のみ）
    if message.channel.id == REALTIME_TARGET_ROOM:
        realtime_logger.append_message(message)
        print(f'[REALTIME] room1メッセージをリアルタイムログに記録')

    # メンション、リプライ、または通常のメッセージで反応
    is_mentioned = bot.user in message.mentions
    is_reply = message.reference and message.reference.message_id
    has_content = bool(message.content.strip())

    print(f'[DEBUG] メンション確認: {is_mentioned}')
    print(f'[DEBUG] リプライ確認: {is_reply}')
    print(f'[DEBUG] メッセージ内容あり: {has_content}')

    if has_content and not message.content.startswith('!'):
        # メッセージをオウム返しする
        original_message = message.content

        # メンションを除去してクリーンなメッセージを取得
        clean_message = original_message
        for mention in message.mentions:
            clean_message = clean_message.replace(f'<@{mention.id}>', '').strip()

        # 実行環境の情報を追加
        if os.path.exists('.env'):
            response = f'{clean_message} (ローカルから) 🏠'
        else:
            response = f'{clean_message} (Railwayから) ☁️'

        print(f'[DEBUG] 条件一致、オウム返し: {response}')
        try:
            await message.channel.send(response)
            print('[DEBUG] 返信送信成功')
        except Exception as e:
            print(f'[DEBUG] 返信送信エラー: {e}')
    else:
        print('[DEBUG] 条件不一致、返信しません（メッセージ内容なしまたはコマンド）')

    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    print(f'[DEBUG] リアクションイベント発生')
    print(f'[DEBUG] リアクション絵文字: {reaction.emoji}')
    print(f'[DEBUG] リアクションしたユーザー: {user} (ID: {user.id})')
    print(f'[DEBUG] メッセージチャンネル: {reaction.message.channel.name} (ID: {reaction.message.channel.id})')
    print(f'[DEBUG] メッセージ内容: "{reaction.message.content}"')

    # ボット自身のリアクションは無視
    if user == bot.user:
        print('[DEBUG] ボット自身のリアクションなのでスキップ')
        return

    # すべてのチャンネルで反応（制限なし）
    print(f'[DEBUG] チャンネル {reaction.message.channel.name} (ID: {reaction.message.channel.id}) でリアクション処理')

    # グッドマーク（👍）リアクションに反応（肌色のバリエーションも含む）
    thumbs_up_emojis = ['👍', '👍🏻', '👍🏼', '👍🏽', '👍🏾', '👍🏿']
    if str(reaction.emoji) in thumbs_up_emojis:
        # 実行環境に応じて返信を変える
        if os.path.exists('.env'):
            response = 'グッドマークが押されたよ！ (ローカルから) 🏠'
        else:
            response = 'グッドマークが押されたよ！ (Railwayから) ☁️'

        print(f'[DEBUG] グッドマーク検知、{response}と返信します')
        try:
            await reaction.message.channel.send(response)
            print('[DEBUG] リアクション返信送信成功')
        except Exception as e:
            print(f'[DEBUG] リアクション返信送信エラー: {e}')
    else:
        print(f'[DEBUG] グッドマーク以外のリアクション ({reaction.emoji}) なので無視')

@bot.event
async def on_raw_reaction_add(payload):
    """
    過去のメッセージ（キャッシュにないメッセージ）へのリアクションにも対応するためのrawイベントハンドラー
    """
    print(f'[DEBUG] RAWリアクションイベント発生')
    print(f'[DEBUG] チャンネルID: {payload.channel_id}')
    print(f'[DEBUG] メッセージID: {payload.message_id}')
    print(f'[DEBUG] ユーザーID: {payload.user_id}')
    print(f'[DEBUG] 絵文字: {payload.emoji}')
    
    # チャンネル名も取得して表示
    channel = bot.get_channel(payload.channel_id)
    if channel:
        print(f'[DEBUG] チャンネル名: {channel.name}')
    else:
        print('[DEBUG] チャンネル情報を取得できませんでした')

    # ボット自身のリアクションは無視
    if payload.user_id == bot.user.id:
        print('[DEBUG] ボット自身のリアクションなのでスキップ')
        return

    # すべてのチャンネルで反応（制限なし）
    print(f'[DEBUG] チャンネル {channel.name if channel else "不明"} (ID: {payload.channel_id}) でRAWリアクション処理')

    # リアクション種類による処理分岐
    emoji_str = str(payload.emoji)
    channel = bot.get_channel(payload.channel_id)
    if not channel:
        print(f'[DEBUG] チャンネル {payload.channel_id} が見つからない')
        return
    
    # グッドマーク（👍）リアクション - ログ収集機能
    thumbs_up_emojis = ['👍', '👍🏻', '👍🏼', '👍🏽', '👍🏾', '👍🏿']
    if emoji_str in thumbs_up_emojis:
        print(f'[DEBUG] RAWイベントでログ収集リアクション検知: {emoji_str}')
        
        # 既に収集中の場合はスキップ
        if log_collector.is_collecting:
            await channel.send("📋 現在他のチャンネルのログを収集中です。しばらくお待ちください。")
            return
        
        # ログ収集開始
        log_collector.is_collecting = True
        
        try:
            # 収集開始メッセージ
            await channel.send(f"📋 **{channel.name}** のログ収集を開始します！\n⏳ 時間がかかる場合があります。お待ちください...")
            
            # メッセージ収集
            messages = await log_collector.collect_all_messages(channel)
            
            if not messages:
                await channel.send("❌ メッセージが見つかりませんでした。")
                return
                
            # ファイル保存
            filepath = log_collector.save_to_file(messages, channel.name)
            
            if filepath and os.path.exists(filepath):
                # Discordにファイルをアップロード
                file_size = os.path.getsize(filepath)
                file_size_mb = file_size / (1024 * 1024)
                
                if file_size_mb > 8:  # Discordの8MB制限
                    await channel.send(f"⚠️ ファイルサイズが大きすぎます ({file_size_mb:.1f}MB)。\nファイルはローカルに保存されました: `{filepath}`")
                else:
                    # ファイルをDiscordにアップロード
                    with open(filepath, 'rb') as f:
                        discord_file = discord.File(f, filename=os.path.basename(filepath))
                        embed = discord.Embed(
                            title="📋 ログ収集完了！", 
                            description=f"**{channel.name}** のログを収集しました",
                            color=0x00ff00
                        )
                        embed.add_field(name="📊 メッセージ数", value=f"{len(messages):,}件", inline=True)
                        embed.add_field(name="📁 ファイルサイズ", value=f"{file_size_mb:.2f}MB", inline=True)
                        embed.add_field(name="⏰ 収集日時", value=datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'), inline=True)
                        
                        await channel.send(embed=embed, file=discord_file)
            else:
                await channel.send("❌ ファイルの保存に失敗しました。")
                
        except Exception as e:
            print(f'[ERROR] ログ収集処理中にエラー: {e}')
            await channel.send(f"❌ エラーが発生しました: {str(e)}")
            
        finally:
            log_collector.is_collecting = False
            
    # ハートマーク（❤️）リアクション - リアルタイムログダウンロード
    elif str(payload.emoji) in ['❤️', '💖', '💕', '💗', '💓', '💝', '🧡', '💛', '💚', '💙', '💜', '🤍', '🖤', '🤎']:
        # room1でのみ動作
        if payload.channel_id == REALTIME_TARGET_ROOM:
            print(f'[DEBUG] RAWイベントでハートマーク検知: {emoji_str}（リアルタイムログダウンロード）')
            
            try:
                # ログ情報取得
                log_info = realtime_logger.get_log_info()
                if not log_info:
                    await channel.send("❌ リアルタイムログ情報を取得できませんでした。")
                    return
                    
                if not os.path.exists(realtime_logger.log_file):
                    await channel.send("❌ リアルタイムログファイルが見つかりません。まずroom1でメッセージを投稿してください。")
                    return
                    
                # ファイルサイズチェック
                if log_info["file_size_mb"] > 8:
                    await channel.send(f"⚠️ リアルタイムログファイルが大きすぎます ({log_info['file_size_mb']:.1f}MB)。")
                    return
                    
                # Discordにアップロード
                with open(realtime_logger.log_file, 'rb') as f:
                    discord_file = discord.File(f, filename=f"realtime_room_{REALTIME_TARGET_ROOM}_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                    
                    embed = discord.Embed(
                        title="❤️ リアルタイムルームログ",
                        description=f"**{channel.name}** のリアルタイムログファイル",
                        color=0xff69b4
                    )
                    
                    # ログ開始時間の表示
                    if log_info["log_start_time"]:
                        start_time = datetime.datetime.fromisoformat(log_info["log_start_time"])
                        embed.add_field(
                            name="📅 ログ開始", 
                            value=start_time.strftime('%Y/%m/%d %H:%M:%S'), 
                            inline=True
                        )
                    
                    # 最終更新時間の表示
                    if log_info["last_updated"]:
                        last_updated = datetime.datetime.fromisoformat(log_info["last_updated"])
                        embed.add_field(
                            name="🔄 最終更新", 
                            value=last_updated.strftime('%Y/%m/%d %H:%M:%S'), 
                            inline=True
                        )
                        
                    embed.add_field(name="📊 メッセージ数", value=f"{log_info['message_count']:,}件", inline=True)
                    embed.add_field(name="📁 ファイルサイズ", value=f"{log_info['file_size_mb']:.2f}MB", inline=True)
                    embed.add_field(name="⏰ ダウンロード時刻", value=datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'), inline=True)
                    embed.add_field(name="💡 説明", value="room1で投稿されたメッセージをリアルタイムで記録", inline=False)
                    
                    await channel.send("❤️ **リアルタイムログファイルをアップロードします！**", embed=embed, file=discord_file)
                    print(f'[LOG] リアルタイムログファイルアップロード完了')
                    
            except Exception as e:
                print(f'[ERROR] リアルタイムログファイルアップロード中にエラー: {e}')
                await channel.send(f"❌ リアルタイムログファイルのアップロードに失敗しました: {str(e)}")
        else:
            print(f'[DEBUG] room1以外でのハートマークなので無視: {payload.channel_id}')
            
    # 目玉マーク（👁️）リアクション - サーバーメンバー一覧取得
    elif str(payload.emoji) in ['👁️', '👀', '🔍', '👁‍🗨']:
        print(f'[DEBUG] RAWイベントで目玉マーク検知: {emoji_str}（メンバー一覧取得）')
        
        try:
            # サーバー（ギルド）取得
            guild = channel.guild if channel else None
            if not guild:
                print(f'[ERROR] サーバー情報が取得できません')
                return
                
            # メンバー一覧取得開始メッセージ
            await channel.send(f"👁️ **{guild.name}** のメンバー情報収集を開始します！\n"
                              f"⏳ メンバー数が多い場合は時間がかかります。お待ちください...\n"
                              f"📊 予想メンバー数: 約{guild.member_count}人")
            
            # メンバー情報収集
            members_data = []
            total_members = 0
            
            async for member in guild.fetch_members(limit=None):
                member_data = {
                    'username': str(member),
                    'display_name': member.display_name,
                    'user_id': member.id,
                    'joined_at': member.joined_at.strftime('%Y-%m-%d %H:%M:%S') if member.joined_at else 'Unknown',
                    'created_at': member.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': str(member.status),
                    'is_bot': member.bot,
                    'roles': [role.name for role in member.roles if role.name != '@everyone'],
                    'top_role': member.top_role.name if member.top_role.name != '@everyone' else 'None',
                    'premium_since': member.premium_since.strftime('%Y-%m-%d %H:%M:%S') if member.premium_since else 'Not boosting'
                }
                members_data.append(member_data)
                total_members += 1
                
                # 100人ごとに1秒待機（レート制限対策）
                if total_members % 100 == 0:
                    await asyncio.sleep(1)
            
            # ファイル作成（テキストファイル）
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            txt_filename = f"guild_{guild.id}_members_{timestamp}.txt"
            txt_filepath = os.path.join(os.getcwd(), txt_filename)
            
            # CSVファイル作成
            csv_filename = f"guild_{guild.id}_members_{timestamp}.csv"
            csv_filepath = os.path.join(os.getcwd(), csv_filename)
            
            # テキストファイル出力
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== {guild.name} サーバーメンバー一覧 ===\n")
                f.write(f"取得日時: {datetime.datetime.now().strftime('%Y年%m月%d日 %H時%M分%S秒')}\n")
                f.write(f"総メンバー数: {len(members_data)}人\n")
                f.write(f"サーバーID: {guild.id}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, member in enumerate(members_data, 1):
                    f.write(f"【{i:04d}】 {member['username']}\n")
                    f.write(f"  表示名: {member['display_name']}\n")
                    f.write(f"  ユーザーID: {member['user_id']}\n")
                    f.write(f"  参加日: {member['joined_at']}\n")
                    f.write(f"  ステータス: {member['status']}\n")
                    f.write(f"  BOT: {'はい' if member['is_bot'] else 'いいえ'}\n")
                    f.write(f"  最高ロール: {member['top_role']}\n")
                    if member['roles']:
                        f.write(f"  ロール: {', '.join(member['roles'])}\n")
                    f.write(f"  ブースト: {member['premium_since']}\n")
                    f.write("-" * 60 + "\n\n")
                
                # 統計情報
                bot_count = sum(1 for member in members_data if member['is_bot'])
                human_count = len(members_data) - bot_count
                boosters = sum(1 for member in members_data if member['premium_since'] != 'Not boosting')
                
                f.write("=== 統計情報 ===\n")
                f.write(f"総メンバー数: {len(members_data)}人\n")
                f.write(f"人間: {human_count}人\n")
                f.write(f"BOT: {bot_count}人\n")
                f.write(f"ブースター: {boosters}人\n")
            
            # CSVファイル出力
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'No', 'ユーザー名', '表示名', 'ユーザーID', 
                    'アカウント作成日', 'サーバー参加日', 'ステータス', 
                    'BOT', '最高ロール', 'ロール数', '全ロール', 
                    'ブースト状況', 'ブースト開始日'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # ヘッダー行
                writer.writeheader()
                
                # データ行
                for i, member in enumerate(members_data, 1):
                    writer.writerow({
                        'No': i,
                        'ユーザー名': member['username'],
                        '表示名': member['display_name'],
                        'ユーザーID': member['user_id'],
                        'アカウント作成日': member['created_at'],
                        'サーバー参加日': member['joined_at'],
                        'ステータス': member['status'],
                        'BOT': 'はい' if member['is_bot'] else 'いいえ',
                        '最高ロール': member['top_role'],
                        'ロール数': len(member['roles']),
                        '全ロール': ', '.join(member['roles']) if member['roles'] else 'なし',
                        'ブースト状況': 'あり' if member['premium_since'] != 'Not boosting' else 'なし',
                        'ブースト開始日': member['premium_since'] if member['premium_since'] != 'Not boosting' else ''
                    })
            
            # ファイルサイズ確認・アップロード
            txt_file_size = os.path.getsize(txt_filepath)
            csv_file_size = os.path.getsize(csv_filepath)
            total_size_mb = (txt_file_size + csv_file_size) / (1024 * 1024)
            txt_size_mb = txt_file_size / (1024 * 1024)
            csv_size_mb = csv_file_size / (1024 * 1024)
            
            if total_size_mb > 8:
                await channel.send(f"⚠️ ファイルサイズが大きすぎます (合計{total_size_mb:.1f}MB)。\n"
                                 f"TXT: {txt_size_mb:.1f}MB, CSV: {csv_size_mb:.1f}MB")
            else:
                # 複数ファイルをアップロード
                files_to_upload = []
                
                # テキストファイル
                with open(txt_filepath, 'rb') as f:
                    files_to_upload.append(discord.File(f, filename=os.path.basename(txt_filepath)))
                
                # CSVファイル
                with open(csv_filepath, 'rb') as f:
                    files_to_upload.append(discord.File(f, filename=os.path.basename(csv_filepath)))
                
                embed = discord.Embed(
                    title="👁️ サーバーメンバー一覧",
                    description=f"**{guild.name}** のメンバー情報",
                    color=0x00bfff
                )
                
                bot_count = sum(1 for member in members_data if member['is_bot'])
                human_count = len(members_data) - bot_count
                boosters = sum(1 for member in members_data if member['premium_since'] != 'Not boosting')
                
                embed.add_field(name="📊 総メンバー数", value=f"{len(members_data):,}人", inline=True)
                embed.add_field(name="👥 人間", value=f"{human_count:,}人", inline=True)
                embed.add_field(name="🤖 BOT", value=f"{bot_count:,}人", inline=True)
                embed.add_field(name="💎 ブースター", value=f"{boosters:,}人", inline=True)
                embed.add_field(name="📁 TXTサイズ", value=f"{txt_size_mb:.2f}MB", inline=True)
                embed.add_field(name="📊 CSVサイズ", value=f"{csv_size_mb:.2f}MB", inline=True)
                embed.add_field(name="⏰ 取得日時", value=datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'), inline=False)
                embed.add_field(name="📋 ファイル形式", value="• TXT: 詳細情報＋統計\n• CSV: 表形式（Excel対応）", inline=False)
                
                await channel.send("👁️ **サーバーメンバー一覧をアップロードします！**", embed=embed, files=files_to_upload)
                print(f'[LOG] メンバー一覧ファイル（TXT+CSV）アップロード完了')
                    
        except Exception as e:
            print(f'[ERROR] メンバー一覧取得中にエラー: {e}')
            await channel.send(f"❌ メンバー一覧取得エラー: {str(e)}")
            
    else:
        print(f'[DEBUG] RAWイベント: 対象外のリアクション ({emoji_str}) なので無視')

@bot.command(name='loginfo')
async def log_info(ctx):
    """ログ収集機能の情報を表示"""
    embed = discord.Embed(
        title="🤖 ボット機能一覧",
        description="すべてのチャンネルで利用可能な機能",
        color=0x0099ff
    )
    embed.add_field(name="💬 メッセージ機能", value="• ボットにメッセージを送る → オウム返し\n• room1でのメッセージ → リアルタイムログに記録", inline=False)
    embed.add_field(name="👍 サムズアップ機能", value="• 任意のメッセージに👍リアクション → そのチャンネルの全ログ一括収集", inline=False)
    embed.add_field(name="❤️ ハートマーク機能", value="• room1で❤️リアクション → リアルタイム蓄積ログをダウンロード", inline=False)
    embed.add_field(name="👁️ 目玉マーク機能", value="• 任意のメッセージに👁️リアクション → サーバーメンバー一覧を取得", inline=False)
    embed.add_field(name="📊 収集内容", value="• ログ: 投稿日時・投稿者・メッセージ内容\n• メンバー: ユーザー情報・ロール・統計", inline=False)
    embed.add_field(name="⚙️ 仕様", value="• 全機能: 8MB以下でDiscordアップロード\n• メンバー数が多いと時間がかかります", inline=False)
    
    await ctx.send(embed=embed)

if __name__ == '__main__':
    print('=== Discord Bot 起動中 ===')
    print(f'現在のディレクトリ: {os.getcwd()}')
    print(f'.envファイルの存在: {os.path.exists(".env")}')
    TOKEN = os.getenv('DISCORD_TOKEN')
    print(f'トークンの確認: {TOKEN[:10] if TOKEN else "None"}...')
    if TOKEN:
        print('ボットを起動します...')
        bot.run(TOKEN)
    else:
        print('エラー: DISCORD_TOKENが設定されていません。.envファイルを確認してください。')