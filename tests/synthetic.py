"""実写真1枚から「余白のある写真らしい画像」を合成するヘルパー。

盤面画像を大きめのキャンバスに貼り付け、回転・ノイズ・明るさ変化を加えることで、
実際のスマホ写真を用意しなくてもグリッド検出の頑健性をある程度検証できるようにする。
"""

import cv2
import numpy as np

from sudoku_solver.grid_detection import order_points


def make_photo_like(
    board_gray: np.ndarray,
    canvas_size: int = 600,
    angle_deg: float = 0,
    noise_sigma: float = 0,
    brightness_shift: int = 0,
    background: int = 220,
) -> tuple[np.ndarray, np.ndarray]:
    """盤面画像を余白付きキャンバスに貼り付け、回転・ノイズ・明るさ変化を加える。

    戻り値は (合成画像, 貼り付けた盤面の正解4頂点[order_points済み]) のタプル。
    正解4頂点は、貼り付け位置に回転と同じアフィン変換を適用して計算する。
    """
    h, w = board_gray.shape
    canvas = np.full((canvas_size, canvas_size), background, dtype=np.uint8)
    offset_x, offset_y = (canvas_size - w) // 2, (canvas_size - h) // 2
    canvas[offset_y:offset_y + h, offset_x:offset_x + w] = board_gray

    corners = np.array(
        [
            [offset_x, offset_y],
            [offset_x + w, offset_y],
            [offset_x, offset_y + h],
            [offset_x + w, offset_y + h],
        ],
        dtype=np.float32,
    )

    center = (canvas_size / 2, canvas_size / 2)
    matrix = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    rotated_img = cv2.warpAffine(
        canvas, matrix, (canvas_size, canvas_size), borderValue=background
    )

    ones = np.ones((4, 1), dtype=np.float32)
    pts_homogeneous = np.hstack([corners, ones])
    rotated_corners = (matrix @ pts_homogeneous.T).T

    result = rotated_img.astype(np.float32)
    if noise_sigma > 0:
        result += np.random.default_rng(0).normal(0, noise_sigma, result.shape)
    if brightness_shift != 0:
        result += brightness_shift
    result = np.clip(result, 0, 255).astype(np.uint8)

    return result, order_points(rotated_corners.astype(np.float32))


def corner_error(rect_a: np.ndarray, rect_b: np.ndarray) -> float:
    """order_points済みの2つの4頂点集合について、対応点間の平均距離を返す。"""
    return float(np.mean(np.linalg.norm(rect_a - rect_b, axis=1)))
