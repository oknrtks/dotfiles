# トラブルシューティング例

実際の問題と解決策の具体例です。

---

## 問題1: テキストが画面から切れる

### 症状
```
スライド下部のテキストが表示されない
```

### 原因
スライドサイズ（16:9の場合、高さ約5.6インチ）を超えてオブジェクトを配置している。

### 診断方法
```python
from pptx import Presentation
from pptx.util import Inches

prs = Presentation('output.pptx')
print(f"Slide height: {prs.slide_height / Inches(1):.2f} inches")

slide = prs.slides[0]
for shape in slide.shapes:
    if shape.has_text_frame:
        bottom = (shape.top + shape.height) / Inches(1)
        print(f"shape_id={shape.shape_id}, bottom={bottom:.2f}in")
```

### 解決策
オブジェクトの `top` と `height` を調整:

```python
# 修正前
shape.top = Inches(6.0)
shape.height = Inches(1.5)
# → bottom = 7.5インチ（スライド高さ5.6インチを超えている！）

# 修正後
shape.top = Inches(4.0)
shape.height = Inches(1.4)
# → bottom = 5.4インチ（スライド内に収まる）
```

---

## 問題2: フォントが明朝体になる

### 症状
```
テンプレートはゴシック体なのに、生成されたスライドが明朝体になる
```

### 原因
`set_text_with_format` 関数の `base_font_name` にデフォルト値を使用している。

### 診断方法
```python
from pptx import Presentation

prs = Presentation('output.pptx')
slide = prs.slides[0]
for shape in slide.shapes:
    if shape.has_text_frame and shape.text_frame.paragraphs:
        para = shape.text_frame.paragraphs[0]
        if para.runs:
            print(f"Font: {para.runs[0].font.name}")
```

### 解決策

1. テンプレートから正しいフォント名を取得:
```python
from pptx import Presentation

prs = Presentation('template.pptx')
slide = prs.slides[3]  # 選択したテンプレートスライド
shape = slide.shapes[0]  # 本文ボックス

if shape.has_text_frame and shape.text_frame.paragraphs:
    para = shape.text_frame.paragraphs[0]
    if para.runs:
        font_name = para.runs[0].font.name
        print(f"Template font: {font_name}")
        # 例: "BIZ UDPゴシック"
```

2. 取得したフォント名を使用:
```python
def set_text_with_format(shape, paragraphs_data, base_font_name='BIZ UDPゴシック'):
    # ↑ この 'BIZ UDPゴシック' を実際のフォント名に変更
    ...
```

---

## 問題3: 下線が残る

### 症状
```
すべてのテキストに下線が引かれている
```

### 原因
テンプレートの書式を引き継いでおり、`run.font.underline = False` を設定していない。

### 解決策
`set_text_with_format` 関数内で明示的に設定:

```python
def set_text_with_format(shape, paragraphs_data, base_font_name='BIZ UDPゴシック'):
    ...
    for run in p.runs:
        run.font.name = base_font_name
        run.font.size = Pt(para_data.get('font_size', 12))
        run.font.bold = para_data.get('bold', False)
        run.font.underline = False  # ← これを追加
        ...
```

---

## 問題4: 強調がなく読みづらい

### 症状
```
すべてのテキストが同じ書式で、メリハリがない
```

### 原因
色・太字・インデントを適切に設定していない。

### 解決策
見出し・セクション・箇条書きに適切な書式を設定:

```python
paragraphs = [
    # 見出し: 赤色・太字・13pt
    {'text': '■問題点', 'font_size': 13, 'bold': True, 'color': 'C00000'},

    # 本文: 通常・12pt
    {'text': '問題の説明', 'font_size': 12},

    # 空行
    {'text': '', 'font_size': 12},

    # セクションラベル: 太字・12pt
    {'text': '【詳細】', 'font_size': 12, 'bold': True},

    # 箇条書き: インデント1・12pt
    {'text': '・項目1', 'font_size': 12, 'indent': 1},
    {'text': '・項目2', 'font_size': 12, 'indent': 1},
]
```

**推奨設定:**
- 見出し（■）: `color='C00000', bold=True, font_size=13`
- セクション（【】）: `bold=True, font_size=12`
- 本文: `font_size=12`
- 箇条書き: `indent=1, font_size=12`

---

## 問題5: 情報が劣化している

### 症状
```
元の資料にあった重要な情報が省略されている
```

### 原因
テンプレートに内容を無理に合わせようとして、情報を削除した。

### 解決策

**正しいアプローチ:**
1. **内容を先に推敲**: 情報を整理し、劣化させない
2. **テンプレート選択**: 情報量に応じて適切なテンプレートを選ぶ
3. **オブジェクト調整**: 必要に応じてテキストボックスのサイズ・位置を調整

**悪い例:**
```
元の内容:
「OCIのオートスケーリング機能が貧弱だったため、REIシステムリフト時に一度断念し、以降選択肢に挙がっていない」

↓ テンプレートに合わせて短縮（情報劣化）

「OCI機能不足で断念」
```

**良い例:**
```
元の内容を保持:
「OCIのオートスケーリング機能が貧弱だったため、REIシステムリフト時に一度断念」
「以降、選択肢に挙がっていない」

↓ 2行に分けて表示
```

---

## 問題6: テキストボックスの文字が重なる

### 症状
```
左カラムと右カラムのテキストが重なって読めない
```

### 原因
テキストボックスの `width` または `left` の設定が適切でない。

### 診断方法
```python
from pptx import Presentation
from pptx.util import Inches

prs = Presentation('output.pptx')
slide = prs.slides[0]

for shape in slide.shapes:
    if shape.has_text_frame:
        left = shape.left / Inches(1)
        width = shape.width / Inches(1)
        right = (shape.left + shape.width) / Inches(1)
        print(f"shape_id={shape.shape_id}, left={left:.2f}, width={width:.2f}, right={right:.2f}")
```

### 解決策
左カラムと右カラムが重ならないように調整:

```python
# 左カラム
shape_left.width = Inches(4.0)
shape_left.left = Inches(0.5)
# → right = 4.5インチ

# 右カラム（左カラムの右端より右に配置）
shape_right.width = Inches(4.5)
shape_right.left = Inches(5.0)  # 4.5より大きい値
# → right = 9.5インチ
```

---

## 問題7: `auto_size` が効かない

### 症状
```
`MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE` を設定したのに、テキストがはみ出る
```

### 原因
`auto_size` はテキストを縮小してボックスに収めるが、ボックス自体が小さすぎる場合は限界がある。

### 解決策

**Option 1: ボックスの高さを増やす**
```python
shape.height = Inches(2.5)  # 高さを増やす
shape.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
```

**Option 2: テキスト量を減らす**
- 内容を簡潔化（最終手段）
- フォントサイズを若干縮小（11pt等）

**Option 3: 別のテンプレートを選択**
- より広いスペースを持つテンプレートに変更

---

## 問題8: スライド削除後のインデックスがずれる

### 症状
```
スライド削除後、意図しないスライドにアクセスしている
```

### 原因
スライド削除後、後続のスライドのインデックスがずれる。

### 解決策
**必ず後ろから順に削除**:

```python
# 正しい（後ろから削除）
for idx in [9, 7, 4]:
    remove_slide(prs, idx)

# 間違い（前から削除）
for idx in [4, 7, 9]:
    remove_slide(prs, idx)
    # idx=4を削除すると、元のidx=7が新しいidx=6になる！
```

---

## 問題9: リード文の背景色が失われる

### 症状
```
リード文の濃紺背景が消えて、白背景になる
```

### 原因
`text_frame.clear()` を実行すると、shapeの背景色は保持されるが、場合によってはテンプレートの書式がリセットされる。

### 診断方法
元のテンプレートでリード文の背景色を確認:

```python
from pptx import Presentation

prs = Presentation('template.pptx')
slide = prs.slides[3]
shape = slide.shapes[1]  # リード文のshape

print(f"Fill type: {shape.fill.type}")
if shape.fill.type == 1:  # SOLID
    print(f"Fill color: {shape.fill.fore_color.rgb}")
```

### 解決策
背景色はshape自体の属性として保持されているため、通常は `text_frame.clear()` を実行しても消えない。ただし、リード文のshapeが正しく選択されているか確認:

```python
# リード文のshape_idが正しいか確認
shape = find_shape_by_id(slide, SLIDE_CONFIG['lead_id'])
print(f"Shape name: {shape.name}")
print(f"Fill type: {shape.fill.type}")
```

---

## 問題10: 目視確認をスキップして失敗

### 症状
```
スクリプトは正常に実行されたが、生成されたスライドが使えない
```

### 原因
目視確認をスキップしたため、テキストの見切れ・重なり・フォント問題に気づかなかった。

### 解決策
**必ず目視確認を実施**:

1. PDF/JPEG化:
```bash
uv run python ~/.claude/skills/pptx/scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf output
```

2. 画像を確認:
- すべてのテキストが視認可能か
- フォントは統一されているか
- 強調は適切か
- テキストボックスからはみ出ていないか

3. 問題があれば修正して再生成

**目視確認は省略しない**: スクリプトの実行が成功しても、視覚的な問題は目視でしか発見できない。
