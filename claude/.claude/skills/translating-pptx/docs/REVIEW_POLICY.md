# 翻訳レビューポリシー

## 目的

PPTX翻訳プロジェクトにおける品質保証と翻訳漏れ防止のためのレビューポリシーを定義する。

## 基本原則

### 1. 数値検証の優先

**数値検証は品質レビューの前に実施すること**。

- ❌ 良い → 翻訳の品質レビュー → 数値検証
- ✅ 正解 → 数値検証 → 品質レビュー

**理由**: 翻訳漏れがある場合、品質レビュー自体が不完全になる。

### 2. 全数カウントの原則

翻訳対象のテキストは、**全てカウントすること**。

- 抽出された日本語テキスト数
- 翻訳JSONに記録された翻訳数
- これらが一致していることを確認する

### 3. 自動化の優先

手動での目視確認は**不可**とする。必ずスクリプトによる数値検証を行う。

## 必須検証プロセス

### フェーズ1: 数値検証（必須）

#### 検証スクリプト

```bash
#!/bin/bash
# verify_translations.sh

for i in {1..6}; do
  echo "=== Slide $i ==="

  # 抽出された日本語テキスト数
  extracted_jp=$(cat extracted/slide${i}_texts.json | jq '.total_japanese_texts')

  # 翻訳JSONのエントリ数（changed: trueの数）
  translated=$(cat translations/slide${i}_translations.json | jq '[.translations[] | select(.changed == true)] | length')

  echo "Extracted Japanese texts: $extracted_jp"
  echo "Translated texts: $translated"

  if [ "$extracted_jp" -eq "$translated" ]; then
    echo "✅ PASS"
  else
    echo "❌ FAIL: Missing $((extracted_jp - translated)) translations"
    echo "Review the following:"
    echo "  - extracted/slide${i}_texts.json (has_japanese: true entries)"
    echo "  - translations/slide${i}_translations.json (changed: true entries)"
    exit 1
  fi
  echo
done

echo "✅ All slides passed numerical verification"
```

#### 合格基準

**全スライドで `extracted_jp == translated` であること**。

不一致がある場合:
- ❌ 品質レビューに進まない
- ❌ 翻訳の適用を行わない
- ✅ 翻訳漏れを特定し、補完する

### フェーズ2: 品質レビュー（必須）

数値検証合格後、以下の品質レビューを行う。

#### チェックリスト

- [ ] 用語の統一性（LLM, Transformer, RAG, OCIなど）
- [ ] トーンの一貫性（謙虚さ、親しみやすさ）
- [ ] 技術的正確性（数字、専門用語）
- [ ] 自然な英語表現
- [ ] Run単位の境界が保持されている
- [ ] スペース調整が適切（日本語・英語境界）

### フェーズ3: 適用後の検証（必須）

翻訳適用後、以下の検証を行う。

```bash
# 内容確認
uv run python -m markitdown converted.pptx

# 未翻訳の日本語テキストを検出
uv run python -m markitdown converted.pptx | grep -P '[\p{Hiragana}\p{Katakana}\p{Han}]'
```

**合格基準**: 画像内テキスト以外に日本語が含まれていないこと。

## レビュー記録

### レビューログの作成

各レビューで以下を記録すること：

1. 数値検証結果（各スライドのカウント）
2. 品質レビュー結果（問題点と修正内容）
3. 適用後の検証結果

### 記録フォーマット

```markdown
## 翻訳レビュー記録

### 日付: YYYY-MM-DD

### 数値検証

| スライド | 抽出された日本語数 | 翻訳数 | 結果 |
|---------|------------------|--------|------|
| 1       | 3                | 3      | ✅   |
| 2       | 27               | 27     | ✅   |
| 3       | 20               | 20     | ✅   |
| 4       | 47               | 5      | ❌   |
| 5       | 6                | 6      | ✅   |
| 6       | 5                | 5      | ✅   |

### 品質レビュー

- 用語統一性: ✅
- トーン一貫性: ✅
- 技術的正確性: ✅

### 適用後検証

- 未翻訳日本語: ❌ スライド4で42個の翻訳漏れ
- 修正必要: 是
```

## よくある間違い

### ❌ 間違ったアプローチ

1. **目視確認のみ**: 「見た感じ全て翻訳されている」
   - 原因: 数値検証を行っていない
   - 結果: 翻訳漏れに気づかない

2. **品質レビュー優先**: 「翻訳の質をレビューしてから数値を確認」
   - 原因: 数値検証の重要性を理解していない
   - 結果: 不完全な翻訳を品質レビューする無駄が発生

3. **Agentの完了報告を鵜呑み**: 「Agentが『完了』と言ったのでOK」
   - 原因: 検証プロセスをスキップ
   - 結果: 翻訳漏れが発見されない

### ✅ 正しいアプローチ

1. **数値検証を最初に**: スクリプトでカウントを確認
2. **不一致を即座に検出**: カウントが合わない場合は原因を特定
3. **品質レビューは数値検証後**: 全て翻訳されていることを確認してから品質をレビュー

## ポリシー違反時の対処

### 翻訳漏れが発見された場合

1. 原因を特定
   - Agentが処理を打ち切ったか？
   - 抽出スクリプトがテキストを取得できなかったか？
   - 翻訳JSONの作成で漏れがあったか？

2. 修正を実施
   - 未翻訳テキストを特定
   - 追加翻訳を実施
   - 数値検証を再実行

3. 文書化
   - レビューログに記録
   - 原因と対策を記載
   - 再発防止策を検討

## 参考

- PLAN.md: 翻訳ワークフローの全体像
- SLIDE_NOTES.md: スライドごとのレビュー記録
- scripts/verify_translations.sh: 数値検証スクリプト（作成予定）
