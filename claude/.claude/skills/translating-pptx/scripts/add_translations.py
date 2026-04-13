#!/usr/bin/env python3
"""
翻訳をJSONファイルに追加するスクリプト

使用方法:
    python add_translations.py <slide_num> <key> <original> <translated>
    python add_translations.py <slide_num> <json_file>

例:
    # 単一追加
    python add_translations.py 2 2_5_2 "も記載ところどころ記載します。" "will be listed here and there."

    # バッチ追加（JSONファイルから）
    python add_translations.py 2 batch_translations.json
"""

import json
import sys
from pathlib import Path


def add_single_translation(slide_num: int, key: str, original: str, translated: str):
    """
    単一の翻訳を追加

    Args:
        slide_num: スライド番号
        key: キー（shape_idx_para_idx_run_idx）
        original: 元のテキスト
        translated: 翻訳済みテキスト
    """
    translations_file = Path(f'translations/slide{slide_num}_translations.json')

    if not translations_file.exists():
        print(f"Error: {translations_file} not found")
        return False

    # 現在の翻訳JSONを読み込み
    with open(translations_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 追加
    data['translations'][key] = {
        'original': original,
        'translated': translated,
        'changed': True
    }

    # 保存
    with open(translations_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Added to slide {slide_num}: {key}")
    return True


def add_batch_translations(slide_num: int, batch_file: str):
    """
    バッチで翻訳を追加

    Args:
        slide_num: スライド番号
        batch_file: バッチ翻訳ファイル（JSON形式）
    """
    batch_path = Path(batch_file)
    if not batch_path.exists():
        print(f"Error: {batch_file} not found")
        return False

    with open(batch_path, 'r', encoding='utf-8') as f:
        batch_data = json.load(f)

    translations_file = Path(f'translations/slide{slide_num}_translations.json')

    # 現在の翻訳JSONを読み込み
    with open(translations_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # バッチ追加
    added_count = 0
    for key, trans in batch_data.items():
        if key not in data['translations']:
            data['translations'][key] = {
                'original': trans['original'],
                'translated': trans['translated'],
                'changed': True
            }
            added_count += 1
            print(f"✅ Added: {key}")
        else:
            print(f"⚠️  Skipped (already exists): {key}")

    # 保存
    with open(translations_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Total added: {added_count} translations")
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Single: python add_translations.py <slide_num> <key> <original> <translated>")
        print("  Batch:  python add_translations.py <slide_num> <batch_file>")
        sys.exit(1)

    slide_num = int(sys.argv[1])

    if sys.argv[2] == 'batch_file' and len(sys.argv) == 4:
        # バッチモード
        batch_file = sys.argv[3]
        add_batch_translations(slide_num, batch_file)
    elif len(sys.argv) == 5:
        # 単一追加モード
        key = sys.argv[2]
        original = sys.argv[3]
        translated = sys.argv[4]
        add_single_translation(slide_num, key, original, translated)
    else:
        print("Error: Invalid arguments")
        sys.exit(1)


if __name__ == "__main__":
    main()
