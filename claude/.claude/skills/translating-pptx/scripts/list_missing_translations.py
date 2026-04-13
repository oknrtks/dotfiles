#!/usr/bin/env python3
"""
未翻訳テキストを特定するスクリプト

抽出されたテキストと翻訳JSONを比較し、
未翻訳の日本語テキストをリストアップする。
"""

import json
import sys
from pathlib import Path


def find_missing_translations(slide_num: int) -> list:
    """
    指定されたスライドの未翻訳テキストを特定

    Args:
        slide_num: スライド番号

    Returns:
        未翻訳テキストのリスト
    """
    # ファイルパス
    extracted_file = Path(f'extracted/slide{slide_num}_texts.json')
    translations_file = Path(f'translations/slide{slide_num}_translations.json')

    if not extracted_file.exists():
        print(f"Error: {extracted_file} not found")
        return []

    if not translations_file.exists():
        print(f"Error: {translations_file} not found")
        return []

    # 抽出データを読み込み
    with open(extracted_file, 'r', encoding='utf-8') as f:
        extracted_data = json.load(f)

    # 翻訳データを読み込み
    with open(translations_file, 'r', encoding='utf-8') as f:
        trans_data = json.load(f)

    trans_keys = set(trans_data['translations'].keys())

    # 日本語テキストを取得
    jp_texts = [t for t in extracted_data['texts'] if t['has_japanese']]

    # 未翻訳のテキストを特定
    missing = []
    for t in jp_texts:
        key = f"{t['shape_idx']}_{t['para_idx']}_{t['run_idx']}"
        if key not in trans_keys:
            missing.append({
                'key': key,
                'text': t['text']
            })

    return missing


def main():
    if len(sys.argv) > 1:
        # 特定スライドのみチェック
        slide_nums = [int(arg) for arg in sys.argv[1:]]
    else:
        # 全スライドをチェック
        slide_nums = range(1, 7)

    total_missing = 0

    for slide_num in slide_nums:
        missing = find_missing_translations(slide_num)

        if missing:
            print(f"\n=== Slide {slide_num}: {len(missing)} missing translations ===")
            for i, m in enumerate(missing, 1):
                print(f"{i}. {m['key']}: {m['text']}")
            total_missing += len(missing)
        else:
            print(f"Slide {slide_num}: ✅ All translations complete")

    if total_missing > 0:
        print(f"\n❌ Total missing translations: {total_missing}")
        sys.exit(1)
    else:
        print(f"\n✅ All slides complete")
        sys.exit(0)


if __name__ == "__main__":
    main()
