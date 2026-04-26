# Changelog

## Iter 6 - 最終仕上げ

- CHANGELOG.md に Iter 0-6 の全変更履歴を記録
- §14 完了基準の最終チェック
- docs/PLAN.md 同梱確認

## Iter 5 - description 最適化

- SKILL.md の description を非発火ケース(T5/T6)対策で強化
- 「ONLY when the user explicitly provides or references a specific .pptx file」を明記
- 「CRITICAL: Do NOT trigger when no reference .pptx is provided」を追加

## Iter 4 - QA Sanity Check 完成

- qa_sanity.py 6 項目の動作検証完了
- 存在しないレイアウト ID の Fail 検出確認
- テキストオーバーフロー推定(Warning)の動作確認

## Iter 3 - Phase 0 入力検証

- pdf-required-notice.md 作成済み
- SKILL.md の Phase 0 ワークフローに PDF 欠落時の動作を明記

## Iter 2 - Voice Profile + PDF ラスタライズ

- profile_voice.py: raw_stats + text_samples_per_slide 抽出
- rasterize_pdf.py: pdftoppm による PDF → PNG 変換
- 4 ページ分の PDF 画像生成確認

## Iter 1 - Visual Profile + Render 最小実装

- profile_visual.py: テーマ色・フォント・レイアウト・placeholder 情報の抽出
- render.py: slide_plan → PPTX レンダリングパイプライン完成
  - 相対パス解決バグ修正
  - sldId ユニーク性修正
  - placeholder 不在時の自動生成
- 全 6 項目 Sanity Check Pass 達成

## Iter 0 - スケルトン作成

- ディレクトリ構成を PLAN.md §4 に従い作成
- SKILL.md 初版(暫定 description)
- references/ ドキュメント群作成
  - visual-profile.md, voice-profile.md, outline-format.md, render-rules.md
  - pdf-required-notice.md, future-work.md
- schemas/ 定義
  - visual_profile.schema.json, voice_profile.schema.json, slide_plan.schema.json
- scripts/ 初版実装
  - _common.py: 公式 pptx スキルのパス解決、ユーティリティ
  - profile_visual.py: visual_profile.json 抽出
  - profile_voice.py: voice_profile.json 抽出
  - rasterize_pdf.py: PDF → PNG 変換
  - render.py: slide_plan → PPTX レンダリング
  - qa_sanity.py: Phase 5 Sanity Check 6 項目
- tests/inputs/ テストデータ作成
  - ref_template.pptx, ref_template.pdf, content_sample.md
- tests/eval/trigger_eval.json 初版(T1-T7)
