import discord
from discord.ext import commands
import os
import datetime
import asyncio
import csv
from dotenv import load_dotenv

load_dotenv()

# Discord サーバーメンバー取得ボット
intents = discord.Intents.all()
intents.members = True
intents.guilds = True
intents.reactions = True
intents.guild_reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 対象チャンネルID（指定されたroom1）
TARGET_CHANNEL_ID = 1418511738046779393

class GuildMemberCollector:
    def __init__(self):
        self.is_collecting = False
        
    async def get_all_guild_members(self, guild):
        """サーバーのすべてのメンバー情報を取得"""
        print(f'[GUILD] {guild.name}のメンバー取得を開始します...')
        
        members_data = []
        total_members = 0
        
        try:
            # メンバー情報を収集
            async for member in guild.fetch_members(limit=None):
                # メンバー情報を構造化
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
                    'avatar_url': str(member.avatar.url) if member.avatar else 'None',
                    'premium_since': member.premium_since.strftime('%Y-%m-%d %H:%M:%S') if member.premium_since else 'Not boosting'
                }
                members_data.append(member_data)
                total_members += 1
                
                # 進捗表示（100人ごと）
                if total_members % 100 == 0:
                    print(f'[GUILD] {total_members}人のメンバー情報を取得完了...')
                    # レート制限対策で少し待機
                    await asyncio.sleep(1)
                    
        except Exception as e:
            print(f'[ERROR] メンバー情報収集中にエラー: {e}')
            
        print(f'[GUILD] 収集完了！総メンバー数: {total_members}人')
        return members_data, guild
    
    def save_members_to_file(self, members_data, guild):
        """メンバー情報をテキストファイルとCSVファイルに保存"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        txt_filename = f"guild_{guild.id}_members_{timestamp}.txt"
        csv_filename = f"guild_{guild.id}_members_{timestamp}.csv"
        txt_filepath = os.path.join("/Users/suguruhirayama/Desktop/AI実験室/Discordbot", txt_filename)
        csv_filepath = os.path.join("/Users/suguruhirayama/Desktop/AI実験室/Discordbot", csv_filename)
        
        try:
            # テキストファイル作成
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== {guild.name} サーバーメンバー一覧 ===\n")
                f.write(f"取得日時: {datetime.datetime.now().strftime('%Y年%m月%d日 %H時%M分%S秒')}\n")
                f.write(f"総メンバー数: {len(members_data)}人\n")
                f.write(f"サーバーID: {guild.id}\n")
                f.write(f"サーバー作成日: {guild.created_at.strftime('%Y年%m月%d日')}\n")
                f.write("=" * 80 + "\n\n")
                
                # メンバー情報を詳細に出力
                for i, member in enumerate(members_data, 1):
                    f.write(f"【{i:04d}】 {member['username']}\n")
                    f.write(f"  表示名: {member['display_name']}\n")
                    f.write(f"  ユーザーID: {member['user_id']}\n")
                    f.write(f"  アカウント作成日: {member['created_at']}\n")
                    f.write(f"  サーバー参加日: {member['joined_at']}\n")
                    f.write(f"  ステータス: {member['status']}\n")
                    f.write(f"  BOT: {'はい' if member['is_bot'] else 'いいえ'}\n")
                    f.write(f"  最高ロール: {member['top_role']}\n")
                    if member['roles']:
                        f.write(f"  所持ロール: {', '.join(member['roles'])}\n")
                    f.write(f"  ブースト状況: {member['premium_since']}\n")
                    f.write(f"  アバター: {member['avatar_url']}\n")
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
                
                # ロール統計
                all_roles = {}
                for member in members_data:
                    for role in member['roles']:
                        all_roles[role] = all_roles.get(role, 0) + 1
                        
                if all_roles:
                    f.write(f"\n=== ロール統計 ===\n")
                    sorted_roles = sorted(all_roles.items(), key=lambda x: x[1], reverse=True)
                    for role_name, count in sorted_roles:
                        f.write(f"{role_name}: {count}人\n")
            
            # CSVファイル作成
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
                    
            print(f'[GUILD] ファイル保存完了: {txt_filepath}, {csv_filepath}')
            return (txt_filepath, csv_filepath)
            
        except Exception as e:
            print(f'[ERROR] ファイル保存中にエラー: {e}')
            return None

# メンバーコレクター初期化
member_collector = GuildMemberCollector()

@bot.event
async def on_ready():
    print(f'{bot.user} でログイン完了！')
    print('Discord サーバーメンバー取得ボットが起動しました')
    print(f'対象チャンネル: {TARGET_CHANNEL_ID}')
    
    # サーバー情報表示
    for guild in bot.guilds:
        print(f'サーバー: {guild.name} (ID: {guild.id})')
        print(f'  メンバー数: {guild.member_count}人')
        print(f'  作成日: {guild.created_at.strftime("%Y年%m月%d日")}')
        print(f'  オーナー: {guild.owner}')
        
        # 対象チャンネルの確認
        target_channel = bot.get_channel(TARGET_CHANNEL_ID)
        if target_channel and target_channel.guild == guild:
            print(f'  ✅ 対象チャンネル発見: {target_channel.name}')
        else:
            print(f'  ❓ 対象チャンネル未発見')

@bot.event
async def on_raw_reaction_add(payload):
    """目玉マークが押されたらメンバー一覧を取得"""
    print(f'[DEBUG] リアクションイベント: {payload.emoji} in {payload.channel_id}')
    
    # ボット自身のリアクションは無視
    if payload.user_id == bot.user.id:
        return
    
    # 対象チャンネルでのみ動作
    if payload.channel_id != TARGET_CHANNEL_ID:
        print(f'[DEBUG] 対象チャンネル外のリアクション: {payload.channel_id}')
        return
        
    # 目玉マーク（👁️）リアクションのみ
    eye_emojis = ['👁️', '👀', '🔍', '👁‍🗨']
    if str(payload.emoji) not in eye_emojis:
        print(f'[DEBUG] 対象外のリアクション: {payload.emoji}')
        return
        
    # 既に収集中の場合はスキップ
    if member_collector.is_collecting:
        channel = bot.get_channel(payload.channel_id)
        if channel:
            await channel.send("👁️ 現在メンバー情報を収集中です。しばらくお待ちください。")
        return
        
    # チャンネル取得
    channel = bot.get_channel(payload.channel_id)
    if not channel:
        print(f'[ERROR] チャンネル {payload.channel_id} が見つかりません')
        return
        
    # サーバー（ギルド）取得
    guild = channel.guild
    if not guild:
        print(f'[ERROR] サーバー情報が取得できません')
        return
        
    print(f'[LOG] 目玉マーク検知！サーバーメンバー取得を開始')
    
    # メンバー収集開始
    member_collector.is_collecting = True
    
    try:
        # 収集開始メッセージ
        await channel.send(f"👁️ **{guild.name}** のメンバー情報収集を開始します！\n"
                          f"⏳ メンバー数が多い場合は時間がかかります。お待ちください...\n"
                          f"📊 予想メンバー数: 約{guild.member_count}人")
        
        # メンバー情報収集
        members_data, guild_info = await member_collector.get_all_guild_members(guild)
        
        if not members_data:
            await channel.send("❌ メンバー情報を取得できませんでした。")
            return
            
        # ファイル保存
        filepaths = member_collector.save_members_to_file(members_data, guild_info)
        
        if filepaths and all(os.path.exists(fp) for fp in filepaths):
            txt_filepath, csv_filepath = filepaths
            
            # ファイルサイズ確認
            txt_size = os.path.getsize(txt_filepath)
            csv_size = os.path.getsize(csv_filepath)
            total_size_mb = (txt_size + csv_size) / (1024 * 1024)
            
            if total_size_mb > 8:  # Discordの8MB制限
                await channel.send(f"⚠️ ファイルサイズが大きすぎます ({total_size_mb:.1f}MB)。\n"
                                 f"ファイルはローカルに保存されました:\n"
                                 f"TXT: `{txt_filepath}`\n"
                                 f"CSV: `{csv_filepath}`")
            else:
                # 複数ファイルをDiscordにアップロード
                files_to_upload = []
                
                with open(txt_filepath, 'rb') as f:
                    files_to_upload.append(discord.File(f, filename=os.path.basename(txt_filepath)))
                    
                with open(csv_filepath, 'rb') as f:
                    files_to_upload.append(discord.File(f, filename=os.path.basename(csv_filepath)))
                    
                    embed = discord.Embed(
                        title="👁️ サーバーメンバー一覧",
                        description=f"**{guild.name}** のメンバー情報",
                        color=0x00bfff
                    )
                    
                    # 統計情報
                    bot_count = sum(1 for member in members_data if member['is_bot'])
                    human_count = len(members_data) - bot_count
                    boosters = sum(1 for member in members_data if member['premium_since'] != 'Not boosting')
                    
                embed.add_field(name="📊 総メンバー数", value=f"{len(members_data):,}人", inline=True)
                embed.add_field(name="👥 人間", value=f"{human_count:,}人", inline=True)
                embed.add_field(name="🤖 BOT", value=f"{bot_count:,}人", inline=True)
                embed.add_field(name="💎 ブースター", value=f"{boosters:,}人", inline=True)
                embed.add_field(name="📁 TXTサイズ", value=f"{txt_size/(1024*1024):.2f}MB", inline=True)
                embed.add_field(name="📊 CSVサイズ", value=f"{csv_size/(1024*1024):.2f}MB", inline=True)
                embed.add_field(name="⏰ 取得日時", value=datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'), inline=False)
                embed.add_field(name="📋 ファイル形式", value="• TXT: 詳細情報＋統計\n• CSV: 表形式（Excel対応）", inline=False)
                
                await channel.send("👁️ **サーバーメンバー一覧ファイルをアップロードします！**", embed=embed, files=files_to_upload)
                    print(f'[LOG] メンバー一覧ファイルアップロード完了')
        else:
            await channel.send("❌ ファイルの保存に失敗しました。")
            
    except Exception as e:
        print(f'[ERROR] メンバー収集処理中にエラー: {e}')
        await channel.send(f"❌ エラーが発生しました: {str(e)}")
        
    finally:
        member_collector.is_collecting = False

@bot.command(name='memberinfo')
async def member_info(ctx):
    """サーバーメンバー取得機能の説明"""
    if ctx.channel.id != TARGET_CHANNEL_ID:
        await ctx.send(f"❌ このコマンドは対象チャンネル (ID: {TARGET_CHANNEL_ID}) でのみ使用できます。")
        return
        
    embed = discord.Embed(
        title="👁️ サーバーメンバー取得機能",
        description="Discordサーバーの全メンバー情報を取得",
        color=0x00bfff
    )
    
    embed.add_field(name="🎯 対象サーバー", value=f"{ctx.guild.name}", inline=False)
    embed.add_field(name="👁️ 取得方法", value="任意のメッセージに 👁️ リアクションを付ける", inline=False)
    embed.add_field(name="📊 取得情報", value="• ユーザー名・表示名・ID\n• 参加日・アカウント作成日\n• ステータス・BOT判定\n• ロール情報・ブースト状況\n• アバターURL", inline=False)
    embed.add_field(name="📈 統計機能", value="• 総メンバー数・人間/BOT数\n• ブースター数\n• ロール別統計", inline=False)
    embed.add_field(name="📁 ファイル形式", value="テキストファイル（UTF-8）\n8MB以下でDiscordにアップロード", inline=False)
    embed.add_field(name="⚠️ 注意事項", value="メンバー数が多いと時間がかかります\n収集中は重複実行をブロックします", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='serverstats')
async def server_stats(ctx):
    """現在のサーバー統計を表示"""
    if ctx.channel.id != TARGET_CHANNEL_ID:
        await ctx.send(f"❌ このコマンドは対象チャンネル (ID: {TARGET_CHANNEL_ID}) でのみ使用できます。")
        return
        
    guild = ctx.guild
    embed = discord.Embed(
        title="📊 サーバー統計情報",
        description=f"**{guild.name}** の基本情報",
        color=0x00ff00
    )
    
    embed.add_field(name="🏷️ サーバー名", value=guild.name, inline=True)
    embed.add_field(name="🆔 サーバーID", value=guild.id, inline=True)
    embed.add_field(name="👑 オーナー", value=guild.owner, inline=True)
    
    embed.add_field(name="📅 作成日", value=guild.created_at.strftime('%Y年%m月%d日'), inline=True)
    embed.add_field(name="👥 メンバー数", value=f"{guild.member_count:,}人", inline=True)
    embed.add_field(name="🔊 チャンネル数", value=f"{len(guild.channels)}個", inline=True)
    
    embed.add_field(name="🎭 ロール数", value=f"{len(guild.roles)}個", inline=True)
    embed.add_field(name="😀 絵文字数", value=f"{len(guild.emojis)}個", inline=True)
    embed.add_field(name="💎 ブーストレベル", value=f"レベル{guild.premium_tier}", inline=True)
    
    # サーバーアイコン
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
        
    embed.add_field(name="💡 使用方法", value="👁️ リアクションで詳細メンバー一覧を取得", inline=False)
    
    await ctx.send(embed=embed)

if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_TOKEN')
    if TOKEN:
        print('=== Discord サーバーメンバー取得ボット起動中 ===')
        print(f'対象チャンネル: {TARGET_CHANNEL_ID}')
        bot.run(TOKEN)
    else:
        print('エラー: DISCORD_TOKENが設定されていません')