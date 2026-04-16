"""slide_plan.json + 参照 .pptx から出力 .pptx を生成する。"""
import argparse
import json
import logging
import re
import shutil
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

from _common import inches_to_emu, run_official_script, setup_logging

logger = setup_logging("render")

NS: dict[str, str] = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

SMART_QUOTE_MAP: dict[str, str] = {
    "\u201c": "&#x201C;",
    "\u201d": "&#x201D;",
    "\u2018": "&#x2018;",
    "\u2019": "&#x2019;",
}


def _escape_smart_quotes(text: str) -> str:
    """スマートクォーテーションを XML エンティティに変換。"""
    for char, entity in SMART_QUOTE_MAP.items():
        text = text.replace(char, entity)
    return text


def _find_layout_rels(unpack_dir: Path, layout_id: str) -> str | None:
    """layout_id に対応する slideLayout ファイルパスを確認。"""
    layout_path = unpack_dir / "ppt" / "slideLayouts" / layout_id
    return str(layout_path) if layout_path.exists() else None


def _remove_existing_slides(unpack_dir: Path) -> None:
    """既存の全スライドを sldIdLst から除去(参照のスライドを消す)。"""
    pres_path = unpack_dir / "ppt" / "presentation.xml"
    content = pres_path.read_text(encoding="utf-8")

    content = re.sub(
        r'<p:sldIdLst>.*?</p:sldIdLst>',
        '<p:sldIdLst/>',
        content,
        flags=re.DOTALL,
    )
    pres_path.write_text(content, encoding="utf-8")


def _add_slide_from_layout(unpack_dir: Path, layout_id: str) -> tuple[str, str]:
    """レイアウトから新しいスライドを追加。add_slide.py を呼び出す。"""
    result = run_official_script("add_slide.py", [str(unpack_dir), layout_id])
    if result.returncode != 0:
        logger.error("add_slide 失敗: %s", result.stderr)
        raise RuntimeError(f"add_slide failed for {layout_id}")

    slide_match = re.search(r'Created (slide\d+\.xml)', result.stdout)
    if not slide_match:
        slide_match = re.search(r'(slide\d+\.xml)', result.stdout)
    sld_id_match = re.search(r'(<p:sldId\s+id="[^"]*"\s+r:id="[^"]*"\s*/>)', result.stdout)

    slide_file = slide_match.group(1) if slide_match else ""
    sld_id_element = sld_id_match.group(1) if sld_id_match else ""

    logger.info("Added slide: %s", slide_file)
    return slide_file, sld_id_element


def _build_text_paragraphs(texts: list[str], lang: str = "ja-JP") -> str:
    """テキストリストから <a:p> 要素群の XML 文字列を生成。"""
    paragraphs: list[str] = []
    for text in texts:
        escaped = _escape_smart_quotes(text)
        paragraphs.append(
            f'<a:p xmlns:a="{NS["a"]}">'
            f'<a:r><a:rPr lang="{lang}" dirty="0"/>'
            f'<a:t xml:space="preserve">{escaped}</a:t></a:r></a:p>'
        )
    return "\n".join(paragraphs)


def _ensure_placeholder_sp(slide_path: Path, idx: int, ph_type: str) -> None:
    """スライドに placeholder shape が無い場合、追加する。"""
    tree = ET.parse(str(slide_path))
    root = tree.getroot()

    for sp in root.iter(f"{{{NS['p']}}}sp"):
        nvSpPr = sp.find(f"{{{NS['p']}}}nvSpPr")
        if nvSpPr is None:
            continue
        nvPr = nvSpPr.find(f"{{{NS['p']}}}nvPr")
        if nvPr is None:
            continue
        ph = nvPr.find(f"{{{NS['p']}}}ph")
        if ph is None:
            continue
        existing_type = ph.get("type", "body")
        existing_idx = int(ph.get("idx", "0"))
        if ph_type in ("title", "ctrTitle") and existing_type in ("title", "ctrTitle"):
            return
        if ph_type not in ("title", "ctrTitle") and existing_idx == idx and existing_type not in ("title", "ctrTitle"):
            return

    sp_tree = root.find(f".//{{{NS['p']}}}spTree")
    if sp_tree is None:
        return

    ph_attr = f'type="{ph_type}"'
    if ph_type not in ("title", "ctrTitle"):
        ph_attr += f' idx="{idx}"'

    sp_xml = (
        f'<p:sp xmlns:p="{NS["p"]}" xmlns:a="{NS["a"]}">'
        f'<p:nvSpPr>'
        f'<p:cNvPr id="{100 + idx}" name="Placeholder {idx}"/>'
        f'<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
        f'<p:nvPr><p:ph {ph_attr}/></p:nvPr>'
        f'</p:nvSpPr>'
        f'<p:spPr/>'
        f'<p:txBody>'
        f'<a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="ja-JP"/></a:p>'
        f'</p:txBody>'
        f'</p:sp>'
    )
    sp_el = ET.fromstring(sp_xml)
    sp_tree.append(sp_el)
    tree.write(str(slide_path), xml_declaration=True, encoding="UTF-8")


def _set_placeholder_text(slide_path: Path, idx: int, texts: list[str], is_title: bool = False) -> None:
    """placeholder にテキストを流し込む。"""
    ph_type = "title" if is_title else "body"
    _ensure_placeholder_sp(slide_path, idx if not is_title else 0, ph_type)

    tree = ET.parse(str(slide_path))
    root = tree.getroot()

    for sp in root.iter(f"{{{NS['p']}}}sp"):
        nvSpPr = sp.find(f"{{{NS['p']}}}nvSpPr")
        if nvSpPr is None:
            continue
        nvPr = nvSpPr.find(f"{{{NS['p']}}}nvPr")
        if nvPr is None:
            continue
        ph = nvPr.find(f"{{{NS['p']}}}ph")
        if ph is None:
            continue

        ph_idx = int(ph.get("idx", "0"))
        existing_type = ph.get("type", "body")

        target = False
        if is_title and existing_type in ("title", "ctrTitle"):
            target = True
        elif not is_title and ph_idx == idx and existing_type not in ("title", "ctrTitle"):
            target = True

        if not target:
            continue

        txBody = sp.find(f"{{{NS['p']}}}txBody")
        if txBody is None:
            txBody = ET.SubElement(sp, f"{{{NS['a']}}}txBody")
            ET.SubElement(txBody, f"{{{NS['a']}}}bodyPr")
            ET.SubElement(txBody, f"{{{NS['a']}}}lstStyle")

        for p in list(txBody.findall(f"{{{NS['a']}}}p")):
            txBody.remove(p)

        for text_line in texts:
            p_el = ET.SubElement(txBody, f"{{{NS['a']}}}p")
            r_el = ET.SubElement(p_el, f"{{{NS['a']}}}r")
            rPr = ET.SubElement(r_el, f"{{{NS['a']}}}rPr")
            rPr.set("lang", "ja-JP")
            rPr.set("dirty", "0")
            t_el = ET.SubElement(r_el, f"{{{NS['a']}}}t")
            t_el.text = _escape_smart_quotes(text_line)
            t_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

        logger.debug("Set placeholder idx=%d with %d lines", idx, len(texts))
        break

    tree.write(str(slide_path), xml_declaration=True, encoding="UTF-8")


def _add_image_placeholder_shape(slide_path: Path, label: str, bbox: dict[str, float]) -> None:
    """灰色矩形 + ラベルの image placeholder shape を追加。"""
    tree = ET.parse(str(slide_path))
    root = tree.getroot()

    sp_tree = root.find(f".//{{{NS['p']}}}spTree")
    if sp_tree is None:
        return

    x_emu = inches_to_emu(bbox.get("x", 1))
    y_emu = inches_to_emu(bbox.get("y", 1))
    w_emu = inches_to_emu(bbox.get("w", 4))
    h_emu = inches_to_emu(bbox.get("h", 3))

    sp_xml = f'''<p:sp xmlns:p="{NS['p']}" xmlns:a="{NS['a']}" xmlns:r="{NS['r']}">
  <p:nvSpPr>
    <p:cNvPr id="9999" name="ImagePlaceholder"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="{x_emu}" y="{y_emu}"/>
      <a:ext cx="{w_emu}" cy="{h_emu}"/>
    </a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="808080"/></a:solidFill>
    <a:ln w="12700"><a:solidFill><a:srgbClr val="404040"/></a:solidFill></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr anchor="ctr" anchorCtr="1"/>
    <a:p>
      <a:pPr algn="ctr"/>
      <a:r>
        <a:rPr lang="ja-JP" sz="1200">
          <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
        </a:rPr>
        <a:t>{_escape_smart_quotes(label)}</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>'''

    sp_el = ET.fromstring(sp_xml)
    sp_tree.append(sp_el)
    tree.write(str(slide_path), xml_declaration=True, encoding="UTF-8")
    logger.debug("Added image placeholder: %s", label)


def _populate_slide(slide_path: Path, slide_plan: dict) -> None:
    """slide_plan の1スライド分をスライドXMLに適用。"""
    kind = slide_plan.get("kind", "content")

    if "title" in slide_plan:
        _set_placeholder_text(slide_path, 0, [slide_plan["title"]], is_title=True)

    if kind == "title" and "subtitle" in slide_plan:
        _set_placeholder_text(slide_path, 1, [slide_plan["subtitle"]])

    elif kind in ("content", "section_header"):
        body_texts: list[str] = []
        if "lead" in slide_plan:
            body_texts.append(slide_plan["lead"])
        if "body" in slide_plan:
            body_texts.extend(slide_plan["body"])
        if body_texts:
            _set_placeholder_text(slide_path, 1, body_texts)

    elif kind == "two_pane":
        if "lead" in slide_plan:
            _set_placeholder_text(slide_path, 1, [slide_plan["lead"]])
        panes = slide_plan.get("panes", [])
        for i, pane in enumerate(panes):
            texts = []
            if "heading" in pane:
                texts.append(pane["heading"])
            texts.extend(pane.get("bullets", []))
            _set_placeholder_text(slide_path, i + 1, texts)

    if "image_placeholder" in slide_plan:
        ip = slide_plan["image_placeholder"]
        _add_image_placeholder_shape(
            slide_path,
            ip.get("label", "[Image]"),
            ip.get("bbox_in", {"x": 1, "y": 1, "w": 4, "h": 3}),
        )


def render(
    reference_pptx: Path,
    slide_plan_path: Path,
    output_path: Path,
) -> Path:
    """slide_plan に基づいて PPTX を生成。"""
    reference_pptx = reference_pptx.resolve()
    slide_plan_path = slide_plan_path.resolve()
    output_path = output_path.resolve()

    with open(slide_plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    work_dir = Path(tempfile.mkdtemp(prefix="pptx_render_"))
    unpack_dir = work_dir / "unpacked"

    result = run_official_script("unpack.py", [str(reference_pptx), str(unpack_dir)])
    if result.returncode != 0:
        raise RuntimeError(f"unpack failed: {result.stderr}")
    logger.info("Unpacked reference to: %s", unpack_dir)

    _remove_existing_slides(unpack_dir)

    pres_path = unpack_dir / "ppt" / "presentation.xml"
    sld_id_entries: list[str] = []
    next_sld_id = 256

    for slide_spec in plan["slides"]:
        layout_id = slide_spec["layout_id"]
        slide_file, sld_id_el = _add_slide_from_layout(unpack_dir, layout_id)

        if sld_id_el:
            sld_id_el = re.sub(r'id="\d+"', f'id="{next_sld_id}"', sld_id_el, count=1)
            sld_id_entries.append(sld_id_el)
            next_sld_id += 1

        slide_path = unpack_dir / "ppt" / "slides" / slide_file
        if slide_path.exists():
            _populate_slide(slide_path, slide_spec)

    if sld_id_entries:
        pres_content = pres_path.read_text(encoding="utf-8")
        sld_list_content = "\n    ".join(sld_id_entries)
        pres_content = pres_content.replace(
            "<p:sldIdLst/>",
            f"<p:sldIdLst>\n    {sld_list_content}\n  </p:sldIdLst>",
        )
        pres_path.write_text(pres_content, encoding="utf-8")

    clean_result = run_official_script("clean.py", [str(unpack_dir)])
    if clean_result.returncode != 0:
        logger.warning("clean.py warning: %s", clean_result.stderr)

    pack_result = run_official_script("pack.py", [
        str(unpack_dir), str(output_path), "--original", str(reference_pptx),
    ])
    if pack_result.returncode != 0:
        error_detail = pack_result.stderr or pack_result.stdout
        logger.error("pack.py failed: %s", error_detail)
        raise RuntimeError(f"pack failed: {error_detail}")

    logger.info("Output saved to: %s", output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="slide_plan + 参照 pptx → 出力 pptx")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--log-file", type=str, default=None)
    args = parser.parse_args()

    if args.log_file:
        setup_logging("render", args.log_file)

    render(args.reference, args.plan, args.output)


if __name__ == "__main__":
    main()
