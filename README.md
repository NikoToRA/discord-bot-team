# Discord Bot Team

Discordボットチーム用のベースボット - 任意のメッセージに「こんにちは」と返信します。

## 機能

- 任意のメッセージ（`!`で始まらない）に「こんにちは」と返信
- 詳細なデバッグログ出力
- 適切なエラーハンドリング

## セットアップ

### 1. 依存関係のインストール

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成し、Discordボットトークンを設定：

```env
DISCORD_TOKEN=あなたのボットトークン
```

### 3. Discord Developer Portal設定

1. [Discord Developer Portal](https://discord.com/developers/applications)でボットを作成
2. Bot設定で「MESSAGE CONTENT INTENT」を有効化
3. OAuth2でボットをサーバーに招待（必要な権限: Send Messages, Read Message History）

### 4. ボットの実行

```bash
source venv/bin/activate
python bot.py
```

## ファイル構成

```
├── bot.py              # メインボットファイル
├── requirements.txt    # Pythonの依存関係
├── .env               # 環境変数（トークン）
├── .gitignore         # Git除外ファイル
└── README.md          # このファイル
```

## 技術仕様

- Python 3.13対応
- discord.py 2.6.3以上
- Message Content Intent対応

## 開発履歴

詳細な開発過程と遭遇した問題については、`../discord-bot-development-history/開発履歴.md`を参照してください。