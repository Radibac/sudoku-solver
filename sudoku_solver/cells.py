"""正面ビューに補正した盤面画像を9x9のセルに分割し、空白セルを判定する。"""

import cv2
import numpy as np


def split_into_cells(warped_image: np.ndarray) -> list[list[np.ndarray]]:
    """warped_image（正方形の盤面画像）を9x9のセル画像のリストに分割する。"""
    size = warped_image.shape[0]
    cell_size = size // 9

    rows = []
    for i in range(9):
        row = []
        for j in range(9):
            y, x = i * cell_size, j * cell_size
            row.append(warped_image[y:y + cell_size, x:x + cell_size])
        rows.append(row)
    return rows


def remove_border(cell: np.ndarray, border_ratio: float = 0.12) -> np.ndarray:
    """セルの外周（グリッド線が残りやすい部分）を切り落とす。"""
    h, w = cell.shape[:2]
    by, bx = int(h * border_ratio), int(w * border_ratio)
    return cell[by:h - by, bx:w - bx]


def is_blank_cell(cell: np.ndarray, black_pixel_ratio_threshold: float = 0.02) -> bool:
    """セルが空白（数字が書かれていない）かどうかを黒画素の比率で判定する。

    グリッド線の写り込みを避けるため、判定前に外周を切り落とす。
    """
    inner = remove_border(cell)
    if inner.size == 0:
        return True

    _, thresh = cv2.threshold(inner, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    black_ratio = float(np.count_nonzero(thresh)) / thresh.size
    return black_ratio < black_pixel_ratio_threshold
