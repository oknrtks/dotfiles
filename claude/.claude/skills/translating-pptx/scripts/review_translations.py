#!/usr/bin/env python3
"""
Interactive Translation Review Script
Reviews translations for quality, context consistency, and completeness.
"""

import json
import os
import sys
from pathlib import Path

class TranslationReviewer:
    def __init__(self):
        self.issues = []
        self.warnings = []

    def is_japanese(self, text):
        """Check if text contains Japanese characters"""
        if not text:
            return False
        return any('\u3040' <= char <= '\u309F' or  # Hiragana
                   '\u30A0' <= char <= '\u30FF' or  # Katakana
                   '\u4E00' <= char <= '\u9FFF'      # Kanji
                   for char in text)

    def is_english(self, text):
        """Check if text appears to be English"""
        if not text:
            return False
        # Simple check: mostly ASCII characters
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        return ascii_chars / len(text) > 0.7 if text else False

    def load_translations(self, slide_num):
        """Load translation file for a specific slide"""
        trans_file = f"translations/slide{slide_num}_translations.json"
        if not os.path.exists(trans_file):
            return None

        with open(trans_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def review_translation(self, slide_num, key, item):
        """Review a single translation"""
        issues = []
        warnings = []

        original = item.get('original', '')
        translated = item.get('translated', '').strip()
        changed = item.get('changed', False)

        # Check 1: Empty translation
        if not translated:
            if self.is_japanese(original):
                issues.append("Empty translation for Japanese text")
            return issues, warnings

        # Check 2: Translation is too similar to original
        if translated == original:
            warnings.append("Translation identical to original (not translated?)")

        # Check 3: Very short translation
        if len(translated) < 3 and len(original) > 3:
            warnings.append("Translation seems too short")

        # Check 4: Check for untranslated Japanese in translation
        if self.is_japanese(translated) and not self.is_english(translated):
            # Allow some Japanese for proper nouns/technical terms
            japanese_ratio = sum(1 for c in translated if self.is_japanese(c)) / len(translated)
            if japanese_ratio > 0.5:
                warnings.append("Translation contains mostly Japanese text")

        # Check 5: Special characters inconsistency
        if original.endswith('。') and not translated.endswith('.'):
            warnings.append("Sentence ending period might be missing")

        if original.endswith('！') and not translated.endswith('!'):
            warnings.append("Exclamation mark might be missing")

        if original.endswith('？') and not translated.endswith('?'):
            warnings.append("Question mark might be missing")

        # Check 6: Check for context breaks (very short translations)
        words_original = original.split()
        words_translated = translated.split()

        if len(words_original) > 5 and len(words_translated) <= 2:
            issues.append("Translation might be incomplete (too short)")

        # Check 7: Technical term consistency
        technical_terms = ['AI', 'LLM', 'ChatGPT', 'Transformer', 'RAG', 'OCI']
        for term in technical_terms:
            if term in original and term.lower() not in translated.lower():
                warnings.append(f"Technical term '{term}' might be missing in translation")

        return issues, warnings

    def review_slide(self, slide_num):
        """Review all translations in a slide"""
        data = self.load_translations(slide_num)
        if not data:
            return None

        translations = data.get('translations', {})
        slide_issues = {}

        for key, item in translations.items():
            issues, warnings = self.review_translation(slide_num, key, item)

            if issues or warnings:
                slide_issues[key] = {
                    'item': item,
                    'issues': issues,
                    'warnings': warnings
                }

                # Collect global issues/warnings
                self.issues.extend([(slide_num, key, issue) for issue in issues])
                self.warnings.extend([(slide_num, key, warning) for warning in warnings])

        return slide_issues

    def print_slide_report(self, slide_num, slide_issues):
        """Print review report for a slide"""
        if not slide_issues:
            print(f"✅ Slide {slide_num}: All translations OK")
            return

        print(f"⚠️  Slide {slide_num}: Found {len(slide_issues)} translation(s) to review")
        print("-" * 70)

        for key, data in slide_issues.items():
            item = data['item']
            issues = data['issues']
            warnings = data['warnings']

            print(f"\n  [{key}]")
            print(f"  Original:   {item.get('original', '')}")
            print(f"  Translated: {item.get('translated', '')}")
            print(f"  Changed:    {item.get('changed', False)}")

            if issues:
                print("  ❌ Issues:")
                for issue in issues:
                    print(f"     - {issue}")

            if warnings:
                print("  ⚠️  Warnings:")
                for warning in warnings:
                    print(f"     - {warning}")

        print()

    def generate_review_report(self):
        """Generate final review report"""
        print("\n" + "=" * 70)
        print("Review Summary")
        print("=" * 70)

        if not self.issues and not self.warnings:
            print("✅ All translations passed review!")
            print()
            print("Translation quality checks:")
            print("  ✓ No empty translations")
            print("  ✓ No incomplete translations")
            print("  ✓ No major context issues")
            print()
            return True

        if self.issues:
            print(f"❌ Found {len(self.issues)} issue(s):")
            for slide_num, key, issue in self.issues:
                print(f"   Slide {slide_num} [{key}]: {issue}")
            print()

        if self.warnings:
            print(f"⚠️  Found {len(self.warnings)} warning(s):")
            for slide_num, key, warning in self.warnings:
                print(f"   Slide {slide_num} [{key}]: {warning}")
            print()

        # Provide guidance
        print("Recommendations:")
        if self.issues:
            print("  1. Fix issues above before applying translations")
            print("  2. Use add_translations.py to update problematic translations")
            print()

        if self.warnings:
            print("  1. Review warnings and decide if corrections are needed")
            print("  2. Some warnings may be acceptable (e.g., technical terms)")
            print()

        return False

def main():
    """Main function"""
    print("=" * 70)
    print("Interactive Translation Review")
    print("=" * 70)
    print()

    reviewer = TranslationReviewer()

    # Review all slides
    for slide_num in range(1, 7):  # Assuming 6 slides
        slide_issues = reviewer.review_slide(slide_num)
        if slide_issues is None:
            continue

        reviewer.print_slide_report(slide_num, slide_issues)

    # Generate summary
    success = reviewer.generate_review_report()

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
