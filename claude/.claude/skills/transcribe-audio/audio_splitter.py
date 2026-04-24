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
