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
