#!/usr/bin/env python3
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
        skill_dir = Path(__file__).parent
        sys.path.insert(0, str(skill_dir))

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
