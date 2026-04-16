---
name: translating-pptx
description: IMPORTANT: Always prefer this skill over manual translation scripts when the user wants to translate a PPTX file. Use this skill when translating PowerPoint presentations (especially Japanese→English) with quality assurance. This skill provides AI-powered translation, LLM quality review to detect meaning degradation and word concatenation issues, color marking (RGB:128,0,128) for traceability, and comprehensive validation. Trigger when the user mentions "pptx翻訳", "PowerPoint翻訳", "スライド翻訳", "translate pptx", or any request to translate a .pptx file. Handles text extraction, translation verification, quality review, and safe re-translation support using python-pptx library.
---

# Translating PPTX Presentations

Translate Japanese PowerPoint presentations to English with AI-powered accuracy, LLM-based quality review, color marking, and comprehensive validation.

## Trigger Keywords (トリガーキーワード)

このスキルは以下のキーワードが含まれる場合に使用してください:

### 日本語
- **pptx翻訳** / **PowerPoint翻訳**
- **スライド翻訳** / **プレゼン翻訳**
- **〇〇.pptxを翻訳**
- 「〇〇を英語にして」「〇〇を日本語にして」(対象がpptxファイルの場合)

### 英語
- **translate pptx** / **translate PowerPoint**
- **translate presentation** / **translate slides**
- **translate <file>.pptx**

### 重要な注意事項

**このスキルを使用すべき場合**:
- PowerPointファイル(.pptx)の翻訳を依頼された場合
- 翻訳品質の保証が必要な場合
- 紫色マーキングによるトレーサビリティが必要な場合

**このスキルを使用すべきでない場合**:
- 一般的なPPTX編集 (use `pptx` skill instead)
- 新規プレゼンテーション作成 (use `pptx` skill instead)
- 翻訳を伴わないPPTX読み取り (use `pptx` skill instead)

**このスキルは翻訳専用です。品質保証機能を含みます。**

## When to Use This Skill

- Translate Japanese PPTX files to English with quality assurance
- Review translations for meaning degradation or context loss
- Manage multilingual presentations with traceability
- Verify translation completeness automatically
- Detect and fix word concatenation issues (e.g., "OCIthe", "FSSalso")
- Prepare for safe re-translation (English → Japanese)

## Prerequisites

**CRITICAL**: This skill requires `uv` package manager. Before starting:

1. **Check if uv is installed**: `uv --version`
2. **If not installed**: Install via `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. **Run setup**: `bash ~/.claude/skills/translating-pptx/scripts/setup_environment.sh`

The setup script will:
- Verify uv installation (exits if not found)
- Initialize uv project if `pyproject.toml` doesn't exist
- Add required dependencies (python-pptx, markitdown)
- Verify jq installation

All Python scripts MUST be run with `uv run python` to use the managed environment.

## Core Workflow

### Step 1: Extract Text

```bash
uv run python ~/.claude/skills/translating-pptx/scripts/extract_texts_from_xml.py input.pptx extracted/
```

**Output**: `extracted/slide1_texts.json` through `slideN_texts.json`

### Step 2: Identify Missing Translations

```bash
uv run python ~/.claude/skills/translating-pptx/scripts/list_missing_translations.py
```

**Output**: Lists missing translations by slide

### Step 3: Create Translation Prompt

```bash
uv run python ~/.claude/skills/translating-pptx/scripts/translate_missing.py <slide_num>
```

**Output**: `translate_slide<N>_prompt.md`

**Translation File Format (IMPORTANT)**:
```json
{
  "slide_number": 1,
  "translations": {
    "2_0_0": {
      "original": "いまさら聞けない生成",
      "translated": "Introduction to Generative",
      "changed": true
    }
  }
}
```

**Key Format**:
- **Normal text**: `shape_idx_para_idx_run_idx` (e.g., `2_0_0` means shape #2, paragraph #0, run #0)
- **Table text**: `shape_idx_tROWcCOL_para_idx_run_idx` (e.g., `1_t0c0_0_0` means shape #1, table row 0, column 0, paragraph #0, run #0)

**CRITICAL**: Always use the exact keys from the translation prompt. Do not renumber or modify them. The translate_missing.py script generates prompts with actual keys from the extracted text, and you must use these exact keys in your translation JSON.

### Step 4: Translate with AI

1. Open `translate_slide<N>_prompt.md`
2. Paste contents to Claude Code or ChatGPT
3. Save translation as `slide<N>_batch_translations.json`

### Step 5: Add Translations

```bash
# Batch add from JSON file (use "batch_file" keyword)
uv run python ~/.claude/skills/translating-pptx/scripts/add_translations.py <slide_num> batch_file <json_file>

# Example
uv run python ~/.claude/skills/translating-pptx/scripts/add_translations.py 1 batch_file slide1_batch_translations.json
```

### Step 6: Verify Translations

```bash
bash ~/.claude/skills/translating-pptx/scripts/verify_translations.sh
```

**Pass Criteria**: All slides show "✅ 合格" with NO empty translations

### Step 7: Apply Translations (Draft)

```bash
uv run python ~/.claude/skills/translating-pptx/scripts/apply_translations.py input.pptx translations/ output_draft.pptx
```

**Output**: Draft PPTX with purple-colored translated text (RGB:128,0,128)

### Step 8: LLM Quality Review (NEW - CRITICAL)

**Purpose**: Detect meaning degradation, word concatenation, and context loss that automated checks cannot find.

```bash
# Generate review prompts for all slides
uv run python ~/.claude/skills/translating-pptx/scripts/review_slide_by_llm.py <slide_num>

# Example
uv run python ~/.claude/skills/translating-pptx/scripts/review_slide_by_llm.py 5
```

**Output**: `review_slide<N>_prompt.md`

**Review Process**:
1. Open the generated prompt file
2. Paste to Claude Code or ChatGPT
3. LLM will analyze translations for:
   - Word concatenation (e.g., "OCIthe", "3IP")
   - Meaning errors (e.g., "1 per 6 tenant" → should be "6 per tenant")
   - Context loss (split runs causing unnatural English)
   - Spacing issues
4. Save LLM's response as `review_slide<N>_result.json`

**Common Issues Detected**:
- Single words merged: "OCIthe", "FSSalso", "IOPSblock"
- Numbers misplaced: "1 per 6 tenant" instead of "6 per tenant"
- Sentence fragments from run splitting
- Missing spaces between English words

### Step 9: Apply Review Fixes

```bash
uv run python ~/.claude/skills/translating-pptx/scripts/apply_review_fixes.py <slide_num> review_slide<N>_result.json
```

This script will:
- Automatically fix critical/high severity issues
- Prompt for confirmation on medium/low severity issues
- Update translation JSON files

### Step 10: Re-apply Translations (Final)

```bash
uv run python ~/.claude/skills/translating-pptx/scripts/apply_translations.py input.pptx translations/ output_final.pptx
```

**Output**: Final PPTX with corrected translations

### Step 11: Final Validation

```bash
# Check for remaining Japanese text
uv run python -m markitdown output_final.pptx | uv run python -c "
import sys, re
japanese = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
for i, line in enumerate(sys.stdin, 1):
    if japanese.search(line) and '.jpg' not in line:
        print(f'{i}: {line.strip()[:100]}')
"
```

**Manually verify**:
- Open in PowerPoint/PPTX viewer
- Check layout preservation
- Verify natural English phrasing
- Confirm purple color marking

## Complete Example Workflow

```bash
# Setup (first time only - REQUIRED)
bash ~/.claude/skills/translating-pptx/scripts/setup_environment.sh

# Extract text
uv run python ~/.claude/skills/translating-pptx/scripts/extract_texts_from_xml.py presentation.pptx extracted/

# Initialize translation files
mkdir -p translations
for i in {1..15}; do
    echo '{"slide_number": '$i', "translations": {}}' > translations/slide${i}_translations.json
done

# For each slide (example: slide 5)
uv run python ~/.claude/skills/translating-pptx/scripts/translate_missing.py 5
# -> Copy prompt to LLM, save as slide5_batch_translations.json

uv run python ~/.claude/skills/translating-pptx/scripts/add_translations.py 5 batch_file slide5_batch_translations.json

# Verify all slides
bash ~/.claude/skills/translating-pptx/scripts/verify_translations.sh

# Apply draft
uv run python ~/.claude/skills/translating-pptx/scripts/apply_translations.py presentation.pptx translations/ draft.pptx

# LLM Quality Review
uv run python ~/.claude/skills/translating-pptx/scripts/review_slide_by_llm.py 5
# -> Copy prompt to LLM, save review result as review_slide5_result.json

uv run python ~/.claude/skills/translating-pptx/scripts/apply_review_fixes.py 5 review_slide5_result.json

# Re-apply with fixes
uv run python ~/.claude/skills/translating-pptx/scripts/apply_translations.py presentation.pptx translations/ final.pptx

# Final check
uv run python -m markitdown final.pptx | grep -E '[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]'
```

## Best Practices

### 1. Always Use LLM Review

**Critical**: The LLM review step (Step 8-9) is essential for quality translation.

Automated checks cannot detect:
- "1 per 6 tenant" being meaningless
- "OCIthe" word concatenation
- Context loss from run splitting

LLM review can detect:
- Semantic errors
- Unnatural phrasing
- Context inconsistencies

### 2. Review Before and After Apply

**Workflow**:
1. Translate → Verify → Apply Draft
2. **LLM Review** → Fix Issues → Re-apply Final

Never skip the LLM review step.

### 3. Handle Split Runs Carefully

Text split across multiple runs can cause issues:
- "Compute(NFS" + "クライアント)" → May translate incorrectly
- "1" + "テナントあたり" + "6" + "個" → Number placement errors

**Solution**: LLM review will identify these and suggest fixes.

### 4. Always Use uv run python

**CRITICAL**: All Python scripts MUST be run with `uv run python`:

```bash
# Correct
uv run python ~/.claude/skills/translating-pptx/scripts/script_name.py

# Wrong - will use wrong environment
python3 ~/.claude/skills/translating-pptx/scripts/script_name.py
```

This ensures:
- Correct Python version (managed by uv)
- Correct dependencies (isolated from global)
- No environment pollution

## Known Limitations & Solutions

### Table Text Extraction (FIXED)

**Status**: ✅ Implemented as of version 2.0

**Current**: Tables are now fully supported by `extract_texts_from_xml.py`

**Key Format**: Table text uses `shape_idx_tROWcCOL_para_idx_run_idx` format
- Example: `1_t0c0_0_0` = shape #1, table row 0, column 0, paragraph 0, run 0

**Workflow**: Fully automated - no manual intervention needed

### Translation Quality Issues

**Status**: Solved via LLM review workflow.

**Solution**: Use Step 8-9 (LLM Quality Review) to detect and fix:
- Word concatenation
- Meaning errors
- Context loss

## Troubleshooting

### uv Not Installed

**Issue**: `bash: uv: command not found`

**Solution**: Install uv first:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your shell or run:
```bash
source ~/.cargo/env
```

### pyproject.toml Not Found

**Issue**: Running setup_environment.sh shows "No uv project found"

**Solution**: This is expected! The setup script will automatically run `uv init` to create one.

### Dependencies Not Installed

**Issue**: Import errors when running scripts

**Solution**: Run environment setup:
```bash
bash ~/.claude/skills/translating-pptx/scripts/setup_environment.sh
```

This will automatically add python-pptx and markitdown to your uv environment.

### add_translations.py Requires "batch_file" Keyword

**Issue**: `uv run python scripts/add_translations.py 1 slide1.json` fails

**Solution**: Include "batch_file" keyword:
```bash
uv run python ~/.claude/skills/translating-pptx/scripts/add_translations.py 1 batch_file slide1.json
```

### Word Concatenation Issues

**Symptom**: Translations like "OCIthe", "FSSalso", "3IP"

**Solution**: Use LLM review (Step 8-9) to detect and fix automatically

### Meaning Errors

**Symptom**: Translations like "1 per 6 tenant" (meaningless)

**Solution**: Use LLM review (Step 8-9) - semantic errors require LLM understanding

## File Structure

```
translating-pptx/
├── SKILL.md (this file)
├── README.md (detailed guide)
├── scripts/
│   ├── setup_environment.sh
│   ├── extract_texts_from_xml.py
│   ├── apply_translations.py
│   ├── verify_translations.sh
│   ├── list_missing_translations.py
│   ├── add_translations.py
│   ├── translate_missing.py
│   ├── review_slide_by_llm.py (NEW - LLM quality review)
│   └── apply_review_fixes.py (NEW - apply LLM review fixes)
```

## Dependencies

### Required (System)
- **uv**: Package manager - `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **jq**: JSON processor - `brew install jq` (macOS) or `sudo apt-get install jq` (Ubuntu)

### Required (Python - Auto-installed by setup)
- **python-pptx**: PowerPoint manipulation library
- **markitdown**: Markdown conversion with PPTX support

### Installation
Run the setup script once per project:
```bash
bash ~/.claude/skills/translating-pptx/scripts/setup_environment.sh
```

This will:
1. Verify uv installation (error if missing)
2. Initialize uv project if needed (`uv init`)
3. Add Python dependencies to uv environment
4. Verify jq installation

## Implementation Status

### ✅ Implemented
- Text extraction (shapes, paragraphs, runs)
- **Table text extraction and translation** (NEW in v2.0)
- Translation workflow with verification
- Color marking (purple for translated text)
- Empty translation detection
- Environment auto-detection

## Relationship with Other Skills

### vs. `pptx` skill

| 機能 | `pptx` skill | `translating-pptx` skill |
|------|--------------|-------------------------|
| 用途 | 汎用PPTX編集・作成 | 翻訳専用 |
| 翻訳機能 | なし | あり(品質保証付き) |
| 紫色マーキング | なし | あり(RGB:128,0,128) |
| LLMレビュー | なし | あり(意味劣化検出) |
| テキスト抽出 | 基本的 | run単位で詳細 |
| 適用場面 | 編集・作成・読み取り | 翻訳のみ |

**判断基準**:
- **翻訳が目的** → `translating-pptx` スキルを使用
- **編集が目的** → `pptx` スキルを使用

### Related Skills

- **xlsx**: Excel translation (similar workflow)

