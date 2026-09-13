"""セル画像から数字（1〜9）を認識する。

old/sudoku-test.ipynb での検証により EasyOCR 単体は精度が低いと判明しているため、
まずは pytesseract（--psm 10: 単一文字モード）を採用する。
グリッド線の写り込みは cells.remove_border で事前に切り落とす前提。
"""

import cv2
import numpy as np
import pytesseract

from sudoku_solver.cells import remove_border

_TESSERACT_CONFIG = "--psm 10 -c tessedit_char_whitelist=123456789"


def recognize_digit(cell: np.ndarray) -> int:
    """セル画像から数字を1つ認識する。読み取れない場合は0（空白）を返す。"""
    inner = remove_border(cell)
    if inner.size == 0:
        return 0

    resized = cv2.resize(inner, (56, 56), interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    text = pytesseract.image_to_string(thresh, config=_TESSERACT_CONFIG).strip()
    return int(text) if text.isdigit() and text != "0" else 0


def recognize_grid(cell_rows: list[list[np.ndarray]], is_blank) -> list[list[int]]:
    """9x9のセル画像から数独盤面（2次元リスト、空白は0）を認識する。

    is_blank: cell画像を受け取り空白かどうかを返す関数（cells.is_blank_cellを想定）。
    """
    grid = [[0] * 9 for _ in range(9)]
    for i, row in enumerate(cell_rows):
        for j, cell in enumerate(row):
            if is_blank(cell):
                continue
            grid[i][j] = recognize_digit(cell)
    return grid
