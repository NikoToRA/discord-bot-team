# Railway デプロイ手順

## 1. Railway環境変数の設定

Railway Dashboard で以下の環境変数を設定してください：

### 必須環境変数
```
DISCORD_TOKEN=あなたのDiscordボットトークン
```

### 設定手順
1. Railway Dashboard にログイン
2. プロジェクトを選択
3. Settings → Environment タブに移動
4. "New Variable" をクリック
5. 変数名: `DISCORD_TOKEN`
6. 値: あなたのDiscordボットトークン
7. "Add" をクリックして保存

## 2. デプロイ設定

### 自動デプロイ設定
- GitHubリポジトリと連携済み
- mainブランチへのプッシュで自動デプロイ

### 起動コマンド
```
python -u bot.py
```

## 3. トラブルシューティング

### エラー: "DISCORD_TOKENが設定されていません"
- Railway Dashboard で環境変数が正しく設定されているか確認
- 変数名が正確に `DISCORD_TOKEN` になっているか確認
- 値にDiscordボットトークンが正しく入力されているか確認

### ログの確認方法
1. Railway Dashboard → Deployments
2. 最新のデプロイメントをクリック
3. Logs タブでリアルタイムログを確認

### 再デプロイ方法
1. Railway Dashboard → Deployments
2. "Redeploy" ボタンをクリック

## 4. 注意事項

- `.env` ファイルはRailwayでは使用されません
- 環境変数はRailway Dashboard で設定する必要があります
- トークンは絶対にGitHubにプッシュしないでください（.gitignoreで除外済み）

## 5. 確認方法

デプロイ成功時のログ例：
```
=== Discord Bot 起動中 ===
現在のディレクトリ: /app
.envファイルの存在: False
トークンの確認: MTQxODQ2OT...
ボットを起動します...
チャピーちゃん#9080 でログインしました！
```