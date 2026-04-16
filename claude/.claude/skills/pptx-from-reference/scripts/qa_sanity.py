"""Phase 5 Sanity Check: 6 項目の品質チェック。"""
import argparse
import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from _common import emu_to_inches, run_official_script, setup_logging

logger = setup_logging("qa_sanity")

NS: dict[str, str] = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}

PLACEHOLDER_REGEX = re.compile(
    r'lorem|ipsum|TODO|\[insert|placeholder',
    re.IGNORECASE,
)


class CheckResult:
    """1 項目のチェック結果。"""
    def __init__(self, name: str, status: str, message: str = "") -> None:
        self.name: str = name
        self.status: str = status  # "Pass", "Fail", "Warning"
        self.message: str = message

    def to_dict(self) -> dict:
        return {"name": self.name, "status": self.status, "message": self.message}


def check_placeholder_residue(output_pptx: Path) -> CheckResult:
    """(a) プレースホルダ残骸検出。"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "markitdown", str(output_pptx)],
            capture_output=True, text=True, timeout=30,
        )
        text = result.stdout
    except Exception:
        from _common import run_official_script
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="qa_text_"))
        result = run_official_script("unpack.py", [str(output_pptx), str(tmp)])
        texts = []
        for xml_file in (tmp / "ppt" / "slides").glob("slide*.xml"):
            tree = ET.parse(str(xml_file))
            for t in tree.iter(f"{{{NS['a']}}}t"):
                if t.text:
                    texts.append(t.text)
        text = " ".join(texts)

    matches = PLACEHOLDER_REGEX.findall(text)
    if matches:
        return CheckResult("placeholder_residue", "Fail", f"残骸検出: {matches[:5]}")
    return CheckResult("placeholder_residue", "Pass")


def check_theme_unchanged(output_pptx: Path, reference_pptx: Path) -> CheckResult:
    """(b) テーマ XML 無改変。"""
    import tempfile
    import zipfile

    def extract_theme_elements(pptx_path: Path) -> tuple[str, str]:
        with zipfile.ZipFile(str(pptx_path), 'r') as zf:
            try:
                theme_xml = zf.read("ppt/theme/theme1.xml").decode("utf-8")
            except KeyError:
                return ("", "")
        root = ET.fromstring(theme_xml)
        clr = root.find(".//a:clrScheme", {"a": NS["a"]})
        font = root.find(".//a:fontScheme", {"a": NS["a"]})
        clr_str = ET.tostring(clr, encoding="unicode") if clr is not None else ""
        font_str = ET.tostring(font, encoding="unicode") if font is not None else ""
        return (clr_str, font_str)

    try:
        ref_clr, ref_font = extract_theme_elements(reference_pptx)
        out_clr, out_font = extract_theme_elements(output_pptx)
    except Exception as e:
        return CheckResult("theme_unchanged", "Fail", str(e))

    if ref_clr != out_clr:
        return CheckResult("theme_unchanged", "Fail", "clrScheme が変更されています")
    if ref_font != out_font:
        return CheckResult("theme_unchanged", "Fail", "fontScheme が変更されています")
    return CheckResult("theme_unchanged", "Pass")


def check_layout_ids_exist(plan_path: Path, visual_profile_path: Path) -> CheckResult:
    """(c) レイアウト ID の実在確認。"""
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)
    with open(visual_profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)

    available_ids = {layout["id"] for layout in profile.get("layouts", [])}
    missing = []
    for slide in plan.get("slides", []):
        lid = slide.get("layout_id", "")
        if lid not in available_ids:
            missing.append(lid)

    if missing:
        return CheckResult("layout_ids_exist", "Fail", f"存在しないレイアウト: {missing}")
    return CheckResult("layout_ids_exist", "Pass")


def check_text_overflow(output_pptx: Path, visual_profile_path: Path) -> CheckResult:
    """(d) テキストオーバーフロー推定。"""
    import zipfile

    with open(visual_profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)

    layout_ph_map: dict[str, list[dict]] = {}
    for layout in profile.get("layouts", []):
        layout_ph_map[layout["id"]] = layout.get("placeholders", [])

    default_body_pt = profile.get("theme", {}).get("default_size_pt", {}).get("body", 14)
    warnings: list[str] = []

    try:
        with zipfile.ZipFile(str(output_pptx), 'r') as zf:
            for name in zf.namelist():
                if not name.startswith("ppt/slides/slide") or not name.endswith(".xml"):
                    continue
                xml_content = zf.read(name).decode("utf-8")
                root = ET.fromstring(xml_content)

                for sp in root.iter(f"{{{NS['p']}}}sp"):
                    txBody = sp.find(f"{{{NS['p']}}}txBody")
                    if txBody is None:
                        continue
                    total_chars = sum(
                        len(t.text or "") for t in txBody.iter(f"{{{NS['a']}}}t")
                    )
                    spPr = sp.find(f"{{{NS['p']}}}spPr")
                    if spPr is None:
                        continue
                    xfrm = spPr.find(f"{{{NS['a']}}}xfrm")
                    if xfrm is None:
                        continue
                    ext = xfrm.find(f"{{{NS['a']}}}ext")
                    if ext is None:
                        continue

                    w_in = emu_to_inches(int(ext.get("cx", "0")))
                    h_in = emu_to_inches(int(ext.get("cy", "0")))
                    if w_in <= 0 or h_in <= 0:
                        continue

                    chars_per_line = max(1, w_in * 72 / default_body_pt)
                    line_height = default_body_pt * 1.5 / 72
                    est_lines = total_chars / chars_per_line
                    est_height = est_lines * line_height

                    if est_height > h_in * 1.2:
                        warnings.append(f"{name}: ~{total_chars} chars, est {est_height:.1f}in > {h_in:.1f}in")
    except Exception as e:
        return CheckResult("text_overflow", "Warning", f"チェック失敗: {e}")

    if warnings:
        return CheckResult("text_overflow", "Warning", "; ".join(warnings[:3]))
    return CheckResult("text_overflow", "Pass")


def check_image_bbox(output_pptx: Path, visual_profile_path: Path) -> CheckResult:
    """(e) 画像 bbox のスライド内収束。"""
    import zipfile

    with open(visual_profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)
    slide_w = profile.get("slide_size_in", {}).get("w", 13.333)
    slide_h = profile.get("slide_size_in", {}).get("h", 7.5)

    violations: list[str] = []
    try:
        with zipfile.ZipFile(str(output_pptx), 'r') as zf:
            for name in zf.namelist():
                if not name.startswith("ppt/slides/slide") or not name.endswith(".xml"):
                    continue
                xml_content = zf.read(name).decode("utf-8")
                root = ET.fromstring(xml_content)

                for pic in root.iter(f"{{{NS['p']}}}pic"):
                    spPr = pic.find(f".//{{{NS['p']}}}spPr")
                    if spPr is None:
                        spPr = pic.find(f".//{{{NS['a']}}}spPr")
                    if spPr is None:
                        continue
                    xfrm = spPr.find(f"{{{NS['a']}}}xfrm")
                    if xfrm is None:
                        continue
                    off = xfrm.find(f"{{{NS['a']}}}off")
                    ext = xfrm.find(f"{{{NS['a']}}}ext")
                    if off is None or ext is None:
                        continue

                    x = emu_to_inches(int(off.get("x", "0")))
                    y = emu_to_inches(int(off.get("y", "0")))
                    w = emu_to_inches(int(ext.get("cx", "0")))
                    h = emu_to_inches(int(ext.get("cy", "0")))

                    if x < 0 or y < 0 or x + w > slide_w or y + h > slide_h:
                        violations.append(f"{name}: ({x},{y},{w},{h}) outside slide")
    except Exception as e:
        return CheckResult("image_bbox", "Fail", str(e))

    if violations:
        return CheckResult("image_bbox", "Fail", "; ".join(violations[:3]))
    return CheckResult("image_bbox", "Pass")


def check_pack_success(output_pptx: Path) -> CheckResult:
    """(f) pack.py 成功(出力ファイルの存在と妥当性)。"""
    if not output_pptx.exists():
        return CheckResult("pack_success", "Fail", "出力ファイルが存在しません")
    if output_pptx.stat().st_size < 1024:
        return CheckResult("pack_success", "Fail", "出力ファイルが小さすぎます")

    import zipfile
    try:
        with zipfile.ZipFile(str(output_pptx), 'r') as zf:
            if "[Content_Types].xml" not in zf.namelist():
                return CheckResult("pack_success", "Fail", "[Content_Types].xml が見つかりません")
    except zipfile.BadZipFile:
        return CheckResult("pack_success", "Fail", "不正な ZIP ファイルです")

    return CheckResult("pack_success", "Pass")


def run_sanity_checks(
    output_pptx: Path,
    reference_pptx: Path,
    plan_path: Path,
    visual_profile_path: Path,
) -> list[CheckResult]:
    """全 6 項目の Sanity Check を実行。"""
    results: list[CheckResult] = []

    results.append(check_pack_success(output_pptx))
    if results[-1].status == "Fail":
        return results

    results.append(check_placeholder_residue(output_pptx))
    results.append(check_theme_unchanged(output_pptx, reference_pptx))
    results.append(check_layout_ids_exist(plan_path, visual_profile_path))
    results.append(check_text_overflow(output_pptx, visual_profile_path))
    results.append(check_image_bbox(output_pptx, visual_profile_path))

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 5 Sanity Check")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--visual-profile", type=Path, required=True)
    parser.add_argument("--log-file", type=str, default=None)
    args = parser.parse_args()

    if args.log_file:
        setup_logging("qa_sanity", args.log_file)

    results = run_sanity_checks(args.output, args.reference, args.plan, args.visual_profile)

    report: dict[str, list[dict]] = {"checks": [r.to_dict() for r in results]}

    fails = [r for r in results if r.status == "Fail"]
    warnings = [r for r in results if r.status == "Warning"]
    passes = [r for r in results if r.status == "Pass"]

    report["summary"] = {
        "total": len(results),
        "pass": len(passes),
        "fail": len(fails),
        "warning": len(warnings),
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if fails:
        logger.error("Sanity Check FAILED: %d failures", len(fails))
        sys.exit(1)
    elif warnings:
        logger.warning("Sanity Check PASSED with %d warnings", len(warnings))
    else:
        logger.info("Sanity Check ALL PASSED")


if __name__ == "__main__":
    main()
