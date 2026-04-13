# PPTX翻訳フレームワーク実行計画

作成日: 2026-04-12
最終更新日: 2026-04-12

## 目的

**汎用的なPPTX翻訳フレームワークを構築する**。

任意のPowerPointファイル（.pptx）について、AIによる意味理解に基づく高精度な多言語翻訳を可能にするツールセットを開発する。

### テストケース

**sample.pptx**（生成AI/LLMについての日本語プレゼンテーション、6スライド）をテストケースとして使用し、フレームワークの検証を行う。

### 汎用性の要件

- 任意のPPTXファイルに適用可能
- 異なる言語ペアに対応可能（日英、英日、など）
- 異なるドメインのプレゼンテーションに対応可能
- スライド数に依存しないスケーラビリティ

## 最終アプローチ：AIによる理解に基づく翻訳

### 基本方針

**重要**: 機械的な完全自動化ではなく、AIによるスライドの意味理解に基づく翻訳を行う。

**理由**:
- スライドの視覚的構造やレイアウトを理解する必要がある
- テキストの関係性（どのテキストがグループなのか）を把握する必要がある
- 文脈を理解した上で、適切な対訳を作成する必要がある
- 再翻訳時に元の表現に戻せるよう、対訳ペアを管理する必要がある

## テストケース: sample.pptx

フレームワーク検証のためのサンプルプレゼンテーション。

### 内容（テスト用）

1. タイトルスライド：「いまさら聞けない生成AIについて」
2. 本資料の目的・伝えたいこと
3. 前編・後編の説明内容
4. ChatGPTなどのLLMの動作仕組み
5. LLMのモデル規模（パラメータ数）
6. ニューラルネットワークの構造

**注意**: この内容はあくまでテストケースであり、フレームワーク自体は任意のトピックのプレゼンテーションに適用可能である。

## 環境設定

- uv仮想環境: `.venv`（Python 3.12.8）
- インストール済みライブラリ:
  - `markitdown[pptx]`
  - `Pillow`
  - `ruff` (dev)
  - `pytest` (dev)

## 翻訳アプローチ

### 基本方針
- **人力翻訳**: Claude Codeによる高精度翻訳（機械翻訳不使用）
- **画像内テキスト**: 翻訳しない（図5.jpg、グラフィックス7.jpg等はそのまま）
- **レイアウト調整**: 行わない（テキスト長変化によるレイアウト崩れは許容）

### 効率化戦略：並列処理

pptxスキルのediting.mdに基づき、各スライド（独立したXMLファイル）をサブエージェントで並列翻訳：

```
1. Unpack（1回）
   └─ sample.pptx → unpacked/ppt/slides/slide1.xml〜slide6.xml

2. 並列翻訳（6スライド同時処理）
   ├─ Agent 1 → slide1.xml翻訳
   ├─ Agent 2 → slide2.xml翻訳
   ├─ Agent 3 → slide3.xml翻訳
   ├─ Agent 4 → slide4.xml翻訳
   ├─ Agent 5 → slide5.xml翻訳
   └─ Agent 6 → slide6.xml翻訳

3. Clean（1回）
4. Pack（1回）
   └─ converted.pptx
```

## 翻訳トレーサビリティ：色マーキング方式

### 目的
再翻訳（英語→日本語）時に、元々英語だった部分を誤って翻訳することを防ぐ。

### 仕組み

**翻訳マーキング**:
- 翻訳したテキスト：**くすんだ紫**（RGB: 128, 0, 128、16進数: `800080`）
- 元から英語だったテキスト：色を変更しない（黒のまま）

### XML実装

```xml
<!-- 翻訳したテキスト（紫色） -->
<a:p>
  <a:r>
    <a:rPr lang="en-US">
      <a:solidFill>
        <a:srgbClr val="800080"/>
      </a:solidFill>
    </a:rPr>
    <a:t>Translated text here</a:t>
  </a:r>
</a:p>

<!-- 元から英語だったテキスト（黒色） -->
<a:p>
  <a:r>
    <a:rPr lang="en-US"/>
    <a:t>Original English text</a:t>
  </a:r>
</a:p>
```

### ワークフロー

#### 第1段階：日本語→英語翻訳

```
1. Unpack
2. 並列翻訳（色付け付き）
   - 日本語テキスト → 英語 + 色"800080"を適用
   - 英語のみ → 変更なし（黒のまま）
3. Clean
4. Pack → converted.pptx
```

#### 第2段階：英語→日本語再翻訳（将来的な場合）

```
1. Unpack converted.pptx
2. 並列再翻訳
   - 「くすんだ紫(val="800080")」のテキストのみを抽出
   - これらを日本語に翻訳
   - 翻訳後、色を黒に戻す
3. Clean
4. Pack → reconverted.pptx
```

### メリット

1. **視覚的確認**: converted.pptxで翻訳箇所が一目でわかる
2. **安全な再翻訳**: 元の英語テキストを誤って翻訳リストに含めない
3. **部分修正**: 特定スライドのみ再翻訳も容易
4. **トレーサビリティ**: 翻訳履歴が色で追跡可能

## サブエージェントへの指示内容

### 翻訳時

```
あなたのタスク：
1. 指定されたslideN.xmlファイルを読み込む
2. 各<a:t>タグを処理：
   - 日本語が含まれる場合 → 英語に翻訳
   - 翻訳したテキストに<a:solidFill><a:srgbClr val="800080"/>を適用
   - 英語のみの場合 → 変更なし（色も黒のまま）
3. XML構造を完全に保持

重要事項：
- 技術用語は適切な英語に翻訳（LLM、ニューラルネットワーク、Transformer等）
- 文脈を考慮して翻訳（専門的なプレゼンテーション）
- <a:rPr>タグがない場合は追加、既にある場合は色を上書き
- Editツールを使用して変更
```

## 使用スクリプト

- `~/.claude/skills/pptx/scripts/office/unpack.py`
- `~/.claude/skills/pptx/scripts/clean.py`
- `~/.claude/skills/pptx/scripts/office/pack.py`

## 実行コマンド（予定）

```bash
# 1. Unpack
uv run python ~/.claude/skills/pptx/scripts/office/unpack.py sample.pptx unpacked/

# 2. 並列翻訳（Agentツール使用）

# 3. Clean
uv run python ~/.claude/skills/pptx/scripts/clean.py unpacked/

# 4. Pack
uv run python ~/.claude/skills/pptx/scripts/office/pack.py unpacked/ converted.pptx --original sample.pptx
```

## 技術用語集（翻訳参考）

| 日本語 | 英語 |
|--------|------|
| 生成AI | Generative AI |
| LLM | LLM (Large Language Model) |
| ニューラルネットワーク | Neural Network |
| ディープラーニング | Deep Learning |
| Transformer | Transformer |
| RAG | RAG (Retrieval-Augmented Generation) |
| パラメータ | Parameters |
| 次単語予測 | Next token prediction |
| 学習 | Training |
| 推論 | Inference |
| ファインチューニング | Fine-tuning |

## 注意事項

- 画像内のテキストは翻訳しない
- レイアウト調整は行わない
---

## 最終ワークフロー

### フェーズ1: 準備（共通スクリプト）

#### 1.1 スライド画像抽出（軽量版）
**スクリプト**: `scripts/extract_slide_images.py`

```bash
# スクリプトの処理内容
# 1. python-pptxでsample.pptxを読み込み
# 2. 各スライドから埋め込み画像を抽出
# 3. スライドごとにディレクトリに保存
```

**出力**:
- `extracted/slide1/images/image_0.png`, `image_1.png`, ...
- `extracted/slide2/images/image_0.png`, ...

**依存**: python-pptxのみ（LibreOffice/Poppler不要）

#### 1.2 XMLからのテキスト抽出
**スクリプト**: `scripts/extract_texts_from_xml.py`

```bash
# スクリプトの処理内容
# 1. python-pptxでsample.pptxを読み込み
# 2. 各スライドの全テキストrunを抽出
# 3. スライドごとにJSON形式で保存
```

**出力**: `extracted/slide1_texts.json` 〜 `slide6_texts.json`

---

### フェーズ2: AIによるスライド理解と翻訳（各スライド）

#### 2.1 スライドの理解（AI）
- スライド画像を確認
- レイアウト、構造、意味を理解
- スライドごとのメモを作成

**出力**: `docs/SLIDE_NOTES.md`

#### 2.2 対訳の作成（AI）
- 抽出されたテキストを確認
- スライドの理解に基づいて対訳を作成
- 文脈を考慮した翻訳

**出力**: `translations/slide1_translations.json` 〜 `slide6_translations.json`

#### 2.3 レビュー（AI）

**重要**: このレビューは**必須**です。省略しないでください。

##### 2.3.1 数値検証（必須）

翻訳漏れを防ぐため、以下の数値検証を**必ず**行ってください：

```bash
# 各スライドの検証
for i in {1..6}; do
  echo "=== Slide $i ==="
  # 抽出された日本語テキスト数
  extracted_jp=$(cat extracted/slide${i}_texts.json | jq '.total_japanese_texts')
  # 翻訳JSONのエントリ数（changed: trueの数）
  translated=$(cat translations/slide${i}_translations.json | jq '[.translations[] | select(.changed == true)] | length')

  echo "Extracted Japanese texts: $extracted_jp"
  echo "Translated texts: $translated"

  if [ "$extracted_jp" -eq "$translated" ]; then
    echo "✅ PASS: Counts match"
  else
    echo "❌ FAIL: Count mismatch! Missing $((extracted_jp - translated)) translations"
    exit 1
  fi
  echo
done
```

**合格基準**: 全てのスライドで `extracted_jp == translated` であること。

##### 2.3.2 品質レビュー

数値検証合格後、以下の品質レビューを行ってください：

- 対訳をレビュー
- 翻訳ミスや意味の逸脱がないか確認
- 用語の統一性を確認（LLM, Transformer, RAGなど）

---

### フェーズ3: 適用（共通スクリプト）

#### 3.1 翻訳の適用と色付け
**スクリプト**: `scripts/apply_translations.py`

```bash
# スクリプトの処理内容
# 1. 対訳JSONを読み込み
# 2. sample.pptxを読み込み
# 3. 各テキストrunについて対訳を確認
# 4. 変更がある場合は翻訳を適用 + 色付け(RGB:128,0,128)
# 5. converted.pptxとして保存
```

**出力**: `converted.pptx`

---

### フェーズ4: 最終検証

#### 4.1 数値検証の再実行（必須）

**翻訳適用前に、再度数値検証を行うこと**:

```bash
# 数値検証スクリプトの実行
bash scripts/verify_translations.sh
```

**合格基準**: 全スライドでカウントが一致していること。

#### 4.2 内容確認

```bash
# テキスト抽出で内容を確認
uv run python -m markitdown converted.pptx
```

#### 4.3 未翻訳テキストの検出（必須）

```bash
# 日本語テキストが含まれていないか検出
uv run python -m markitdown converted.pptx | grep -P '[\p{Hiragana}\p{Katakana}\p{Han}]'
```

**合格基準**: 画像内テキスト以外に日本語が含まれていないこと。

日本語が検出された場合:
1. 該当スライドを特定
2. 翻訳漏れの原因を調査
3. 翻訳を補完
4. 再度適用と検証

#### 4.4 全体レビュー（AI）

数値検証と未翻訳検査の合格後、品質レビューを行う：

- 全スライドの翻訳品質を確認
- 一貫性をチェック（用語、トーン）
- 必要に応じて修正

---

## 作成するスクリプト

### 1. scripts/extract_slide_images.py

**目的**: PPTXから埋め込み画像を抽出（軽量版）

**引数**:
- `input_pptx`: 入力PPTXファイルパス
- `output_dir`: 出力ディレクトリ

**処理内容**:
```python
#!/usr/bin/env python
"""PPTXから埋め込み画像を抽出するスクリプト（軽量版）"""

from pptx import Presentation
from PIL import Image
import io
import sys
from pathlib import Path

def extract_slide_images(input_pptx: str, output_dir: str):
    """
    任意のPPTXファイルから埋め込み画像を抽出

    Args:
        input_pptx: PPTXファイルパス
        output_dir: 出力ディレクトリ

    処理:
        1. python-pptxでPPTXを読み込み
        2. 各スライドの画像を抽出
        3. スライドごとのディレクトリに保存

    出力:
        extracted/slide1/images/image_0.png, image_1.png, ...
    """
    pass

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_slide_images.py <input.pptx> <output_dir>")
        sys.exit(1)

    extract_slide_images(sys.argv[1], sys.argv[2])
```

**依存**: python-pptx, Pillow（既にインストール済み）

**出力構造**:
```
extracted/
├── slide1/
│   └── images/
│       ├── image_0.png
│       └── image_1.png
├── slide2/
│   └── images/
│       └── image_0.png
...
```

---

### 2. scripts/extract_texts_from_xml.py

**目的**: 任意のPPTXファイルから全テキストを抽出（汎用）

**引数**:
- `input_pptx`: 入力PPTXファイルパス
- `output_dir`: 出力ディレクトリ

**処理内容**:
```python
#!/usr/bin/env python
"""PPTXからテキストを抽出するスクリプト（汎用）"""

from pptx import Presentation
import json
import sys
from pathlib import Path

def has_japanese(text: str) -> bool:
    """テキストに日本語が含まれるか判定"""
    for char in text:
        if '\u3040' <= char <= '\u309F': return True
        if '\u30A0' <= char <= '\u30FF': return True
        if '\u4E00' <= char <= '\u9FFF': return True
    return False

def extract_all_slide_texts(input_pptx: str, output_dir: str):
    """
    任意のPPTXファイルから全スライドのテキストを抽出

    Args:
        input_pptx: PPTXファイルパス
        output_dir: 出力ディレクトリ

    出力:
        slide1_texts.json, slide2_texts.json, ...
    """
    prs = Presentation(input_pptx)

    for slide_idx, slide in enumerate(prs.slides, start=1):
        texts = []

        for shape_idx, shape in enumerate(slide.shapes):
            if not hasattr(shape, "text_frame"):
                continue

            for para_idx, para in enumerate(shape.text_frame.paragraphs):
                for run_idx, run in enumerate(para.runs):
                    if run.text.strip():
                        texts.append({
                            'shape_idx': shape_idx,
                            'para_idx': para_idx,
                            'run_idx': run_idx,
                            'text': run.text,
                            'has_japanese': has_japanese(run.text)
                        })

        # スライドごとにJSONファイルとして保存
        output_path = Path(output_dir) / f"slide{slide_idx}_texts.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'slide_number': slide_idx,
                'total_texts': len(texts),
                'texts': texts
            }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_texts_from_xml.py <input.pptx> <output_dir>")
        sys.exit(1)

    extract_all_slide_texts(sys.argv[1], sys.argv[2])
```

**出力形式**（各スライド）:
```json
{
  "slide_number": 1,
  "total_texts": 5,
  "texts": [
    {
      "shape_idx": 0,
      "para_idx": 0,
      "run_idx": 0,
      "text": "いまさら聞けない生成",
      "has_japanese": true
    }
  ]
}
```

---

### 3. scripts/apply_translations.py

**目的**: 対訳を任意のPPTXファイルに適用し、色付け（汎用）

**引数**:
- `input_pptx`: 入力PPTXファイルパス
- `translations_dir`: 翻訳JSONファイルのあるディレクトリ
- `output_pptx`: 出力PPTXファイルパス

**処理内容**:
```python
#!/usr/bin/env python
"""対訳をPPTXに適用するスクリプト（汎用）"""

from pptx import Presentation
from pptx.dml.color import RGBColor
import json
import sys
from pathlib import Path

def get_char_type(char: str) -> str:
    """文字の種類を判定"""
    if '\u3040' <= char <= '\u9FFF':  # 日本語（ひらがな、カタカナ、漢字）
        return "japanese"
    if char.isalnum():  # 英数字
        return "english"
    return "other"

def insert_spaces_at_language_boundaries(text: str) -> str:
    """
    日本語と英語の境界にスペースを挿入
    
    日→英翻訳時にスペース不足を防ぐための処理。
    英→日再翻訳時は単語境界が保持されるため安全。
    """
    result = []
    prev_type = None
    
    for char in text:
        curr_type = get_char_type(char)
        
        # 日本語→英語、英語→日本語の境界にスペースを挿入
        if ((prev_type == "japanese" and curr_type == "english") or
            (prev_type == "english" and curr_type == "japanese")):
            result.append(' ')
        
        result.append(char)
        prev_type = curr_type
    
    return ''.join(result)

def apply_all_translations(input_pptx: str, translations_dir: str, output_pptx: str):
    """
    任意のPPTXファイルに対訳を適用
    
    重要: run単位の境界を保持し、連結しすぎないことで
    再翻訳時の安全性を確保する。
    """
    prs = Presentation(input_pptx)
    marking_color = RGBColor(128, 0, 128)

    for slide_idx, slide in enumerate(prs.slides, start=1):
        # 翻訳JSONファイルを読み込み
        trans_path = Path(translations_dir) / f"slide{slide_idx}_translations.json"

        if not trans_path.exists():
            continue

        with open(trans_path, 'r', encoding='utf-8') as f:
            trans_data = json.load(f)

        # スライドに対訳を適用
        for shape_idx, shape in enumerate(slide.shapes):
            if not hasattr(shape, "text_frame"):
                continue

            for para_idx, para in enumerate(shape.text_frame.paragraphs):
                for run_idx, run in enumerate(para.runs):
                    # キーは {shape_idx}_{para_idx}_{run_idx}
                    key = f"{shape_idx}_{para_idx}_{run_idx}"

                    if key in trans_data['translations']:
                        trans_item = trans_data['translations'][key]

                        if trans_item['changed'] and trans_item['translated'] != run.text:
                            # 翻訳テキストにスペース調整を適用
                            adjusted_text = insert_spaces_at_language_boundaries(trans_item['translated'])
                            
                            run.text = adjusted_text
                            run.font.color.rgb = marking_color
```

    prs.save(output_pptx)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python apply_translations.py <input.pptx> <translations_dir> <output.pptx>")
        sys.exit(1)

    apply_all_translations(sys.argv[1], sys.argv[2], sys.argv[3])
```

**入力**: `translations/slide{n}_translations.json`

**対訳JSON形式**:
```json
{
  "slide_number": 1,
  "translations": {
    "0_0_0": {
      "original": "いまさら聞けない生成",
      "translated": "An Introduction to",
      "changed": true
    }
  }
}
```

---

## 実行手順（汎用版・軽量）

### ステップ1: 準備

```bash
# ディレクトリ作成
mkdir -p extracted translations docs

# 入力PPTXファイルを指定
INPUT_PPTX="your_presentation.pptx"

# 画像抽出（python-pptxのみ）
uv run python scripts/extract_slide_images.py $INPUT_PPTX extracted/

# テキスト抽出（python-pptxのみ）
uv run python scripts/extract_texts_from_xml.py $INPUT_PPTX extracted/
```

### ステップ2: 各スライドの処理（AI）

抽出されたスライドごとに以下を実行：

**スライドN**:
1. `extracted/slideN/images/`の画像を見てメモ作成（`docs/SLIDE_NOTES.md`）
2. `extracted/slideN_texts.json`を見て対訳作成
3. レビュー（翻訳ミス、用語統一、自然さ）
4. `translations/slideN_translations.json`に保存

### ステップ3: 適用

```bash
# 入力PPTX、翻訳ディレクトリ、出力PPTXを指定
INPUT_PPTX="your_presentation.pptx"
TRANSLATIONS_DIR="translations/"
OUTPUT_PPTX="converted.pptx"

# 全スライドに対訳を適用
uv run python scripts/apply_translations.py $INPUT_PPTX $TRANSLATIONS_DIR $OUTPUT_PPTX
```

### ステップ4: 検証

```bash
# 内容確認
uv run python -m markitdown $OUTPUT_PPTX

# 画像抽出で視覚確認
uv run python scripts/extract_slide_images.py $OUTPUT_PPTX converted_images/
```

---

## テストケースでの実行例

sample.pptxでのテスト実行：

```bash
# ステップ1
uv run python scripts/extract_slide_images.py sample.pptx extracted/
uv run python scripts/extract_texts_from_xml.py sample.pptx extracted/

# ステップ2（スライド1-6を順に処理）

# ステップ3
uv run python scripts/apply_translations.py sample.pptx translations/ converted.pptx

# ステップ4
uv run python -m markitdown converted.pptx
uv run python scripts/extract_slide_images.py converted.pptx converted_images/
```

**実行結果（サンプル）**:
```
Extracting images from sample.pptx...
Total slides: 6

Slide 4: Extracted 2 image(s)
Slide 5: Extracted 2 image(s)

✓ Successfully extracted 4 images
```

---

## 再翻訳への対応

### 対訳ペアの活用とRun境界の保持

**重要**: 再翻訳時の安全性を確保するため、run単位の境界を保持することが必須です。

#### なぜ連結してはいけないのか

**問題例**:
```
元の日本語（3つのrun）:
- Run 1: 「私は」
- Run 2: 「LLM」
- Run 3: 「について詳しくない」

翻訳（連結）:
- "I" + "am" + "not" + "familiar" + "with" + "LLM"
- → "IamnotfamiliarwithLLM"

再翻訳時:
- 単語境界が失われる
- 「LLM」→「大規模言語モデル」と過剰翻訳される可能性
- 元の技術用語が維持されない
```

#### 正しいアプローチ: Run境界の保持

**対訳JSON構造**:
```json
{
  "translations": {
    "2_0_0": {
      "original": "いまさら聞けない生成",
      "translated": "A Beginner's Guide to ",
      "changed": true
    },
    "2_0_1": {
      "original": "AI",
      "translated": "Generative AI",
      "changed": true
    },
    "2_0_2": {
      "original": "について",
      "translated": "",
      "changed": true
    }
  }
}
```

**日→英翻訳時**:
- 各runを独立して処理
- 必要に応じてrunの末尾にスペースを追加
- 言語境界の検出で自動調整も可能

**英→日再翻訳時**:
- 色付きテキスト（翻訳済み）をrun単位で抽出
- 対訳ペアから元の日本語を復元
- run境界が保持されているため、正確に復元可能
- 「LLM」などの技術用語が維持される

**手順**:
1. 色付きテキスト（翻訳済み）を抽出（run単位）
2. 対訳ペアを参照して原文に戻す（run単位）
3. 色を黒に戻す

**メリット**:
- 表現の不要な変更を防げる
- 元の日本語表現を維持できる
- 技術用語（LLM, AI, Transformer等）が保持される
- 過剰な再翻訳を防げる

---

## 品質管理

### AIによるレビューチェックリスト

- [ ] 翻訳ミスがないか
- [ ] 意味の逸脱がないか
- [ ] 用語が統一されているか（LLM, Generative AI, Transformer等）
- [ ] 技術用語が適切に翻訳されているか
- [ ] 自然な英語表現になっているか
- [ ] スライド間で一貫性があるか

---

## トラブルシューティング

### 問題1: スペース不足

**現象**: `GenerativeAI`、`A Beginner's Guide toGenerative AI` のようにスペース不足

**原因**:
- 元のPPTXでテキストが複数のrunに分割されている
- 日本語→英語翻訳時に単語間にスペースが必要だが、run境界で分割されている

**解決策**:
1. **言語境界の検出**: 日本語と英語の境界に自動的にスペースを挿入
2. **手動スペース追加**: 翻訳時にrunの末尾にスペースを追加
3. **Run境界の保持**: 連結せず、run単位で処理

**実装**:
```python
def insert_spaces_at_language_boundaries(text: str) -> str:
    """日本語と英語の境界にスペースを挿入"""
    result = []
    prev_type = None
    
    for char in text:
        curr_type = get_char_type(char)
        
        # 境界検出：日本語→英語、英語→日本語
        if (prev_type == "japanese" and curr_type == "english" or
            prev_type == "english" and curr_type == "japanese"):
            result.append(' ')
        
        result.append(char)
        prev_type = curr_type
    
    return ''.join(result)
```

---

### 問題2: 過剰な再翻訳

**現象**: 英→日再翻訳時に「LLM」→「大規模言語モデル」と変換される

**原因**:
- テキストが連結されすぎて単語境界が失われる
- 再翻訳時に元の技術用語が認識されない

**解決策**:
- **Run境界の保持**: 対訳JSONでrun単位を管理
- **対訳ペアの活用**: 元の表現を正確に復元
- **技術用語の保護**: LLM, AI, Transformer等は維持

---

### 問題3: テキストが結合されている（古いアプローチ）

**現象**: `GenerativeAI` のようにスペース不足

**原因**: 元のPPTXで「生成」と「AI」が別々のrunだが、隣接している

**解決**: AIがスライドの意味を理解し、適切にスペースを入れた対訳を作成

**解決**: 言語境界の自動検出またはrun境界の保持

---

## 過去のアプローチと問題点

### アプローチ1: XML直接編集 + サブエージェント並列処理

**問題**:
- XML構造破損
- サブエージェントの編集品質に依存
- エラー検出が遅れる

### アプローチ2: python-pptx + 完全自動翻訳

**問題**:
- テキストが細かく分割され、文脈が失われる
- スペース不足や過剰分割
- 意味理解がないため、不自然な翻訳

### 現アプローチ: AIによる理解に基づく翻訳

**メリット**:
- スライド全体の意味を理解
- 視覚的構造を考慮
- 文脈を維持した翻訳
- 対訳ペアによる再翻訳が容易

---

## 用語集（翻訳参考）

| 日本語 | 英語 |
|--------|------|
| 生成AI | Generative AI |
| LLM | LLM (Large Language Model) |
| ニューラルネットワーク | Neural Network |
| ディープラーニング | Deep Learning |
| Transformer | Transformer |
| RAG | RAG (Retrieval-Augmented Generation) |
| パラメータ | Parameters |
| 次単語予測 | Next token prediction |
| 学習 | Training |
| 推論 | Inference |
| ファインチューニング | Fine-tuning |
| 重み | Weights |
| 入力ノード | Input nodes |
| 出力層 | Output layer |

---

## 環境設定

- uv仮想環境: `.venv`（Python 3.12.8）
- インストール済みライブラリ:
  - `markitdown[pptx]`
  - `Pillow`
  - `python-pptx`
  - `ruff` (dev)
  - `pytest` (dev)

---

## 注意事項

- 画像内のテキストは翻訳しない
- レイアウト調整は行わない（テキスト長変化によるレイアウト崩れは許容）
- 色マーキングは「くすんだ紫(RGB:128,0,128)」を使用
- AIによるレビューを必ず行う
- 対訳ペアは必ず保存する（再翻訳用）

---

## 次のステップ

### フレームワーク開発

1. スライド画像化スクリプトを作成（汎用）
2. テキスト抽出スクリプトを作成（汎用）
3. 適用スクリプトを作成（汎用）

### テストと検証

4. sample.pptxを使用してフレームワークをテスト
5. スライド1から順に処理開始（AIによる理解と対訳作成）
6. converted.pptxを生成して検証

### 将来の拡張

- 異なる言語ペアのサポート（英日、中英、など）
- 異なるドメインのテストケース追加
- 対訳ペアのデータベース化
- 再翻訳機能の実装

---

## フレームワークの設計原則

1. **汎用性**: 任意のPPTXファイル、言語ペア、ドメインに対応
2. **AI主導**: 機械的処理ではなく、AIによる意味理解を重視
3. **トレーサビリティ**: 色マーキングと対訳ペアによる追跡可能性
4. **再利用性**: 対訳ペアの蓄積と再翻訳への活用
5. **品質重視**: AIによるレビューと品質チェックプロセス

---

## リスクと代替手段

### 現在アプローチ（XML直接編集 + サブエージェント並列処理）のリスク

#### ⚠️ 高リスク：XML構造破損

**実際に発生した問題**：
- `<a:endParaRPr>`タグの閉じ忘れ（20箇所以上）
- `<a:solidFill>`タグ内に複数の色定義が混在（5箇所）
- `<a:rPr>`タグの不整合（10箇所以上）
- 結果：packスクリプトが失敗、converted.pptx生成不能

**根本原因**：
- PowerPoint XMLは極めて複雑（数百のタグ、ネスト構造）
- サブエージェントがEditツールで部分的編集するとタグの整合性が崩れやすい
- `<a:solidFill>`内の色定義は1つのみ許可されるが、追加時に元の色定義を削除し忘れる
- `<a:endParaRPr>`は自己終了タグとして扱われるべきが、閉じタグを追加すると破損

#### ⚠️ 中リスク：サブエージェントの編集品質に依存

- 6つのサブエージェントが並列でXML編集
- 各エージェントのXML理解度にばらつき
- エラー検出がpack実行時まで遅れる
- 修正に数時間要する可能性

#### ⚠️ 低リスク：翻訳の一貫性

- 並列処理により用語の統一が困難
- 技術用語集を共有しても、文脈により翻訳が異なる可能性

### 代替手段

#### 代替案1：python-pptxライブラリ使用（推奨）

**メリット**：
- ✅ XMLを直接操作せず、ライブラリが自動的に構造を維持
- ✅ 色付けも `font.color.rgb = RGBColor(128, 0, 128)` で安全に適用
- ✅ エラー処理が容易、デバッグが簡単
- ✅ コードが読みやすく、将来のメンテナンスが容易

**デメリット**：
- ❌ 並列処理ができない（順次処理）
- ❌ 処理時間は長くなる（6スライドで約5-10分程度）

**実装例**：
```python
from pptx import Presentation
from pptx.util import RGBColor

prs = Presentation("sample.pptx")

for slide in prs.slides:
    for shape in slide.shapes:
        if not hasattr(shape, "text_frame"):
            continue
        
        for paragraph in shape.text_frame.paragraphs:
            for run in paragraph.runs:
                if has_japanese(run.text):
                    run.text = translate(run.text)
                    run.font.color.rgb = RGBColor(128, 0, 128)

prs.save("converted.pptx")
```

**所要時間見込み**：
- 翻訳処理：5-10分（Claude Code APIのレスポンス時間に依存）
- 検証・調整：1-2分
- 合計：6-12分

#### 代替案2：簡易的なXML編訳（色付け後から追加）

**メリット**：
- ✅ 並列処理のメリットを維持
- ✅ 色付けを手動で後から行う（PDFなどで確認しながら）

**デメリット**：
- ❌ 二度手間（翻訳→色付け）
- ❌ 手動作業が増える

**手順**：
1. Unpack
2. サブエージェントで翻訳のみ（色付けなし）
3. Pack
4. PowerPointで開き、手動で色付け（または別スクリプト）

#### 代替案3：少数のサブエージェントでXML検証を強化

**メリット**：
- ✅ 並列処理のメリットを維持
- ✅ 各サブエージェントが2スライド担当

**デメリット**：
- ❌ XML構造破損のリスクは残る
- ❌ 検証コストが増加

**手順**：
1. Unpack
2. サブエージェント（3つ）で各2スライドを翻訳
3. 各エージェントにXMLパース検証を義務付ける
4. 全スライド検証完了後にClean & Pack

### 推奨アクション

**優先順位**：
1. **第一選択**：代替案1（python-pptxライブラリ）- 安全性重視
2. **第二選択**：代替案2（色付け後から追加）- 並列処理重視の場合
3. **第三選択**：現在アプローチの改善（XML検証強化）- リスク許容の場合

**判断基準**：
- 時間の余裕がある → 代替案1
- 並列処理のスピードが必須 → 代替案2
- XML編集の経験がある → 代替案3

### 2026-04-12の教訓

- PowerPoint XMLの直接編集は、専門知識がない限り避けるべき
- ライブラリ（python-pptx等）の使用を優先
- サブエージェント並列処理は、データが独立している場合にのみ有効
- 早期にエラー検出する仕組み（各スライド編集後にXMLパース検証）が必要
