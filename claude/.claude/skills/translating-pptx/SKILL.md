---
name: translating-pptx
description: Use this skill when translating Japanese PowerPoint presentations to English, including extracting text, AI-powered translation with color marking (RGB:128,0,128), verification of translation completeness, and safe re-translation support. Handles PPTX files using python-pptx library with automated workflow scripts for extraction, translation, verification, and application.
---

# Translating PPTX Presentations

Translate Japanese PowerPoint presentations to English with AI-powered accuracy, color marking, and re-translation safety.

## When to Use This Skill

- Translate Japanese PPTX files to English
- Manage multilingual presentations
- Need translation traceability with color marking
- Verify translation completeness automatically
- Prepare for safe re-translation (English → Japanese)

## Core Workflow

### Step 1: Extract Text

```bash
python scripts/extract_texts_from_xml.py input.pptx extracted/
```

**Output**: `extracted/slide1_texts.json` through `slide6_texts.json`

### Step 2: Identify Missing Translations

```bash
python scripts/list_missing_translations.py
```

**Output**: Lists missing translations by slide

### Step 3: Create Translation Prompt

```bash
python3 scripts/translate_missing.py <slide_num>
```

**Output**: `translate_slide<N>_prompt.md`

**Translation File Format (IMPORTANT)**:
Each translation must include these fields:
- `original`: Original Japanese text
- `translated`: English translation (REQUIRED - not "translation")
- `changed`: Boolean flag (true if translated, false if empty/original)

Example:
```json
{
  "slide_number": 1,
  "translations": {
    "2_0_0": {
      "shape_idx": 2,
      "para_idx": 0,
      "run_idx": 0,
      "original": "いまさら聞けない生成",
      "translated": "Introduction to Generative",
      "changed": true
    }
  }
}
```

### Step 4: Translate with AI

1. Open `translate_slide<N>_prompt.md`
2. Paste contents to Claude Code
3. Save translation as `slide<N>_batch_translations.json`

### Step 5: Add Translations

```bash
# Batch add from JSON file
python3 scripts/add_translations.py <slide_num> <json_file>

# Or add single translation
python3 scripts/add_translations.py <slide_num> <key> "<original>" "<translated>"
```

### Step 6: Review Translations (REQUIRED)

**NEW**: Interactive review process to ensure translation quality.

```bash
python3 scripts/review_translations.py
```

This script will:
1. Display each original text with its translation
2. Check for empty translations
3. Check for context consistency
4. Allow you to approve or request changes
5. Generate a review report

**Review Checklist**:
- [ ] No empty translations (`translated` field is not empty)
- [ ] Context is preserved (split runs are coherent)
- [ ] Technical terms are translated consistently
- [ ] Natural English phrasing
- [ ] No untranslated Japanese (except proper nouns/technical terms)

### Step 7: Verify (REQUIRED)

```bash
bash scripts/verify_translations.sh
```

**Pass Criteria**: All slides show "✅ 合格" with NO empty translations

**Critical**: Never skip verification. The script now:
- Rejects translations with empty `translated` fields
- Checks for context consistency across split runs
- Validates `changed` field is set correctly
- Reports specific issues for correction

### Step 7: Apply Translations

```bash
python scripts/apply_translations.py input.pptx translations/ output.pptx
```

**Output**: `output.pptx` with purple-colored translated text (RGB:128,0,128)

### Step 8: Final Validation (REQUIRED)

**NEW**: Comprehensive final validation with automated checks.

```bash
python3 scripts/final_validation.sh output.pptx
```

This script performs:
1. **File integrity check**: Verify PPTX structure is valid
2. **Japanese detection**: Find remaining Japanese text (excluding images)
3. **Translation completeness**: Ensure all Japanese text is translated
4. **Color marking check**: Verify purple color (RGB:128,0,128) is applied
5. **Layout validation**: Check that text layout is preserved
6. **Generate validation report**: Create detailed validation report

**Manual validation** (also recommended):
```bash
# Check content
python3 -m markitdown output.pptx

# Detect remaining Japanese (excluding images)
python3 -m markitdown output.pptx | python3 -c "
import sys, re
japanese = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
for i, line in enumerate(sys.stdin, 1):
    if japanese.search(line) and '.jpg' not in line:
        print(f'{i}: {line.strip()[:100]}')
"
```

**Open in PowerPoint/PPTX viewer** to visually verify:
- Layout is preserved
- Text is readable
- Color marking is applied correctly
- No formatting issues

## Examples

### Complete Workflow Example

```bash
# 0. Setup (first time only)
bash scripts/setup_environment.sh

# 1. Extract
python3 scripts/extract_texts_from_xml.py sample.pptx extracted/

# 2. Check all slides
python3 scripts/list_missing_translations.py

# 3. Translate slide 4
python3 scripts/translate_missing.py 4
# -> Copy prompt to Claude Code
# -> Save as slide4_batch_translations.json

# 4. Add translations
python3 scripts/add_translations.py 4 slide4_batch_translations.json

# 5. Review translations (NEW - REQUIRED)
python3 scripts/review_translations.py

# 6. Verify ALL slides (IMPROVED - now checks empty translations)
bash scripts/verify_translations.sh

# 7. Apply
python3 scripts/apply_translations.py sample.pptx translations/ converted.pptx

# 8. Final validation (NEW - REQUIRED)
bash scripts/final_validation.sh converted.pptx
```

### Single Translation Addition

```bash
python3 scripts/add_translations.py 3 2_0_1 "大規模言語モデル" "Large Language Model "
```

## Best Practices

### 1. Always Review and Verify First

**Incorrect**: Translate → Apply → Check
**Correct**: Translate → **Review** → **Verify** → Apply

- Use `review_translations.py` to check translation quality
- Use `verify_translations.sh` to ensure completeness
- Never skip these steps

### 2. Use Key-Based Verification

The `verify_translations.sh` script uses key-based matching, not simple counting. This identifies exact missing translations and empty translations.

### 3. Maintain Context Awareness

- Text may be split across multiple runs (shape_idx_para_idx_run_idx)
- Review the full context when translating
- Consider merging split runs for better context
- Use `review_translations.py` to see context information

### 4. Ensure Translation Completeness

- **Never leave `translated` field empty** unless intentionally keeping original text
- Use `list_empty_translations.py` to find empty translations
- All Japanese text should be translated (except proper nouns/technical terms)

### 5. Use python3 Explicitly

**Cross-platform compatibility**:
- Use `python3` instead of `python` in scripts
- The skill includes automatic Python detection
- Or use `scripts/setup_environment.sh` for environment setup

### 6. Validate Translation Quality

**Review checklist**:
- [ ] No empty translations
- [ ] Context is preserved (split runs are coherent)
- [ ] Technical terms are translated consistently
- [ ] Natural English phrasing
- [ ] No untranslated Japanese (except proper nouns/technical terms)

### 7. Space Adjustment

The `apply_translations.py` script automatically adjusts spaces:
- Between Japanese and English text
- Between runs when needed

### 8. Color Marking

- **Translated text**: Purple (RGB:128,0,128, hex: `800080`)
- **Original English**: Black (unchanged)

This enables safe re-translation by identifying what was translated.

## Troubleshooting

### Python Command Not Found

```bash
# Use python3 explicitly
python3 scripts/extract_texts_from_xml.py input.pptx extracted/

# Or set up environment
bash scripts/setup_environment.sh
```

### Empty Translations Detected

The verification script now reports empty translations:

```bash
# Fix empty translations
python3 scripts/list_empty_translations.py

# This will show:
# - Which slides have empty translations
# - Which keys need translation
# - Context information for each empty translation
```

### Translation Gaps Detected

```bash
# 1. Identify missing translations
python3 scripts/list_missing_translations.py <slide_num>

# 2. Create prompt
python3 scripts/translate_missing.py <slide_num>

# 3. Add translations
python3 scripts/add_translations.py <slide_num> <json_file>

# 4. Re-verify
bash scripts/verify_translations.sh
```

### Context Issues (Split Runs)

When text is split across multiple runs (e.g., "今更ですが、生成" + "AI" + "について"):

1. **Review context**: Use `review_translations.py` to see full context
2. **Merge translations**: Consider translating the full phrase together
3. **Adjust boundaries**: If needed, manually edit the translation JSON to merge context

Example fix:
```json
{
  "0_0_1": {
    "original": "今更ですが、生成",
    "translated": "Better late than never, about Generative",
    "changed": true
  },
  "0_0_2": {
    "original": "AI",
    "translated": "AI",
    "changed": false
  },
  "0_0_3": {
    "original": "について",
    "translated": "",
    "changed": false
  }
}
```

Better approach (context-aware):
```json
{
  "0_0_1": {
    "original": "今更ですが、生成AIについて",
    "translated": "Better late than never, about Generative AI",
    "changed": true
  }
}
```

### Space Issues

If words are concatenated (e.g., "ChatGPTsuch as"):

1. Check `apply_translations.py` `ensure_trailing_space()` function
2. Verify next run's first character triggers space addition
3. Re-apply translations

### Color Marking Not Applied

```bash
# Unpack and check
python3 ~/.claude/skills/pptx/scripts/office/unpack.py output.pptx unpacked/
grep "800080" unpacked/ppt/slides/slide*.xml
```

### Dependencies Not Installed

```bash
# Run environment setup
bash scripts/setup_environment.sh

# Or manually install
pip install python-pptx "markitdown[pptx]"
# or
uv add python-pptx "markitdown[pptx]"
```

## File Structure

```
translating-pptx/
├── SKILL.md (this file)
├── README.md (detailed guide)
├── scripts/
│   ├── setup_environment.sh (NEW - environment setup)
│   ├── extract_texts_from_xml.py
│   ├── apply_translations.py
│   ├── verify_translations.sh (IMPROVED - detects empty translations)
│   ├── list_missing_translations.py
│   ├── list_empty_translations.py (NEW - lists empty translations)
│   ├── review_translations.py (NEW - interactive review)
│   ├── add_translations.py
│   ├── translate_missing.py
│   └── final_validation.sh (NEW - comprehensive validation)
└── docs/
    ├── REVIEW_POLICY.md (review guidelines)
    └── PLAN.md (complete documentation)
```

## Dependencies

- **Python 3.12+** (自動検出: `python3` または `python`)
- **python-pptx**: `pip install python-pptx` または `uv add python-pptx`
- **jq**: `brew install jq`
- **markitdown**: `pip install "markitdown[pptx]"` または `uv add "markitdown[pptx]"`

## Environment Setup

The skill includes automatic environment detection and setup:

```bash
# 環境チェックと依存関係のインストール
bash scripts/setup_environment.sh
```

This script will:
1. Detect Python 3 (python3 or python)
2. Check and install required dependencies
3. Verify all tools are available
4. Provide clear error messages for missing dependencies

## Related Skills

- **pptx**: PPTX editing and manipulation
- **xlsx**: Excel translation (future)

## Reference Documentation

See `./docs/REVIEW_POLICY.md` for detailed review guidelines and `./docs/PLAN.md` for complete workflow documentation.
