---
name: pptx-from-template
description: Creates new PowerPoint slides from template PPTX files by selecting appropriate layouts, preserving fonts and colors, and adding proper formatting with emphasis. Use when the user provides a template PPTX file and wants to create slides with specific content, or when working with existing PPTX templates to generate new presentations.
---

# Creating Slides from PPTX Templates

このスキルは、テンプレートPPTXファイルから新しいスライドを作成するための体系的なアプローチを提供します。

## 重要な原則

1. **内容優先、テンプレート選択は後**: テンプレートに内容を無理に合わせず、内容を整理してから適切なテンプレートを選択する
2. **書式の保持**: テンプレートのフォント・配色を保持し、下線などの不要な書式のみ除去
3. **柔軟な調整**: オブジェクトのサイズ・位置は必要に応じて調整可能
4. **適切な強調**: 色・太字・インデントで視認性を向上

---

## フェーズ1: 内容の推敲と整理

テンプレート選択の前に、まず伝えるべき内容を明確化します。

### 手順

1. **情報の抽出と整理**
   - 提供された資料（マークダウン、テキスト等）から要点を抽出
   - 情報を論理的な構造（問題・解決策・背景・対応等）に整理
   - 情報量と階層構造を把握

2. **内容の推敲**
   - 情報の劣化を避け、重要な詳細を保持
   - 簡潔さと完全性のバランスを取る
   - スライド1枚に収まる範囲で最大限の情報を含める

3. **推敲結果の記録**
   - `_work/slide_content_draft.md` に整理した内容を記録
   - 各セクションのボリュームを明記
   - 推奨テンプレート構成を記載

**推敲時の判断基準:**
- 見出しレベル: いくつの主要セクションがあるか？（2-3ブロック / 左右カラム等）
- 情報密度: 各セクションにどの程度の情報量があるか？
- 階層構造: 箇条書き・サブセクションはどの程度必要か？

---

## フェーズ2: テンプレートの分析と選択

テンプレートPPTXファイルからスライド構造を理解し、適切なレイアウトを選択します。

### 手順1: テンプレートの全体確認

```bash
uv run python - <<'EOF'
from pptx import Presentation

prs = Presentation('template.pptx')
print(f"Total slides: {len(prs.slides)}\n")

for idx, slide in enumerate(prs.slides):
    print(f"--- Slide {idx + 1} ---")
    # タイトルを含むshapeを探す
    title_text = ""
    for shape in slide.shapes:
        if shape.has_text_frame:
            text = shape.text.strip()
            if text and ('テンプレート' in text or 'スライド' in text or '表紙' in text):
                title_text = text
                break
    print(f"Type: {title_text if title_text else '(タイトル不明)'}\n")
EOF
```

### 手順2: 各スライドの構造確認

選択候補のスライドについて、詳細な構造を確認:

```bash
uv run python - <<'EOF'
from pptx import Presentation

prs = Presentation('template.pptx')
slide_idx = 2  # 確認したいスライドのindex

slide = prs.slides[slide_idx]
print(f"=== Slide {slide_idx + 1} Structure ===\n")

for shape in slide.shapes:
    if shape.has_text_frame:
        text = shape.text[:50].replace('\n', ' ')
        print(f"shape_id={shape.shape_id}, text={text!r}")
EOF
```

### 手順3: テンプレート選択の判断

フェーズ1で整理した内容の構造に基づいて選択:

**2カラム構成（左右分割）が適切な場合:**
- 「問題と原因」「現状と対策」など、対比する情報がある
- 複数の独立した情報ブロックを並列表示したい
- 横幅を有効活用したい

**3ブロック構成（背景・目的・対応等）が適切な場合:**
- 時系列または論理的な流れがある（過去・現在・未来等）
- 3つの独立したトピックがある
- 縦方向のスペースに余裕がある

**選択基準:**
- 情報量が多い → 2カラム構成を優先
- 情報が少なく階層が浅い → 3ブロック構成でも可
- 対比・比較が重要 → 2カラム構成

---

## フェーズ3: テンプレートのフォント情報取得

選択したテンプレートスライドから、保持すべきフォント情報を取得します。

```bash
uv run python - <<'EOF'
from pptx import Presentation

prs = Presentation('template.pptx')
slide_idx = 3  # 選択したスライドのindex
slide = prs.slides[slide_idx]

# 本文ボックスのshape_idを指定（フェーズ2で確認したもの）
body_shape_id = 49

for shape in slide.shapes:
    if shape.shape_id == body_shape_id and shape.has_text_frame:
        if shape.text_frame.paragraphs:
            para = shape.text_frame.paragraphs[0]
            if para.runs:
                run = para.runs[0]
                print(f"Font name: {run.font.name}")
                print(f"Font size: {run.font.size.pt if run.font.size else 'None'} pt")
                print(f"Bold: {run.font.bold}")
                print(f"Underline: {run.font.underline}")
                break
EOF
```

この情報（特にフォント名）を記録し、フェーズ4で使用します。

---

## フェーズ4: スライド作成スクリプトの実装

テンプレートから新しいスライドを作成するPythonスクリプトを実装します。

### スクリプト構造

詳細は [./script-implementation-guide.md](./script-implementation-guide.md) を参照してください。

### 重要なポイント

1. **書式設定関数の実装**
   - テンプレートのフォント名を保持
   - 下線を明示的にオフ（`run.font.underline = False`）
   - 色・太字・インデントを適切に設定

2. **テキスト内容の構造化**
   - 見出し: 赤色（`#C00000`）、太字、サイズ13pt
   - セクションラベル【】: 太字、サイズ12pt
   - 本文: 通常、サイズ12pt
   - 箇条書き: インデントレベル1を使用

3. **オブジェクトの配置調整**
   - スライドサイズを確認（16:9の場合、高さは約5.6インチ）
   - テキストボックスの位置・サイズを調整
   - `shape.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE` で自動調整

4. **不要スライドの削除**
   - 使用しないテンプレートスライドを後ろから順に削除
   - `remove_slide(prs, idx)` を使用

---

## フェーズ5: 目視確認と調整

生成したスライドを確認し、必要に応じて調整します。

### 確認手順

1. **PDF/JPEG化**
```bash
uv run python ~/.claude/skills/pptx/scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf output
```

2. **目視確認項目**
   - すべてのテキストが視認可能か
   - フォントは統一されているか
   - 強調（色・太字）は適切か
   - インデントは正しく表示されているか
   - テキストボックスからはみ出ていないか

3. **調整が必要な場合**
   - テキストボックスのサイズ・位置を微調整
   - フォントサイズを若干縮小
   - 内容を簡潔化（最終手段）

---

## ベストプラクティス

### やるべきこと

- ✓ 内容を先に推敲し、テンプレート選択は後
- ✓ テンプレートのフォント名を取得して保持
- ✓ 下線を明示的に除去
- ✓ 見出しに赤色、セクションに太字で強調
- ✓ 箇条書きにインデントを使用
- ✓ 目視確認を必ず実施

### やってはいけないこと

- ✗ テンプレートに内容を無理に合わせる（情報劣化）
- ✗ フォントをデフォルトに戻す
- ✗ `set_text_preserve_style` を使用（下線が引き継がれる）
- ✗ スライドサイズを考慮せずにオブジェクトを配置
- ✗ 目視確認をスキップ

---

## トラブルシューティング

### 問題: テキストが見切れる

**原因**: テキストボックスの高さが不足、またはスライドサイズを超えている

**解決策**:
1. スライドサイズを確認: `prs.slide_height / Inches(1)`
2. テキストボックスの `top + height` がスライド高さを超えないように調整
3. `auto_size` を有効化

### 問題: フォントが明朝体になる

**原因**: `set_text_with_format` 関数でフォント名を指定していない

**解決策**:
1. フェーズ3でフォント名を取得
2. 関数の `base_font_name` パラメータに設定

### 問題: 下線が残る

**原因**: `run.font.underline = False` を設定していない

**解決策**:
- 書式設定関数内で明示的に `run.font.underline = False` を追加

### 問題: 強調がない

**原因**: 色・太字の設定が不足

**解決策**:
- 見出し: `color='C00000', bold=True`
- セクションラベル: `bold=True`
- 箇条書き: `indent=1`

---

## 参考資料

- [./script-implementation-guide.md](./script-implementation-guide.md) - スクリプト実装の詳細
- [./troubleshooting-examples.md](./troubleshooting-examples.md) - よくある問題と解決例
