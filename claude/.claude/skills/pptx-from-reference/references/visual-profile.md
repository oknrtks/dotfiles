# Visual Profile 抽出仕様 (R1)

`profile_visual.py` が参照 .pptx から機械的に抽出する情報の仕様。

## 抽出対象

### theme (テーマ情報)
- `color_scheme`: `ppt/theme/theme1.xml` の `<a:clrScheme>` から全色を抽出
  - bg1, tx1, bg2, tx2, accent1-6, hlink, folHlink
- `font_scheme`: `<a:fontScheme>` から
  - major_latin, minor_latin, major_ea, minor_ea
- `default_size_pt`: スライドマスタの placeholder からデフォルトフォントサイズを抽出
  - title, body

### layouts (レイアウト一覧)
- `ppt/slideLayouts/` の各 XML を走査
- 各レイアウトから:
  - `id`: ファイル名 (e.g., `slideLayout3.xml`)
  - `name`: `<p:cSld name="...">` の name 属性
  - `placeholders`: 各 `<p:sp>` の placeholder 情報
    - idx, type (title/body/subtitle/etc.), bbox_in (インチ単位の位置・サイズ)
  - `decorative_shapes_count`: placeholder 以外の shape 数

### slide_size_in (スライドサイズ)
- `ppt/presentation.xml` の `<p:sldSz>` から cx/cy を EMU → インチ変換

## 出力フォーマット

`schemas/visual_profile.schema.json` に準拠した JSON。
