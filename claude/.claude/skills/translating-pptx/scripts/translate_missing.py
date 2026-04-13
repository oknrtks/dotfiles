#!/usr/bin/env python3
"""
未翻訳テキストをAIに翻訳させるスクリプト

使用方法:
    python translate_missing.py <slide_num>

処理フロー:
1. 未翻訳テキストを特定
2. AIに翻訳を依頼
3. 翻訳結果をJSONファイルに追加
"""

import json
import sys
from pathlib import Path


def find_missing_translations(slide_num: int) -> list:
    """未翻訳テキストを特定"""
    extracted_file = Path(f'extracted/slide{slide_num}_texts.json')
    translations_file = Path(f'translations/slide{slide_num}_translations.json')

    with open(extracted_file, 'r', encoding='utf-8') as f:
        extracted_data = json.load(f)

    with open(translations_file, 'r', encoding='utf-8') as f:
        trans_data = json.load(f)

    trans_keys = set(trans_data['translations'].keys())
    jp_texts = [t for t in extracted_data['texts'] if t['has_japanese']]

    missing = []
    for t in jp_texts:
        key = f"{t['shape_idx']}_{t['para_idx']}_{t['run_idx']}"
        if key not in trans_keys:
            missing.append({
                'key': key,
                'original': t['text']
            })

    return missing


def create_translation_prompt(slide_num: int, missing_texts: list) -> str:
    """
    翻訳依頼用のプロンプトを作成

    Args:
        slide_num: スライド番号
        missing_texts: 未翻訳テキストのリスト

    Returns:
        翻訳依頼プロンプト
    """
    prompt = f"""
# 翻訳依頼: スライド{slide_num}の未翻訳テキスト

以下の{len(missing_texts)}個の日本語テキストを英語に翻訳してください。

## 翻訳ルール

1. **文脈を考慮**: 生成AI/LLMについての技術的プレゼンテーションです
2. **用語の統一**: LLM, Transformer, RAG, OCIはそのまま維持
3. **トーン**: 親しみやすく、謙虚なトーンを保持
4. **スペース**: 英語の単語間にスペースを含める

## 未翻訳テキスト

"""

    for i, text in enumerate(missing_texts, 1):
        prompt += f"\n{i}. `{text['key']}: {text['original']}`\n"

    prompt += """

## 出力形式

以下のJSON形式で出力してください：

```json
{
  "2_5_2": {
    "original": "も記載ところどころ記載します。",
    "translated": "will be listed here and there.",
    "changed": true
  },
  ...
}
```

注意:
- キーは元のキーを維持
- `original`は元の日本語テキスト
- `translated`は翻訳済み英語テキスト
- `changed`はtrue
"""

    return prompt


def main():
    if len(sys.argv) != 2:
        print("Usage: python translate_missing.py <slide_num>")
        sys.exit(1)

    slide_num = int(sys.argv[1])

    # 未翻訳テキストを特定
    print(f"Checking slide {slide_num}...")
    missing = find_missing_translations(slide_num)

    if not missing:
        print(f"✅ Slide {slide_num}: No missing translations")
        return

    print(f"❌ Found {len(missing)} missing translations")

    # プロンプトを作成
    prompt = create_translation_prompt(slide_num, missing)

    # プロンプトをファイルに保存
    prompt_file = Path(f'translate_slide{slide_num}_prompt.md')
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)

    print(f"\n✅ Created translation prompt: {prompt_file}")
    print(f"\n📋 Next steps:")
    print(f"1. Copy the prompt from {prompt_file}")
    print(f"2. Paste to AI (Claude/ChatGPT)")
    print(f"3. Save the response to slide{slide_num}_batch_translations.json")
    print(f"4. Run: python add_translations.py {slide_num} batch_file slide{slide_num}_batch_translations.json")


if __name__ == "__main__":
    main()
