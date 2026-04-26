"""pptx-from-reference 汎用ライブラリ

PPTXテンプレート作成のための再利用可能な関数群
"""

from .core import set_text_preserve_style, remove_slide
from .shapes import find_shape_by_id, add_placeholder_rect, remove_shape_by_id, detect_text_style
from .tables import extract_table_structure, convert_table_to_placeholder, placeholderize_table_cell, convert_table_to_placeholder_with_details

__all__ = [
    'set_text_preserve_style',
    'remove_slide',
    'find_shape_by_id',
    'add_placeholder_rect',
    'remove_shape_by_id',
    'detect_text_style',
    'extract_table_structure',
    'convert_table_to_placeholder',
    'placeholderize_table_cell',
    'convert_table_to_placeholder_with_details',
]
