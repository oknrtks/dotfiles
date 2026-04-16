"""参照 .pptx から visual_profile.json を抽出する。"""
import argparse
import json
import logging
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from _common import emu_to_inches, setup_logging

logger = setup_logging("profile_visual")

NS: dict[str, str] = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def _register_ns() -> None:
    for prefix, uri in NS.items():
        ET.register_namespace(prefix, uri)


def _parse_xml(path: Path) -> ET.Element:
    """XML ファイルをパースして root を返す。"""
    return ET.parse(str(path)).getroot()


def _extract_color_scheme(theme_root: ET.Element) -> dict[str, str]:
    """<a:clrScheme> から色を抽出。"""
    scheme: dict[str, str] = {}
    clr_scheme = theme_root.find(".//a:clrScheme", NS)
    if clr_scheme is None:
        return scheme

    color_names = [
        "dk1", "lt1", "dk2", "lt2",
        "accent1", "accent2", "accent3", "accent4", "accent5", "accent6",
        "hlink", "folHlink",
    ]
    name_map = {"dk1": "tx1", "lt1": "bg1", "dk2": "tx2", "lt2": "bg2"}

    for name in color_names:
        el = clr_scheme.find(f"a:{name}", NS)
        if el is None:
            continue
        srgb = el.find("a:srgbClr", NS)
        if srgb is not None:
            val = srgb.get("val", "")
        else:
            sys_clr = el.find("a:sysClr", NS)
            val = sys_clr.get("lastClr", "") if sys_clr is not None else ""
        key = name_map.get(name, name)
        if val:
            scheme[key] = val
    return scheme


def _extract_font_scheme(theme_root: ET.Element) -> dict[str, str]:
    """<a:fontScheme> からフォントを抽出。"""
    fonts: dict[str, str] = {}
    font_scheme = theme_root.find(".//a:fontScheme", NS)
    if font_scheme is None:
        return fonts

    for kind in ("majorFont", "minorFont"):
        font_el = font_scheme.find(f"a:{kind}", NS)
        if font_el is None:
            continue
        prefix = "major" if "major" in kind else "minor"
        latin = font_el.find("a:latin", NS)
        if latin is not None:
            fonts[f"{prefix}_latin"] = latin.get("typeface", "")
        ea = font_el.find("a:ea", NS)
        if ea is not None:
            fonts[f"{prefix}_ea"] = ea.get("typeface", "")
    return fonts


def _extract_default_sizes(slide_master_path: Path) -> dict[str, float]:
    """スライドマスタの placeholder からデフォルトフォントサイズを抽出。"""
    sizes: dict[str, float] = {}
    if not slide_master_path.exists():
        return sizes

    root = _parse_xml(slide_master_path)
    for sp in root.iter(f"{{{NS['p']}}}sp"):
        nvSpPr = sp.find(f"{{{NS['p']}}}nvSpPr", NS)
        if nvSpPr is None:
            continue
        nvPr = nvSpPr.find(f"{{{NS['p']}}}nvPr")
        if nvPr is None:
            continue
        ph = nvPr.find(f"{{{NS['p']}}}ph")
        if ph is None:
            continue
        ph_type = ph.get("type", "body")
        txBody = sp.find(f"{{{NS['p']}}}txBody")
        if txBody is None:
            continue
        for rPr in txBody.iter(f"{{{NS['a']}}}defRPr"):
            sz = rPr.get("sz")
            if sz:
                size_pt = int(sz) / 100
                if ph_type in ("title", "ctrTitle"):
                    sizes.setdefault("title", size_pt)
                else:
                    sizes.setdefault("body", size_pt)
    return sizes


def _extract_slide_size(presentation_path: Path) -> dict[str, float]:
    """presentation.xml からスライドサイズを抽出。"""
    root = _parse_xml(presentation_path)
    sld_sz = root.find(f"{{{NS['p']}}}sldSz")
    if sld_sz is None:
        return {"w": 13.333, "h": 7.5}
    cx = int(sld_sz.get("cx", "0"))
    cy = int(sld_sz.get("cy", "0"))
    return {"w": emu_to_inches(cx), "h": emu_to_inches(cy)}


def _extract_placeholder_info(sp_el: ET.Element) -> dict | None:
    """shape 要素から placeholder 情報を抽出。"""
    nvSpPr = sp_el.find(f"{{{NS['p']}}}nvSpPr")
    if nvSpPr is None:
        return None
    nvPr = nvSpPr.find(f"{{{NS['p']}}}nvPr")
    if nvPr is None:
        return None
    ph = nvPr.find(f"{{{NS['p']}}}ph")
    if ph is None:
        return None

    idx = int(ph.get("idx", "0"))
    ph_type = ph.get("type", "body")

    spPr = sp_el.find(f"{{{NS['p']}}}spPr")
    bbox: dict[str, float] = {"x": 0, "y": 0, "w": 0, "h": 0}
    if spPr is not None:
        xfrm = spPr.find(f"{{{NS['a']}}}xfrm")
        if xfrm is not None:
            off = xfrm.find(f"{{{NS['a']}}}off")
            ext = xfrm.find(f"{{{NS['a']}}}ext")
            if off is not None:
                bbox["x"] = emu_to_inches(int(off.get("x", "0")))
                bbox["y"] = emu_to_inches(int(off.get("y", "0")))
            if ext is not None:
                bbox["w"] = emu_to_inches(int(ext.get("cx", "0")))
                bbox["h"] = emu_to_inches(int(ext.get("cy", "0")))

    return {"idx": idx, "type": ph_type, "bbox_in": bbox}


def _extract_layouts(layouts_dir: Path) -> list[dict]:
    """slideLayouts/ から全レイアウト情報を抽出。"""
    layouts: list[dict] = []
    if not layouts_dir.exists():
        return layouts

    for layout_file in sorted(layouts_dir.glob("slideLayout*.xml")):
        root = _parse_xml(layout_file)
        cSld = root.find(f"{{{NS['p']}}}cSld")
        name = cSld.get("name", "") if cSld is not None else ""

        placeholders: list[dict] = []
        decorative_count = 0
        sp_tree = root.find(f".//{{{NS['p']}}}spTree")
        if sp_tree is not None:
            for sp in sp_tree.findall(f"{{{NS['p']}}}sp"):
                ph_info = _extract_placeholder_info(sp)
                if ph_info:
                    placeholders.append(ph_info)
                else:
                    decorative_count += 1

        layouts.append({
            "id": layout_file.name,
            "name": name,
            "placeholders": placeholders,
            "decorative_shapes_count": decorative_count,
        })
    return layouts


def extract_visual_profile(pptx_path: Path, unpack_dir: Path) -> dict:
    """参照 .pptx の unpack 済みディレクトリから visual_profile を抽出。"""
    ppt_dir = unpack_dir / "ppt"

    theme_path = ppt_dir / "theme" / "theme1.xml"
    theme_root = _parse_xml(theme_path) if theme_path.exists() else None

    color_scheme = _extract_color_scheme(theme_root) if theme_root is not None else {}
    font_scheme = _extract_font_scheme(theme_root) if theme_root is not None else {}

    master_files = sorted((ppt_dir / "slideMasters").glob("slideMaster*.xml")) if (ppt_dir / "slideMasters").exists() else []
    default_sizes = _extract_default_sizes(master_files[0]) if master_files else {}

    slide_size = _extract_slide_size(ppt_dir / "presentation.xml")
    layouts = _extract_layouts(ppt_dir / "slideLayouts")

    return {
        "source_file": str(pptx_path.name),
        "theme": {
            "color_scheme": color_scheme,
            "font_scheme": font_scheme,
            "default_size_pt": default_sizes,
        },
        "layouts": layouts,
        "slide_size_in": slide_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="参照 .pptx から visual_profile.json を抽出")
    parser.add_argument("pptx_path", type=Path, help="参照 .pptx ファイル")
    parser.add_argument("--unpack-dir", type=Path, default=None, help="unpack 済みディレクトリ(省略時は自動 unpack)")
    parser.add_argument("--output", type=Path, default=Path("visual_profile.json"), help="出力先")
    parser.add_argument("--log-file", type=str, default=None, help="ログファイルパス")
    args = parser.parse_args()

    if args.log_file:
        setup_logging("profile_visual", args.log_file)

    pptx_path: Path = args.pptx_path.resolve()
    if not pptx_path.exists():
        logger.error("ファイルが見つかりません: %s", pptx_path)
        sys.exit(1)

    import tempfile
    if args.unpack_dir:
        unpack_dir = args.unpack_dir
    else:
        unpack_dir = Path(tempfile.mkdtemp(prefix="pptx_ref_visual_"))
        from _common import run_official_script
        result = run_official_script("unpack.py", [str(pptx_path), str(unpack_dir)])
        if result.returncode != 0:
            logger.error("unpack 失敗: %s", result.stderr)
            sys.exit(1)
        logger.info("Unpacked to: %s", unpack_dir)

    profile = extract_visual_profile(pptx_path, unpack_dir)

    args.output.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Visual profile saved to: %s", args.output)
    print(json.dumps(profile, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
