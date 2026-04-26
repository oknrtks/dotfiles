# oci-design-queryスキル改善計画（FastAPIサーバー方式）

## 作成日時

2026-04-26

## 現状の問題点

### 重大な問題

1. **思想と実装の矛盾**
   - 設計：「DataFrameをメモリにキャッシュ」
   - 実装：CLIツールで毎回プロセス終了
   - 結果：キャッシュが保持されない

2. **プロセスのライフサイクル無視**
   - CLIツールは実行のたびに新しいプロセス
   - プロセス終了時にメモリ上のDataFrameは破棄
   - 「キャッシュ」の意味がない

3. **「誰がプロセスとして生き続けるか」の不明確さ**
   - DataFrameを保持するプロセスがいない
   - PLAN.mdの思想を実現できていない

### 原因の分析

**問い**: 「メモリにDataFrameを保持」と言いつつ、どう実現するつもりだったか？

**答え**: 深く考えていなかった。具体性が欠如していた。

---

## 解決策: FastAPIサーバー方式

### アーキテクチャ概要

```
┌─────────────┐         HTTP          ┌──────────────────────┐
│   Claude    │ ───────────────────→  │  FastAPI Server      │
│  (Client)   │ ←───────────────────  │  (常駐プロセス)       │
└─────────────┘   JSON Response       └──────────────────────┘
                                                │
                                                ↓
                                          ┌──────────┐
                                          │  Memory  │
                                          │  │
                                          │  ├─ DataFrameキャッシュ
                                          │  ├─ インデックス
                                          │  └─ タイムスタンプ
                                          └──────────┘
```

**核となる概念**:
- **サーバーが常駐プロセスとして動く**
- **サーバー内でDataFrameをメモリに保持**
- **ClaudeはHTTPで問い合わせる**

---

## Phase 1: FastAPIサーバーの実装

### 1.1 サーバーエンドポイント

**ファイル**: `lib/server.py`

```python
#!/usr/bin/env python
"""OCI設計書問い合わせサーバー"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from lib.oci_inventory import OCIInventory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="OCI Inventory Server")
inventory: Optional[OCIInventory] = None
server_start_time = time.time()


class ServerConfig:
    """サーバー設定"""
    def __init__(self):
        self.base_dir = Path.cwd()  # プロジェクトルート
        self.port = 8000
        self.host = "127.0.0.1"


config = ServerConfig()


class StartupConfig(BaseModel):
    """起動時設定"""
    base_dir: str


@app.on_event("startup")
async def startup_event():
    """サーバー起動時の初期化"""
    global inventory

    logger.info("Starting OCI Inventory Server...")
    logger.info(f"Base directory: {config.base_dir}")

    inventory = OCIInventory(config.base_dir)
    logger.info("OCI Inventory initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """サーバー終了時のクリーンアップ"""
    logger.info("Shutting down OCI Inventory Server...")

    if inventory:
        # 統計情報をログ
        stats = inventory.get_stats()
        logger.info(f"Final stats: {stats}")


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "uptime_seconds": time.time() - server_start_time,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/row/{tenant_id}/{resource_type}/{primary_key}")
async def get_row(tenant_id: str, resource_type: str, primary_key: str):
    """特定リソースの全属性値を取得"""
    try:
        result = inventory.get_row(tenant_id, resource_type, primary_key)
        return result
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_row: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/column/{tenant_id}/{column_name}")
async def get_column_values(tenant_id: str, column_name: str):
    """列の全設定値を取得"""
    try:
        result = inventory.get_column_values(tenant_id, column_name)
        return result
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_column_values: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/{tenant_id}")
async def search(tenant_id: str, filters: dict):
    """条件検索"""
    try:
        result = inventory.search(tenant_id, filters)
        return result
    except Exception as e:
        logger.error(f"Error in search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/tenants")
async def search_tenants(filters: dict):
    """テナント横断検索"""
    try:
        result = inventory.search_across_tenants(filters)
        return result
    except Exception as e:
        logger.error(f"Error in search_tenants: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reload/{tenant_id}")
async def reload_tenant(tenant_id: str):
    """テナントデータの手動リロード"""
    try:
        inventory.reload_tenant(tenant_id)
        return {"status": "reloaded", "tenant_id": tenant_id}
    except Exception as e:
        logger.error(f"Error in reload_tenant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """統計情報"""
    return inventory.get_stats()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "lib.server:app",
        host=config.host,
        port=config.port,
        log_level="info",
        reload=False  # 本番環境ではリロード無効
    )
```

---

### 1.2 OCIInventoryクラス（キャッシュ管理）

**ファイル**: `lib/oci_inventory.py`

```python
#!/usr/bin/env python
"""OCI設計書在庫管理クラス"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TenantCache:
    """テナント単位のキャッシュ"""

    def __init__(self, tenant_dir: Path):
        self.tenant_dir = tenant_dir
        self.tenant_id = tenant_dir.name
        self.cache_dir = tenant_dir / ".cache"
        self.cache_dir.mkdir(exist_ok=True)

        # キャッシュ
        self._dataframes: Dict[str, pd.DataFrame] = {}  # {file:sheet → DataFrame}
        self._index: Optional[dict] = None
        self._mtimes: Dict[str, float] = {}

        logger.info(f"Initialized cache for tenant: {self.tenant_id}")

    def load_index(self) -> dict:
        """インデックスをロード（必要なら再構築）"""
        if self._index:
            return self._index

        index_file = self.cache_dir / f"{self.tenant_id}_index.json"

        # 更新チェック
        if self._needs_rebuild():
            logger.info(f"Rebuilding index for {self.tenant_id}")
            self._rebuild_index()
        else:
            logger.info(f"Loading cached index for {self.tenant_id}")
            self._index = json.loads(index_file.read_text())

        return self._index

    def _needs_rebuild(self) -> bool:
        """インデックスの再構築が必要かチェック"""
        index_file = self.cache_dir / f"{self.tenant_id}_index.json"

        if not index_file.exists():
            return True

        # タイムスタンプ比較
        try:
            index = json.loads(index_file.read_text())
            cached_mtimes = index.get("files_mtime", {})
        except:
            return True

        current_mtimes = {
            f.name: f.stat().st_mtime
            for f in self.tenant_dir.glob("*.xlsx")
        }

        return current_mtimes != cached_mtimes

    def _rebuild_index(self):
        """インデックスを再構築"""
        from lib.index_builder import build_tenant_index

        self._index = build_tenant_index(self.tenant_dir, self)

        # 保存
        index_file = self.cache_dir / f"{self.tenant_id}_index.json"
        index_file.write_text(
            json.dumps(self._index, ensure_ascii=False, indent=2)
        )

        logger.info(f"Index rebuilt for {self.tenant_id}")

    def get_dataframe(self, file_name: str, sheet_name: str) -> pd.DataFrame:
        """DataFrameを取得（キャッシュからまたはロード）"""
        key = f"{file_name}:{sheet_name}"

        if key in self._dataframes:
            logger.debug(f"Cache hit: {key}")
            return self._dataframes[key]

        logger.info(f"Loading DataFrame: {key}")
        file_path = self.tenant_dir / file_name

        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            self._dataframes[key] = df
            self._mtimes[file_name] = file_path.stat().st_mtime
            return df
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise

    def invalidate_file(self, file_name: str):
        """特定ファイルのキャッシュを無効化"""
        keys_to_remove = [k for k in self._dataframes.keys() if k.startswith(f"{file_name}:")]

        for key in keys_to_remove:
            del self._dataframes[key]
            logger.info(f"Invalidated cache: {key}")

    def get_row(self, sheet: str, row: int, file_name: str) -> dict:
        """キャッシュされたDataFrameから行を取得"""
        df = self.get_dataframe(file_name, sheet)
        return df.iloc[row].to_dict()


class OCIInventory:
    """OCI設計書在庫管理（マルチテナント対応）"""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self._tenants: Dict[str, TenantCache] = {}

        logger.info(f"OCI Inventory initialized with base_dir: {base_dir}")

    def _get_tenant(self, tenant_id: str) -> TenantCache:
        """テナントキャッシュを取得（遅延ロード）"""
        if tenant_id not in self._tenants:
            tenant_dir = self.base_dir / tenant_id

            if not tenant_dir.is_dir():
                raise ValueError(f"Tenant directory not found: {tenant_id}")

            self._tenants[tenant_id] = TenantCache(tenant_dir)

        return self._tenants[tenant_id]

    def get_row(self, tenant_id: str, resource_type: str, primary_key: str) -> dict:
        """特定リソースの全属性値を取得"""
        tenant = self._get_tenant(tenant_id)
        index = tenant.load_index()

        if resource_type not in index["index"]["by_resource"]:
            available = list(index["index"]["by_resource"].keys())
            raise KeyError(
                f"Resource type not found: {resource_type}. "
                f"Available: {available}"
            )

        if primary_key not in index["index"]["by_resource"][resource_type]:
            available = list(index["index"]["by_resource"][resource_type].keys())[:5]
            raise KeyError(
                f"Resource not found: {primary_key}. "
                f"Available examples: {available}"
            )

        location = index["index"]["by_resource"][resource_type][primary_key]

        # キャッシュされたDataFrameから取得
        row_data = tenant.get_row(location["sheet"], location["row"], location["file"])

        # pandasの型をJSONシリアライズ可能に変換
        return {k: str(v) if pd.notna(v) else None for k, v in row_data.items()}

    def get_column_values(self, tenant_id: str, column_name: str) -> dict:
        """列の全設定値を取得"""
        tenant = self._get_tenant(tenant_id)
        index = tenant.load_index()

        if column_name not in index["index"]["by_column_values"]:
            available = list(index["index"]["by_column_values"].keys())[:5]
            raise KeyError(
                f"Column not found: {column_name}. "
                f"Available: {available}"
            )

        return index["index"]["by_column_values"][column_name]

    def search(self, tenant_id: str, filters: dict) -> list:
        """条件検索"""
        # TODO: 実装
        return []

    def search_across_tenants(self, filters: dict) -> dict:
        """テナント横断検索"""
        # TODO: 実装
        return {}

    def reload_tenant(self, tenant_id: str):
        """テナントデータの手動リロード"""
        if tenant_id in self._tenants:
            del self._tenants[tenant_id]
            logger.info(f"Reloaded tenant: {tenant_id}")

    def get_stats(self) -> dict:
        """統計情報"""
        stats = {
            "base_dir": str(self.base_dir),
            "tenants_loaded": len(self._tenants),
            "tenants": {}
        }

        for tenant_id, tenant in self._tenants.items():
            stats["tenants"][tenant_id] = {
                "dataframes_cached": len(tenant._dataframes),
                "index_loaded": tenant._index is not None
            }

        return stats
```

---

### 1.3 インデックスビルダー

**ファイル**: `lib/index_builder.py`

```python
#!/usr/bin/env python
"""インデックス構築モジュール"""

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_tenant_index(tenant_dir: Path, tenant_cache) -> dict:
    """テナントディレクトリからインデックスを構築"""
    index = {
        "tenant_id": tenant_dir.name,
        "last_updated": None,  # 呼び出し元で設定
        "files_mtime": {},
        "index": {
            "by_resource": {},
            "by_column_values": {}
        }
    }

    excel_files = list(tenant_dir.glob("*.xlsx"))
    logger.info(f"Found {len(excel_files)} Excel files in {tenant_dir}")

    for file in excel_files:
        logger.info(f"Processing: {file.name}")
        index["files_mtime"][file.name] = file.stat().st_mtime

        xl = pd.ExcelFile(file)
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(file, sheet_name=sheet_name)

            # 主キー列を探す
            if '#' not in df.columns:
                logger.debug(f"Skipping sheet {sheet_name} in {file.name}: no '#' column")
                continue

            # by_resourceインデックス構築
            for idx, row in df.iterrows():
                if pd.notna(row['#']):
                    primary_key = str(row['#']).strip()
                    resource_type = sheet_name

                    if resource_type not in index["index"]["by_resource"]:
                        index["index"]["by_resource"][resource_type] = {}

                    index["index"]["by_resource"][resource_type][primary_key] = {
                        "sheet": sheet_name,
                        "row": idx,
                        "file": file.name
                    }

            # by_column_valuesインデックス構築
            for col in df.columns:
                if col == '#':
                    continue

                if col not in index["index"]["by_column_values"]:
                    index["index"]["by_column_values"][col] = {}

                for val in df[col].dropna().unique():
                    val_str = str(val)
                    if val_str not in index["index"]["by_column_values"][col]:
                        index["index"]["by_column_values"][col][val_str] = []

                    # 該当するリソースを追加（重複防止）
                    matching_rows = df[df[col] == val]
                    for _, row in matching_rows.iterrows():
                        if pd.notna(row['#']):
                            primary_key = str(row['#']).strip()
                            resource_type = sheet_name
                            key = f"{resource_type}:{primary_key}"
                            if key not in index["index"]["by_column_values"][col][val_str]:
                                index["index"]["by_column_values"][col][val_str].append(key)

    return index
```

---

## Phase 2: サーバー管理スクリプト

### 2.1 サーバー起動スクリプト

**ファイル**: `scripts/start-server.sh`

```bash
#!/bin/bash
# FastAPIサーバーをバックグラウンドで起動

set -e

PORT="${OCI_INVENTORY_PORT:-8000}"
HOST="${OCI_INVENTORY_HOST:-127.0.0.1}"
PID_FILE="$HOME/.oci_inventory_server.pid"
LOG_FILE="$HOME/.oci_inventory_server.log"

# 既に起動していないかチェック
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "サーバーは既に起動しています (PID: $PID)"
        exit 0
    else
        echo "古いPIDファイルを削除します"
        rm -f "$PID_FILE"
    fi
fi

echo "==> OCI Inventory Serverを起動します"
echo "    Port: $PORT"
echo "    Host: $HOST"
echo "    Log: $LOG_FILE"

# uv環境の確認
if ! command -v uv &> /dev/null; then
    echo "エラー: uvがインストールされていません"
    exit 1
fi

# サーバーをバックグラウンドで起動
nohup uv run uvicorn lib.server:app \
    --host "$HOST" \
    --port "$PORT" \
    --log-level info \
    >> "$LOG_FILE" 2>&1 &

SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"

echo "==> サーバーを起動しました (PID: $SERVER_PID)"

# ヘルスチェックを待機
echo "==> ヘルスチェック中..."
for i in {1..30}; do
    if curl -s "http://$HOST:$PORT/health" > /dev/null 2>&1; then
        echo "✓ サーバーが準備完了しました"
        echo ""
        echo "次のコマンドで確認できます:"
        echo "  curl http://$HOST:$PORT/health"
        exit 0
    fi
    sleep 1
done

echo "エラー: サーバーが起動しませんでした"
echo "ログを確認してください: $LOG_FILE"
exit 1
```

---

### 2.2 サーバー停止スクリプト

**ファイル**: `scripts/stop-server.sh`

```bash
#!/bin/bash
# FastAPIサーバーを停止

PID_FILE="$HOME/.oci_inventory_server.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "サーバーは起動していません"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "サーバーは既に停止しています"
    rm -f "$PID_FILE"
    exit 0
fi

echo "==> サーバーを停止します (PID: $PID)"
kill "$PID"

# プロセス終了を待機
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "✓ サーバーを停止しました"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# 強制終了
echo "==> サーバーが応答しないため強制終了します"
kill -9 "$PID"
rm -f "$PID_FILE"
echo "✓ サーバーを強制終了しました"
```

---

### 2.3 サーバー状態確認スクリプト

**ファイル**: `scripts/server-status.sh`

```bash
#!/bin/bash
# サーバーの状態を確認

PORT="${OCI_INVENTORY_PORT:-8000}"
HOST="${OCI_INVENTORY_HOST:-127.0.0.1}"
PID_FILE="$HOME/.oci_inventory_server.pid"

echo "==> OCI Inventory Server Status"
echo ""

# プロセスチェック
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "プロセス: 実行中 (PID: $PID)"
    else
        echo "プロセス: 停止中 (古いPIDファイルがあります)"
        rm -f "$PID_FILE"
    fi
else
    echo "プロセス: 停止中"
fi

# ヘルスチェック
echo ""
echo "==> ヘルスチェック"
if curl -s "http://$HOST:$PORT/health" | jq .; then
    echo ""
    echo "✓ サーバーは正常に動作しています"
    exit 0
else
    echo "✗ サーバーに接続できません"
    exit 1
fi
```

---

## Phase 3: クライアントライブラリ

### 3.1 Pythonクライアント

**ファイル**: `lib/client.py`

```python
#!/usr/bin/env python
"""OCI Inventory ServerのPythonクライアント"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCIInventoryClient:
    """OCI Inventory Serverのクライアント"""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def _ensure_server(self):
        """サーバーが起動していることを確認"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=2)
            response.raise_for_status()
            return True
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"OCI Inventory Serverが起動していません: {self.base_url}\n"
                f"起動してください: ./scripts/start-server.sh"
            )

    def get_row(self, tenant_id: str, resource_type: str, primary_key: str) -> dict:
        """特定リソースの全属性値を取得"""
        self._ensure_server()

        url = f"{self.base_url}/row/{tenant_id}/{resource_type}/{primary_key}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_column_values(self, tenant_id: str, column_name: str) -> dict:
        """列の全設定値を取得"""
        self._ensure_server()

        url = f"{self.base_url}/column/{tenant_id}/{column_name}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def search(self, tenant_id: str, filters: dict) -> list:
        """条件検索"""
        self._ensure_server()

        url = f"{self.base_url}/search/{tenant_id}"
        response = self.session.post(url, json=filters)
        response.raise_for_status()
        return response.json()

    def search_tenants(self, filters: dict) -> dict:
        """テナント横断検索"""
        self._ensure_server()

        url = f"{self.base_url}/search/tenants"
        response = self.session.post(url, json=filters)
        response.raise_for_status()
        return response.json()

    def reload_tenant(self, tenant_id: str):
        """テナントデータの手動リロード"""
        self._ensure_server()

        url = f"{self.base_url}/reload/{tenant_id}"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()

    def get_stats(self) -> dict:
        """統計情報"""
        self._ensure_server()

        url = f"{self.base_url}/stats"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


# ユーティリティ関数（Claudeが使いやすいように）

def get_client() -> OCIInventoryClient:
    """クライアントインスタンスを取得"""
    return OCIInventoryClient()


def ensure_server_running(max_retries=3) -> bool:
    """サーバーが起動していることを確認し、必要なら起動"""
    from lib.server_utils import start_server_if_not_running

    for _ in range(max_retries):
        try:
            client = get_client()
            client.get_stats()  # サーバー確認
            return True
        except RuntimeError:
            logger.info("サーバーを起動します")
            start_server_if_not_running()
            time.sleep(3)

    return False
```

---

### 3.2 サーバーユーティリティ

**ファイル**: `lib/server_utils.py`

```python
#!/usr/bin/env python
"""サーバー管理ユーティリティ"""

import os
import subprocess
import time
from pathlib import Path


PID_FILE = Path.home() / ".oci_inventory_server.pid"
DEFAULT_PORT = 8000
DEFAULT_HOST = "127.0.0.1"


def is_server_running() -> bool:
    """サーバーが起動しているかチェック"""
    if not PID_FILE.exists():
        return False

    pid = int(PID_FILE.read_text())

    try:
        os.kill(pid, 0)  # シグナル0でプロセス生存確認
        return True
    except OSError:
        return False


def start_server_if_not_running():
    """サーバーが起動していなければ起動"""
    if is_server_running():
        return

    script_path = Path(__file__).parent.parent / "scripts" / "start-server.sh"

    if not script_path.exists():
        raise FileNotFoundError(f"起動スクリプトが見つかりません: {script_path}")

    subprocess.run([str(script_path)], check=True)


def stop_server():
    """サーバーを停止"""
    if not is_server_running():
        return

    script_path = Path(__file__).parent.parent / "scripts" / "stop-server.sh"

    if not script_path.exists():
        raise FileNotFoundError(f"停止スクリプトが見つかりません: {script_path}")

    subprocess.run([str(script_path)], check=True)


def get_server_url() -> str:
    """サーバーのベースURLを取得"""
    host = os.getenv("OCI_INVENTORY_HOST", DEFAULT_HOST)
    port = os.getenv("OCI_INVENTORY_PORT", DEFAULT_PORT)
    return f"http://{host}:{port}"
```

---

## Phase 4: 使用方法の更新

### 4.1 SKILL.mdへの追記

**「エンドツーエンドの例」セクション**:

```markdown
## エンドツーエンドの例

### 準備

```bash
# 1. 環境セットアップ（初回のみ）
./scripts/setup-env.sh

# 2. サーバーを起動
./scripts/start-server.sh

# 3. サーバー状態を確認
./scripts/server-status.sh
```

### 例1: 特定VCNの情報を取得

```python
from lib.client import get_client, ensure_server_running

# サーバー起動確認（必要なら自動起動）
ensure_server_running()

# クライアント取得
client = get_client()

# 問い合わせ
result = client.get_row("ocicloudjapanuser1", "VCN", "ai-vcn")
print(result)
# 出力: {'名前': 'ai-vcn', 'コンパートメント名': 'ai-cmp', 'IPv4 CIDR blocks': '10.0.0.0/16', ...}
```

### 例2: 列の全設定値を取得

```python
from lib.client import get_client

client = get_client()
values = client.get_column_values("ocicloudjapanuser1", "環境")
print(values)
# 出力: {'ルート': ['VCN:ai-vcn', 'VCN:web-vcn', ...], 'sandbox': [...]}
```

### 例3: 統計情報の確認

```python
client = get_client()
stats = client.get_stats()
print(stats)
# 出力: {'tenants_loaded': 1, 'tenants': {'ocicloudjapanuser1': {'dataframes_cached': 5, ...}}}
```

### 使い終わったら

```bash
# サーバーを停止
./scripts/stop-server.sh
```
```

---

## Phase 5: 追加の考慮事項

### 5.1 ポート競合の問題

**問題**: デフォルトポート8000が使用されている場合

**解決策**:
```bash
# 環境変数でポート指定
export OCI_INVENTORY_PORT=8001
./scripts/start-server.sh
```

### 5.2 複数テナントの扱い

**ディレクトリ構造**:
```
/root/work/pj_excel1/
├── tenant1/
│   ├── *.xlsx
│   └── .cache/
│       └── tenant1_index.json
├── tenant2/
│   ├── *.xlsx
│   └── .cache/
│       └── tenant2_index.json
```

**使用方法**:
```python
# tenant1に問い合わせ
client.get_row("tenant1", "VCN", "ai-vcn")

# tenant2に問い合わせ
client.get_row("tenant2", "VCN", "sandbox-vcn-1")
```

### 5.3 タイムアウトによる自動停止

**実装案**:
```python
# lib/server.pyに追加
from datetime import datetime, timedelta

class IdleTimeout:
    def __init__(self, timeout_minutes=60):
        self.timeout = timedelta(minutes=timeout_minutes)
        self.last_activity = datetime.now()

    def update(self):
        self.last_activity = datetime.now()

    def is_expired(self):
        return datetime.now() - self.last_activity > self.timeout

@app.middleware("http")
async def update_activity(request: Request, call_next):
    response = await call_next(request)
    idle_timeout.update()
    return response
```

### 5.4 ログのローテーション

**実装**: Pythonのlogging.handlers.RotatingFileHandlerを使用

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "~/.oci_inventory_server.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

---

## Phase 6: 依存関係の追加

### 6.1 pyproject.tomlへの追加

```toml
[project]
dependencies = [
    "pandas",
    "openpyxl",
    "fastapi",
    "uvicorn[standard]",
    "requests",
    "pydantic",
]
```

```bash
uv add fastapi uvicorn requests pydantic
```

---

## 優先順位（再評価）

### 🔴 最優先（サーバー方式への移行）

1. FastAPI, uvicornを依存関係に追加
2. `lib/server.py`の実装
3. `lib/oci_inventory.py`の実装（キャッシュ管理）
4. `lib/index_builder.py`の実装
5. `lib/client.py`の実装

### 🟡 高優先（サーバー管理）

6. `scripts/start-server.sh`の実装
7. `scripts/stop-server.sh`の実装
8. `scripts/server-status.sh`の実装
9. 各スクリプトに実行権限付与

### 🟢 中優先（使い勝手の改善）

10. SKILL.mdへの使用例の追加
11. エラーハンドリングの強化
12. ログ設定の追加

### ⚪ 低優先（追加機能）

13. タイムアウトによる自動停止
14. ポート競合の自動解決
15. 統計情報の拡充

---

## 検証チェックリスト

サーバー方式実装後、以下を検証：

- [ ] サーバーが正常に起動する
- [ ] サーバーがバックグラウンドで実行され続ける
- [ ] ヘルスチェックが正常に動作する
- [ ] クライアントから行データを取得できる
- [ ] クライアントから列データを取得できる
- [ ] 複数回の問い合わせでキャッシュが効いている（ログで確認）
- [ ] ファイル更新時、自動的にキャッシュが無効化される
- [ ] サーバーの起動・停止・状態確認が正しく動作する
- [ ] PIDファイルが正しく管理されている
- [ ] エラーメッセージが適切に表示される

---

## 期待される改善効果

### 実装前（CLI方式）
- ❌ 毎回Excelをパース（〜数秒）
- ❌ プロセス終了時にキャッシュ消失
- ❌ 「メモリにキャッシュ」の意味がない

### 実装後（FastAPI方式）
- ✅ サーバーがメモリにDataFrameを保持
- ✅ 2回目以降は数msで応答
- ✅ PLAN.mdの設計思想が実現
- ✅ 複数の問い合わせでキャッシュが有効に機能

---

## 次のアクション

1. FastAPI, uvicornをインストール
2. `lib/server.py`を実装
3. `lib/oci_inventory.py`を実装
4. `lib/client.py`を実装
5. サーバー管理スクリプトを実装
6. エンドツーエンドでテスト
7. CHECKBOXを全てチェック
