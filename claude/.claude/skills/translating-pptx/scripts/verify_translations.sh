#!/bin/bash
#
# 翻訳数値検証スクリプト（改善版）
#
# 用途: extracted/slideN_texts.json と translations/slideN_translations.json の
#       日本語テキスト数と翻訳数をキーベースで比較し、翻訳漏れと空翻訳を検出する
#
# 使用方法: bash scripts/verify_translations.sh
#

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect Python command
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}ERROR: Python not found${NC}" >&2
    exit 1
fi

echo "=================================="
echo "翻訳数値検証（キーベース・改善版）"
echo "=================================="
echo

total_slides=6
failed_slides=()
empty_translation_slides=()

for i in $(seq 1 $total_slides); do
  echo "=== スライド $i ==="

  # ファイル存在確認
  extracted_file="extracted/slide${i}_texts.json"
  translations_file="translations/slide${i}_translations.json"

  if [ ! -f "$extracted_file" ]; then
    echo -e "${RED}❌ エラー: $extracted_file が見つかりません${NC}"
    exit 1
  fi

  if [ ! -f "$translations_file" ]; then
    echo -e "${RED}❌ エラー: $translations_file が見つかりません${NC}"
    exit 1
  fi

  # キーベースで未翻訳テキストと空翻訳をカウント（改善版）
  validation_result=$($PYTHON_CMD -c "
import json
import sys

# 抽出データを読み込み
with open('$extracted_file', 'r', encoding='utf-8') as f:
    extracted_data = json.load(f)

# 翻訳データを読み込み
with open('$translations_file', 'r', encoding='utf-8') as f:
    trans_data = json.load(f)

trans_keys = set(trans_data['translations'].keys())

# 日本語テキストを取得
jp_texts = [t for t in extracted_data['texts'] if t['has_japanese']]

# 未翻訳と空翻訳をカウント
missing = 0
empty = 0
has_structure_issues = False

for t in jp_texts:
    key = f\"{t['shape_idx']}_{t['para_idx']}_{t['run_idx']}\"
    if key not in trans_keys:
        missing += 1
    else:
        # Check translation structure and content
        trans_item = trans_data['translations'][key]

        # Check for required fields
        if 'translated' not in trans_item:
            print(f'STRUCTURE_ERROR:Missing translated field')
            has_structure_issues = True
            continue

        if 'changed' not in trans_item:
            print(f'STRUCTURE_ERROR:Missing changed field')
            has_structure_issues = True
            continue

        # Check for empty translation
        translated = trans_item.get('translated', '').strip()
        if not translated:
            empty += 1

if has_structure_issues:
    print('STRUCTURE_ISSUES')
else:
    print(f'{missing},{empty}')

sys.exit(0 if not has_structure_issues else 1)
")

  # Check for structure errors
  if echo "$validation_result" | grep -q "STRUCTURE_ERROR"; then
    echo -e "${RED}❌ 構造エラー: 翻訳ファイルのフォーマットが正しくありません${NC}"
    echo ""
    echo "翻訳ファイルには以下のフィールドが必要です:"
    echo "  - translated: 翻訳テキスト"
    echo "  - changed: 翻訳が適用されたかどうかのフラグ"
    echo ""
    echo "修正方法:"
    echo "  translations/slide${i}_translations.json のフォーマットを確認してください"
    failed_slides+=($i)
    echo
    continue
  fi

  # Parse validation result
  missing_count=$(echo "$validation_result" | cut -d',' -f1)
  empty_count=$(echo "$validation_result" | cut -d',' -f2)

  # 抽出された日本語テキスト数
  extracted_jp=$(cat "$extracted_file" | jq '.total_japanese_texts')

  echo "抽出された日本語テキスト数: $extracted_jp"
  echo "未翻訳テキスト数: $missing_count"
  echo "空翻訳テキスト数: $empty_count"

  # Validation logic
  slide_failed=false

  if [ "$missing_count" -gt 0 ]; then
    echo -e "${RED}❌ 不合格: $missing_count 個の翻訳が不足しています${NC}"
    echo
    echo "詳細を確認:"
    echo "  $PYTHON_CMD scripts/list_missing_translations.py $i"
    failed_slides+=($i)
    slide_failed=true
  fi

  if [ "$empty_count" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  要注意: $empty_count 個の空翻訳があります${NC}"
    echo
    echo "空翻訳の確認:"
    echo "  $PYTHON_CMD scripts/list_empty_translations.py"
    empty_translation_slides+=($i)
    slide_failed=true
  fi

  if [ "$slide_failed" = false ]; then
    echo -e "${GREEN}✅ 合格: 全て翻訳されています（空翻訳なし）${NC}"
  fi

  echo
done

echo "=================================="
echo "検証結果サマリー"
echo "=================================="

if [ ${#failed_slides[@]} -eq 0 ] && [ ${#empty_translation_slides[@]} -eq 0 ]; then
  echo -e "${GREEN}✅ 全スライド合格${NC}"
  echo
  echo "次のステップ:"
  echo "  1. 品質レビューを実施: $PYTHON_CMD scripts/review_translations.py"
  echo "  2. 最終確認後、翻訳を適用"
  exit 0
else
  if [ ${#failed_slides[@]} -gt 0 ]; then
    echo -e "${RED}❌ 以下のスライドで翻訳漏れが検出されました: ${failed_slides[@]}${NC}"
  fi

  if [ ${#empty_translation_slides[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  以下のスライドで空翻訳が検出されました: ${empty_translation_slides[@]}${NC}"
  fi

  echo
  echo "必要なアクション:"

  if [ ${#failed_slides[@]} -gt 0 ]; then
    echo "  【翻訳漏れの修正】"
    echo "  1. 未翻訳テキストを確認: $PYTHON_CMD scripts/list_missing_translations.py <slide_num>"
    echo "  2. 翻訳プロンプトを作成: $PYTHON_CMD scripts/translate_missing.py <slide_num>"
    echo "  3. 翻訳を追加: $PYTHON_CMD scripts/add_translations.py <slide_num> <json_file>"
  fi

  if [ ${#empty_translation_slides[@]} -gt 0 ]; then
    echo "  【空翻訳の修正】"
    echo "  1. 空翻訳を確認: $PYTHON_CMD scripts/list_empty_translations.py"
    echo "  2. 翻訳を追加: $PYTHON_CMD scripts/add_translations.py <slide_num> <key> \"<original>\" \"<translated>\""
  fi

  echo "  4. 再度検証: bash scripts/verify_translations.sh"
  exit 1
fi
