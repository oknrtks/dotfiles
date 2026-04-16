"""参照 .pptx + .pdf から voice_profile.json を抽出する。"""
import argparse
import json
import logging
import statistics
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from _common import setup_logging

logger = setup_logging("profile_voice")

NS: dict[str, str] = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}

MAX_SAMPLE_SLIDES: int = 20


def _count_bullets_in_slide(root: ET.Element) -> tuple[int, int]:
    """箇条書き数と最大深さを返す。"""
    bullet_count = 0
    max_depth = 0
    for txBody in root.iter(f"{{{NS['a']}}}txBody"):
        for p in txBody.findall(f"{{{NS['a']}}}p"):
            pPr = p.find(f"{{{NS['a']}}}pPr")
            if pPr is not None:
                lvl = int(pPr.get("lvl", "0"))
                buNone = pPr.find(f"{{{NS['a']}}}buNone")
                if buNone is None:
                    buChar = pPr.find(f"{{{NS['a']}}}buChar")
                    buAutoNum = pPr.find(f"{{{NS['a']}}}buAutoNum")
                    if buChar is not None or buAutoNum is not None or lvl > 0:
                        bullet_count += 1
                        max_depth = max(max_depth, lvl + 1)
    return bullet_count, max_depth


def _extract_texts_from_slide(root: ET.Element) -> tuple[str, list[str]]:
    """スライドからタイトルとボディテキストを抽出。"""
    title = ""
    body_texts: list[str] = []

    for sp in root.iter(f"{{{NS['p']}}}sp"):
        nvSpPr = sp.find(f"{{{NS['p']}}}nvSpPr")
        if nvSpPr is None:
            continue
        nvPr = nvSpPr.find(f"{{{NS['p']}}}nvPr")
        if nvPr is None:
            continue
        ph = nvPr.find(f"{{{NS['p']}}}ph")

        texts: list[str] = []
        txBody = sp.find(f"{{{NS['p']}}}txBody")
        if txBody is not None:
            for p_el in txBody.findall(f"{{{NS['a']}}}p"):
                runs = p_el.findall(f".//{{{NS['a']}}}t")
                line = "".join(r.text or "" for r in runs).strip()
                if line:
                    texts.append(line)

        if ph is not None:
            ph_type = ph.get("type", "body")
            if ph_type in ("title", "ctrTitle"):
                title = " ".join(texts)
            else:
                body_texts.extend(texts)
        elif texts:
            body_texts.extend(texts)

    return title, body_texts


def _count_shapes(root: ET.Element) -> int:
    """shape 数を返す。"""
    sp_tree = root.find(f".//{{{NS['p']}}}spTree")
    if sp_tree is None:
        return 0
    count = 0
    for tag in ("sp", "pic", "graphicFrame", "grpSp", "cxnSp"):
        count += len(sp_tree.findall(f"{{{NS['p']}}}{tag}"))
    return count


def extract_voice_profile(
    pptx_path: Path,
    unpack_dir: Path,
    pdf_images: list[str],
    max_samples: int = MAX_SAMPLE_SLIDES,
) -> dict:
    """voice_profile を抽出。"""
    slides_dir = unpack_dir / "ppt" / "slides"
    slide_files = sorted(slides_dir.glob("slide*.xml"), key=lambda f: int("".join(c for c in f.stem if c.isdigit()) or "0"))

    if len(slide_files) > max_samples:
        slide_files = slide_files[:max_samples]

    chars_per_slide: list[int] = []
    bullets_per_slide: list[int] = []
    max_bullet_depth = 0
    title_lengths: list[int] = []
    shapes_per_slide: list[int] = []
    text_samples: list[dict] = []

    for i, sf in enumerate(slide_files, 1):
        root = ET.parse(str(sf)).getroot()

        title, body_texts = _extract_texts_from_slide(root)
        all_text = title + " " + " ".join(body_texts)
        chars_per_slide.append(len(all_text.strip()))

        bc, md = _count_bullets_in_slide(root)
        bullets_per_slide.append(bc)
        max_bullet_depth = max(max_bullet_depth, md)

        title_lengths.append(len(title))
        shapes_per_slide.append(_count_shapes(root))

        text_samples.append({
            "n": i,
            "title": title,
            "body_texts": body_texts,
        })

    return {
        "source_file": str(pptx_path.name),
        "sample_slide_count": len(slide_files),
        "pdf_page_images": pdf_images,
        "raw_stats": {
            "avg_chars_per_slide": round(statistics.mean(chars_per_slide), 1) if chars_per_slide else 0,
            "bullet_count_per_slide_median": statistics.median(bullets_per_slide) if bullets_per_slide else 0,
            "max_bullet_depth": max_bullet_depth,
            "title_length_median": statistics.median(title_lengths) if title_lengths else 0,
            "shape_count_per_slide_median": statistics.median(shapes_per_slide) if shapes_per_slide else 0,
        },
        "text_samples_per_slide": text_samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="参照 .pptx + .pdf から voice_profile.json を抽出")
    parser.add_argument("pptx_path", type=Path, help="参照 .pptx ファイル")
    parser.add_argument("pdf_path", type=Path, help="参照 .pdf ファイル")
    parser.add_argument("--unpack-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path("voice_profile.json"))
    parser.add_argument("--image-output-dir", type=Path, default=None)
    parser.add_argument("--sample-slides", type=int, default=MAX_SAMPLE_SLIDES)
    parser.add_argument("--log-file", type=str, default=None)
    args = parser.parse_args()

    if args.log_file:
        setup_logging("profile_voice", args.log_file)

    pptx_path: Path = args.pptx_path.resolve()
    pdf_path: Path = args.pdf_path.resolve()

    if not pptx_path.exists():
        logger.error("pptx が見つかりません: %s", pptx_path)
        sys.exit(1)
    if not pdf_path.exists():
        logger.error("pdf が見つかりません: %s", pdf_path)
        sys.exit(1)

    import tempfile
    if args.unpack_dir:
        unpack_dir = args.unpack_dir
    else:
        unpack_dir = Path(tempfile.mkdtemp(prefix="pptx_ref_voice_"))
        from _common import run_official_script
        result = run_official_script("unpack.py", [str(pptx_path), str(unpack_dir)])
        if result.returncode != 0:
            logger.error("unpack 失敗: %s", result.stderr)
            sys.exit(1)

    image_dir = args.image_output_dir or Path(tempfile.mkdtemp(prefix="pptx_ref_pdf_"))
    from rasterize_pdf import rasterize_pdf
    pdf_images = rasterize_pdf(pdf_path, image_dir)

    profile = extract_voice_profile(pptx_path, unpack_dir, pdf_images, args.sample_slides)

    args.output.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Voice profile saved to: %s", args.output)
    print(json.dumps(profile, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
