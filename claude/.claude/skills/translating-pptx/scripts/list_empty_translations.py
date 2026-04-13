#!/usr/bin/env python3
"""
List Empty Translations Script
Identifies translations with empty 'translated' fields or untranslated Japanese text.
"""

import json
import os
import sys
from pathlib import Path

def is_japanese(text):
    """Check if text contains Japanese characters"""
    if not text:
        return False
    japanese_chars = any('\u3040' <= char <= '\u309F' or  # Hiragana
                          '\u30A0' <= char <= '\u30FF' or  # Katakana
                          '\u4E00' <= char <= '\u9FFF'      # Kanji
                          for char in text)
    return japanese_chars

def load_translations(slide_num):
    """Load translation file for a specific slide"""
    trans_file = f"translations/slide{slide_num}_translations.json"
    if not os.path.exists(trans_file):
        return None

    with open(trans_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_slide(slide_num):
    """Check a slide for empty translations"""
    data = load_translations(slide_num)
    if not data:
        return None

    empty_translations = []
    translations = data.get('translations', {})

    for key, item in translations.items():
        translated = item.get('translated', '').strip()
        original = item.get('original', '')

        # Check if translation is empty
        if not translated:
            # Check if original has Japanese (should be translated)
            if is_japanese(original):
                empty_translations.append({
                    'key': key,
                    'original': original,
                    'shape_idx': item.get('shape_idx'),
                    'para_idx': item.get('para_idx'),
                    'run_idx': item.get('run_idx'),
                    'context': get_context(translations, key)
                })

    return empty_translations

def get_context(translations, current_key):
    """Get context around the current key"""
    # Parse current key
    try:
        shape_idx, para_idx, run_idx = map(int, current_key.split('_'))
    except:
        return {}

    # Find adjacent runs in same paragraph
    context = {
        'before': [],
        'after': []
    }

    for key, item in translations.items():
        try:
            s_idx, p_idx, r_idx = map(int, key.split('_'))
            if s_idx == shape_idx and p_idx == para_idx:
                if r_idx < run_idx:
                    context['before'].append({
                        'key': key,
                        'run_idx': r_idx,
                        'original': item.get('original', '')[:50]
                    })
                elif r_idx > run_idx:
                    context['after'].append({
                        'key': key,
                        'run_idx': r_idx,
                        'original': item.get('original', '')[:50]
                    })
        except:
            continue

    # Sort by run_idx
    context['before'].sort(key=lambda x: x['run_idx'])
    context['after'].sort(key=lambda x: x['run_idx'])

    return context

def print_slide_report(slide_num, empty_translations):
    """Print report for a single slide"""
    if not empty_translations:
        print(f"✅ Slide {slide_num}: No empty translations")
        return

    print(f"❌ Slide {slide_num}: Found {len(empty_translations)} empty translation(s)")
    print("-" * 60)

    for i, trans in enumerate(empty_translations, 1):
        print(f"\n  {i}. Key: {trans['key']}")
        print(f"     Location: shape={trans['shape_idx']}, para={trans['para_idx']}, run={trans['run_idx']}")
        print(f"     Original: {trans['original']}")

        # Show context
        context = trans.get('context', {})
        if context.get('before'):
            print("     Before:")
            for ctx in context['before'][-2:]:  # Show last 2 before
                print(f"       {ctx['key']}: {ctx['original']}")

        if context.get('after'):
            print("     After:")
            for ctx in context['after'][:2]:  # Show first 2 after
                print(f"       {ctx['key']}: {ctx['original']}")

        print()

def main():
    """Main function"""
    print("=" * 60)
    print("Empty Translation Detector")
    print("=" * 60)
    print()

    # Check all slides
    all_empty = {}
    total_empty = 0

    for slide_num in range(1, 7):  # Assuming 6 slides
        empty = check_slide(slide_num)
        if empty is None:
            continue

        if empty:
            all_empty[slide_num] = empty
            total_empty += len(empty)

    # Print reports
    if not all_empty:
        print("✅ No empty translations found!")
        print()
        print("All Japanese text has been translated.")
        return

    for slide_num, empty in all_empty.items():
        print_slide_report(slide_num, empty)

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total empty translations: {total_empty}")
    print(f"Slides affected: {len(all_empty)}")
    print()

    # Provide guidance
    print("To fix empty translations:")
    print("1. Use add_translations.py to add missing translations:")
    print("   python3 scripts/add_translations.py <slide_num> <key> \"<original>\" \"<translated>\"")
    print()
    print("2. Or edit the translation file directly:")
    print("   translations/slide<N>_translations.json")
    print()
    print("3. Then verify again:")
    print("   bash scripts/verify_translations.sh")
    print()

    # Exit with error code
    sys.exit(1)

if __name__ == "__main__":
    main()
