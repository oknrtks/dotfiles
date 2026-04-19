---
name: pptx-from-reference
description: 参照PPTXファイルを視覚的に解析し、再利用可能なテンプレートPPTXを生成するスキル。与えられたPPTX資料のレイアウト・文体・デザインルールを目視確認し、タイトル・リード文・本文などの要素を特定してPlaceholder付きテンプレートを作成する。「pptxをテンプレート化して」「参照資料からテンプレートを作って」「このpptxのレイアウトを雛形にして」などのリクエストで使用する。
---

# pptx-from-reference スキル

与えられたPPTXを参照資料として、そのデザイン・レイアウト・文体を解析し、再利用可能なテンプレートPPTXを生成する。

## フェーズ構成

| フェーズ | 内容 |
|---------|------|
| Phase 0 | 環境チェック（必須ツール・フォント確認） |
| Phase 1 | 仮想環境・ライブラリ確認、ワーク領域作成 |
| Phase 2 | 全スライド目視確認、参照スライド選定、メモ記録 |
| Phase 3 | テンプレートPPTX生成（コピー→整形→Placeholder設定） |
| Phase 4 | 自己レビュー（元スライドと比較確認→修正ループ） |

---

## Phase 0 — 環境チェック

以下をすべて確認する。**1つでも不足していればスキルを中断し**、利用者に案内する。

```bash
which soffice    # LibreOffice
which pdftoppm   # Poppler
which uv         # uv パッケージマネージャ
ls ~/.claude/skills/pptx/   # pptx スキル
fc-list | grep -iE "noto|gothic|mincho" | head -5  # 日本語フォント
```

不足時の案内文:
```
以下の環境が必須です:
- LibreOffice:    apt-get install -y libreoffice
- Poppler:        apt-get install -y poppler-utils
- uv:             curl -LsSf https://astral.sh/uv/install.sh | sh
- pptxスキル:     ~/.claude/skills/pptx/ が存在すること
- 日本語フォント: apt-get install -y fonts-noto-cjk
```

> 日本語フォントが欠けていると LibreOffice でのPDF変換時に日本語が□で表示され、視覚確認が不可能になる。

---

## Phase 1 — 仮想環境・ライブラリ確認

### 仮想環境

作業ディレクトリ（PPTXファイルが存在するディレクトリ）で確認:

```bash
# .venv がなければ初期化
ls .venv 2>/dev/null || uv init --no-readme

# 必要ライブラリ確認・追加
uv run python -c "import markitdown, PIL, pptx, lxml" 2>/dev/null \
  || uv add "markitdown[pptx]" Pillow python-pptx lxml
```

### ワーク領域

作業ファイルはすべて `_work/` に集約する（ルートを汚さない）:

```bash
mkdir -p _work
```

```
<入力PPTXのディレクトリ>/
├── <input>.pptx              # 入力（読み取り専用）
├── template_<input>.pptx     # 最終成果物
└── _work/
    ├── layout_memo.md        # Phase 2: 分析メモ
    ├── slide-01.jpg          # 元スライド画像
    ├── template-01.jpg       # テンプレート確認用画像
    ├── build_template.py     # Phase 3: 生成スクリプト
    └── build_YYYYMMDD_HHMMSS.log
```

---

## Phase 2 — 目視確認編

> **重要:** Phase 2開始前に必ず [`placeholder_templates.md`](./placeholder_templates.md) をReadツールで開くこと。

詳細フォーマットは [slide-analysis-guide.md](./slide-analysis-guide.md) を参照。

### Placeholderテキスト作成時の必須ルール

**Phase 2開始前に必ず `placeholder_templates.md` をReadツールで開くこと。**

#### 手順
1. `placeholder_templates.md` をReadツールで開く
2. 該当するテンプレート（本文/リード文/タイトル等）をコピー
3. `#XXXXXX` `XXpt` 等のプレースホルダーを元スライドの実際の値に置換
4. 独自のフォーマットを作成してはならない

#### 禁止事項
- 「【本文ブロック1】・ 箇条書き項目1」のような簡略フォーマットの作成
- `placeholder_templates.md` にない構造の使用

### 2-1. 全スライド画像化

```bash
# PDF変換
uv run python ~/.claude/skills/pptx/scripts/office/soffice.py \
  --headless --convert-to pdf <input.pptx>
mv <input>.pdf _work/

# JPEG変換
pdftoppm -jpeg -r 150 _work/<input>.pdf _work/slide
```

Read ツールで `_work/slide-01.jpg` から順に全スライドを確認する。

### 2-2. 参照スライドの選定

**対話モード:** 全スライドの概要を報告し、**選定案を提示して利用者の明示的な承認を得てから**次のフェーズに進む。承認なしに自動進行してはならない。

**委任・非対話モード:** 利用者から「LLMが考えてくれ」「適当に選べ」「適切に選べ」等の回答、または確認できない場合は以下の基準で自動選定（最大5点）:
- 汎用性が高く特定データ・固有名詞に依存しない構造
- タイトル・リード文・本文などの要素が揃っている
- 類似レイアウトは代表1点のみ
- 表紙・中表紙・背表紙は存在すれば別途記録

**表紙・中表紙の取り扱い:** タイトル・サブタイトルなどのshapeを特定し、`テンプレートスライド` と同様にPlaceholderテキスト（例: `【表紙タイトル】ここにタイトルを記載`）に置き換える。

**背表紙の取り扱い:** テンプレートに含めるが、一切手を加えない（画像・ロゴ主体のため）。

### 2-3. shapeの特定（必須ルール）

> **視覚照合なしにshapeの役割を断定してはならない。**
> PPTXではタイトルがプレースホルダー（`ph_idx==0`）でなく、通常のテキストボックスとして実装されているケースがある。
> 以下の手順で確認する:

```bash
uv run python - <<'EOF'
from pptx import Presentation
prs = Presentation('<input.pptx>')
slide = prs.slides[N]  # 対象スライドのインデックス
for shape in slide.shapes:
    ph = shape.placeholder_format if shape.is_placeholder else None
    text = shape.text_frame.text[:40] if shape.has_text_frame else '(no text)'
    print(f"id={shape.shape_id} name={shape.name!r} ph_idx={ph.idx if ph else '-'} text={text!r}")
EOF
```

コード出力と視覚画像を照合して各shapeの役割（タイトル・リード文・本文）を確定する。

> **注意:** 同一テンプレートレイアウト由来のスライドでは、異なるスライドに同一の `shape_id` が存在することがある。shape_id はスライド内でユニークだが、スライドをまたいだ場合は重複しうる。処理はスライドごとに行うこと。

### 2-4. フォントサイズの記録と検証

各shapeのフォントサイズをコードで取得し、以下の階層順序を確認する:

```
スライドタイトル >= リード文 >= サブタイトル・サブリード文（存在する場合） >= 本文
```

```bash
uv run python - <<'EOF'
from pptx import Presentation
prs = Presentation('<input.pptx>')
slide = prs.slides[N]
for shape in slide.shapes:
    if not shape.has_text_frame:
        continue
    sizes = [run.font.size for para in shape.text_frame.paragraphs for run in para.runs if run.font.size]
    print(f"id={shape.shape_id} font_sizes={sizes}")
EOF
```

フォントサイズが上記階層に反する場合（例: 本文 > リード文）、`build_template.py` 内でサイズを補正する。補正はPlaceholderテキスト設定時に `run.font.size = Pt(N)` で行う。

### 2-5. メモ記録

`_work/layout_memo.md` に記録する。フォーマットは [slide-analysis-guide.md](./slide-analysis-guide.md) を参照。

---

## Phase 3 — テンプレート作成編

詳細・コードスニペットは [template-building-guide.md](./template-building-guide.md) を参照。

---

## ⚠️ 禁止パターン（絶対に使用しないこと）

### 1. text_frame.clear() の使用

**絶対に禁止:** `text_frame.clear()` を使用すると、すべての書式情報（フォント・サイズ・色等）が失われます。

```python
# ❌ 絶対に禁止
text_frame.clear()
p.text = text  # これで書式が破壊される

# ✓ 正しい実装
from lib.core import set_text_preserve_style
set_text_preserve_style(shape, text)
```

### 2. 独自実装の作成

以下の機能は必ずライブラリ関数を使用すること：

- **テキスト置換**: `set_text_preserve_style()`（書式保持）
- **スライド削除**: `remove_slide()`（インデックスずれ防止）
- **図領域代替**: `add_placeholder_rect()`（視認性確保）
- **Shape検索**: `find_shape_by_id()`（一貫性確保）

**理由:**
- 書式保持の実装は複雑で、自作するとバグりやすい
- 用意された関数はテスト済みで、正しく動作する
- ライブラリ関数を使うことで品質が均一化される

### 3. shape_idのハードコーディング

スクリプト本体にshape_idを直接埋め込まず、ファイル先頭で変数として定義すること。

```python
# ❌ 禁止
def process_slide(slide):
    set_text_preserve_style(slide.shapes[141], "【タイトル】...")  # 固有値

# ✓ 正しい
SLIDE_CONFIG = {
    0: {'title_id': 141},  # 変数として定義
}

def process_slide(slide, config):
    shape = find_shape_by_id(slide, config['title_id'])
    if shape:
        set_text_preserve_style(shape, "【タイトル】...")
```

---

### 3-1. テンプレートファイル生成とライブラリ設定

```bash
cp <input.pptx> template_<input.pptx>
```

`_work/build_template.py` を作成し、以降の操作をすべてこのスクリプトで実行する。logging でタイムスタンプ付きログを `_work/build_YYYYMMDD_HHMMSS.log` に出力する。

**必ず以下の構造に従うこと:**

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
from pptx import Presentation
from datetime import datetime
import logging

# ライブラリパスを設定
sys.path.insert(0, str(Path.home() / '.claude' / 'skills' / 'pptx-from-reference'))
from lib.core import set_text_preserve_style, remove_slide
from lib.shapes import find_shape_by_id, add_placeholder_rect, remove_shape_by_id

# ログ設定
logging.basicConfig(
    filename=f'_work/build_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)

# ========================================
# ファイル固有変数の定義
# ========================================
# layout_memo.md で特定したshape_idを変数化
SLIDE_CONFIG = {
    0: {'title_id': 3, 'subtitle_id': 4},
    1: {'title_id': 141, 'lead_id': 155, 'body_ids': [2, 11]},
    # ...
}

# ========================================
# メイン処理
# ========================================
def main():
    prs = Presentation('template_xxx.pptx')
    
    # ライブラリ関数を使用して処理
    for slide_idx, config in SLIDE_CONFIG.items():
        slide = prs.slides[slide_idx]
        if 'title_id' in config:
            shape = find_shape_by_id(slide, config['title_id'])
            if shape:
                set_text_preserve_style(shape, "【タイトル】...")
    
    prs.save('template_xxx.pptx')

if __name__ == '__main__':
    main()
```

**重要:**
- 必ず `sys.path.insert()` でライブラリをインポートすること
- ファイル固有値（shape_id等）はファイル先頭で変数として定義すること
- 独自実装を書かず、必ずライブラリ関数を使用すること

### 3-2. タイトルの書き換え

選定した各スライドのタイトルshapeのテキストを `テンプレートスライド1`（連番）に書き換える。**フォント・色・サイズは元のrunを継承し、テキストのみ置換する（書式破壊禁止）**。

タイトルがプレースホルダーか通常のテキストボックスかは `layout_memo.md` で特定した `shape_id` を使う。

### 3-3. 不要スライドの削除

選定しなかったスライドを**後ろのインデックスから順に**削除する（インデックスずれ防止）。

### 3-4. Placeholderテキストの設定

> **重要:** build_template.py でPlaceholderテキストを設定する前に、以下の「挿入前レビュー」を実施すること。

#### 挿入前レビュー（必須）

build_template.py でPlaceholderテキストを設定する際、以下を自己確認：

1. `placeholder_templates.md` をReadツールで確認済みか？
2. 設定しようとしているテキストが、テンプレートの構造に従っているか？

**チェック項目（例: 本文の場合）:**
- 【本文】で始まっているか？
- 「文字色: ... / サイズ: ...」の記載があるか？
- 「強調方法: ...」の記載があるか？
- 「文体: ...」の記載があるか？
- 「構成: ...」の記載があるか？

✓ 全てOK → コードに組み込む
✗ 不足あり → placeholder_templates.md を再確認して修正

**確認方法:**
- コードを書く前に、設定するテキストをメモ帳等に一時的に書き出す
- それが placeholder_templates.md の構造に従っているか確認
- 従っていれば、そのテキストをコードに組み込む

各shapeに役割とスタイル情報を含むPlaceholderテキストを設定する。書式は `set_text_preserve_style()` で保持する。

Placeholder文の内容規則・コードスニペットは [template-building-guide.md](./template-building-guide.md) を参照。

**フォントサイズの補正:** 2-4 で確認した階層順序に反するshapeは、Placeholderテキスト設定時に `run.font.size` を明示的に補正する。補正後のサイズは `layout_memo.md` に記録する。

**Placeholderテキストの長さ:** shapeのフォントサイズが大きい（例: 20pt以上）場合、長いPlaceholderテキストはオーバーフローする。`【左タイトル】` のような短い表現にとどめること。

**図・画像・グラフ領域の処理:**
1. 削除前に対象shapeの座標（left, top, width, height）をEMUで記録する
2. shapeを削除する
3. 記録した座標を使って代替長方形を同位置・同サイズで配置する

```python
# 座標を記録してから削除する例
shape = find_shape(slide, rm_id)
if shape:
    coords = (shape.left, shape.top, shape.width, shape.height)
    slide.shapes._spTree.remove(shape.element)
    add_placeholder_rect(slide, *coords, '【図領域】...')
```

---

## Phase 4 — 自己レビュー編

### 4-1. テンプレートの画像化

```bash
uv run python ~/.claude/skills/pptx/scripts/office/soffice.py \
  --headless --convert-to pdf template_<input.pptx>
pdftoppm -jpeg -r 150 template_<input>.pdf _work/template
```

### 4-2. 元スライドとの比較確認

各テンプレートスライドについて、`_work/slide-NN.jpg`（元）と `_work/template-NN.jpg`（テンプレート）を Read ツールで読み込み、以下を確認する:

- [ ] タイトル・リード文・本文のPlaceholderが適切な位置に表示されているか
- [ ] 削除すべきshapeが残っていないか
- [ ] フォント・色・サイズ・背景色が元スライドから継承されているか
- [ ] 図領域の代替長方形が適切な位置・サイズか
- [ ] 意図しない要素の欠落・重複がないか
- [ ] Placeholderテキストがshapeからはみ出していないか（特に大フォントshape）

### 4-3. 修正ループ

**少なくとも1回は修正→再確認サイクルを実施する**（問題ゼロに見えても必ず1周行う）。

問題が見つかった場合:
1. `_work/build_template.py` を修正
2. 再実行してテンプレートを再生成
3. 4-2 の確認を繰り返す
4. 問題がなくなるまで継続

**最終確認:** すべての修正ループが完了した後、**全スライドを改めて通しで確認する**（修正対象以外のスライドに意図しない影響が出ていないか）。

---

## 完了報告

完了時に以下を報告する:
- 生成したテンプレートファイルのパス
- 選定したスライド番号と理由の概要
- 特記事項（タイトルがテキストボックス代替だった等）
