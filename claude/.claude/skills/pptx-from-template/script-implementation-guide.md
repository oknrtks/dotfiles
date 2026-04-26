# スクリプト実装ガイド

テンプレートからスライドを作成するPythonスクリプトの実装詳細です。

## 基本構造

```python
import sys
import shutil
import logging
from datetime import datetime
from pathlib import Path

# ライブラリパスの追加（pptx-from-referenceスキルのライブラリを使用）
sys.path.insert(0, str(Path.home() / '.claude/skills/pptx-from-reference'))

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.dml.color import RGBColor
from lib.core import remove_slide
from lib.shapes import find_shape_by_id, remove_shape_by_id

# ログ設定
logging.basicConfig(
    filename=f'_work/create_slide_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)
```

---

## 書式設定関数

テンプレートのフォントを保持し、不要な書式を除去する関数:

```python
def set_text_with_format(shape, paragraphs_data, base_font_name='BIZ UDPゴシック'):
    """テキストを書式付きで設定（元のフォントを保持、下線のみ除去）

    Args:
        shape: テキストを設定するshape
        paragraphs_data: list of dict
            - text: str (段落のテキスト)
            - font_size: float (pt, デフォルト12)
            - bold: bool (太字、デフォルトFalse)
            - color: str (16進数カラーコード、例: 'FF0000', Noneの場合は黒)
            - indent: int (インデントレベル、0=なし)
        base_font_name: str (テンプレートから取得したフォント名)
    """
    text_frame = shape.text_frame
    text_frame.clear()
    text_frame.word_wrap = True

    for para_data in paragraphs_data:
        # 段落の追加
        if len(text_frame.paragraphs) == 1 and not text_frame.paragraphs[0].text:
            p = text_frame.paragraphs[0]
        else:
            p = text_frame.add_paragraph()

        p.text = para_data['text']
        p.level = para_data.get('indent', 0)

        # 各runに書式を適用
        for run in p.runs:
            run.font.name = base_font_name  # フォント名を保持
            run.font.size = Pt(para_data.get('font_size', 12))
            run.font.bold = para_data.get('bold', False)
            run.font.underline = False  # 下線を明示的にオフ

            if para_data.get('color'):
                run.font.color.rgb = RGBColor.from_string(para_data['color'])
            else:
                run.font.color.rgb = RGBColor(0, 0, 0)  # 黒
```

---

## テンプレートのコピーとスライド削除

```python
TEMPLATE = Path('template.pptx')
OUTPUT = Path('output.pptx')

# テンプレートをコピー
shutil.copy(TEMPLATE, OUTPUT)
prs = Presentation(OUTPUT)

# 使用しないスライドを削除（後ろから順に）
# 例: スライド2（index=3）のみを残す場合
for idx in [6, 5, 4, 2, 1, 0]:
    remove_slide(prs, idx)
    logging.info(f'Removed slide at index {idx}')

# 現在、選択したスライドのみが残っている（index=0）
slide = prs.slides[0]
```

---

## Shape IDの管理

```python
# 選択したテンプレートスライドのshape_idを定義
SLIDE_CONFIG = {
    'title_id': 41,        # タイトルのshape_id
    'lead_id': 15,         # リード文のshape_id
    'body_left_id': 49,    # 左カラム本文のshape_id
    'body_right_id': 50,   # 右カラム本文のshape_id
    'body_bottom_id': 20,  # 下部本文のshape_id
}
```

---

## テキストの設定例

### タイトルの設定

```python
shape = find_shape_by_id(slide, SLIDE_CONFIG['title_id'])
if shape:
    set_text_with_format(shape, [
        {'text': 'スライドタイトル', 'font_size': 20, 'bold': True}
    ])
```

### リード文の設定（白文字・濃紺背景）

```python
shape = find_shape_by_id(slide, SLIDE_CONFIG['lead_id'])
if shape:
    set_text_with_format(shape, [
        {'text': 'キーメッセージを1文で記載。', 'font_size': 14, 'bold': True, 'color': 'FFFFFF'},
        {'text': '必要に応じて2文目も記載。', 'font_size': 14, 'bold': True, 'color': 'FFFFFF'},
    ])
```

### 本文の設定（見出し・箇条書き・空行）

```python
shape = find_shape_by_id(slide, SLIDE_CONFIG['body_left_id'])
if shape:
    paragraphs = [
        # 見出し（赤色・太字・13pt）
        {'text': '■セクション1', 'font_size': 13, 'bold': True, 'color': 'C00000'},
        # 本文
        {'text': '説明文を記載', 'font_size': 12},
        # 空行
        {'text': '', 'font_size': 12},
        # 次の見出し
        {'text': '■セクション2', 'font_size': 13, 'bold': True, 'color': 'C00000'},
        # 箇条書き（インデント1）
        {'text': '・項目1', 'font_size': 12, 'indent': 1},
        {'text': '・項目2', 'font_size': 12, 'indent': 1},
        # 空行
        {'text': '', 'font_size': 12},
        # セクションラベル【】（太字・12pt）
        {'text': '【サブセクション】', 'font_size': 12, 'bold': True},
        {'text': '・サブ項目1', 'font_size': 12, 'indent': 1},
    ]
    set_text_with_format(shape, paragraphs)

    # オブジェクトのサイズと位置を調整
    shape.width = Inches(4.0)
    shape.height = Inches(2.35)
    shape.top = Inches(1.65)
    shape.left = Inches(0.5)

    # 自動サイズ調整を有効化
    shape.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
```

---

## スライドサイズの確認と調整

```python
# スライドサイズを確認
slide_width = prs.slide_width / Inches(1)
slide_height = prs.slide_height / Inches(1)
logging.info(f'Slide size: {slide_width:.2f} x {slide_height:.2f} inches')

# 16:9の場合、高さは約5.6インチ
# オブジェクトの配置が範囲内に収まるように注意
```

---

## 不要なオブジェクトの削除

図領域のプレースホルダーなど、不要なshapeを削除:

```python
# 図領域の削除
figure_id = 51
shape = find_shape_by_id(slide, figure_id)
if shape:
    remove_shape_by_id(slide, figure_id)
    logging.info('Removed figure placeholder')
```

---

## 保存

```python
prs.save(OUTPUT)
logging.info(f'Saved: {OUTPUT}')
print(f'スライド作成完了: {OUTPUT}')
```

---

## 完全な実装例

2カラム構成のスライドを作成する完全な例:

```python
import sys
import shutil
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path.home() / '.claude/skills/pptx-from-reference'))

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.dml.color import RGBColor
from lib.core import remove_slide
from lib.shapes import find_shape_by_id, remove_shape_by_id

logging.basicConfig(
    filename=f'_work/create_slide_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)

def set_text_with_format(shape, paragraphs_data, base_font_name='BIZ UDPゴシック'):
    text_frame = shape.text_frame
    text_frame.clear()
    text_frame.word_wrap = True

    for para_data in paragraphs_data:
        if len(text_frame.paragraphs) == 1 and not text_frame.paragraphs[0].text:
            p = text_frame.paragraphs[0]
        else:
            p = text_frame.add_paragraph()

        p.text = para_data['text']
        p.level = para_data.get('indent', 0)

        for run in p.runs:
            run.font.name = base_font_name
            run.font.size = Pt(para_data.get('font_size', 12))
            run.font.bold = para_data.get('bold', False)
            run.font.underline = False

            if para_data.get('color'):
                run.font.color.rgb = RGBColor.from_string(para_data['color'])
            else:
                run.font.color.rgb = RGBColor(0, 0, 0)

# メイン処理
TEMPLATE = Path('template.pptx')
OUTPUT = Path('output.pptx')

shutil.copy(TEMPLATE, OUTPUT)
prs = Presentation(OUTPUT)

# スライド削除（例: index=3のスライドのみ残す）
for idx in [6, 5, 4, 2, 1, 0]:
    remove_slide(prs, idx)

slide = prs.slides[0]

SLIDE_CONFIG = {
    'title_id': 41,
    'lead_id': 15,
    'body_left_id': 49,
    'body_right_id': 50,
    'body_bottom_id': 20,
}

# タイトル
shape = find_shape_by_id(slide, SLIDE_CONFIG['title_id'])
if shape:
    set_text_with_format(shape, [
        {'text': 'スライドタイトル', 'font_size': 20, 'bold': True}
    ])

# リード文
shape = find_shape_by_id(slide, SLIDE_CONFIG['lead_id'])
if shape:
    set_text_with_format(shape, [
        {'text': 'キーメッセージを記載。', 'font_size': 14, 'bold': True, 'color': 'FFFFFF'},
    ])

# 左カラム
shape = find_shape_by_id(slide, SLIDE_CONFIG['body_left_id'])
if shape:
    paragraphs = [
        {'text': '■問題点', 'font_size': 13, 'bold': True, 'color': 'C00000'},
        {'text': '問題の説明', 'font_size': 12},
        {'text': '', 'font_size': 12},
        {'text': '■解決策', 'font_size': 13, 'bold': True, 'color': 'C00000'},
        {'text': '・解決策1', 'font_size': 12, 'indent': 1},
        {'text': '・解決策2', 'font_size': 12, 'indent': 1},
    ]
    set_text_with_format(shape, paragraphs)
    shape.width = Inches(4.0)
    shape.height = Inches(2.35)
    shape.top = Inches(1.65)
    shape.left = Inches(0.5)
    shape.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE

# 右カラム
shape = find_shape_by_id(slide, SLIDE_CONFIG['body_right_id'])
if shape:
    paragraphs = [
        {'text': '■背景', 'font_size': 13, 'bold': True, 'color': 'C00000'},
        {'text': '', 'font_size': 12},
        {'text': '【詳細】', 'font_size': 12, 'bold': True},
        {'text': '・詳細1', 'font_size': 12, 'indent': 1},
        {'text': '・詳細2', 'font_size': 12, 'indent': 1},
    ]
    set_text_with_format(shape, paragraphs)
    shape.width = Inches(4.5)
    shape.height = Inches(2.35)
    shape.top = Inches(1.65)
    shape.left = Inches(5.0)
    shape.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE

# 下部
shape = find_shape_by_id(slide, SLIDE_CONFIG['body_bottom_id'])
if shape:
    paragraphs = [
        {'text': '■今後の対応', 'font_size': 13, 'bold': True, 'color': 'C00000'},
        {'text': '', 'font_size': 12},
        {'text': '【短期対応】', 'font_size': 12, 'bold': True},
        {'text': '・対応1', 'font_size': 12, 'indent': 1},
        {'text': '', 'font_size': 12},
        {'text': '【長期対応】', 'font_size': 12, 'bold': True},
        {'text': '・対応2', 'font_size': 12, 'indent': 1},
    ]
    set_text_with_format(shape, paragraphs)
    shape.width = Inches(9.0)
    shape.height = Inches(1.45)
    shape.top = Inches(4.05)
    shape.left = Inches(0.5)
    shape.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE

# 保存
prs.save(OUTPUT)
logging.info(f'Saved: {OUTPUT}')
print(f'スライド作成完了: {OUTPUT}')
```

---

## 重要な注意事項

1. **フォント名の取得**: 必ずフェーズ3でテンプレートから実際のフォント名を取得し、`base_font_name` に設定する

2. **下線の除去**: `run.font.underline = False` は必須

3. **スライドサイズの確認**: 16:9の場合、高さは約5.6インチ。オブジェクトが範囲外に出ないように注意

4. **インデックスの注意**: スライド削除後はインデックスが変わる。削除は必ず後ろから順に行う

5. **auto_size の活用**: テキストが多い場合は `MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE` で自動調整

6. **ログの活用**: 問題が発生した場合、ログファイルで詳細を確認
