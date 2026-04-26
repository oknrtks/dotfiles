# uv環境セットアップ

## 目的

Python仮想環境を作成し、必要ライブラリをインストールします。

## 手順

### 1. プロジェクトディレクトリへ移動

```bash
cd /root/work/pj_excel1
```

### 2. uvで仮想環境初期化

既存の仮想環境がない場合、新規作成します。

```bash
uv init
```

### 3. ライブラリ追加

pandasとopenpyxlを追加します。

```bash
uv add pandas openpyxl
```

**注意**: `uv pip install`は使用せず、必ず`uv add`を使用してください。`uv pip install`の結果は揮発的です。

### 4. Pythonコード実行

uv環境上でPythonコードを実行する場合、`uv run`を使用します。

```bash
uv run python your_script.py
```

## 検証

```bash
uv run python -c "import pandas; import openpyxl; print('OK')"
```

"OK"と表示されればセットアップ完了です。
