"""PDF を各ページの PNG に変換する(Poppler pdftoppm 使用)。"""
import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

from _common import setup_logging

logger = setup_logging("rasterize_pdf")

DEFAULT_DPI: int = 150
MAX_PAGES: int = 30


def rasterize_pdf(
    pdf_path: Path,
    output_dir: Path,
    dpi: int = DEFAULT_DPI,
    max_pages: int = MAX_PAGES,
) -> list[str]:
    """PDF を各ページ PNG に変換し、パスのリストを返す。"""
    if not shutil.which("pdftoppm"):
        logger.error("pdftoppm が見つかりません。poppler-utils をインストールしてください。")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / "page"

    cmd = [
        "pdftoppm",
        "-png",
        "-r", str(dpi),
        "-l", str(max_pages),
        str(pdf_path),
        str(prefix),
    ]
    logger.info("Running: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        logger.error("pdftoppm 失敗: %s", result.stderr)
        return []

    images = sorted(output_dir.glob("page-*.png"))
    paths = [str(p) for p in images]
    logger.info("Generated %d page images", len(paths))
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF を各ページ PNG に変換")
    parser.add_argument("pdf_path", type=Path, help="入力 PDF ファイル")
    parser.add_argument("--output-dir", type=Path, default=Path("/tmp/pdf_pages"))
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    parser.add_argument("--max-pages", type=int, default=MAX_PAGES)
    args = parser.parse_args()

    paths = rasterize_pdf(args.pdf_path, args.output_dir, args.dpi, args.max_pages)
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
