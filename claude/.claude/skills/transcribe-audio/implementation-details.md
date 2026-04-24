# Implementation Details

Complete Python implementation for the audio transcription workflow.

## Directory Structure

```
~/.claude/skills/transcribe-audio/
├── SKILL.md
├── implementation-details.md (this file)
├── transcribe_audio.py
├── audio_splitter.py
├── transcriber.py
├── timestamp_corrector.py
└── refiner.py
```

## transcribe_audio.py (Main Orchestrator)

```python
"""Main script for audio transcription workflow"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def setup_logging() -> logging.Logger:
    """Setup logging to file and console"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"transcribe_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)


def setup_environment(logger: logging.Logger):
    """Setup uv environment and dependencies"""
    logger.info("=== Environment Setup ===")

    # Check uv availability
    if shutil.which("uv") is None:
        raise RuntimeError("uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh")

    # Initialize uv project if needed
    if not Path("pyproject.toml").exists():
        logger.info("Initializing uv project...")
        subprocess.run(["uv", "init"], check=True)

    # Add dependencies
    logger.info("Installing dependencies...")
    subprocess.run(["uv", "add", "google-genai", "pydub", "tqdm"], check=True)

    # Check ffmpeg
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg not found. Install with:\n"
            "  Ubuntu/Debian: sudo apt install ffmpeg\n"
            "  macOS: brew install ffmpeg"
        )

    # Check API key
    if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" not in os.environ:
        raise RuntimeError(
            "API key not found. Set with:\n"
            "  export GOOGLE_API_KEY='your-key-here'"
        )

    logger.info("Environment setup complete")


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio files using Gemini API")
    parser.add_argument("input", type=Path, help="Input audio file")
    parser.add_argument("--target-size", type=float, default=1.0, help="Target segment size in MB")
    parser.add_argument("--parallel", type=int, default=5, help="Parallel transcription workers")
    parser.add_argument("--silence-thresh", type=int, default=-40, help="Silence detection threshold in dB")
    parser.add_argument("--min-silence", type=float, default=0.5, help="Minimum silence duration in seconds")
    parser.add_argument("--refine", action="store_true", help="Generate refined transcript")
    parser.add_argument("--skip-setup", action="store_true", help="Skip environment setup")
    parser.add_argument("--output-dir", type=Path, default=Path("segments"), help="Output directory")

    args = parser.parse_args()

    logger = setup_logging()
    logger.info("=== Audio Transcription Workflow ===")
    logger.info(f"Input: {args.input}")
    logger.info(f"Target size: {args.target_size}MB")
    logger.info(f"Parallel workers: {args.parallel}")

    try:
        # 1. Environment setup
        if not args.skip_setup:
            setup_environment(logger)

        # 2. Import modules (after setup)
        from audio_splitter import split_audio_with_metadata
        from transcriber import transcribe_parallel
        from timestamp_corrector import correct_all_transcripts
        from refiner import refine_transcript

        # 3. Split audio
        logger.info("=== Splitting Audio ===")
        metadata = split_audio_with_metadata(
            args.input,
            args.output_dir,
            args.target_size,
            args.silence_thresh,
            args.min_silence,
            logger
        )

        # 4. Parallel transcription
        logger.info("=== Transcribing Segments ===")
        transcripts = transcribe_parallel(
            args.output_dir,
            metadata,
            args.parallel,
            logger
        )

        # 5. Correct timestamps
        logger.info("=== Correcting Timestamps ===")
        corrected = correct_all_transcripts(
            transcripts,
            metadata,
            args.output_dir,
            logger
        )

        # 6. Combine results
        logger.info("=== Combining Results ===")
        combined_path = Path("transcript_combined.txt")
        with open(combined_path, "w", encoding="utf-8") as f:
            # Sort by segment order
            sorted_files = sorted(corrected.keys())
            for i, seg_file in enumerate(sorted_files):
                if i > 0:
                    f.write("\n\n")
                f.write(corrected[seg_file])

        logger.info(f"Combined transcript saved: {combined_path}")

        # 7. Refine (optional)
        if args.refine:
            logger.info("=== Refining Transcript ===")
            with open(combined_path, "r", encoding="utf-8") as f:
                combined_text = f.read()

            refined_path = Path("transcript_refined.txt")
            refine_transcript(combined_text, refined_path, logger)
            logger.info(f"Refined transcript saved: {refined_path}")

        logger.info("=== Transcription Complete ===")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## audio_splitter.py

```python
"""Audio segmentation with metadata recording"""

import json
import logging
import subprocess
from pathlib import Path
from pydub import AudioSegment


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds"""
    audio = AudioSegment.from_file(str(audio_path))
    return len(audio) / 1000.0


def detect_silence_points(
    audio_path: Path,
    silence_thresh: int = -40,
    min_silence: float = 0.5,
    logger: logging.Logger = None
) -> list[float]:
    """Detect silence points using ffmpeg silencedetect"""
    if logger:
        logger.info(f"Detecting silence: threshold={silence_thresh}dB, min={min_silence}s")

    cmd = [
        "ffmpeg", "-i", str(audio_path),
        "-af", f"silencedetect=n={silence_thresh}dB:d={min_silence}",
        "-f", "null", "-"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stderr

    silence_points = []
    for line in output.split("\n"):
        if "silence_end" in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "silence_end:":
                    time = float(parts[i + 1])
                    silence_points.append(time)

    if logger:
        logger.info(f"Found {len(silence_points)} silence points")

    return silence_points


def calculate_split_points(
    audio_path: Path,
    silence_points: list[float],
    target_size_mb: float,
    logger: logging.Logger = None
) -> list[tuple[float, float]]:
    """Calculate segment boundaries"""
    total_duration = get_audio_duration(audio_path)
    file_size_bytes = audio_path.stat().st_size
    bitrate = file_size_bytes / total_duration

    target_bytes = target_size_mb * 1024 * 1024
    target_duration = target_bytes / bitrate
    split_threshold = target_duration * 0.95

    if logger:
        logger.info(f"Total duration: {total_duration:.2f}s")
        logger.info(f"Estimated bitrate: {bitrate:.0f} bytes/s")
        logger.info(f"Target duration: {target_duration:.2f}s")
        logger.info(f"Split threshold: {split_threshold:.2f}s (95%)")

    segments = []
    current_start = 0.0

    for silence_point in silence_points:
        if silence_point - current_start >= split_threshold:
            segments.append((current_start, silence_point))
            current_start = silence_point
            if logger:
                logger.info(f"Split point: {silence_point:.2f}s")

    # Last segment
    if current_start < total_duration:
        segments.append((current_start, total_duration))

    return segments


def split_audio_segment(
    audio_path: Path,
    start: float,
    end: float,
    output_path: Path
):
    """Split audio segment using ffmpeg"""
    duration = end - start
    cmd = [
        "ffmpeg", "-i", str(audio_path),
        "-ss", str(start),
        "-t", str(duration),
        "-c", "copy",
        str(output_path),
        "-y", "-loglevel", "error"
    ]
    subprocess.run(cmd, check=True)


def split_audio_with_metadata(
    audio_path: Path,
    output_dir: Path,
    target_size_mb: float = 1.0,
    silence_thresh: int = -40,
    min_silence: float = 0.5,
    logger: logging.Logger = None
) -> dict:
    """Split audio and save metadata"""
    output_dir.mkdir(exist_ok=True)

    # Detect silence points
    silence_points = detect_silence_points(
        audio_path, silence_thresh, min_silence, logger
    )

    # Calculate split points
    split_points = calculate_split_points(
        audio_path, silence_points, target_size_mb, logger
    )

    # Split audio
    segments = []
    for i, (start, end) in enumerate(split_points):
        segment_file = output_dir / f"segment_{i:03d}.mp3"
        if logger:
            logger.info(f"Creating segment {i}: {start:.2f}s - {end:.2f}s")

        split_audio_segment(audio_path, start, end, segment_file)

        segments.append({
            "file": segment_file.name,
            "start": start,
            "end": end,
            "duration": end - start
        })

    # Save metadata
    metadata = {
        "source_file": str(audio_path),
        "total_duration": get_audio_duration(audio_path),
        "target_size_mb": target_size_mb,
        "segments": segments
    }

    metadata_path = output_dir / "segments_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    if logger:
        logger.info(f"Metadata saved: {metadata_path}")

    return metadata
```

## transcriber.py

```python
"""Parallel audio transcription using Gemini API"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from google import genai
from google.genai import types
from tqdm import tqdm


STRICT_PROMPT = """このオーディオを文字起こししてください。

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
"""


def transcribe_segment(
    client: genai.Client,
    audio_path: Path,
    seg_name: str,
    logger: logging.Logger = None
) -> str:
    """Transcribe single audio segment"""
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    contents = [
        types.Part(text=STRICT_PROMPT),
        types.Part.from_bytes(data=audio_bytes, mime_type="audio/mpeg")
    ]

    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=contents
    )

    return response.text


def transcribe_parallel(
    segments_dir: Path,
    metadata: dict,
    parallel: int = 5,
    logger: logging.Logger = None
) -> dict:
    """Transcribe segments in parallel"""
    client = genai.Client()
    results = {}

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {}
        for seg in metadata["segments"]:
            seg_path = segments_dir / seg["file"]
            future = executor.submit(
                transcribe_segment,
                client,
                seg_path,
                seg["file"],
                logger
            )
            futures[future] = seg["file"]

        with tqdm(total=len(futures), desc="Transcribing") as pbar:
            for future in as_completed(futures):
                seg_file = futures[future]
                try:
                    results[seg_file] = future.result()
                    if logger:
                        logger.info(f"Completed: {seg_file}")
                except Exception as e:
                    if logger:
                        logger.error(f"Error transcribing {seg_file}: {e}", exc_info=True)
                    results[seg_file] = None
                pbar.update(1)

    return results
```

## timestamp_corrector.py

```python
"""Timeline correction for segmented transcripts"""

import logging
import re
from datetime import timedelta
from pathlib import Path


def correct_timestamps(transcript: str, start_offset: float) -> str:
    """Correct timestamps by adding offset"""
    def add_offset(match):
        timestamp = match.group(1)
        h, m, s = map(int, timestamp.split(':'))
        original_seconds = h * 3600 + m * 60 + s
        corrected_seconds = original_seconds + start_offset

        td = timedelta(seconds=corrected_seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        seconds = int(td.total_seconds() % 60)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    pattern = r'(\d{2}:\d{2}:\d{2})'
    corrected = re.sub(pattern, add_offset, transcript)

    return corrected


def correct_all_transcripts(
    transcripts: dict,
    metadata: dict,
    output_dir: Path,
    logger: logging.Logger = None
) -> dict:
    """Correct timestamps for all segments"""
    corrected_transcripts = {}

    for seg in metadata["segments"]:
        seg_file = seg["file"]
        if seg_file not in transcripts or transcripts[seg_file] is None:
            if logger:
                logger.warning(f"Skipping {seg_file}: no transcript")
            continue

        original = transcripts[seg_file]
        corrected = correct_timestamps(original, seg["start"])

        # Save corrected transcript
        output_path = output_dir / f"{seg_file}.corrected.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(corrected)

        corrected_transcripts[seg_file] = corrected

        if logger:
            logger.info(f"Corrected: {seg_file} (offset: {seg['start']:.2f}s)")

    return corrected_transcripts
```

## refiner.py

```python
"""Transcript refinement using Gemini API"""

import logging
from pathlib import Path
from google import genai


def refine_transcript(
    combined_transcript: str,
    output_path: Path,
    logger: logging.Logger = None
):
    """Refine transcript by removing fillers and improving readability"""
    client = genai.Client()

    prompt = f"""以下の文字起こしテキストを整形してください。

【要件】
- 話し言葉のフィラー（えー、あのー、なんか、など）を除去
- 意味を損なわず読みやすく整理
- タイムスタンプと話者ラベルは保持
- 文の構造は維持

{combined_transcript}
"""

    if logger:
        logger.info("Refining transcript with Gemini API...")

    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=prompt
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response.text)

    if logger:
        logger.info(f"Refined transcript saved: {output_path}")
```

## Usage Example

```bash
# Navigate to your audio project directory
cd /path/to/audio/project

# Run transcription
python ~/.claude/skills/transcribe-audio/transcribe_audio.py audio.mp3 --refine

# With custom options
python ~/.claude/skills/transcribe-audio/transcribe_audio.py audio.mp3 \
    --target-size 2 \
    --parallel 10 \
    --silence-thresh -35 \
    --min-silence 1.0 \
    --refine
```

## Notes

- All scripts assume they're run from the audio project directory, not the skill directory
- The skill creates `segments/`, `logs/`, and output files in the current directory
- Logs are timestamped for tracking multiple runs
- Failed segments don't stop the entire process
