# レンダリングルール (R4)

`render.py` が slide_plan.json に基づいて PPTX を生成する際のルール。

## 基本方針

- 公式 pptx スキルの editing.md ワークフローに従う
- unpack → スライド複製 → コンテンツ差し込み → clean → pack
- テーマ XML は一切変更しない

## レイアウト選択

- slide_plan の `layout_id` は visual_profile.layouts[*].id から選択されたもののみ使用
- 存在しない layout_id は Fail

## テキスト差し込みルール

- placeholder の `<a:p>` 要素にテキストを流し込む
- 複数の箇条書き項目は複数の `<a:p>` 要素に分割
- Unicode 箇条書き記号(・, ● 等)は使用禁止、`<a:buChar>` を使用
- smart quotes は XML エンティティ化: `"` → `&#x201C;`, `"` → `&#x201D;`
- 日本語鉤括弧「」はそのまま(Unicode 範囲が異なるため)

## Shape 配置ルール

- 図形は PowerPoint ネイティブ shape で生成
- image_placeholder は灰色矩形(`808080`)+ 中央にラベルテキスト
- 座標系: EMU (English Metric Units), 1 inch = 914400 EMU
- すべての shape は `x >= 0, y >= 0, x+w <= slide_w, y+h <= slide_h`

## 行間ルール

- `lineSpacing` と bullet の併用禁止
- 行間調整は `paraSpaceAfter` を使用
- `ROUNDED_RECTANGLE` + 矩形アクセントの組み合わせ禁止

## Pack 時の注意

- `pack.py` は `--original reference.pptx` 付きで実行し検証を有効化
