# Markdown Frontmatter 仕様 (R3)

入力コンテンツの Markdown フォーマット仕様。

## Frontmatter フィールド

```yaml
---
reference_pptx: ./refs/template.pptx    # 参照 PPTX パス (必須)
reference_pdf:  ./refs/template.pdf      # 参照 PDF パス (必須)
output: ./out/deliverable.pptx           # 出力パス (任意, デフォルト: ./output.pptx)
target_slide_count: 8                    # 目標スライド数 (任意, ±2 まで LLM 裁量)
language: ja                             # 言語 (任意, デフォルト: ja)
---
```

## Frontmatter が無い場合

frontmatter が無い場合、ユーザの指示から以下を推定する:
- `reference_pptx`: ユーザが提示した .pptx ファイルパス
- `reference_pdf`: reference_pptx と同じステム + .pdf
- `output`: `./output.pptx`
- `target_slide_count`: LLM がコンテンツ量から判断
- `language`: `ja`

## 本文フォーマット

```markdown
# タイトル

## セクション1
- 箇条書き項目
- 箇条書き項目

## セクション2
本文テキスト...

### サブセクション
- 詳細項目
```

- `#` → プレゼンテーション全体のタイトル
- `##` → 各スライドまたはセクションの区切り
- `###` → サブセクション(ペイン内の見出し等)
- `-` → 箇条書き
- 本文テキスト → リード文や説明文
