---
name: transcribe-audio
description: Transcribe audio files (MP3, WAV, etc.) to text using Gemini API with automatic segmentation, parallel processing, and timeline correction. Use when the user wants to transcribe audio, convert speech to text, or mentions audio files, recordings, podcasts, meetings, or interviews.
---

# Audio Transcription Skill

Transcribes audio files to text using Gemini API with intelligent segmentation, parallel processing, and accurate timeline preservation.

## Prerequisites

- **ffmpeg**: Required for audio segmentation (install with `sudo apt install ffmpeg` or equivalent)
- **API Key**: Set `GOOGLE_API_KEY` or `GEMINI_API_KEY` environment variable
- **Python uv**: For dependency management (this skill will auto-initialize if needed)

## Workflow

### 1. Environment Setup

Check and prepare the environment:

```bash
# Check if ffmpeg is installed
which ffmpeg

# Verify API key is set
echo $GOOGLE_API_KEY
```

If `pyproject.toml` doesn't exist in the current directory:

```bash
uv init
uv add google-genai pydub tqdm
```

### 2. (Optional) Trim Audio File

For long audio files, trim to desired length before transcription:

```bash
# Trim to first 60 minutes (3600 seconds)
ffmpeg -i input.mp3 -t 3600 -c copy trimmed.mp3

# Trim from 5:00 to 30:00 (use -to for end position)
ffmpeg -i input.mp3 -ss 00:05:00 -to 00:30:00 -c copy trimmed.mp3

# Trim from 10:00 to end (fast seek)
ffmpeg -ss 00:10:00 -i input.mp3 -c copy trimmed.mp3
```

**Options:**
- `-t DURATION`: Duration (length) in seconds or HH:MM:SS
- `-to POSITION`: End position (timestamp)
- `-ss POSITION`: Start position (HH:MM:SS or seconds)
  - **Before `-i`**: Fast seek but less precise (keyframe-based)
  - **After `-i`**: Slower but frame-accurate
- `-c copy`: Fast copy without re-encoding (no quality loss)

**Note:** `-c copy` cuts at frame boundaries, not sample-accurate. For precise cuts, omit `-c copy` to re-encode (slower but accurate).

### 3. Audio Segmentation

Split audio into manageable segments:

- Uses ffmpeg `silencedetect` filter to find natural break points
- Target: 1MB per segment (configurable)
- Strategy: Reach 95% of target size, then split at next silence
- Saves metadata to `segments/segments_metadata.json`

### 4. Parallel Transcription

Process segments concurrently:

- Default parallelism: 5 (adjustable based on API rate limits)
- Model: `gemini-3.1-pro-preview` (optimal for batch audio transcription)
- Strict output format enforcement
- Progress tracking with tqdm

**Critical: Strict Format Prompt**

Use this exact prompt to ensure consistent output:

```
このオーディオを文字起こししてください。

【必須要件】
- イントロ文や説明文は一切不要です
- タイムスタンプは HH:MM:SS 形式（例: 00:03:25）
- 各行のフォーマット: HH:MM:SS 話者N: 発言内容
- 話者が変わる場合は話者1、話者2のようにラベル付け
- 笑い声や沈黙は (笑い声)、(沈黙) のように括弧書き

フォーマット例:
00:00:11 話者1: これだから、事前の送付だったかな。
00:00:14 話者2: あ、はい。
00:00:21 (笑い声)
```

### 5. Timeline Correction

Correct timestamps to reflect original audio timeline:

- Read `segments_metadata.json` for segment offsets
- Extract timestamps with regex: `(\d{2}:\d{2}:\d{2})`
- Add segment start offset to each timestamp
- Example: segment_001.mp3 starts at 188.69s → `00:00:00` becomes `00:03:08`

### 6. Combine Results

Merge corrected transcripts into single file:

- Combine all `.corrected.txt` files
- No segment markers needed (timeline is continuous)
- Save to `transcript_combined.txt`

### 7. Refine (Optional)

Clean up the transcript:

- Remove fillers (えー, あのー, なんか, etc.)
- Improve readability
- Preserve timestamps and speaker labels
- Save to `transcript_refined.txt`

## Implementation Scripts

The skill uses these Python scripts:

- `transcribe_audio.py`: Main orchestrator
- `audio_splitter.py`: Segmentation with metadata recording
- `transcriber.py`: Parallel transcription
- `timestamp_corrector.py`: Timeline reconstruction
- `refiner.py`: Optional cleanup

See [./implementation-details.md](./implementation-details.md) for complete code.

## Example Usage

```bash
# Basic usage (auto-setup environment)
python transcribe_audio.py input.mp3

# With options
python transcribe_audio.py input.mp3 --parallel 10 --target-size 2 --refine

# Skip environment setup if already configured
python transcribe_audio.py input.mp3 --skip-setup
```

## Output Files

1. `segments/` - Audio segments (segment_000.mp3, segment_001.mp3, ...)
2. `segments/segments_metadata.json` - Segment timing information
3. `segments/segment_XXX.mp3.corrected.txt` - Individual corrected transcripts
4. `transcript_combined.txt` - Full transcript with corrected timeline
5. `transcript_refined.txt` - Cleaned version (if --refine used)
6. `logs/transcribe_YYYYMMDD_HHMMSS.log` - Execution log

## Performance

- **Before**: 15 segments sequential processing → ~12 minutes
- **After** (parallel=5): 15 segments parallel processing → ~2.4 minutes (5x faster)
- **After** (parallel=10): 15 segments parallel processing → ~1.5 minutes (8x faster)

Adjust `--parallel` based on API rate limits.

## Troubleshooting

**ffmpeg not found**:
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

**API key missing**:
```bash
export GOOGLE_API_KEY="your-key-here"
```

**Format inconsistency**:
- Ensure using the exact strict format prompt shown above
- Gemini may add intro text despite instructions; filter programmatically if needed

**Timeline gaps**:
- Verify `segments_metadata.json` exists and has correct offsets
- Check timestamp regex pattern matches output format

## Best Practices

1. **Test with small file first**: Verify setup before processing large files
2. **Monitor API costs**: Each segment = 1 API call
3. **Adjust parallel**: Balance speed vs rate limits (start with 5)
4. **Preserve originals**: Keep source audio until verification complete
5. **Check logs**: Review `logs/` for errors or warnings
