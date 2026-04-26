# 問い合わせパターン

## パターン1: 特定リソースの全属性値

### 例

「ai-vcnの全設定を教えて」

### フロー

1. `by_resource["ocicloudjapanuser1"]["VCN"]["ai-vcn"]` から `{"sheet": "VCN", "row": 3}` を取得
2. DataFrame `df_dict["ocicloudjapanuser1"]["VCN"].iloc[3]` で行データを取得
3. 辞書形式 `{"名前": "ai-vcn", "コンパートメント名": "ai-cmp", ...}` で返す

### 計算量

O(1)

## パターン2: 列単位の全設定値

### 例

「環境カラムの全設定値を教えて」

### フロー

1. `by_column_values["ocicloudjapanuser1"]["環境"]` から値ごとのリソースリストを取得
2. 必要に応じてDataFrameから詳細情報を補完
3. 集約して返す

### 計算量

O(1)

## パターン3: 複雑な条件検索

### 例

「コンパートメントがai-cmpでCIDRが10.0.0.0/16のVCN」

### フロー

1. インデックスで候補を絞り込む（例: `by_column_values["コンパートメント名"]["ai-cmp"]`）
2. DataFrameでフィルタリング（`df[(df["コンパートメント名"] == "ai-cmp") & (df["IPv4 CIDR blocks"] == "10.0.0.0/16")]`）
3. 結果を返す

### 計算量

O(n) ただしインデックスで事前絞り込みによりnは小さい

## パターン4: テナント横断検索

### 例

「全テナントのsandboxコンパートメントを教えて」

### フロー

1. 複数テナントのインデックスを並列検索
2. 各テナントのDataFrameから詳細を取得
3. テナント別に集約して返す

### 計算量

O(テナント数)

## メソッド定義

```python
class OCIInventory:
    def get_row(self, tenant_id: str, resource_type: str, primary_key: str) -> dict:
        """特定リソースの全属性値を取得"""
        ...

    def get_column_values(self, tenant_id: str, column_name: str) -> dict:
        """列の全設定値を取得"""
        ...

    def search(self, tenant_id: str, filters: dict) -> list:
        """条件検索"""
        ...

    def search_across_tenants(self, filters: dict) -> dict[str, list]:
        """テナント横断検索"""
        ...
```
