"""実写真がなくても検証できる、合成画像によるグリッド検出の頑健性テスト。

old/sudoku.jpg を余白付きキャンバスに貼り付け、回転・明るさ変化を加えた上で
detect_grid_from_gray が正しい4頂点を検出できるかを確認する。
"""

import cv2
import numpy as np
import pytest

from sudoku_solver.grid_detection import GridNotFoundError, detect_grid_from_gray
from tests.synthetic import corner_error, make_photo_like

MAX_CORNER_ERROR_PX = 20.0


@pytest.fixture
def board_gray(sample_photo_path):
    return cv2.imread(sample_photo_path, cv2.IMREAD_GRAYSCALE)


@pytest.mark.parametrize("angle_deg", [0, 5, 10, 15, 20])
def test_detect_grid_survives_padding_and_rotation(board_gray, angle_deg):
    """盤面の周囲に背景の余白があり、かつ回転していても正しく検出できることを確認する。

    以前は「盤面+背景の余白」全体が最大面積の輪郭として誤検出されるバグがあり、
    このテストで再現・修正した（選定基準を面積からインク密度に変更）。
    """
    img, expected_rect = make_photo_like(board_gray, angle_deg=angle_deg)

    _warped, rect = detect_grid_from_gray(img)

    assert corner_error(rect, expected_rect) < MAX_CORNER_ERROR_PX


@pytest.mark.parametrize("brightness_shift", [-60, 60])
def test_detect_grid_survives_brightness_shift(board_gray, brightness_shift):
    img, expected_rect = make_photo_like(
        board_gray, angle_deg=8, brightness_shift=brightness_shift
    )

    _warped, rect = detect_grid_from_gray(img)

    assert corner_error(rect, expected_rect) < MAX_CORNER_ERROR_PX


@pytest.mark.xfail(
    reason=(
        "強いガウスノイズ(sigma=15)下では、ノイズ除去が細い罫線ごと消してしまい、"
        "盤面+余白全体が誤検出される既知の限界。docs/roadmap.md参照。"
    ),
    strict=True,
)
def test_detect_grid_under_heavy_noise_is_a_known_limitation(board_gray):
    img, expected_rect = make_photo_like(board_gray, angle_deg=8, noise_sigma=15)

    _warped, rect = detect_grid_from_gray(img)

    assert corner_error(rect, expected_rect) < MAX_CORNER_ERROR_PX


def test_detect_grid_raises_on_pure_background_canvas():
    """盤面が全く含まれない、背景だけのキャンバスでは検出に失敗するべき。"""
    blank_canvas = np.full((600, 600), 220, dtype="uint8")

    with pytest.raises(GridNotFoundError):
        detect_grid_from_gray(blank_canvas)
