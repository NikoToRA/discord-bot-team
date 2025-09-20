import discord
from discord.ext import commands
import os
import asyncio
import logging
from dotenv import load_dotenv
import openai
from openai import OpenAI
import datetime

load_dotenv()

# ChatGPT連携Discordボット
intents = discord.Intents.all()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 対象チャンネルID（指定された部屋）
TARGET_CHANNEL_ID = 1418512165165465600

# OpenAI クライアント初期化
client = None
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
    print(f'[SETUP] OpenAI APIキーが設定されました')
else:
    print('[WARNING] OPENAI_API_KEYが設定されていません')

class ChatGPTResponder:
    def __init__(self, openai_client):
        self.client = openai_client
        self.is_responding = False
        self.response_history = []  # 会話履歴を保持
        
    async def generate_response(self, user_message, user_name, channel_name):
        """ChatGPTに返答を生成させる"""
        if not self.client:
            return "❌ OpenAI APIが設定されていません。"
            
        try:
            print(f'[CHATGPT] {user_name}からのメッセージに応答中: {user_message[:50]}...')
            
            # システムメッセージでボットの性格を定義
            system_message = {
                "role": "system",
                "content": f"""あなたは親しみやすく知識豊富なDiscordボットのアシスタントです。
                
特徴:
- 親しみやすく、フレンドリーな口調で話す
- 質問には具体的で有用な情報を提供する
- 必要に応じて絵文字を使用して表現を豊かにする
- 日本語で返答する
- 返答は簡潔で分かりやすくする（500文字以内を目安）
- コード例が必要な場合は、適切にフォーマットして提供する

現在の状況:
- チャンネル: {channel_name}
- ユーザー: {user_name}
- 日時: {datetime.datetime.now().strftime('%Y年%m月%d日 %H時%M分')}"""
            }
            
            # 会話履歴を含むメッセージを作成
            messages = [system_message]
            
            # 最近の履歴を含める（最大5件）
            recent_history = self.response_history[-5:] if self.response_history else []
            for hist in recent_history:
                messages.append({"role": "user", "content": hist["user_message"]})
                messages.append({"role": "assistant", "content": hist["bot_response"]})
            
            # 現在のユーザーメッセージを追加
            messages.append({"role": "user", "content": user_message})
            
            # ChatGPT API呼び出し
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=800,
                temperature=0.7,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # 履歴に追加（最大10件まで保持）
            self.response_history.append({
                "user_name": user_name,
                "user_message": user_message,
                "bot_response": ai_response,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # 履歴が10件を超えたら古いものを削除
            if len(self.response_history) > 10:
                self.response_history = self.response_history[-10:]
            
            print(f'[CHATGPT] 応答生成完了: {ai_response[:50]}...')
            return ai_response
            
        except Exception as e:
            error_message = f"ChatGPTとの通信中にエラーが発生しました: {str(e)}"
            print(f'[ERROR] {error_message}')
            return f"❌ {error_message}"
    
    def get_usage_stats(self):
        """使用統計を取得"""
        return {
            "total_responses": len(self.response_history),
            "recent_responses": len([h for h in self.response_history 
                                   if (datetime.datetime.now() - datetime.datetime.fromisoformat(h['timestamp'])).seconds < 3600])
        }

# ChatGPT応答者初期化
chatgpt_responder = ChatGPTResponder(client) if client else None

@bot.event
async def on_ready():
    print(f'{bot.user} でログイン完了！')
    print('ChatGPT連携ボットが起動しました')
    print(f'対象チャンネル: {TARGET_CHANNEL_ID}')
    print(f'OpenAI API: {"✅ 設定済み" if client else "❌ 未設定"}')
    
    # サーバー情報表示
    for guild in bot.guilds:
        print(f'サーバー: {guild.name} (ID: {guild.id})')
        target_channel = bot.get_channel(TARGET_CHANNEL_ID)
        if target_channel and target_channel.guild == guild:
            print(f'  ✅ 対象チャンネル発見: {target_channel.name}')
        else:
            print(f'  ❓ 対象チャンネル未発見')

@bot.event
async def on_message(message):
    """特定チャンネルのメッセージにChatGPTで自動返答"""
    # ボット自身のメッセージは無視
    if message.author == bot.user:
        return
    
    # 対象チャンネル以外は無視
    if message.channel.id != TARGET_CHANNEL_ID:
        return
    
    # 空のメッセージやコマンドは無視
    if not message.content.strip() or message.content.startswith('!'):
        return
    
    print(f'[DEBUG] 対象チャンネルでメッセージ検出: {message.author} - {message.content[:50]}...')
    
    # ChatGPTが利用可能かチェック
    if not chatgpt_responder:
        await message.reply("❌ ChatGPT機能が利用できません。OPENAI_API_KEYを設定してください。")
        return
    
    # 応答中の重複処理を防ぐ
    if chatgpt_responder.is_responding:
        await message.add_reaction("⏳")  # 処理中を示すリアクション
        return
    
    try:
        chatgpt_responder.is_responding = True
        
        # タイピング中を表示
        async with message.channel.typing():
            # ChatGPTに応答生成を依頼
            ai_response = await chatgpt_responder.generate_response(
                user_message=message.content,
                user_name=str(message.author),
                channel_name=message.channel.name
            )
        
        # 応答が長すぎる場合は分割
        if len(ai_response) > 2000:
            # Discord の文字数制限（2000文字）を超える場合は分割
            chunks = [ai_response[i:i+1900] for i in range(0, len(ai_response), 1900)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await message.reply(f"🤖 **ChatGPTからの返答 (1/{len(chunks)})**\n\n{chunk}")
                else:
                    await message.channel.send(f"🤖 **ChatGPTからの返答 ({i+1}/{len(chunks)})**\n\n{chunk}")
                
                # 分割送信の間に短い間隔を空ける
                if i < len(chunks) - 1:
                    await asyncio.sleep(1)
        else:
            # 通常の返答
            await message.reply(f"🤖 **ChatGPTからの返答**\n\n{ai_response}")
        
        print(f'[SUCCESS] ChatGPT応答送信完了')
        
    except Exception as e:
        print(f'[ERROR] メッセージ処理中にエラー: {e}')
        await message.reply(f"❌ 処理中にエラーが発生しました: {str(e)}")
    
    finally:
        chatgpt_responder.is_responding = False
    
    # コマンドも処理（必要に応じて）
    await bot.process_commands(message)

@bot.command(name='gptinfo')
async def gpt_info(ctx):
    """ChatGPT機能の情報を表示"""
    embed = discord.Embed(
        title="🤖 ChatGPT連携機能",
        description="OpenAI ChatGPTと連携したAI応答機能",
        color=0x00ff88
    )
    
    embed.add_field(name="🎯 対象チャンネル", value=f"<#{TARGET_CHANNEL_ID}>", inline=False)
    embed.add_field(name="🔧 動作方式", value="メッセージ投稿 → 自動でChatGPTが返答", inline=False)
    embed.add_field(name="💡 使用モデル", value="gpt-3.5-turbo", inline=True)
    embed.add_field(name="📝 文字数制限", value="2000文字（自動分割対応）", inline=True)
    embed.add_field(name="🧠 記憶機能", value="直近10回の会話を記憶", inline=True)
    
    # 使用統計
    if chatgpt_responder:
        stats = chatgpt_responder.get_usage_stats()
        embed.add_field(name="📊 使用統計", 
                       value=f"総応答数: {stats['total_responses']}\n直近1時間: {stats['recent_responses']}", 
                       inline=False)
        
        embed.add_field(name="✅ API状態", value="正常動作中", inline=True)
    else:
        embed.add_field(name="❌ API状態", value="未設定", inline=True)
    
    embed.add_field(name="⚠️ 注意事項", 
                   value="• コマンド（!で始まる）は無視\n• 空メッセージは無視\n• API利用料が発生します", 
                   inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='gptclear')
async def gpt_clear(ctx):
    """ChatGPTの会話履歴をクリア"""
    if ctx.channel.id != TARGET_CHANNEL_ID:
        await ctx.send("❌ このコマンドは対象チャンネルでのみ使用できます。")
        return
    
    if not chatgpt_responder:
        await ctx.send("❌ ChatGPT機能が利用できません。")
        return
    
    old_count = len(chatgpt_responder.response_history)
    chatgpt_responder.response_history = []
    
    embed = discord.Embed(
        title="🧹 会話履歴クリア完了",
        description=f"ChatGPTの会話履歴を削除しました",
        color=0x00ff00
    )
    embed.add_field(name="削除した履歴数", value=f"{old_count}件", inline=True)
    embed.add_field(name="効果", value="新しい会話として扱われます", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='gpttest')
async def gpt_test(ctx):
    """ChatGPT機能のテスト"""
    if ctx.channel.id != TARGET_CHANNEL_ID:
        await ctx.send("❌ このコマンドは対象チャンネルでのみ使用できます。")
        return
    
    if not chatgpt_responder:
        await ctx.send("❌ ChatGPT機能が利用できません。")
        return
    
    test_message = "こんにちは！テストメッセージです。簡単に自己紹介をしてください。"
    
    try:
        async with ctx.typing():
            response = await chatgpt_responder.generate_response(
                user_message=test_message,
                user_name=str(ctx.author),
                channel_name=ctx.channel.name
            )
        
        embed = discord.Embed(
            title="🧪 ChatGPTテスト結果",
            description="テストメッセージへの応答",
            color=0x0099ff
        )
        embed.add_field(name="📝 テストメッセージ", value=test_message, inline=False)
        embed.add_field(name="🤖 ChatGPT応答", value=response, inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ テスト中にエラー: {str(e)}")

if __name__ == '__main__':
    # 環境変数チェック
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    print('=== ChatGPT連携Discordボット起動中 ===')
    print(f'対象チャンネル: {TARGET_CHANNEL_ID}')
    print(f'Discord Token: {"✅ 設定済み" if DISCORD_TOKEN else "❌ 未設定"}')
    print(f'OpenAI API Key: {"✅ 設定済み" if OPENAI_API_KEY else "❌ 未設定"}')
    
    if DISCORD_TOKEN:
        if OPENAI_API_KEY:
            print('✅ すべての設定が完了しています。ボットを起動します...')
        else:
            print('⚠️  OPENAI_API_KEYが未設定です。ChatGPT機能は無効になります。')
        
        bot.run(DISCORD_TOKEN)
    else:
        print('❌ DISCORD_TOKENが設定されていません。.envファイルを確認してください。')