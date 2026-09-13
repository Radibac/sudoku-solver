import numpy as np
import pytest

from sudoku_solver.grid_detection import (
    GridNotFoundError,
    detect_grid,
    find_grid_corners,
    order_points,
    preprocess_image,
)


def test_order_points_sorts_corners_regardless_of_input_order():
    # 右下, 左上, 右上, 左下の順にわざと崩して渡す
    pts = np.array([[100, 100], [0, 0], [100, 0], [0, 100]], dtype="float32")
    rect = order_points(pts)
    top_left, top_right, bottom_left, bottom_right = rect

    assert tuple(top_left) == (0.0, 0.0)
    assert tuple(top_right) == (100.0, 0.0)
    assert tuple(bottom_left) == (0.0, 100.0)
    assert tuple(bottom_right) == (100.0, 100.0)


def test_detect_grid_on_sample_photo_returns_square_image(sample_photo_path):
    warped, rect = detect_grid(sample_photo_path)

    assert warped.shape[0] == warped.shape[1]
    assert warped.shape[0] > 50
    assert rect.shape == (4, 2)


def test_find_grid_corners_raises_on_blank_image():
    blank = np.full((200, 200), 255, dtype=np.uint8)
    binary = preprocess_image(blank)

    with pytest.raises(GridNotFoundError):
        find_grid_corners(blank, binary)


def test_find_grid_corners_rejects_non_square_contour():
    # 横長の矩形だけが写る画像。縦横比フィルタで棄却され、Houghフォールバックも
    # 直線が水平方向にしかないため失敗し、GridNotFoundError になるはず。
    img = np.full((200, 400), 255, dtype=np.uint8)
    img[20:180, 20:380] = 0
    binary = preprocess_image(img)

    with pytest.raises(GridNotFoundError):
        find_grid_corners(img, binary)
