# ChatGPT連携Discordボット

特定のDiscordチャンネルに投稿されたメッセージに対して、ChatGPTが自動で返答するボットです。

## 機能概要

### 🤖 自動返答機能
- **対象チャンネル**: `1418512165165465600`
- **動作**: メッセージが投稿されると自動的にChatGPTが返答
- **モデル**: OpenAI GPT-5
- **会話記憶**: 直近10回の会話を記憶して文脈を理解

### 💬 ChatGPTの特徴
- **親しみやすい口調**: フレンドリーで親近感のある応答
- **日本語対応**: 日本語で自然な会話
- **絵文字使用**: 表現豊かな返答
- **簡潔性**: 500文字以内を目安とした分かりやすい返答
- **高度な推論**: GPT-5の強化された推論能力を活用
- **コード対応**: プログラミング関連の質問にも対応

## 使用方法

### 1. 環境設定

#### 環境変数の設定
1. **`.env`ファイルの作成**
   ```bash
   cd /Users/suguruhirayama/Desktop/AI実験室/Discordbot
   cp .env.example .env
   ```

2. **`.env`ファイルに以下を設定**
   ```bash
   # Discord Bot Configuration
   DISCORD_TOKEN=your_discord_bot_token_here
   
   # OpenAI API Configuration (GPT-5)
   OPENAI_API_KEY=sk-your-actual-api-key-here
   
   # Optional: Organization ID (if you have one)
   # OPENAI_ORGANIZATION=your_organization_id_here
   ```

#### OpenAI APIキーの取得手順
1. [OpenAI Platform](https://platform.openai.com/)にアクセス
2. アカウント作成またはログイン
3. **API Keys** セクションに移動
4. **"Create new secret key"** をクリック
5. キーに名前を付けて生成
6. **重要**: 生成されたキー（`sk-`で始まる文字列）をコピー
7. `.env`ファイルの`OPENAI_API_KEY`に設定

#### セキュリティ注意事項
⚠️ **APIキーの取り扱い注意**
- APIキーは絶対に他人と共有しない
- GitHubなどの公開リポジトリにコミットしない
- `.env`ファイルは`.gitignore`で除外する
- キーが漏洩した場合は即座にOpenAIで無効化する

### 2. ボット実行

#### スタンドアロン実行
```bash
cd /Users/suguruhirayama/Desktop/AI実験室/Discordbot
python sample04_chatgpt.py
```

#### Railway実行（統合版）
メインの`bot.py`に統合して運用も可能

### 3. Discord上での使用

#### 自動返答
- 対象チャンネル（ID: 1418512165165465600）でメッセージを投稿
- ボットが自動的にChatGPTで返答を生成
- 長い返答は自動で分割して送信

#### コマンド
```
!gptinfo    - ChatGPT機能の情報表示
!gptclear   - 会話履歴をクリア
!gpttest    - ChatGPT機能のテスト
```

## 動作例

### 入力例
```
ユーザー: Pythonでリストの重複を削除する方法を教えて
```

### ChatGPT返答例
```
🤖 ChatGPTからの返答

Pythonでリストの重複を削除する方法はいくつかありますね！😊

**1. set()を使う方法（最も簡単）**
```python
original_list = [1, 2, 2, 3, 4, 4, 5]
unique_list = list(set(original_list))
print(unique_list)  # [1, 2, 3, 4, 5] (順序は変わる可能性あり)
```

**2. dict.fromkeys()を使う方法（順序を保持）**
```python
original_list = [1, 2, 2, 3, 4, 4, 5]
unique_list = list(dict.fromkeys(original_list))
print(unique_list)  # [1, 2, 3, 4, 5]
```

順序を保持したい場合は2番目の方法がおすすめです！🎯
```

## 特徴

### ✅ メリット
- **リアルタイム対応**: メッセージ投稿と同時に返答
- **文脈理解**: 過去の会話を記憶して適切な返答
- **長文対応**: 2000文字を超える返答は自動分割
- **エラーハンドリング**: API通信エラー時の適切な対応
- **使用統計**: 応答回数などの統計情報を表示

### ⚠️ 注意事項
- **API料金**: OpenAI APIの使用料金が発生
- **レスポンス時間**: ChatGPT APIの応答待ち時間（1-5秒程度）
- **対象チャンネル限定**: 指定チャンネルのみで動作
- **コマンド無視**: `!`で始まるコマンドは処理しない
- **重複処理防止**: 同時応答を防ぐロック機能

## トラブルシューティング

### ChatGPTが応答しない
1. `OPENAI_API_KEY`が正しく設定されているか確認
2. OpenAI APIの残高があるか確認
3. 対象チャンネルでメッセージを投稿しているか確認

### API呼び出しエラー
- インターネット接続を確認
- APIキーの有効性を確認
- OpenAIサービスの状態を確認

### ボットが反応しない
- Discord BOTトークンの確認
- ボットが対象サーバーに参加しているか確認
- 適切な権限が付与されているか確認

## セキュリティ

### APIキー管理
- **`.env`ファイル**: Gitにコミットしない
- **環境変数**: 本番環境では環境変数で管理
- **権限最小化**: 必要最小限の権限のみ付与

### プライバシー
- **会話記憶**: 最大10回まで（メモリ内のみ）
- **ログ記録**: 必要最小限の情報のみ
- **データ保持**: ボット再起動でリセット

## コスト管理

### API使用料目安
- **GPT-5**: より高性能だが、料金は変動する可能性があります
- **平均的な会話**: 1回あたり約0.5-2円（推定）
- **月額**: 使用頻度による（100回/日で月約1,500-6,000円程度を想定）
- **注意**: GPT-5の正式な料金体系は公式発表をご確認ください

### 節約方法
- 対象チャンネルを限定
- 会話履歴の保持数を調整
- 不要時はボット停止

## 必要な権限

Discord Application で以下の権限が必要：
- `Read Messages`
- `Send Messages`
- `Read Message History`
- `Use Slash Commands`