"""Shape操作ヘルパー関数

shape検索、座標取得、Placeholder長方形追加等の機能
"""

import logging
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.util import Pt


def find_shape_by_id(slide, shape_id: int):
    """shape_idからshapeを見つける

    Args:
        slide: スライドオブジェクト
        shape_id: 検索するshape_id

    Returns:
        見つかったshapeオブジェクト。見つからない場合はNone。
    """
    for shape in slide.shapes:
        if shape.shape_id == shape_id:
            return shape
    return None


def get_shape_bounds(shape):
    """shapeの座標とサイズを取得

    Args:
        shape: シェイプオブジェクト

    Returns:
        (left, top, width, height) のタプル（EMU単位）
    """
    return (shape.left, shape.top, shape.width, shape.height)


def remove_shape_by_id(slide, shape_id: int) -> bool:
    """shape_idで指定したshapeを削除

    Args:
        slide: スライドオブジェクト
        shape_id: 削除するshape_id

    Returns:
        削除成功時はTrue、shapeが見つからない場合はFalse
    """
    shape = find_shape_by_id(slide, shape_id)
    if shape:
        slide.shapes._spTree.remove(shape.element)
        logging.info(f'Removed shape id={shape_id}')
        return True
    return False


def add_placeholder_rect(slide, left, top, width, height, text: str):
    """Placeholder長方形を追加（図領域代替用）

    視認性を確保するため、薄いグレー背景とグレー枠線を設定。

    Args:
        slide: スライドオブジェクト
        left: 左位置（EMU単位）
        top: 上位置（EMU単位）
        width: 幅（EMU単位）
        height: 高さ（EMU単位）
        text: Placeholderテキスト

    Returns:
        作成されたshapeオブジェクト
    """
    shape = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
        left, top, width, height
    )

    # 薄いグレー背景（視認性確保）
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(240, 240, 240)

    # グレー枠線
    shape.line.color.rgb = RGBColor(150, 150, 150)
    shape.line.width = Pt(1)

    # テキスト設定
    if shape.has_text_frame:
        text_frame = shape.text_frame
        text_frame.word_wrap = True
        p = text_frame.paragraphs[0]
        p.text = text

        # フォント設定（見やすいサイズと色）
        for run in p.runs:
            run.font.size = Pt(14)
            run.font.color.rgb = RGBColor(80, 80, 80)

    logging.info(f'Added placeholder rect at left={left}, top={top}, w={width}, h={height}')
    return shape
