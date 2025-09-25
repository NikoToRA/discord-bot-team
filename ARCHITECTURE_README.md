# Discord Bot アーキテクチャ

## 🏗️ 新しい統合アーキテクチャ

管理しやすい機能ベースの構造に改善しました。

```
Discordbot/
├── main_bot.py              # 🤖 メインボット（統合実行）
├── config.py                # ⚙️ 機能ON/OFF・設定管理
├── .env                     # 🔐 環境変数（トークン類）
├── features/                # 📁 機能モジュール
│   ├── __init__.py
│   ├── image_ocr.py         # 🦀 画像文字起こし
│   ├── voice_transcribe.py  # 🎤 音声文字起こし
│   ├── basic_greeting.py    # 👋 基本挨拶
│   └── chatgpt_text.py      # 💬 ChatGPTテキスト会話
├── legacy/                  # 📂 従来のサンプルファイル
│   ├── sample01_*.py
│   ├── sample02_*.py
│   └── ...
└── requirements.txt
```

## 🚀 使用方法

### 1. メインボットを起動
```bash
# 仮想環境を有効化
source venv/bin/activate

# 統合ボットを実行
python main_bot.py
```

### 2. 機能のON/OFF設定
`config.py` を編集してください：

```python
FEATURES = {
    'basic_greeting': True,         # 基本挨拶
    'chatgpt_text': True,           # ChatGPTテキスト
    'chatgpt_voice': True,          # 音声文字起こし
    'chatgpt_image_ocr': True,      # 🦀画像文字起こし
    'room_logging': False,          # 無効化例
    'debug_logging': True,          # デバッグログ
}
```

## 📋 機能一覧

| 機能 | リアクション | 説明 | 設定キー |
|------|-------------|------|----------|
| 🦀 画像文字起こし | 🦀 | 画像からテキスト抽出 | `chatgpt_image_ocr` |
| 🎤 音声文字起こし | 🎤 | 音声ファイルからテキスト抽出 | `chatgpt_voice` |
| 💬 ChatGPTテキスト | - | テキスト会話 | `chatgpt_text` |
| 👋 基本挨拶 | - | 簡単な返答 | `basic_greeting` |

## 🎯 利点

### ✅ 管理しやすさ
- **機能ごとに独立したファイル**
- **簡単なON/OFF切り替え**
- **1つのトークンで全機能動作**

### ✅ 開発効率
- **新機能の追加が簡単**
- **既存機能に影響なし**
- **テスト・デバッグが楽**

### ✅ 運用面
- **トークン競合問題解決**
- **Railway等でもそのまま動作**
- **設定変更だけで機能制御**

## 🛠️ 新機能の追加方法

### 1. 機能モジュールを作成
```python
# features/new_feature.py
async def handle_new_feature(message, bot):
    # 機能の実装
    pass
```

### 2. config.pyに設定追加
```python
FEATURES = {
    # 既存設定...
    'new_feature': True,  # 新機能
}
```

### 3. main_bot.pyで統合
```python
from features.new_feature import handle_new_feature

@bot.event
async def on_message(message):
    if FEATURES['new_feature']:
        await handle_new_feature(message, bot)
```

## 🔧 コマンド

| コマンド | 説明 |
|----------|------|
| `!features` | 有効機能一覧表示 |
| `!help_reactions` | リアクション一覧表示 |

## 🔄 従来ファイルからの移行

従来のsample*.pyファイルの機能は統合済みです：
- `sample06_chatgpt_image.py` → `features/image_ocr.py`
- `sample05_chatgpt_voice.py` → `features/voice_transcribe.py`
- `bot.py` → `features/basic_greeting.py`

古いファイルは`legacy/`フォルダに移動できます。

## 🚨 トラブルシューティング

### Discord Token エラー
- 他のボットプロセスを停止してください
- `main_bot.py`を1つだけ実行してください

### 機能が動作しない
1. `config.py`で機能がTrueになっているか確認
2. `.env`にAPIキーが設定されているか確認
3. `!features`コマンドで状態確認