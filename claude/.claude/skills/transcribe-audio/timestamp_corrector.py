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
