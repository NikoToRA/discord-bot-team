# ChatGPT連携ボット セットアップガイド

## 🚀 クイックスタート

### 1. 環境ファイルの準備
```bash
cd /Users/suguruhirayama/Desktop/AI実験室/Discordbot
cp .env.example .env
```

### 2. APIキーの設定
`.env`ファイルを編集して以下を設定：

```bash
# Discord Bot Token
DISCORD_TOKEN=your_discord_bot_token_here

# OpenAI API Key for GPT-5
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3. OpenAI APIキーの取得

#### 手順
1. **[OpenAI Platform](https://platform.openai.com/)** にアクセス
2. アカウント作成またはログイン
3. 左サイドバーの **「API keys」** をクリック
4. **「Create new secret key」** をクリック
5. キーに名前を付けて **「Create secret key」** をクリック
6. **重要**: 表示されたキー（`sk-`で始まる）をコピー
7. `.env`ファイルに貼り付け

#### APIキーの例
```
OPENAI_API_KEY=sk-proj-abc123def456ghi789...
```

### 4. 必要な依存関係のインストール
```bash
pip install -r requirements.txt
```

### 5. ボットの起動
```bash
python sample04_chatgpt.py
```

## ⚠️ 重要な注意事項

### セキュリティ
- **APIキーは絶対に公開しない**
- `.env`ファイルはGitにコミットしない（.gitignoreで除外済み）
- APIキーが漏洩した場合は即座にOpenAIで無効化する

### コスト管理
- GPT-5は使用量に応じて課金されます
- 使用前に[OpenAIの料金体系](https://openai.com/pricing)を確認
- 予算アラートの設定を推奨

### 対象チャンネル
- 現在の設定: `1418512165165465600`
- 他のチャンネルでは動作しません

## 🔧 トラブルシューティング

### よくあるエラー

#### 1. "OPENAI_API_KEYが設定されていません"
```bash
# .envファイルを確認
cat .env

# APIキーが正しく設定されているか確認
# sk-で始まる文字列が設定されているはず
```

#### 2. "Invalid API key"
- APIキーが正しくコピーされているか確認
- OpenAI Platformでキーが有効か確認
- 必要に応じて新しいキーを生成

#### 3. "insufficient_quota"
- OpenAIアカウントの残高を確認
- 支払い方法が設定されているか確認

#### 4. ボットが反応しない
- 対象チャンネル（`1418512165165465600`）で投稿しているか確認
- ボットがサーバーに参加しているか確認
- 必要な権限が付与されているか確認

## 📊 使用状況の確認

ボットが起動したら、以下のコマンドで状況を確認：

```
!gptinfo    # GPT機能の詳細情報
!gpttest    # テスト実行
!gptclear   # 会話履歴のクリア
```

## 💰 コスト管理のヒント

1. **使用量モニタリング**
   - `!gptinfo`コマンドで使用量確認
   - OpenAI Dashboardで詳細な使用量を確認

2. **予算設定**
   - OpenAI Platformで使用量上限を設定
   - 予算アラートを設定

3. **効率的な使用**
   - 不要な場合はボットを停止
   - 対象チャンネルを限定

## 🆘 サポート

問題が解決しない場合は：
1. エラーメッセージを確認
2. ログファイルを確認
3. OpenAI Platformのステータスページを確認
4. 設定を再確認