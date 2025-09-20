import discord
from discord.ext import commands
import asyncio
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

# ログ収集機能付きDiscordボット
intents = discord.Intents.all()
intents.reactions = True
intents.guild_reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

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
        filepath = os.path.join("/Users/suguruhirayama/Desktop/AI実験室/Discordbot/sample01_room_get_contents", filename)
        
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

@bot.event
async def on_ready():
    print(f'{bot.user} でログイン完了！')
    print('ログ収集ボットが起動しました')
    print('Goodボタン（👍）が押されたらそのチャンネルのログを収集します')

@bot.event
async def on_raw_reaction_add(payload):
    """Goodボタンが押されたらログ収集を開始"""
    print(f'[DEBUG] リアクションイベント: {payload.emoji}')
    
    # ボット自身は無視
    if payload.user_id == bot.user.id:
        return
    
    # Goodボタン（👍）の確認
    thumbs_up_emojis = ['👍', '👍🏻', '👍🏼', '👍🏽', '👍🏾', '👍🏿']
    if str(payload.emoji) not in thumbs_up_emojis:
        return
        
    # 既に収集中の場合はスキップ
    if log_collector.is_collecting:
        channel = bot.get_channel(payload.channel_id)
        if channel:
            await channel.send("📋 現在他のチャンネルのログを収集中です。しばらくお待ちください。")
        return
    
    # チャンネル取得
    channel = bot.get_channel(payload.channel_id)
    if not channel:
        print(f'[ERROR] チャンネル {payload.channel_id} が見つかりません')
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

@bot.command(name='loginfo')
async def log_info(ctx):
    """ログ収集機能の情報を表示"""
    embed = discord.Embed(
        title="📋 ログ収集ボット",
        description="チャンネルのメッセージログを収集します",
        color=0x0099ff
    )
    embed.add_field(name="🔧 使用方法", value="任意のメッセージに 👍 リアクションを付ける", inline=False)
    embed.add_field(name="📊 収集内容", value="• 投稿日時\n• 投稿者\n• メッセージ内容\n• 添付ファイル\n• リアクション", inline=False)
    embed.add_field(name="⚙️ 仕様", value="• 100件ごとに2秒休憩\n• 8MB以下でDiscordにアップロード\n• それ以上はローカル保存", inline=False)
    
    await ctx.send(embed=embed)

if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_TOKEN')
    if TOKEN:
        print('ログ収集ボットを起動します...')
        bot.run(TOKEN)
    else:
        print('エラー: DISCORD_TOKENが設定されていません')