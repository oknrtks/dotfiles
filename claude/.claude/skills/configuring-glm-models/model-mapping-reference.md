# GLMモデルマッピング参考情報

このファイルは、Claudeエイリアス（Opus/Sonnet/Haiku）へのGLMモデルマッピングを設計するための参考情報。

**重要**: GLMモデルは頻繁にアップデートされる。以下は**調査時点（2026年7月）の情報**であり、スキル実行時は必ずSKILL.mdのステップ1でGeminiに最新情報を確認すること。

## Claudeエイリアスの役割

Claude Codeは3つのモデルエイリアスを内部で使い分ける：

| エイリアス | 役割 | Claude相当 |
|---|---|---|
| `opus` | 複雑な推論・計画・長時間エージェントタスク | Claude Opus（最上位） |
| `sonnet` | 日次コーディング・通常タスク | Claude Sonnet（バランス） |
| `haiku` | 軽量処理・バックグラウンド・高速応答 | Claude Haiku（軽量） |

エイリアスは以下の環境変数で制御する：
- `ANTHROPIC_DEFAULT_OPUS_MODEL`
- `ANTHROPIC_DEFAULT_SONNET_MODEL`
- `ANTHROPIC_DEFAULT_HAIKU_MODEL`

## GLMモデルラインナップ（2026年7月時点）

### Opus相当（フラッグシップ）
- **GLM-5.2**: 最新フラッグシップ
  - コンテキスト: 最大1Mトークン（`glm-5.2[1m]`）
  - 最大出力: 131,072トークン
  - 用途: 長時間エージェントワークフロー、複雑なコーディング
  - ライセンス: MIT

### Sonnet相当（中堅）
- **GLM-4.7**: 中堅フラッグシップ
  - コーディング・推論・エージェント機能が強化
  - バランス型
- **GLM-4.6**: コーディング特化（コンテキスト200K）

### Haiku相当（軽量）
- **GLM-4.5-Air**: 軽量・効率モデル
  - パラメータ: 106B総数、12Bアクティブ
  - 低コスト・高速応答

## 設計指針

### モデル選択の基準
1. **Opus**: 必ず最新の最大フラッグシップを割り当てる（推論性能が最も重要）
2. **Sonnet**: コーディング性能とコストのバランスが良い中堅モデル
3. **Haiku**: レイテンシとコスト重視の軽量モデル

### 検証すべきAPIモデルID
設定には**正確なモデルID文字列**が必要。調査時に以下を確認する：
- z.aiのドキュメントに記載のAPIモデルID（例: `glm-5.2`, `glm-4.5-air`）
- 大文字・小文字、ハイフンの有無（例: `glm-4.5-air` が正しく `glm-4.5-Air` は誤りの場合がある）
- コンテキスト拡張版の指定方法（例: `glm-5.2[1m]`）

## 設定ファイルの場所と構造

### 2層構造（重要）
z.aiをClaude Codeで使うには**接続層**と**モデル層**の2つを設定する必要がある。これらは別の場所で管理される:

| 層 | 役割 | 設定場所 | 効果範囲 |
|---|---|---|---|
| 接続層 | z.aiへの接続（BASE_URL/TOKEN） | `~/.bash_local`（シェル環境変数） | 全bashターミナル |
| モデル層 | `/model`リストへのGLM表示（DEFAULT_*_MODEL） | `~/.claude/settings.json`（Claude Code設定） | 設定した階層 |

**よくあるトラブル**: 接続層だけ設定し、モデル層をプロジェクト固有設定に置くと、別ディレクトリで `/model` リストにGLMが出ない（接続はz.aiでも表示はデフォルトのOpus/Sonnet/Haikuになる）。

### モデル層の設定ファイル優先順位（Claude Code）
1. `~/.claude/settings.json`（グローバル・**推奨**・全プロジェクト・全ディレクトリで有効）
2. `<project>/.claude/settings.json`（プロジェクト共有・git管理）
3. `<project>/.claude/settings.local.json`（プロジェクト固有・通常git管理外）

**推奨**: GLMを日常的に使うなら `~/.claude/settings.json`（グローバル）に設定し、全ディレクトリで有効にする。

### dotfiles環境の構造（バインドマウント）
本環境では `~/.claude/` 配下の一部が dotfilesとバインドマウント（同一inode）されており、編集が即座に両方へ反映される:
```
~/.claude/skills/         ←→ dotfiles/claude/.claude/skills/         （スキル）
~/.claude/settings.json   ←→ dotfiles/claude/.claude/settings.json   （グローバル設定）
```
スキルや設定をdotfiles側で編集すると、即座に `~/.claude` から認識・反映され、git管理もされる。

## 設定例（テンプレート）

### 基本設定
```json
{
  "permissions": {
    "allow": [
      "// 既存の権限設定を保持"
    ]
  },
  "env": {
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-5.2",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-4.7",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-4.5-air",
    "ANTHROPIC_DEFAULT_OPUS_MODEL_NAME": "GLM-5.2 via Z.ai",
    "ANTHROPIC_DEFAULT_OPUS_MODEL_DESCRIPTION": "Flagship model for long-horizon tasks",
    "ANTHROPIC_DEFAULT_SONNET_MODEL_NAME": "GLM-4.7 via Z.ai",
    "ANTHROPIC_DEFAULT_SONNET_MODEL_DESCRIPTION": "Balanced model for daily coding",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL_NAME": "GLM-4.5-Air via Z.ai",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL_DESCRIPTION": "Lightweight model for simple tasks"
  }
}
```

### タイムアウト延長が必要な場合
```json
{
  "env": {
    "API_TIMEOUT_MS": "3000000"
  }
}
```

## 情報ソース

- z.ai リリースノート: https://docs.z.ai/release-notes/new-released
- z.ai ブログ: https://z.ai/blog
- 価格表: https://bigmodel.cn/pricing
- Claude Code モデル設定ドキュメント: https://code.claude.com/docs/en/model-config

## 更新履歴

- 2026-07-05: 初版作成（GLM-5.2 / GLM-4.7 / GLM-4.5-Air で構成）
- 2026-07-05: 2層構造（接続層=`.bash_local`／モデル層=`settings.json`）を明記。モデルマッピングをグローバル `~/.claude/settings.json` に置くことを推奨に変更（別ディレクトリで `/model` にGLMが出ない問題の対策）。`settings.json` のバインドマウント構造も追記
