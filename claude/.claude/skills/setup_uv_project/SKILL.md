---
name: setup_uv_project
description: Use this skill when creating new Python projects using uv package manager. This includes initializing projects with uv init, setting up library or CLI tool structures with --lib flag, adding dependencies, configuring development tools like ruff and pytest, and establishing Python version requirements. Invoke when the user wants to start a Python project, create a new package, scaffold a CLI tool, or set up a Python development environment with uv.
---

# uv を使用した Python プロジェクト初期化

`uv` パッケージマネージャーを使用して、ベストプラクティスに基づいた堅牢な Python プロジェクトを初期化します。

## 入力パラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|------|------|-----------|------|
| `project_name` | string | Yes | - | プロジェクト名（ケバブケース推奨: `my-awesome-tool`） |
| `is_cli_tool` | boolean | No | `false` | CLIツールとして設定する場合は `true` |
| `dependencies` | list | No | `[]` | 初期インストールするライブラリのリスト |
| `python_version` | string | No | `"3.12"` | Python のバージョン |

## 処理フロー

### 1. プロジェクトの初期化

`uv init --lib` でプロジェクトを作成します。`--lib` オプションにより `src/` レイアウトが強制されます。

```bash
uv init --lib <project_name> --python <python_version>
```

生成されるディレクトリ構造:

```
<project_name>/
├── src/
│   └── <project_name>/     # パッケージ名（ハイフン→アンダースコア変換）
│       └── __init__.py
├── pyproject.toml
├── .python-version
└── README.md
```

### 2. CLI ツール設定（オプション）

`is_cli_tool = true` の場合、`pyproject.toml` に CLI エントリーポイントを追加します。

**命名規則**: プロジェクト名のハイフン(`-`)をアンダースコア(`_`)に変換

例: `my-awesome-tool` → `my_awesome_tool`

```toml
[project.scripts]
my-awesome-tool = "my_awesome_tool.main:main"
```

### 3. 依存関係の追加

```bash
cd <project_name>
uv add <dep1> <dep2> ...
```

### 4. 開発用ツールの追加

品質管理のため、開発用ツールを追加します。

```bash
uv add --dev ruff pytest
```

## pyproject.toml の構造

初期設定後の `pyproject.toml` は以下の構造になります:

```toml
[project]
name = "<project_name>"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=<python_version>"
dependencies = []

# is_cli_tool = true の場合のみ
[project.scripts]
<project_name> = "<project_name_underscore>.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## 使用例

### ライブラリプロジェクトの作成

```bash
# 基本的なライブラリ
uv init --lib my-data-utils --python 3.12
cd my-data-utils
uv add --dev ruff pytest
```

### CLI ツールの作成

```bash
# CLI ツールとして設定
uv init --lib my-awesome-tool --python 3.12
cd my-awesome-tool
uv add --dev ruff pytest

# pyproject.toml に追記
# [project.scripts]
# my-awesome-tool = "my_awesome_tool.main:main"

# src/my_awesome_tool/main.py を作成
def main():
    print("Hello from my-awesome-tool!")
```

### 特定ライブラリを含むプロジェクト

```bash
uv init --lib my-service --python 3.12
cd my-service
uv add requests pydantic
uv add --dev ruff pytest
```

## ベストプラクティス

- プロジェクト名はケバブケース（`my-awesome-tool`）を使用
- Python バージョンは明示的に指定（推奨: `3.12`）
- 必ず `--lib` オプションを使用して `src/` レイアウトを適用
- 開発用ツール（ruff, pytest）は最初から導入
- CLI ツールの場合はエントリーポイントを適切に設定

## トラブルシューティング

### `uv` コマンドが見つからない

```bash
# uv のインストール
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Python バージョンが利用できない

```bash
# 利用可能な Python バージョンを確認
uv python list

# 特定バージョンの Python をインストール
uv python install 3.12
```

### 依存関係の追加に失敗

```bash
# キャッシュをクリア
uv cache clean

# 再試行
uv add <package>
```
