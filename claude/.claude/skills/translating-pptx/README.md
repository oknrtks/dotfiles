# PPTX翻訳スキル詳細ガイド

## 概要

日本語のPowerPointプレゼンテーションを英語に翻訳するためのスキルです。

## 完全なワークフロー

### フェーズ1: 準備

```bash
# 1. カレントディレクトリを確認
pwd
# /path/to/your/project

# 2. 入力ファイルを確認
ls -lh input.pptx

# 3. 出力ディレクトリを作成
mkdir -p extracted translations

# 4. 環境セットアップ（初回のみ）
bash scripts/setup_environment.sh
```

**環境セットアップについて**:
- Python 3.12+を自動検出
- 必要なパッケージをチェック・インストール
- スクリプトに実行権限を付与
- 詳細は「環境セットアップ」セクションを参照

### フェーズ2: テキスト抽出

```bash
python3 scripts/extract_texts_from_xml.py input.pptx extracted/
```

**出力ファイルの確認**:
```bash
ls -la extracted/
# slide1_texts.json
# slide2_texts.json
# ...
# slide6_texts.json
```

**抽出結果の確認**:
```bash
cat extracted/slide1_texts.json | jq '.total_texts, .total_japanese_texts'
```

### フェーズ3: 翻訳

#### ステップ3.1: 未翻訳テキストの確認

```bash
python3 scripts/list_missing_translations.py
```

**出力例**:
```
Slide 1: 2 missing translations
Slide 2: ✅ All translations complete
Slide 3: 5 missing translations
...
```

#### ステップ3.2: 翻訳プロンプトの作成

```bash
python3 scripts/translate_missing.py 3
```

**出力ファイル**: `translate_slide3_prompt.md`

#### ステップ3.3: AI翻訳

1. `translate_slide3_prompt.md`を開く
2. 内容をClaude Codeに貼り付け
3. 翻訳結果をコピー
4. `slide3_batch_translations.json`として保存

#### ステップ3.4: 翻訳の追加

```bash
python3 scripts/add_translations.py 3 slide3_batch_translations.json
```

**または、単一追加**:
```bash
python3 scripts/add_translations.py 3 2_0_1 "大規模言語モデル" "Large Language Model"
```

### フェーズ4: レビュー（必須・新規）

```bash
python3 scripts/review_translations.py
```

**レビュー項目**:
- 空翻訳の検出
- 文脈の一貫性チェック
- 技術用語の整合性確認
- 自然な英語表現の検証

**不合格の場合**:
```bash
# 空翻訳の一覧を表示
python3 scripts/list_empty_translations.py

# 翻訳を修正
python3 scripts/add_translations.py <slide_num> <key> "<original>" "<translated>"

# 再レビュー
python3 scripts/review_translations.py
```

### フェーズ5: 検証（必須・改善）

```bash
bash scripts/verify_translations.sh
```

**合格基準**: 全スライドで「✅ 合格（空翻訳なし）」であること。

**検証項目**:
- 翻訳漏れのチェック（キーベース）
- 空翻訳の検出（新規）
- 構造チェック（`translated`、`changed`フィールド）

**不合格の場合**:
```bash
# 不合格のスライドを詳細確認
python3 scripts/list_missing_translations.py <slide_num>

# 空翻訳を確認
python3 scripts/list_empty_translations.py

# 翻訳プロンプトを再作成
python3 scripts/translate_missing.py <slide_num>

# 翻訳を追加
python3 scripts/add_translations.py <slide_num> <json_file>

# 再度検証
bash scripts/verify_translations.sh
```

### フェーズ6: 適用

```bash
python3 scripts/apply_translations.py input.pptx translations/ output.pptx
```

**出力**: `output.pptx` （紫色でマーキングされた翻訳テキスト）

### フェーズ7: 最終検証（必須・新規）

```bash
bash scripts/final_validation.sh output.pptx
```

**検証項目**:
- ファイル整合性チェック
- 日本語テキストの検出
- カラーマーキングの確認
- レイアウト検証
- 検証レポートの生成

**手動確認も推奨**:
```bash
# 内容確認
python3 -m markitdown output.pptx > output.md

# PowerPointで開いて視覚的に確認
open output.pptx  # macOS
# xdg-open output.pptx  # Linux
# start output.pptx  # Windows
```
    if japanese.search(line) and '!' not in line and '.jpg' not in line:
        print(f'{i}: {line.strip()[:100]}')
        found = True
if not found:
    print('✅ No Japanese text found (except image captions)')
"
```

## 翻訳JSON形式

### 単一翻訳

```json
{
  "slide_number": 1,
  "translations": {
    "0_0_1": {
      "original": "今更ですが、生成",
      "translated": "Belatedly, Generative ",
      "changed": true
    }
  }
}
```

### バッチ翻訳

```json
{
  "2_0_1": {
    "original": "大規模言語モデル",
    "translated": "Large Language Model ",
    "changed": true
  },
  "2_0_3": {
    "original": "は多様なタスクをこなしますが、ここでは",
    "translated": "can perform various tasks, but here ",
    "changed": true
  }
}
```

## よくあるエラーと解決策

### エラー1: 構造エラー - フィールドが不足

```
❌ 構造エラー: 翻訳ファイルのフォーマットが正しくありません
```

**原因**: 翻訳JSONに必須フィールド（`translated`、`changed`）が不足

**解決策**:
```bash
# 正しいフォーマット
{
  "slide_number": 1,
  "translations": {
    "0_0_1": {
      "shape_idx": 0,
      "para_idx": 0,
      "run_idx": 1,
      "original": "今更ですが、生成",
      "translated": "Better late than never, about Generative",
      "changed": true
    }
  }
}
```

**注意**:
- `translation`フィールドではなく`translated`フィールドを使用
- `changed`フィールドは必須（翻訳がある場合はtrue、空の場合はfalse）

### エラー2: 空翻訳の検出

```
⚠️ 要注意: 5 個の空翻訳があります
```

**原因**: `translated`フィールドが空の翻訳が存在

**解決策**:
```bash
# 空翻訳を一覧表示
python3 scripts/list_empty_translations.py

# 空翻訳を修正
python3 scripts/add_translations.py <slide_num> <key> "<original>" "<translated>"
```

### エラー3: 翻訳数が過剰

```
❌ 不合格: -3 個の翻訳が不足しています
```

**原因**: 翻訳JSONに重複したキーが存在

**解決策**:
```bash
# 未翻訳テキストをキーベースで確認
python3 scripts/list_missing_translations.py <slide_num>

# 重複を削除
cat translations/slide<N>_translations.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
keys = list(data['translations'].keys())
print(f'Total keys: {len(keys)}')
print(f'Unique keys: {len(set(keys))}')
"
```

### エラー4: スペース不足

```
ChatGPTsuch asLLMHow do they work?
```

**原因**: `apply_translations.py`のスペース調整が不十分

**解決策**:
- `apply_translations.py`の`ensure_trailing_space()`関数を確認
- 次のrunの先頭が英数字・括弧の場合にスペースを追加

### エラー5: 色マーキングが適用されない

**原因**: `changed: false`のテキストに色がつかない

**確認方法**:
```bash
# unpackしてXMLを確認
python3 ~/.claude/skills/pptx/scripts/office/unpack.py output.pptx unpacked/
grep "800080" unpacked/ppt/slides/slide1.xml
```

### エラー6: 文脈が途切れている

```
Original: "今更ですが、生成AI（特にLLM）について"
Translation: "Better late than never, about Generative (especially"
```

**原因**: テキストが複数のrunに分割され、個別に翻訳されている

**解決策**:
```bash
# レビュースクリプトで文脈を確認
python3 scripts/review_translations.py

# 文脈を考慮して再翻訳
# 複数のrunをまとめて翻訳することを検討
```

## 詳細な設定

### スペース調整

`apply_translations.py`には以下のスペース調整機能があります：

1. **日本語・英語境界**: `insert_spaces_at_language_boundaries()`
2. **Run間スペース**: `ensure_trailing_space()`

### 色マーキング

- **翻訳済み**: RGB(128, 0, 128) = `800080`
- **元から英語**: 変更なし（黒）

### Run境界の保持

各runは個別に翻訳され、連結されません。これにより再翻訳時の安全が確保されます。

## パフォーマンス

- 抽出: 数秒〜数十秒（スライド数による）
- 翻訳: AIの処理時間に依存（スライド1につき5〜15分）
- 適用: 数秒
- 検証: 数秒

## トラブルシューティング

### Pythonコマンドが見つからない

```bash
# 環境セットアップを実行
bash scripts/setup_environment.sh

# またはpython3を明示的に使用
python3 scripts/extract_texts_from_xml.py input.pptx extracted/
```

### 依存関係が不足している

```bash
# 環境セットアップで一括インストール
bash scripts/setup_environment.sh

# または個別にインストール
# python-pptx
pip install python-pptx

# jq
brew install jq

# markitdown
pip install "markitdown[pptx]"
```

### スクリプトが実行できない

```bash
# 実行権限を確認
ls -la scripts/*.sh scripts/*.py

# 実行権限を追加
chmod +x scripts/*.sh scripts/*.py

# または環境セットアップで自動設定
bash scripts/setup_environment.sh
```

### ファイルパスの問題

```bash
# 絶対パスを使用
python3 /full/path/to/scripts/extract_texts_from_xml.py /full/path/to/input.pptx /full/path/to/extracted/

# またはカレントディレクトリを確認
pwd
ls -la input.pptx
```

## 関連リソース

- **PPTX編集**: `/dotfiles/claude/.claude/skills/pptx/`
- **レビューポリシー**: `docs/REVIEW_POLICY.md`
- **完全な計画**: `docs/PLAN.md`
