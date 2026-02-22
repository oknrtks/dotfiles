---
name: configuring-claude-notifications
description: Claude Codeのフック機能を使ってntfy.shによるプッシュ通知を設定・管理します。ユーザーが「通知を設定したい」「ntfyで通知を受け取りたい」「フック設定をしたい」と言った場合にこのスキルを使用します。また、通知が届かないトラブルシューティングや通知設定のカスタマイズにも対応します。
---

# Claude Code通知設定スキル

このスキルはClaude Codeのフック機能とntfy.shを使って、プッシュ通知システムを設定します。

## スキルのファイル構成

```
configuring-claude-notifications/
├── SKILL.md                    # このファイル
├── config-template.json        # 設定ファイルのひな形
├── claude-ntfy.py             # Python通知スクリプト（標準ライブラリのみ）
└── setup-examples.md          # 詳細な設定例とトラブルシューティング
```

## 設定手順

### 対話的な設定手順

このスキルは対話的な設定フローをサポートしています。以下の手順で進めます。

#### 1. ntfy.shトピック名の入力

まず、ntfy.shのトピック名を決定してください。

1. https://ntfy.sh にアクセス
2. トピック名を決める（例: `claude-notifications-username`）
3. ntfyアプリ（iOS/Android/Web）でトピックを購読

**トピック名を入力してください**（例: `claude-notifications-user123`）:

#### 2. ファイルの配置

トピック名を入力したら、以下のコマンドを実行してファイルを配置します：

```bash
# スクリプトを配置
cp claude-ntfy.py ~/.local/bin/
chmod +x ~/.local/bin/claude-ntfy.py

# 設定ファイルを配置
mkdir -p ~/.local/share/claude-ntfy
cp config-template.json ~/.local/share/claude-ntfy/config.json
```

**重要**: `~/.local/share/claude-ntfy/config.json` を編集して、`ntfy_url` の `YOUR_TOPIC_NAME` を手順1で入力したトピック名に書き換えてください。

#### 3. settings.jsonの更新

`~/.claude/settings.json` に以下を追加：

```json
{
  "hooks": {
    "Notification": [
      { "matcher": "*", "hooks": [{ "type": "command", "command": "~/.local/bin/claude-ntfy.py" }] }
    ],
    "Stop": [
      { "matcher": "*", "hooks": [{ "type": "command", "command": "~/.local/bin/claude-ntfy.py" }] }
    ]
  }
}
```

### 動作確認フロー

#### 1. デバッグモードでのテスト

最初の通知はデバッグモードでテストすることをお勧めします。

1. `~/.local/share/claude-ntfy/config.json` を開く
2. `debug_mode` を `true` に設定:

```json
{
  "debug_mode": true,
  ...
}
```

3. 以下のコマンドでテスト通知を送信:

```bash
echo '{"hook_event_name":"Notification","message":"Test notification","cwd":"/tmp","session_id":"test","transcript_path":"/tmp"}' \
  | ~/.local/bin/claude-ntfy.py
```

デバッグモードでは標準出力に詳細ログが表示されます。

#### 2. 通知の確認

**通知は届きましたか？**

- **YES**: おめでとうございます！設定は成功です。デバッグモードをOFFにしてください。
- **NO**: 以下のトラブルシューティングを参照してください。

#### 3. デバッグモードをOFFにする

通知が正常に届いたら、デバッグモードをOFFにします：

1. `~/.local/share/claude-ntfy/config.json` を開く
2. `debug_mode` を `false` に設定:

```json
{
  "debug_mode": false,
  ...
}
```

---

## 手動設定手順（上級者向け）

### 1. ntfy.shトピックの作成

1. https://ntfy.sh にアクセス
2. トピック名を決める（例: `claude-notifications-username`）
3. ntfyアプリ（iOS/Android/Web）でトピックを購読

### 2. ファイルの配置（手動設定）

```bash
# スクリプトを配置
cp claude-ntfy.py ~/.local/bin/
chmod +x ~/.local/bin/claude-ntfy.py

# 設定ファイルを配置（ntfy_urlを編集してから）
mkdir -p ~/.local/share/claude-ntfy
cp config-template.json ~/.local/share/claude-ntfy/config.json
# ~/.local/share/claude-ntfy/config.json を編集してntfy_urlを設定
```

### 3. settings.jsonの更新（手動設定）

`~/.claude/settings.json` に以下を追加：

```json
{
  "hooks": {
    "Notification": [
      { "matcher": "*", "hooks": [{ "type": "command", "command": "~/.local/bin/claude-ntfy.py" }] }
    ],
    "Stop": [
      { "matcher": "*", "hooks": [{ "type": "command", "command": "~/.local/bin/claude-ntfy.py" }] }
    ]
  }
}
```

## 通知イベント

| イベント | タイミング |
|----------|-----------|
| **Notification** | ツール使用の許可プロンプト時 |
| **Stop** | コマンド中断時（Ctrl+Cなど） |

## カスタマイズ

設定ファイル `~/.local/share/claude-ntfy/config.json` で以下を調整：

- **priority**: 1-5（5が最高）
- **title**: 通知タイトル（ASCII文字のみ）
- **tags**: ntfy.shのタグ（カンマ区切り）

詳細は `./setup-examples.md` を参照してください。

## 動作確認

```bash
# 手動実行テスト
echo '{"hook_event_name":"Notification","message":"Test","cwd":"/tmp","session_id":"test","transcript_path":"/tmp"}' \
  | ~/.local/bin/claude-ntfy.py
```

## トラブルシューティング

### 通知が届かない

#### 基本的な確認事項

1. **デバッグモードでテスト**
   ```bash
   # 設定ファイルでdebug_modeをtrueに設定
   echo '{"hook_event_name":"Notification","message":"Test","cwd":"/tmp","session_id":"test","transcript_path":"/tmp"}' \
     | ~/.local/bin/claude-ntfy.py
   ```
   標準出力に詳細ログが表示されます。

2. **エラーログを確認**: `cat ~/claude_ntfy_errors.log`

3. **ntfy_urlが正しいか確認**
   - `~/.local/share/claude-ntfy/config.json` のURLを確認
   - ブラウザで `https://ntfy.sh/YOUR_TOPIC_NAME` にアクセスしてエラーが出ないか確認

4. **ntfyアプリでトピックを購読しているか確認**
   - iOS/Androidアプリでトピックを購読
   - またはWebブラウザで `https://ntfy.sh/YOUR_TOPIC_NAME` を開いて購読

#### 詳細なトラブルシューティング

詳細な手順は `./setup-examples.md` を参照してください。

### エラーの詳細

`./setup-examples.md` に詳細なトラブルシューティング手順があります。

## Pythonスクリプトの要件

- Python 3.6+ で動作
- 標準ライブラリのみ使用（追加インストール不要）
- HTTPヘッダーのサニタイズ機能付き（絵文字対応）

## 既存環境への適用

既に設定されている環境からファイルをコピーして再利用できます：

```bash
# 既存の設定をコピー
cp ~/.local/bin/claude-ntfy.py ./claude-ntfy.py
cp ~/.local/share/claude-ntfy/config.json ./config-template.json
```
