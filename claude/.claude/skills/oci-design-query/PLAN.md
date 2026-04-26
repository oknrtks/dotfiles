# OCI設計書効率的問い合わせシステム設計

## Context
OCI設計書が固定フォーマット（ファイル名規則、シート構造、マルチヘッダ）で複数テナント分存在し、繰り返しLLM経由で問い合わせが発生する。毎回Excelをアンパックして構造解析するのは非効率なため、下準備を行い効率化する。

## Requirements
- 複数テナントの設計書Excelを扱える
- ファイル名、シート種類、マルチヘッダ構造は固定と仮定
- 繰り返し問い合わせに対して高速に応答
- LLMコンテキスト内で完結するシンプルさ

## Recommended Approach: 前処理キャッシュ＋多層インデックス（遅延ロード）

**最適化根拠**:
- **テナント数10-50、各50ファイル** → 全てを常時メモリに載せる必要なし（遅延ロードで対応）
- **更新頻度低、イベント駆動** → タイムスタンプ監視で自動再構築
- **列単位・行単位抽出** → 値の逆引きインデックスを追加

### Phase 1: スキーマ定義ファイル生成（一度のみ）

**目的**: 設計書フォーマットをコードとして定義

**生成物**:
```python
# schema/oci_excel_schema.py
@dataclass
class SheetSchema:
    sheet_name: str
    header_rows: int  # マルチヘッダ行数
    primary_key: str  # 主カラム名
    columns: dict[str, str]  # {カラム名: データ型}
    relationships: list[str]  # 関連シート名

@dataclass
class FileGroupSchema:
    group_name: str  # "VCN", "Identity" 等
    filename_pattern: str  # "*_{環境}_{グループ}.xlsx"
    sheets: dict[str, SheetSchema]
    index_columns: list[str]  # インデックス対象カラム

SCHEMA_CATALOG: dict[str, FileGroupSchema] = {
    "VCN": FileGroupSchema(
        group_name="VCN",
        filename_pattern="*_{env}_VCN.xlsx",
        sheets={
            "VCN": SheetSchema(
                sheet_name="VCN",
                header_rows=2,
                primary_key="#",
                columns={"#": "int", "名前": "str", "コンパートメント名": "str", "IPv4 CIDR blocks": "str"},
                relationships=["サブネット", "DHCPオプション"]
            ),
            # 他シートも定義
        },
        index_columns=["名前", "コンパートメント名"]
    ),
    # 他グループも定義
}
```

**作成タイミング**: 新規リソースグループ追加時のみ

---

### Phase 2: 初期ロード時の前処理（テナント毎に一度）

**目的**: Excelから高速検索可能な中間表現を生成

**処理フロー**:
1. テナントディレクトリスキャン
2. スキーマ定義に従いExcel解析
3. 階層構造（ファイル→シート→行）のインメモリインデックス生成

**生成物**:
```python
# cache/{tenant_id}_index.json
{
  "tenant_id": "ocicloudjapanuser1",
  "last_updated": "2025-04-26T14:30:00Z",
  "files_mtime": {
    "ocicloudjapanuser1_ルート_VCN.xlsx": 1714100400.0
  },
  "index": {
    "by_resource": {
      "VCN": {
        "ai-vcn": {
          "file": "ocicloudjapanuser1_ルート_VCN.xlsx",
          "sheet": "VCN",
          "row": 3,
          "data": {"名前": "ai-vcn", "コンパートメント名": "ai-cmp", "IPv4 CIDR blocks": "10.0.0.0/16"},
          "relations": {
            "サブネット": ["subnet-1", "subnet-2"],
            "DHCPオプション": ["Default DHCP Options for ai-vcn"]
          }
        }
      }
    },
    "by_compartment": {
      "ai-cmp": {
        "VCN": ["ai-vcn", "web-vcn"],
        "インスタンス": ["ubuntu_server"]
      }
    },
    "by_column_values": {
      "環境": {
        "ルート": ["VCN:ai-vcn", "VCN:web-vcn", "Instance:ubuntu_server"]
      },
      "コンパートメント名": {
        "ai-cmp": ["VCN:ai-vcn", "Instance:ubuntu_server"],
        "sandbox": ["VCN:sandbox-vcn-1"]
      }
    }
  }
}
```

**作成タイミング**:
- イベント駆動: 設計書入手時
- タイムスタンプチェック: `files_mtime`と現在のmtime比較
- 手動再構築: 強制更新時

---

### Phase 3: 問い合わせ時のインメモリ検索

**実装**:
```python
class OCIInventory:
    def __init__(self, tenants_base_dir: Path):
        self.schema_catalog = load_schema()
        self.tenants_base_dir = tenants_base_dir
        self._loaded_tenants: dict[str, dict] = {}  # 遅延ロードキャッシュ

    def _load_tenant(self, tenant_id: str, force_rebuild: bool = False):
        """タイムスタンプチェックしてからロード"""
        cache_file = self.tenants_base_dir / f"cache/{tenant_id}_index.json"
        tenant_dir = self.tenants_base_dir / tenant_id

        # キャッシュ存在チェック
        if not force_rebuild and cache_file.exists():
            index = json.loads(cache_file.read_text())
            # タイムスタンプ比較
            current_mtimes = {f.name: f.stat().st_mtime for f in tenant_dir.glob("*.xlsx")}
            cached_mtimes = index.get("files_mtime", {})

            if current_mtimes == cached_mtimes:
                self._loaded_tenants[tenant_id] = index
                return

        # 再構築
        index = build_tenant_index(tenant_dir, self.schema_catalog)
        cache_file.write_text(json.dumps(index, ensure_ascii=False, indent=2))
        self._loaded_tenants[tenant_id] = index

    def get_column_values(self, tenant_id: str, column_name: str) -> dict:
        """列単位の全設定値を取得"""
        self._load_tenant(tenant_id)
        index = self._loaded_tenants[tenant_id]
        return index["index"]["by_column_values"].get(column_name, {})

    def get_row(self, tenant_id: str, resource_type: str, primary_key: str) -> dict:
        """特定リソースの全属性値を取得"""
        self._load_tenant(tenant_id)
        index = self._loaded_tenants[tenant_id]
        return index["index"]["by_resource"][resource_type][primary_key]

    def search_across_tenants(self, filters: dict) -> dict[str, list]:
        """テナント横断検索"""
        results = {}
        for tenant_dir in self.tenants_base_dir.iterdir():
            if not tenant_dir.is_dir():
                continue
            tenant_id = tenant_dir.name
            self._load_tenant(tenant_id)
            # 検索ロジック
            ...
        return results
```

**メリット**:
- **遅延ロード**: 必要なテナントのみロード（メモリ効率）
- **タイムスタンプチェック**: 更新あるテナントのみ再構築
- **列単位抽出**: `by_column_values`インデックスで高速
- **行単位抽出**: `by_resource`インデックスで即座取得

---

## Implementation Plan

### Step 1: スキーマ抽出ツール作成
現在のExcelからスキーマ定義を自動生成するツールを作成：
```bash
python tools/extract_schema.py /root/work/pj_excel1/test_excels/ > schema/oci_excel_schema.py
```

**出力**: マルチヘッダ構造、カラム名、型を抽出したPythonファイル

### Step 2: インデックス生成ツール作成
```python
# tools/build_index.py
def build_tenant_index(tenant_dir: Path, schema: FileGroupSchema) -> dict:
    """ExcelからインデックスJSONを生成"""
    index = {
        "tenant_id": tenant_dir.name,
        "last_updated": datetime.now().isoformat(),
        "files_mtime": {},
        "index": {
            "by_resource": {},
            "by_compartment": {},
            "by_column_values": {}  # 列単位抽出用
        }
    }

    for file in tenant_dir.glob("*.xlsx"):
        index["files_mtime"][file.name] = file.stat().st_mtime
        file_schema = match_schema(file, schema)
        for sheet_name, sheet_schema in file_schema.sheets.items():
            df = pd.read_excel(file, sheet_name=sheet_name, header=list(range(sheet_schema.header_rows)))

            # by_resource, by_compartment, by_column_valuesの構築
            # ...

    return index
```

### Step 3: 問い合わせクラス実装（遅延ロード対応）
```python
# lib/oci_inventory.py
class OCIInventory:
    def __init__(self, tenants_base_dir: Path):
        self.schema_catalog = load_schema()
        self.tenants_base_dir = tenants_base_dir
        self._loaded_tenants: dict[str, dict] = {}  # 遅延ロードキャッシュ

    def _load_tenant(self, tenant_id: str, force_rebuild: bool = False):
        """タイムスタンプチェックしてからロード（上記実装参照）"""
        ...

    def get_column_values(self, tenant_id: str, column_name: str) -> dict:
        """列単位の全設定値を取得"""
        ...

    def get_row(self, tenant_id: str, resource_type: str, primary_key: str) -> dict:
        """特定リソースの全属性値を取得"""
        ...

    def search_across_tenants(self, filters: dict) -> dict[str, list]:
        """テナント横断検索"""
        ...
```

### Step 4: イベント駆動更新フック
```python
# hooks/on_new_design.py
def on_design_files_received(tenant_id: str):
    """設計書入手時のイベントハンドラ"""
    inventory = OCIInventory(Path("/tenants"))
    inventory._load_tenant(tenant_id, force_rebuild=True)
    print(f"[{tenant_id}] インデックス更新完了")
```

### Step 5: LLMインターフェース
```python
# cli.py
inventory = OCIInventory(Path("/tenants"))

# 列単位: 「全VCNの環境設定値を教えて」
env_values = inventory.get_column_values("ocicloudjapanuser1", "環境")
# {"ルート": ["VCN:ai-vcn", ...]}

# 行単位: 「ai-vcnの全設定を教えて」
ai_vcn = inventory.get_row("ocicloudjapanuser1", "VCN", "ai-vcn")
# {"名前": "ai-vcn", "コンパートメント名": "ai-cmp", ...}

# 横断: 「全テナントのsandboxコンパートメントを教えて」
results = inventory.search_across_tenants({"compartment": "sandbox"})
# {"tenant1": [...], "tenant2": [...]}
```

---

## Verification

### テストシナリオ
1. **スキーマ抽出**: 現行10ファイルから正しくスキーマ生成される
2. **インデックス生成**: JSONが生成され、`by_column_values`が正しく構築される
3. **列単位抽出**: `get_column_values(tenant, "環境")` で全リソースの環境値が取得できる
4. **行単位抽出**: `get_row(tenant, "VCN", "ai-vcn")` で全属性が取得できる
5. **横断検索**: `search_across_tenants({"compartment": "sandbox"})` で複数テナントから検索
6. **タイムスタンプ更新**: ファイル更新時、自動でインデックス再構築
7. **遅延ロード**: 未アクセステナントはロードされない（メモリ効率）

### 性能目標（中規模: 50テナント、各50ファイル）
- 初回ロード（1テナント）: <3秒
- 遅延ロード（1テナント）: <3秒
- 列単位検索: <50ms（インメモリ）
- 行単位検索: <50ms（インメモリ）
- 横断検索（10テナント）: <500ms
- メモリ使用（1テナント）: <50MB
- メモリ使用（50テナント全ロード時）: <2.5GB（運用では数十テナント同時アクセス想定）

---

## Files to Create/Modify

### New Files
- `schema/oci_excel_schema.py` - スキーマ定義（自動生成）
- `tools/extract_schema.py` - スキーマ抽出ツール
- `tools/build_index.py` - インデックス生成ツール（`by_column_values`含む）
- `lib/oci_inventory.py` - 問い合わせクラス（遅延ロード対応）
- `hooks/on_new_design.py` - イベント駆動更新フック
- `cache/{tenant_id}_index.json` - 生成されるインデックス（Git管理外）
- `cli.py` - LLMインターフェース示例

### Existing Files
- `analyze_excel.py`, `analyze_structure.py` - 参考として活用（スキーマ抽出のベース）

---

## Trade-offs Considered

### ❌ 採用しないアプローチ
1. **完全DB化**: スキーマ変更に弱い、オーバーエンジニアリング（50テナント×50ファイル=2,500ファイルには過剰）
2. **毎回Excel解析**: 遅すぎる（〜10秒/回）、コスト高い
3. **常時全ロード**: 50テナントを常時メモリに載せるのは非効率（未使用テナントもあるため）
4. **定期実行更新**: 更新頻度低（毎週〜不定期）に不釣り合い、イベント駆動で十分

### ✅ 採用理由（遅延ロード＋キャッシュ方式）
- **更新頻度低**: タイムスタンプチェックで効率的（イベント駆動＋mtime比較）
- **中規模対応**: 遅延ロードで必要なテナントのみメモリに載せる（メモリ効率）
- **列/行抽出**: `by_column_values`インデックスで高速（50ms以下）
- **横断検索**: テナント独立インデックスで並列検索可能
- **シンプルさ**: LLMコンテキスト内で完結、DB不要
