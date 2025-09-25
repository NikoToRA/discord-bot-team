# Railway デプロイ手順

## 🚀 新しい統合ボットをRailwayにデプロイ

### 1. Railway設定の確認

現在のProcfile: `web: python -u main_bot.py`

### 2. 環境変数の設定

Railwayのダッシュボードで以下の環境変数を設定：

```
DISCORD_TOKEN=your_discord_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. 機能のON/OFF制御

デプロイ前に `config.py` を編集：

```python
# Railway本番環境用設定例
FEATURES = {
    'basic_greeting': True,         # 基本挨拶
    'chatgpt_text': True,           # ChatGPTテキスト会話
    'chatgpt_voice': True,          # 🎤音声文字起こし
    'chatgpt_image_ocr': True,      # 🦀画像文字起こし
    'room_logging': False,          # ログ機能は無効
    'debug_logging': False,         # 本番では無効
}

BOT_CONFIG = {
    'debug_level': 'INFO',          # 本番用ログレベル
    # 他の設定...
}
```

### 4. デプロイ手順

#### A. 既存Railwayプロジェクトの更新
```bash
# ローカルでコミット
git add .
git commit -m "Upgrade to unified bot architecture"
git push origin main  # Railwayが自動デプロイ
```

#### B. 新しいRailwayプロジェクト作成
1. Railway.appでNew Project作成
2. GitHubリポジトリ連携
3. 環境変数設定
4. デプロイ実行

### 5. デプロイ後の確認

#### Discord上で確認：
- ボットがオンラインか確認
- `!features` コマンドで機能確認
- `!help_reactions` でリアクション確認

#### 機能テスト：
1. **🦀 画像文字起こし**
   - 画像を投稿 → 自動で🦀リアクション追加
   - 🦀をクリック → ChatGPTで文字起こし

2. **🎤 音声文字起こし**
   - 音声ファイル投稿 → 自動で🎤リアクション追加
   - 🎤をクリック → Whisperで文字起こし

3. **💬 ChatGPTテキスト会話**
   - "chatgpt 今日の天気は？" などで応答確認

### 6. トラブルシューティング

#### ログ確認
```bash
railway logs
```

#### よくある問題：
1. **環境変数未設定** → Railway設定確認
2. **OpenAIクレジット不足** → 課金状況確認
3. **Discord権限不足** → bot権限設定確認

### 7. Railway vs ローカル制御

現在の状況：
- **Railway**: 統合ボット本番稼働 ✅
- **ローカル**: 開発・テスト用 ⚡

トークン競合を避けるため、どちらか一方のみ稼働させてください。

### 8. ローカル開発時

Railway停止してローカルテスト：
```bash
railway down  # Railway停止
python main_bot.py  # ローカル起動
```

### 9. スケーリング設定

Railway設定で：
- **CPU**: 0.25 vCPU（基本的なボット用）
- **Memory**: 512MB（十分）
- **Instances**: 1（ボットは1つのみ）