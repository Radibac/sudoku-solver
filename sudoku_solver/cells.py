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
    """セルの外周を固定比率で切り落とす（罫線が薄い場合の簡易フォールバック用）。"""
    h, w = cell.shape[:2]
    by, bx = int(h * border_ratio), int(w * border_ratio)
    return cell[by:h - by, bx:w - bx]


def remove_grid_lines(cell: np.ndarray, brightness_threshold: int = 200) -> np.ndarray:
    """セル四辺から内側へスキャンし、辺に接する暗い画素（グリッド線）を白く塗りつぶす。

    盤面の外枠は3x3ブロックの内側の罫線より太く描かれることが多く、
    remove_border のような固定比率のクロップでは太い外枠を除去しきれないことがある。
    この関数は罫線の太さに関わらず、各辺から連続する暗い画素だけを消していく。
    """
    result = cell.copy()
    h, w = result.shape[:2]

    for x in range(w):
        y = 0
        while y < h and result[y, x] < brightness_threshold:
            result[y, x] = 255
            y += 1
        y = h - 1
        while y >= 0 and result[y, x] < brightness_threshold:
            result[y, x] = 255
            y -= 1

    for y in range(h):
        x = 0
        while x < w and result[y, x] < brightness_threshold:
            result[y, x] = 255
            x += 1
        x = w - 1
        while x >= 0 and result[y, x] < brightness_threshold:
            result[y, x] = 255
            x -= 1

    return result


def is_blank_cell(
    cell: np.ndarray,
    darkness_threshold: int = 150,
    dark_pixel_ratio_threshold: float = 0.03,
) -> bool:
    """セルが空白（数字が書かれていない）かどうかを暗画素の比率で判定する。

    Otsu二値化は「ほぼ均一に明るいだけ」の空白セルに対しても無理に閾値を作ってしまい、
    JPEGノイズなどのわずかな暗みを誤って前景と判定しがちなので、固定の明度閾値を使う。
    グリッド線の写り込みを避けるため、判定前に remove_grid_lines と外周クロップを適用する。
    """
    cleaned = remove_border(remove_grid_lines(cell))
    if cleaned.size == 0:
        return True

    dark_ratio = float(np.count_nonzero(cleaned < darkness_threshold)) / cleaned.size
    return dark_ratio < dark_pixel_ratio_threshold
