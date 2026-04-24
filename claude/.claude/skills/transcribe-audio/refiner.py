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
