# テンプレート作成ガイド — Phase 3 詳細

Phase 3 で使用するコードスニペットとPlaceholder文の規則。

---

## build_template.py の基本構造

```python
import copy
import shutil
import logging
from datetime import datetime
from pathlib import Path
from pptx import Presentation

logging.basicConfig(
    filename=f'_work/build_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)

INPUT  = Path('<input.pptx>')
OUTPUT = Path('template_<input.pptx>')
R_NS   = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

shutil.copy(INPUT, OUTPUT)
prs = Presentation(OUTPUT)
# ... 以下に各操作を実装
prs.save(OUTPUT)
logging.info(f'Saved: {OUTPUT}')
```

---

## スライド削除

**後ろのインデックスから順に削除**する（インデックスずれ防止）。

```python
def remove_slide(prs: Presentation, index: int) -> None:
    sll = prs.slides._sldIdLst
    sld_id = sll[index]
    rId = sld_id.attrib.get(f'{{{R_NS}}}id')
    sll.remove(sld_id)
    prs.part.drop_rel(rId)
    logging.info(f'Removed slide index={index} rId={rId}')

# 例: スライド5, 4, 3, 2を削除（選定外）
for i in sorted([2, 3, 4, 5], reverse=True):
    remove_slide(prs, i)
```

---

## テキスト置換（書式保持）

**`text_frame.text = ...` は絶対に使わない**（書式が破壊される）。
先頭段落・先頭runのテキストのみ置換し、色・フォント・サイズを保持する。

```python
def set_text_preserve_style(shape, text: str) -> None:
    tf = shape.text_frame
    first_para = tf.paragraphs[0]
    # 2段落目以降を削除
    for para in list(tf.paragraphs[1:]):
        tf._txBody.remove(para._p)
    runs = first_para.runs
    if runs:
        runs[0].text = text
        # 2run目以降を削除
        for run in list(runs[1:]):
            first_para._p.remove(run._r)
    else:
        first_para.add_run().text = text
    logging.info(f'Set text on shape id={shape.shape_id}')
```

フォントサイズを補正する場合は設定後に上書きする:

```python
def set_text_with_font_size(shape, text: str, font_size_pt: float) -> None:
    set_text_preserve_style(shape, text)
    tf = shape.text_frame
    run = tf.paragraphs[0].runs[0]
    run.font.size = Pt(font_size_pt)
    logging.info(f'Set font size {font_size_pt}pt on shape id={shape.shape_id}')
```

shape_idでshapeを検索するヘルパー:

```python
def find_shape_by_id(slide, shape_id: int):
    for shape in slide.shapes:
        if shape.shape_id == shape_id:
            return shape
    return None
```

---

## フォントサイズ階層の検証と補正

Placeholder設定前に各shapeのフォントサイズが以下の順序を満たすか確認する:

```
スライドタイトル >= リード文 >= サブタイトル・サブリード文（存在する場合） >= 本文
```

- 違反がある場合（例: 本文 > リード文）、`set_text_with_font_size()` で補正する
- 補正値はリード文フォントサイズ未満の適切な値を選ぶ
- フォントサイズが大きいshape（目安: 20pt以上）のPlaceholderテキストは短くする（オーバーフロー防止）

---

## Placeholder文の規則

**必ず [`placeholder_templates.md`](./placeholder_templates.md) をReadツールで開き、そこに定義されたフォーマットを使用すること。**

独自のフォーマットを作成してはならない。

### 主なテンプレート種類
- 本文（汎用）
- 本文（左カラム・右カラム）
- 本文（補足・下部強調）
- リード文
- タイトル
- 表紙タイトル・サブタイトル
- カラムタイトル
- 図領域

詳細は `placeholder_templates.md` を参照。

---

## 表の処理

表は以下のいずれかの方法で処理する:

### 方法1: 構造保持+Placeholder化（推奨）

データ性の強い表（日程表、進捗表、比較表等）の場合、表の構造を保持してセル内容のみをPlaceholder化する。

```python
from lib.tables import convert_table_to_placeholder

# layout_memo.md で特定した表のshape_idを使用
table_id = 123  # TODO: shape_idを設定
success = convert_table_to_placeholder(slide, table_id)
if success:
    logging.info(f'Table shape_id={table_id} converted to placeholder')
else:
    logging.warning(f'Table shape_id={table_id} not found')
```

### 方法2: 削除→代替矩形

装飾的な表、または複雑な結合セルが多い表の場合、削除して代替矩形に置換する。

```python
from lib.shapes import find_shape_by_id, remove_shape_by_id, add_placeholder_rect

table_shape = find_shape_by_id(slide, table_id)
if table_shape:
    coords = (table_shape.left, table_shape.top, table_shape.width, table_shape.height)
    remove_shape_by_id(slide, table_id)
    add_placeholder_rect(
        slide, *coords,
        '【表領域】この箇所にスケジュール表・データ表を配置する\n'
        '（元スライドではXXX表が使用されていた）'
    )
```

### 判断基準

| 条件 | 処理方法 |
|------|---------|
| データ性の強い表 | **構造保持+Placeholder化** |
| 装飾的な表 | 削除→代替矩形 |
| 複雑な結合セル | 削除→代替矩形 |

**注意:** layout_memo.md で表の構造と処理方針を必ず記録すること。

---

## 図・画像・グラフ領域の代替処理

元スライドに画像・グラフ・複雑な図形群がある場合、削除して同位置・同サイズの長方形に置換する。

**必ず削除前に座標を記録する**（削除後はアクセス不可）:

```python
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

def add_placeholder_rect(slide, left: int, top: int, width: int, height: int, text: str) -> None:
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0xE0, 0xE0, 0xE0)  # 薄グレー
    shape.line.color.rgb = RGBColor(0x99, 0x99, 0x99)

    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    logging.info(f'Added placeholder rect: {text[:30]}')

# 使用例: 削除前に座標を取得し、削除後に同位置に矩形を配置
shape = find_shape_by_id(slide, rm_id)
if shape:
    left, top, width, height = shape.left, shape.top, shape.width, shape.height
    slide.shapes._spTree.remove(shape.element)
    logging.info(f'Removed image shape id={rm_id}')
    add_placeholder_rect(slide, left, top, width, height, '【図領域】...')
```

Placeholder文:
```
【図領域】この箇所には概念図・グラフ・イメージ図を配置する
（元スライドでは XXX が使用されていた）
```

---

## 座標の調べ方

元スライドのshapeの位置・サイズをEMUで取得:

```python
from pptx import Presentation
from pptx.util import Emu

prs = Presentation('<input.pptx>')
slide = prs.slides[N]
for shape in slide.shapes:
    print(
        f"id={shape.shape_id} name={shape.name!r} "
        f"left={shape.left} top={shape.top} "
        f"width={shape.width} height={shape.height}"
    )
```

1 inch = 914400 EMU。`pptx.util.Inches(x)` で変換可能。
座標は必ず元shapeから実測値を使う（概算値・Inches換算の近似値は使わない）。
