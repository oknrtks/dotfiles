# Claude Code通知設定の詳細

## ファイル配置

```
~/.local/bin/claude-ntfy.py           # 通知スクリプト（実行権限必要）
~/.local/share/claude-ntfy/config.json # 設定ファイル
~/.claude/settings.json                # Claude Code設定（フック登録）
```

## インストール手順

### 1. 通知スクリプトの配置

```bash
# スクリプトをコピー
cp claude-ntfy.py ~/.local/bin/
chmod +x ~/.local/bin/claude-ntfy.py

# 動作確認（JSON入力のテスト）
echo '{"hook_event_name":"Notification","message":"Test","cwd":"/tmp","session_id":"test","transcript_path":"/tmp"}' \
  | ~/.local/bin/claude-ntfy.py
```

### 2. 設定ファイルの配置

```bash
# ディレクトリ作成
mkdir -p ~/.local/share/claude-ntfy

# 設定ファイルを配置（ntfy_urlを変更してから）
cp config-template.json ~/.local/share/claude-ntfy/config.json
```

### 3. ntfy.shトピックの作成

1. https://ntfy.sh にアクセス
2. トピック名を決定（例: `claude-notifications-user123`）
3. 設定ファイルの `ntfy_url` を更新: `"https://ntfy.sh/YOUR_TOPIC_NAME"`
4. ntfyアプリでトピックを購読

### 4. Claude Code設定の更新

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

## 通知イベントの種類

| イベント | 発火タイミング | デフォルト優先度 |
|----------|----------------|------------------|
| Notification | ツール使用の許可プロンプト時 | 5 |
| Stop | コマンド中断時（Ctrl+Cなど） | 4 |
| Error | エラー発生時 | 5 |

## ntfy.sh設定のカスタマイズ

### 優先度（Priority）

- `1`: 最小
- `3`: 通常（デフォルト）
- `5`: 最大

### タグ（Tags）

カンマ区切りで複数指定可能。ntfy.shで絵文字として表示：

- `warning,computer` - 警告アイコン
- `checkmark,tada` - 完了アイコン
- `x,fire` - エラーアイコン

### タイトル（Title）

HTTPヘッダーとして送信されるため、**絵文字は使用できません**。

## トラブルシューティング

### デバッグモードの使用

デバッグモードを有効にすると、スクリプトの実行詳細が標準出力に表示されます。

#### デバッグモードの有効化

**方法1: 設定ファイルで有効化（推奨）**

`~/.local/share/claude-ntfy/config.json` を編集:

```json
{
  "debug_mode": true,
  "ntfy_url": "https://ntfy.sh/YOUR_TOPIC_NAME",
  ...
}
```

**方法2: 環境変数で有効化**

```bash
export CLAUDE_NTFY_DEBUG=true
echo '{"hook_event_name":"Notification","message":"Test","cwd":"/tmp","session_id":"test","transcript_path":"/tmp"}' \
  | ~/.local/bin/claude-ntfy.py
```

#### デバッグログの出力例

```
[DEBUG] [1234567890.12] === Claude ntfy通知フック開始 ===
[DEBUG] [1234567890.12] デバッグモード: True
[DEBUG] [1234567890.13] 設定ファイルを読み込み: /home/user/.local/share/claude-ntfy/config.json
[DEBUG] [1234567890.13] イベント設定読み込み: Notification (priority=5, title=Claude: Input Required, tags=warning,computer)
[DEBUG] [1234567890.14] 入力JSON: {"hook_event_name":"Notification","message":"Test","cwd":"/tmp","session_id":"test","transcript_path":"/tmp"}
[DEBUG] [1234567890.14] フック入力解析: event=Notification, cwd=/tmp
[DEBUG] [1234567890.15] 通知送信開始: event=Notification, url=https://ntfy.sh/YOUR_TOPIC_NAME, body=[Global @ hostname] Test
[DEBUG] [1234567890.15] ヘッダー: {'Priority': '5', 'Title': 'Claude: Input Required', 'Tags': 'warning,computer'}
[DEBUG] [1234567890.45] 通知送信成功: HTTP 200
[DEBUG] [1234567890.45] === Claude ntfy通知フック完了 ===
```

#### トラブルシューティングフローチャート

```
通知が届かない
    │
    ├─ デバッグモードでテスト実行
    │   └─ 標準出力にエラーはある？
    │       │
    │       ├─ あり → エラーメッセージを確認
    │       │       │
    │       │       ├─ "設定ファイルが見つかりません"
    │       │       │   → 設定ファイルのパスを確認
    │       │       │
    │       │       ├─ "未定義のイベント"
    │       │       │   → 設定ファイルのeventsセクションを確認
    │       │       │
    │       │       ├─ "通知送信エラー"
    │       │       │   ├─ "Connection refused" → ネットワーク接続を確認
    │       │       │   ├─ "HTTP 404" → ntfy_urlのトピック名を確認
    │       │       │   └─ "HTTP 4xx" → ntfy.shの制限を確認
    │       │       │
    │       │       └─ "JSONパースエラー"
    │       │           → 標準入力のJSON形式を確認
    │       │
    │       └─ なし → 次へ
    │
    ├─ エラーログを確認
    │   └─ cat ~/claude_ntfy_errors.log
    │
    ├─ ntfy_urlを確認
    │   └─ ブラウザで https://ntfy.sh/YOUR_TOPIC_NAME にアクセス
    │       └─ エラーが出る → トピック名が間違っている可能性
    │
    ├─ ntfyアプリで購読を確認
    │   └─ トピックを購読しているか再確認
    │
    └─ 手動でntfy.shにテスト送信
        └─ curl -d "Test message" ntfy.sh/YOUR_TOPIC_NAME
```

### 通知が届かない

#### 基本的な確認事項

1. **デバッグモードでテスト**: 上記の手順でデバッグモードを有効にして実行
2. **エラーログを確認**: `cat ~/claude_ntfy_errors.log`
3. **ntfy.shトピックが正しいか確認**:
   ```bash
   # ブラウザでトピックにアクセス
   xdg-open https://ntfy.sh/YOUR_TOPIC_NAME
   ```
4. **ntfyアプリでトピックを購読しているか確認**
5. **手動でntfy.shに直接送信**:
   ```bash
   curl -d "Test message" ntfy.sh/YOUR_TOPIC_NAME
   ```

### HTTPエラーが発生する

- 設定ファイルのJSON構文を確認
- ntfy_urlが正しいか確認
- ネットワーク接続を確認

### 絵文字が表示されない

- HTTPヘッダーはASCIIのみ対応
- 絵文字をタイトルから削除するか、本文に含める

## フック入力のJSON構造

### Notificationイベント

```json
{
  "session_id": "uuid",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "hook_event_name": "Notification",
  "message": "Claude needs your permission to use Bash",
  "notification_type": "permission_prompt"
}
```

### Stopイベント

```json
{
  "session_id": "uuid",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "hook_event_name": "Stop",
  "permission_mode": "acceptEdits",
  "stop_hook_active": false,
  "last_assistant_message": "最後のメッセージ..."
}
```

## 通知メッセージの形式

```
[プロジェクト名 @ ホスト名] メッセージ本文
```

例:
```
[LLMComunicator @ macbook.local] Claude needs your permission to use Bash
```
