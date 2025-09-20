import discord
from discord.ext import commands
import os
import asyncio
import logging
import time
from dotenv import load_dotenv
from openai import OpenAI
import datetime
import json
import tiktoken

load_dotenv()

# GPT-4連携Discordボット
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
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        print(f'[SETUP] OpenAI APIクライアント初期化完了')
    except Exception as e:
        print(f'[ERROR] OpenAI APIクライアント初期化失敗: {e}')
else:
    print('[WARNING] OPENAI_API_KEYが設定されていません')

# トークンエンコーダー初期化
try:
    # GPT-4用のエンコーダー
    encoding = tiktoken.encoding_for_model("gpt-4")
    print('[SETUP] Tiktokenエンコーダー初期化完了 (GPT-4対応)')
except Exception as e:
    print(f'[WARNING] Tiktokenエンコーダー初期化失敗: {e}')
    encoding = None

class ChatGPTResponder:
    def __init__(self, openai_client):
        self.client = openai_client
        self.is_responding = False
        self.response_history = []  # 会話履歴を保持
        self.max_tokens = 4000  # GPT-4用最大応答トークン数
        self.max_context_tokens = 8192  # GPT-4用コンテキスト最大トークン数
        self.retry_count = 3  # リトライ回数
        self.rate_limit_delay = 1  # レート制限時の待機時間
        
    def count_tokens(self, text):
        """テキストのトークン数をカウント"""
        if encoding:
            try:
                return len(encoding.encode(text))
            except Exception:
                return len(text) // 4  # おおよその推定
        return len(text) // 4  # おおよその推定
    
    def trim_conversation_history(self, messages):
        """会話履歴をトークン制限内に収める"""
        if not encoding:
            return messages[-8:]  # エンコーダーがない場合は直近8件
        
        total_tokens = 0
        trimmed_messages = []
        
        # 逆順で処理して、制限内の最新履歴を保持
        for message in reversed(messages):
            message_tokens = self.count_tokens(json.dumps(message, ensure_ascii=False))
            if total_tokens + message_tokens > self.max_context_tokens:
                break
            total_tokens += message_tokens
            trimmed_messages.insert(0, message)
        
        return trimmed_messages
    
    async def generate_response(self, user_message, user_name, channel_name):
        """ChatGPTに返答を生成させる（リトライ機能付き）"""
        if not self.client:
            return "❌ OpenAI APIが設定されていません。"
        
        for attempt in range(self.retry_count):
            try:
                print(f'[GPT-4] {user_name}からのメッセージに応答中 (試行 {attempt + 1}/{self.retry_count}): {user_message[:50]}...')
            
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
- 不適切な内容には応答しない

現在の状況:
- チャンネル: {channel_name}
- ユーザー: {user_name}
- 日時: {datetime.datetime.now().strftime('%Y年%m月%d日 %H時%M分')}"""
                }
                
                # 会話履歴を含むメッセージを作成
                messages = [system_message]
                
                # 最近の履歴を含める（GPT-4のコンテキストを活用）
                recent_history = self.response_history[-8:] if self.response_history else []
                for hist in recent_history:
                    messages.append({"role": "user", "content": hist["user_message"]})
                    messages.append({"role": "assistant", "content": hist["bot_response"]})
                
                # 現在のユーザーメッセージを追加
                messages.append({"role": "user", "content": user_message})
                
                # トークン制限内に履歴を調整
                messages = self.trim_conversation_history(messages)
            
                # GPT-4 Chat Completions API呼び出し
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=0.7,
                    user=f"discord_user_{hash(user_name) % 10000}"  # ユーザー識別用
                )

                ai_response = response.choices[0].message.content.strip()

                # 使用量情報をログに記録
                usage = response.usage
                print(f'[API] トークン使用量 - 入力: {usage.prompt_tokens}, 出力: {usage.completion_tokens}, 合計: {usage.total_tokens}')
                
                # 履歴に追加（最大10件まで保持）
                self.response_history.append({
                    "user_name": user_name,
                    "user_message": user_message,
                    "bot_response": ai_response,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "tokens_used": usage.total_tokens
                })
                
                # 履歴が10件を超えたら古いものを削除
                if len(self.response_history) > 10:
                    self.response_history = self.response_history[-10:]
                
                print(f'[GPT-4] 応答生成完了: {ai_response[:50]}...')
                return ai_response
                
            except Exception as e:
                error_type = type(e).__name__
                error_message = str(e)
                
                print(f'[ERROR] API呼び出しエラー (試行 {attempt + 1}/{self.retry_count}): {error_type} - {error_message}')
                
                # 特定のエラーに対する対応
                if "rate_limit" in error_message.lower():
                    print(f'[WARNING] レート制限検出。{self.rate_limit_delay * (attempt + 1)}秒待機中...')
                    await asyncio.sleep(self.rate_limit_delay * (attempt + 1))
                    continue
                elif "insufficient_quota" in error_message.lower():
                    return "❌ OpenAI APIの利用枠を超過しました。APIキーの残高を確認してください。"
                elif "invalid_api_key" in error_message.lower():
                    return "❌ OpenAI APIキーが無効です。設定を確認してください。"
                elif "model_not_found" in error_message.lower() or "model does not exist" in error_message.lower():
                    return "❌ GPT-4モデルにアクセスできません。APIキーの権限またはアカウント設定を確認してください。"
                elif attempt == self.retry_count - 1:  # 最後の試行
                    return f"❌ GPT-4との通信中にエラーが発生しました: {error_type}"
                
                # リトライ前の短い待機
                await asyncio.sleep(0.5)
        
        return "❌ 複数回の試行後もGPT-4との通信に失敗しました。"
    
    def get_usage_stats(self):
        """使用統計を取得"""
        total_tokens = sum(h.get('tokens_used', 0) for h in self.response_history)
        recent_responses = [h for h in self.response_history 
                           if (datetime.datetime.now() - datetime.datetime.fromisoformat(h['timestamp'])).seconds < 3600]
        recent_tokens = sum(h.get('tokens_used', 0) for h in recent_responses)
        
        return {
            "total_responses": len(self.response_history),
            "recent_responses": len(recent_responses),
            "total_tokens": total_tokens,
            "recent_tokens": recent_tokens,
            "estimated_cost_usd": total_tokens * 0.00001  # GPT-4 Turboのおおよそのコスト計算（仮定値、実際の料金は要確認）
        }

# GPT-4応答者初期化
chatgpt_responder = ChatGPTResponder(client) if client else None

@bot.event
async def on_ready():
    print(f'{bot.user} でログイン完了！')
    print('GPT-4連携ボットが起動しました')
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
    """特定チャンネルのメッセージにGPT-4で自動返答"""
    print(f'[DEBUG] メッセージイベント発生: {message.channel.id} vs {TARGET_CHANNEL_ID}')
    print(f'[DEBUG] 送信者: {message.author} (ID: {message.author.id})')
    print(f'[DEBUG] ボット自身: {bot.user} (ID: {bot.user.id if bot.user else "None"})')
    print(f'[DEBUG] メッセージ内容: "{message.content}"')
    
    # ボット自身のメッセージは無視
    if message.author == bot.user:
        print('[DEBUG] ボット自身のメッセージなのでスキップ')
        return
    
    # 対象チャンネル以外は無視
    if message.channel.id != TARGET_CHANNEL_ID:
        print(f'[DEBUG] 対象外チャンネル ({message.channel.id}) なのでスキップ')
        return
    
    # 空のメッセージやコマンドは無視
    if not message.content.strip() or message.content.startswith('!'):
        print(f'[DEBUG] 空メッセージまたはコマンドなのでスキップ: "{message.content}"')
        return
    
    print(f'[DEBUG] 対象チャンネルでメッセージ検出: {message.author} - {message.content[:50]}...')
    
    # GPT-4が利用可能かチェック
    if not chatgpt_responder:
        print(f'[ERROR] GPT-4機能が利用できません（OpenAI APIキー未設定）')
        await message.reply("❌ GPT-4機能が利用できません。OPENAI_API_KEYを設定してください。\n"
                           "設定方法: `!gptinfo` コマンドで詳細確認")
        return
    
    # 応答中の重複処理を防ぐ
    if chatgpt_responder.is_responding:
        await message.add_reaction("⏳")  # 処理中を示すリアクション
        return
    
    try:
        chatgpt_responder.is_responding = True
        
        # タイピング中を表示
        async with message.channel.typing():
            # GPT-4に応答生成を依頼
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
                    await message.reply(f"🤖 **GPT-4からの返答 (1/{len(chunks)})**\n\n{chunk}")
                else:
                    await message.channel.send(f"🤖 **GPT-4からの返答 ({i+1}/{len(chunks)})**\n\n{chunk}")
                
                # 分割送信の間に短い間隔を空ける
                if i < len(chunks) - 1:
                    await asyncio.sleep(1)
        else:
            # 通常の返答
            await message.reply(f"🤖 **GPT-4からの返答**\n\n{ai_response}")
        
        print(f'[SUCCESS] GPT-4応答送信完了')
        
    except Exception as e:
        print(f'[ERROR] メッセージ処理中にエラー: {e}')
        await message.reply(f"❌ 処理中にエラーが発生しました: {str(e)}")
    
    finally:
        chatgpt_responder.is_responding = False
    
    # コマンドも処理（必要に応じて）
    await bot.process_commands(message)

@bot.command(name='gptinfo')
async def gpt_info(ctx):
    """GPT-4機能の情報を表示"""
    embed = discord.Embed(
        title="🤖 GPT-4連携機能",
        description="OpenAI GPT-4と連携したAI応答機能",
        color=0x00ff88
    )
    
    embed.add_field(name="🎯 対象チャンネル", value=f"<#{TARGET_CHANNEL_ID}>", inline=False)
    embed.add_field(name="🔧 動作方式", value="メッセージ投稿 → 自動でChatGPTが返答", inline=False)
    embed.add_field(name="💡 使用モデル", value="GPT-4 Turbo 🚀", inline=True)
    embed.add_field(name="📝 文字数制限", value="2000文字（自動分割対応）", inline=True)
    embed.add_field(name="🧠 記憶機能", value="直近10回の会話を記憶", inline=True)
    
    # 使用統計
    if chatgpt_responder:
        stats = chatgpt_responder.get_usage_stats()
        embed.add_field(name="📊 使用統計", 
                       value=f"総応答数: {stats['total_responses']}\n直近1時間: {stats['recent_responses']}", 
                       inline=True)
        embed.add_field(name="💰 トークン使用量", 
                       value=f"総計: {stats['total_tokens']:,}\n直近1時間: {stats['recent_tokens']:,}\n推定コスト: ${stats['estimated_cost_usd']:.4f}", 
                       inline=True)
        
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
    
    print('=== GPT-4連携Discordボット起動中 ===')
    print(f'対象チャンネル: {TARGET_CHANNEL_ID}')
    print(f'Discord Token: {"✅ 設定済み" if DISCORD_TOKEN else "❌ 未設定"}')
    print(f'OpenAI API Key: {"✅ 設定済み" if OPENAI_API_KEY else "❌ 未設定"}')
    
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
        print('   3. ChatGPT機能は無効になります。')
        print('🔄 現在はChatGPT機能無効でボットを起動します...')
        
    print('✅ 設定確認完了。ボットを起動します...')
    bot.run(DISCORD_TOKEN)