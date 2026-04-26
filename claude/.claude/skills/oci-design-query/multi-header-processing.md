# マルチヘッダー結合

## 問題

Excelのマルチヘッダー構造で、親ヘッダーが複数列にまたがって結合されている場合、pandasが読み込むと「Unnamed」になります。

### 例

```
Excel上の見た目:
┌─────────────────────────────────────────────┐
│         コンパートメント設定                 │
├──────────┬──────────┬──────────┬──────────┤
│コンパート│  説明    │親コンパ   │セキュリ   │
│メント名  │          │ートメント │ティ・ゾーン│
└──────────┴──────────┴──────────┴──────────┘

pandasが読むと:
行0: 'Unnamed: 0', 'コンパートメント設定', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4'
行1: 'Unnamed: 0', 'コンパートメント名', '説明', '親コンパートメント', 'セキュリティ・ゾーン'
```

## 結合ルール

### 縦方向の結合

- Unnamedカラムは、前行の**最も左の非Unnamed値**を継承する
- 同じ階層のヘッダー名は左側で省略される（Excelの結合セル構造）

### 自動化アルゴリズム

1. **データ開始行の判定**: 最初の「#」を含む行をデータ開始行とみなす
2. **ヘッダー行の判定**: データ開始行の手前までをヘッダー行とする
3. **カラムごとの走査**: 各列について、上から下に走査して非Unnamed値を収集
4. **結合**: 階層構造を維持しつつ結合（例: "親:子" または "_".join([親, 子])）

### 出力

結合されたカラム名リスト

```python
['#', 'コンパートメント名', '説明', '親コンパートメント', 'セキュリティ・ゾーン']
```

## 実装例

```python
def combine_multi_header(df: pd.DataFrame) -> list[str]:
    """マルチヘッダーを結合してカラム名リストを返す"""
    # データ開始行を探す（最初の「#」を含む行）
    for idx, row in df.iterrows():
        if any('#' in str(val) for val in row.values if pd.notna(val)):
            data_start_row = idx
            break
    else:
        return list(df.columns)  # 「#」が見つからない場合はそのまま返す

    # ヘッダー行を抽出
    header_rows = df.iloc[:data_start_row]

    # 各カラムについて結合
    combined_columns = []
    for col_idx in range(len(header_rows.columns)):
        values = []
        for row_idx in range(len(header_rows)):
            val = header_rows.iloc[row_idx, col_idx]
            if pd.notna(val) and not str(val).startswith('Unnamed'):
                values.append(str(val))
            elif values:
                # Unnamedの場合、前行の値を継承
                values.append(values[-1])

        # 重複を除去して結合
        unique_vals = []
        for v in values:
            if not unique_vals or v != unique_vals[-1]:
                unique_vals.append(v)

        combined_name = '_'.join(unique_vals) if unique_vals else f'column_{col_idx}'
        combined_columns.append(combined_name)

    return combined_columns
```

## 検証

現行10ファイルで正しく結合できるか確認します。
