---
name: configuring-glm-models
description: z.ai（Zhipu AI）のGLMモデルをClaude Codeで使用するための設定を行います。最新GLMモデルのバージョン調査、settings.json/settings.local.jsonへのモデル設定追加、Opus/Sonnet/HaikuエイリアスのGLMモデルへのマッピング、モデル切り替えと検証までを網羅します。ユーザーが「GLMを使いたい」「z.aiを設定したい」「Claude CodeでGLMを使う」「最新のGLMモデルを調べたい」「GLMのバージョンをアップデートしたい」などと言った場合に使用します。
---

# Configuring GLM Models for Claude Code

z.ai（Zhipu AI）のGLMモデルをClaude Codeで使用できるように設定するスキル。
OpenAI互換APIエンドポイント（`https://api.z.ai/api/anthropic`）経由でGLMモデルを利用する。

## 前提条件の確認

設定開始前に以下を確認する：

1. **API認証情報が設定済みか**:
   ```bash
   env | grep -E "ANTHROPIC_BASE_URL|ANTHROPIC_AUTH_TOKEN"
   ```
   - `ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic` が設定されていること
   - `ANTHROPIC_AUTH_TOKEN` が設定されていること
   - 未設定の場合は、ユーザーにz.ai（https://z.ai ）でのAPIキー取得を案内する

2. **APIキーが未設定の場合**:
   - z.aiでアカウント作成後にAPIキーを取得
   - `settings.json` の `env` セクションに追加:
     ```json
     {
       "env": {
         "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
         "ANTHROPIC_AUTH_TOKEN": "YOUR_ZAI_API_KEY"
       }
     }
     ```

## 実行手順

### ステップ1: 最新GLMモデルの調査

GLMモデルは頻繁にアップデートされるため、**必ず最新情報をGeminiで調査**する（CLAUDE.mdの指示に従う）：

```bash
uvx git+https://github.com/oknrtks/gemini-ask "z.ai（Zhipu AI）のGLMモデルの最新バージョンと特徴、Claude Code（ANTHROPIC互換APIエンドポイント https://api.z.ai/api/anthropic）で利用可能なモデルID一覧を教えてください。Opus/Sonnet/Haiku相当の使い分けも含めて。" --model "gemini-2.5-flash"
```

503が返ってきた場合は数秒待って再実行する。

調査で得るべき情報：
- 最新のフラッグシップモデル（Opus相当）
- 中堅モデル（Sonnet相当）
- 軽量モデル（Haiku相当）
- 各モデルの正確なモデルID（API呼び出しで使用する文字列）

### ステップ2: 現在の設定確認

既存の設定ファイルを確認し、上書きしないようにする：

```bash
# プロジェクト設定（推奨：dotfiles管理）
cat .claude/settings.local.json 2>/dev/null
# グローバル設定
cat ~/.claude/settings.json 2>/dev/null
```

モデル設定が既存の`env`セクションにないか確認。既にある場合は最新情報に更新する。

### ステップ3: モデルマッピングの設計

Geminiの調査結果を基に、Claudeの3エイリアスをGLMモデルにマッピングする。マッピング指針と最新モデル情報は `./model-mapping-reference.md` を参照。

基本方針：
| Claudeエイリアス | 役割 | GLMモデル選択基準 |
|---|---|---|
| `opus` | 複雑な推論・長時間タスク | 最新フラッグシップ（長コンテキスト） |
| `sonnet` | 日次コーディング | バランス型中堅モデル |
| `haiku` | 軽量・高速タスク | 軽量・低コストモデル |

### ステップ4: 設定ファイルの更新

**更新対象ファイルの優先順位**:
1. プロジェクトの `.claude/settings.local.json`（推奨・dotfiles管理される）
2. グローバルの `~/.claude/settings.json`（全プロジェクト共通にしたい場合）

`permissions`など既存の設定を**保持したまま**、`env`セクションに以下を追記する（`<最新フラッグシップ>`等はステップ1の調査結果で置換）：

```json
{
  "permissions": {
    "allow": [
      "// 既存の権限設定を保持"
    ]
  },
  "env": {
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "<フラッグシップのモデルID>",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "<中堅のモデルID>",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "<軽量のモデルID>",
    "ANTHROPIC_DEFAULT_OPUS_MODEL_NAME": "<フラッグシップ名> via Z.ai",
    "ANTHROPIC_DEFAULT_OPUS_MODEL_DESCRIPTION": "<フラッグシップの説明>",
    "ANTHROPIC_DEFAULT_SONNET_MODEL_NAME": "<中堅名> via Z.ai",
    "ANTHROPIC_DEFAULT_SONNET_MODEL_DESCRIPTION": "<中堅の説明>",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL_NAME": "<軽量名> via Z.ai",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL_DESCRIPTION": "<軽量の説明>"
  }
}
```

**編集時の注意**:
- Editツールで `old_string`/`new_string` を使い、既存JSON構造を破損しない
- JSONのカンマや括弧の対応に注意（編集後は必ずReadで検証）

### ステップ5: モデル切り替えと検証

設定を有効化するにはClaude Codeの**再起動が必要**。ユーザーに以下を案内する：

1. **Claude Codeを再起動**（現在のセッションを終了して新規起動）
2. **モデル切り替え**: `/model` コマンドでGLMモデルを選択
   ```
   /model glm-5.2
   ```
   または `/model` で対話的に選択
3. **動作確認**: 短い応答をリクエストして、GLMモデルが応答することを確認

## トラブルシューティング

### 設定が反映されない
- Claude Codeを完全に再起動したか確認
- 設定ファイルのJSON構文エラーがないか確認（`cat` で確認）
- `env` セクションが正しい階層にあるか確認

### モデル呼び出しでエラー
- `ANTHROPIC_BASE_URL` と `ANTHROPIC_AUTH_TOKEN` が正しく設定されているか確認
- モデルIDが正しいか確認（ステップ1の調査結果と照合）
- z.aiのAPIキーが有効期限切れでないか確認
- APIタイムアウト設定が必要な場合: `env` に `"API_TIMEOUT_MS": "3000000"` を追加

### 既存のAnthropic使用設定と競合
- `ANTHROPIC_API_KEY` やデフォルトの `ANTHROPIC_BASE_URL` が別途設定されている場合、z.ai設定が上書きされる可能性
- 環境変数と settings.json の `env` の優先順位に注意

## 補足: OpenRouter経由での代替利用

z.ai直接接続以外に、OpenRouter経由でもGLMモデルを利用可能：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://openrouter.ai/api/v1/proxy",
    "ANTHROPIC_AUTH_TOKEN": "YOUR_OPENROUTER_API_KEY",
    "ANTHROPIC_MODEL": "zhipu-ai/glm-5.2"
  }
}
```

## 参考情報

- **z.ai リリースノート**: https://docs.z.ai/release-notes/new-released
- **モデルマッピングの詳細**: `./model-mapping-reference.md`
- **Geminiへの質問方法**: `consulting-gemini` スキルを参照
