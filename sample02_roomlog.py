import discord
from discord.ext import commands
import os
import datetime
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

# リアルタイムルームログ機能付きDiscordボット
intents = discord.Intents.all()
intents.reactions = True
intents.guild_reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 対象ルームID（指定されたroom1）
TARGET_ROOM_ID = 1418511738046779393

class RoomLogger:
    def __init__(self, room_id):
        self.room_id = room_id
        self.log_dir = "/Users/suguruhirayama/Desktop/AI実験室/Discordbot"
        self.log_file = os.path.join(self.log_dir, f"room_{room_id}_log.txt")
        self.metadata_file = os.path.join(self.log_dir, f"room_{room_id}_metadata.json")
        self.ensure_log_files()
        
    def ensure_log_files(self):
        """ログファイルとメタデータファイルの存在確認・作成"""
        # ログファイル作成
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Room {self.room_id} リアルタイムログ ===\n")
                f.write(f"ログ開始: {datetime.datetime.now().strftime('%Y年%m月%d日 %H時%M分%S秒')}\n")
                f.write("=" * 60 + "\n\n")
                
        # メタデータファイル作成
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
            # メインログファイルに追記
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
                
            # メタデータ更新
            self.update_metadata()
            
            print(f'[LOG] メッセージをログに追記: {message.author} - {message.content[:50]}...')
            
        except Exception as e:
            print(f'[ERROR] ログ追記中にエラー: {e}')
    
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
            print(f'[ERROR] メタデータ更新中にエラー: {e}')
    
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
            print(f'[ERROR] ログ情報取得中にエラー: {e}')
            return None

# ルームロガー初期化
room_logger = RoomLogger(TARGET_ROOM_ID)

@bot.event
async def on_ready():
    print(f'{bot.user} でログイン完了！')
    print('リアルタイムルームログボットが起動しました')
    print(f'対象ルーム: {TARGET_ROOM_ID}')
    print(f'ログファイル: {room_logger.log_file}')
    
    # サーバー情報表示
    for guild in bot.guilds:
        print(f'サーバー: {guild.name} (ID: {guild.id})')
        target_channel = bot.get_channel(TARGET_ROOM_ID)
        if target_channel:
            print(f'  ✅ 対象チャンネル発見: {target_channel.name}')
        else:
            print(f'  ❌ 対象チャンネル未発見: {TARGET_ROOM_ID}')

@bot.event
async def on_message(message):
    """メッセージが投稿されるたびにログに記録"""
    print(f'[DEBUG] メッセージイベント: {message.channel.id} vs {TARGET_ROOM_ID}')
    
    # ボット自身のメッセージは無視
    if message.author == bot.user:
        return
    
    # 対象ルームのメッセージのみ記録
    if message.channel.id == TARGET_ROOM_ID:
        print(f'[LOG] 対象ルームのメッセージを記録開始')
        room_logger.append_message(message)
        
    # コマンドも処理
    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    """グッドマークが押されたらログファイルをアップロード"""
    print(f'[DEBUG] リアクションイベント: {payload.emoji} in {payload.channel_id}')
    
    # ボット自身のリアクションは無視
    if payload.user_id == bot.user.id:
        return
    
    # 対象ルームでのみ動作
    if payload.channel_id != TARGET_ROOM_ID:
        print(f'[DEBUG] 対象ルーム外のリアクション: {payload.channel_id}')
        return
        
    # グッドマーク（👍）リアクションのみ
    thumbs_up_emojis = ['👍', '👍🏻', '👍🏼', '👍🏽', '👍🏾', '👍🏿']
    if str(payload.emoji) not in thumbs_up_emojis:
        print(f'[DEBUG] 対象外のリアクション: {payload.emoji}')
        return
        
    # チャンネル取得
    channel = bot.get_channel(payload.channel_id)
    if not channel:
        print(f'[ERROR] チャンネル {payload.channel_id} が見つかりません')
        return
        
    print(f'[LOG] ハートマーク検知！リアルタイムログファイルをアップロード開始')
    
    try:
        # ログ情報取得
        log_info = room_logger.get_log_info()
        if not log_info:
            await channel.send("❌ ログ情報を取得できませんでした。")
            return
            
        if not os.path.exists(room_logger.log_file):
            await channel.send("❌ ログファイルが見つかりません。")
            return
            
        # ファイルサイズチェック
        if log_info["file_size_mb"] > 8:
            await channel.send(f"⚠️ ログファイルが大きすぎます ({log_info['file_size_mb']:.1f}MB)。\n"
                             f"ファイルパス: `{log_info['file_path']}`")
            return
            
        # Discordにアップロード
        with open(room_logger.log_file, 'rb') as f:
            discord_file = discord.File(f, filename=f"room_{TARGET_ROOM_ID}_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            
            embed = discord.Embed(
                title="📋 リアルタイムルームログ",
                description=f"**{channel.name}** のリアルタイムログファイル",
                color=0x00ff00
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
            
            await channel.send("📋 **リアルタイムログファイルをアップロードします！**", embed=embed, file=discord_file)
            print(f'[LOG] ログファイルアップロード完了')
            
    except Exception as e:
        print(f'[ERROR] ログファイルアップロード中にエラー: {e}')
        await channel.send(f"❌ ログファイルのアップロードに失敗しました: {str(e)}")

@bot.command(name='logstatus')
async def log_status(ctx):
    """現在のログ状況を表示"""
    if ctx.channel.id != TARGET_ROOM_ID:
        await ctx.send(f"❌ このコマンドは対象ルーム (ID: {TARGET_ROOM_ID}) でのみ使用できます。")
        return
        
    log_info = room_logger.get_log_info()
    if not log_info:
        await ctx.send("❌ ログ情報を取得できませんでした。")
        return
        
    embed = discord.Embed(
        title="📊 リアルタイムログ状況",
        description="現在のログ収集状況",
        color=0x0099ff
    )
    
    embed.add_field(name="📋 対象ルーム", value=f"<#{TARGET_ROOM_ID}>", inline=False)
    embed.add_field(name="📊 累計メッセージ数", value=f"{log_info['message_count']:,}件", inline=True)
    embed.add_field(name="📁 ログファイルサイズ", value=f"{log_info['file_size_mb']:.2f}MB", inline=True)
    
    if log_info["log_start_time"]:
        start_time = datetime.datetime.fromisoformat(log_info["log_start_time"])
        embed.add_field(name="📅 ログ開始時刻", value=start_time.strftime('%Y/%m/%d %H:%M:%S'), inline=True)
    
    if log_info["last_updated"]:
        last_updated = datetime.datetime.fromisoformat(log_info["last_updated"])
        embed.add_field(name="🔄 最終更新", value=last_updated.strftime('%Y/%m/%d %H:%M:%S'), inline=True)
        
    embed.add_field(name="💡 使用方法", value="任意のメッセージに ❤️ を付けるとログファイルをダウンロード", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='roomloginfo')
async def roomlog_info(ctx):
    """リアルタイムルームログ機能の説明"""
    embed = discord.Embed(
        title="🤖 リアルタイムルームログボット",
        description="指定ルームのメッセージをリアルタイムで記録",
        color=0x0099ff
    )
    
    embed.add_field(name="📋 対象ルーム", value=f"<#{TARGET_ROOM_ID}>", inline=False)
    embed.add_field(name="⚡ リアルタイム記録", value="メッセージ投稿と同時にログファイルに自動追記", inline=False)
    embed.add_field(name="❤️ ログダウンロード", value="任意のメッセージに❤️リアクション → ログファイルをアップロード", inline=False)
    embed.add_field(name="📊 コマンド", value="`!logstatus` - 現在のログ状況\n`!roomloginfo` - この説明", inline=False)
    embed.add_field(name="📁 ファイル形式", value="テキストファイル（UTF-8）\n8MB以下でDiscordにアップロード", inline=False)
    
    await ctx.send(embed=embed)

if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_TOKEN')
    if TOKEN:
        print('=== リアルタイムルームログボット起動中 ===')
        print(f'対象ルーム: {TARGET_ROOM_ID}')
        print(f'ログディレクトリ: {room_logger.log_dir}')
        bot.run(TOKEN)
    else:
        print('エラー: DISCORD_TOKENが設定されていません')