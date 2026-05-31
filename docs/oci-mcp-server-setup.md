# OCI MCP Server Setup Guide

Oracle Cloud Infrastructure (OCI) MCP サーバーの設定手順。

## 概要

Oracle は公式に OCI 用の MCP (Model Context Protocol) サーバーを 2 種類提供しています。

| サーバー | 内容 | リポジトリ |
|---------|------|-----------|
| **oci-api-mcp-server** | OCI CLI コマンド実行 | `oracle/mcp` |
| **oci-cloud-mcp-server** | OCI Python SDK 直接呼び出し | `oracle/mcp` |

## 事前準備

### 1. OCI CLI のインストール

```bash
# Linux/macOS
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# バージョン確認
oci --version
```

### 2. OCI CLI の設定

```bash
# API Key 認証
oci setup config

# セッショントークン認証（推奨）
oci session authenticate --region=<region> --tenancy-name=<tenancy_name>
```

設定ファイルは `~/.oci/config` に保存されます。

### 3. uv のインストール

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## MCP サーバーの追加

### 1. グローバル MCP サーバー設定の追加

**全プロジェクトで使用する場合**、`~/.claude.json` のルートレベルに `mcpServers` を追加します：

```bash
# ~/.claude.json を編集
```

```json
{
  "mcpServers": {
    "oracle-oci-api-mcp-server": {
      "command": "uvx",
      "args": ["oracle.oci-api-mcp-server@latest"],
      "env": {
        "OCI_CONFIG_PROFILE": "DEFAULT",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    },
    "oracle-oci-cloud-mcp-server": {
      "command": "uvx",
      "args": ["oracle.oci-cloud-mcp-server@latest"],
      "env": {
        "OCI_CONFIG_PROFILE": "DEFAULT",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

### 2. Claude Code の再起動

設定を反映させるために Claude Code を再起動します。

### 3. 動作確認

MCP サーバーが正しく読み込まれたか確認するには、`claude mcp list` コマンドを使用します：

```bash
claude mcp list
```

## 利用可能なツール

### oci-api-mcp-server（CLI 実行）

| ツール名 | 説明 |
|---------|------|
| `get_oci_command_help` | OCI CLI コマンドのヘルプ取得 |
| `run_oci_command` | OCI CLI コマンド実行 |
| `get_oci_commands` | OCI サービスとコマンドの情報取得 |

### oci-cloud-mcp-server（SDK 呼び出し）

| ツール名 | 説明 |
|---------|------|
| `list_oci_clients` | 利用可能な OCI SDK クライアントを一覧表示 |
| `find_oci_api` | SDK メソッドをキーワード検索 |
| `describe_oci_operation` | SDK メソッドの詳細取得 |
| `invoke_oci_api` | SDK メソッド直接呼び出し |
| `list_client_operations` | 指定クライアントの操作を一覧表示 |

## 認証方式

### API Key 認証（デフォルト）

永続的な API キーを使用。`~/.oci/config` で設定：

```ini
[DEFAULT]
user=ocid1.user.oc1..aaaa...
fingerprint=a6:8f:43:ec:ad:8f:2a:22:af:f4:e0:cf:47:ff:59:cd
tenancy=ocid1.tenancy.oc1..aaaa...
region=ap-osaka-1
key_file=~/.oci/oci_api_key.pem
```

CLI サーバーで API Key 認証を強制する場合：

```json
{
  "env": {
    "OCI_CLI_AUTH": "api_key"
  }
}
```

### セッショントークン認証

一時的なセッショントークンを使用。ブラウザでの認証が必要。

```bash
oci session authenticate --region=ap-osaka-1 --tenancy-name=<tenancy_name>
```

ブラウザで表示された URL を開き、OCI のログイン画面で認証を完了すると、`localhost:8181` にリダイレクトされてトークンが保存されます。

## 使用例

### SDK サーバーでコンパートメント一覧取得

```
invoke_oci_api(
  client_fqn="oci.identity.IdentityClient",
  operation="list_compartments",
  params={"compartment_id": "ocid1.tenancy.oc1..aaaa..."}
)
```

### SDK サーバーでクライアント一覧取得

```
list_oci_clients()
```

### CLI サーバーでインスタンス一覧取得

```
run_oci_command(
  command="compute instance list --compartment-id ocid1.tenancy.oc1..aaaa..."
)
```

## トラブルシューティング

### "Config value for 'security_token_file' must be specified"

CLI サーバーがセッショントークン認証を試みています。以下のいずれかで対応：

1. API Key 認証を強制：`OCI_CLI_AUTH=api_key` を環境変数に追加
2. セッショントークン認証を設定：`oci session authenticate` を実行

### MCP サーバーが読み込まれない

1. `~/.claude.json` の `mcpServers` が正しく設定されているか確認
2. `claude mcp list` でサーバーが認識されているか確認
3. Claude Code を再起動

### 認証エラー

1. `~/.oci/config` の権限を確認（`chmod 600 ~/.oci/config`）
2. プロファイル名が正しいか確認
3. トークンの有効期限が切れていないか確認

### uvx が見つからない

```bash
# uv がインストールされているか確認
which uvx

# インストールされていない場合
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 参考リンク

- Oracle MCP リポジトリ: https://github.com/oracle/mcp
- OCI CLI ドキュメント: https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm
- OCI SDK ドキュメント: https://docs.oracle.com/en-us/iaas/tools/python/latest/

## 設定ファイルの場所

| ファイル | 場所 | 説明 |
|---------|------|------|
| MCP サーバー設定 | `~/.claude.json`（ルートの `mcpServers`） | グローバル（全プロジェクトで使用） |
| プロジェクト MCP 設定 | `<project>/.mcp.json` | プロジェクト固有の設定 |
| Claude Code 設定 | `~/.claude/settings.json` | グローバル設定 |
| OCI 設定 | `~/.oci/config` | OCI CLI 設定 |
| OCI セッショントークン | `~/.oci/<profile>_token` | セッショントークン認証時 |

## 更新履歴

- 2026-05-31: グローバル設定を `~/.claude.json` に修正
- 2026-05-31: `enableAllProjectMcpServers` の使用を廃止
- 2026-05-31: `claude mcp list` コマンドの記載を追加
- 2026-05-31: 初版作成
