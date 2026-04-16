# Voice Profile 抽出仕様 (R2)

`profile_voice.py` が参照 .pptx + .pdf から機械的に抽出する情報の仕様。

## スクリプトが抽出する情報(純粋機械的処理)

### raw_stats (統計情報)
- `avg_chars_per_slide`: スライドあたり平均文字数
- `bullet_count_per_slide_median`: スライドあたり箇条書き数の中央値
- `max_bullet_depth`: 箇条書きの最大深さ
- `title_length_median`: タイトル文字数の中央値
- `shape_count_per_slide_median`: スライドあたり shape 数の中央値

### text_samples_per_slide
- 各スライドのタイトルと本文テキストサンプル
- `--sample-slides 20` で上限制御

### pdf_page_images
- `rasterize_pdf.py` で生成した各ページの PNG パス一覧

## スクリプトが「やらない」こと(LLM 判断領域)

以下は Phase 2 で LLM が PDF 画像と突き合わせて判断する:
- 敬体/常体/体言止めの分類
- リード文ゾーンの特定
- 2 ペイン・グリッド等の空間構造判定
- 頻出表現や定型句の抽出
- 語尾の傾向分析

## 出力フォーマット

`schemas/voice_profile.schema.json` に準拠した JSON + PDF 画像ファイル群。
