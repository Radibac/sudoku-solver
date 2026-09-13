import numpy as np

from sudoku_solver.cells import is_blank_cell, split_into_cells
from sudoku_solver.digit_recognition import recognize_digit, recognize_grid
from sudoku_solver.grid_detection import detect_grid

# old/sudoku.jpg に写っている盤面の正解（目視で確認済み）
GROUND_TRUTH = [
    [8, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 3, 6, 0, 0, 0, 0, 0],
    [0, 7, 0, 0, 9, 0, 2, 0, 0],
    [0, 5, 0, 0, 0, 7, 0, 0, 0],
    [0, 0, 0, 0, 4, 5, 7, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 3, 0],
    [0, 0, 1, 0, 0, 0, 0, 6, 8],
    [0, 0, 8, 5, 0, 0, 0, 1, 0],
    [0, 9, 0, 0, 0, 0, 4, 0, 0],
]

# 現状のpytesseractベースの認識精度に対する下限。
# これを下回ったら前処理・OCR設定のどこかで退行している。
MIN_ACCURACY = 0.90


def test_recognize_digit_returns_zero_for_blank_cell():
    blank_cell = np.full((60, 60), 255, dtype=np.uint8)
    assert recognize_digit(blank_cell) == 0


def test_recognize_grid_accuracy_on_sample_photo(sample_photo_path):
    warped, _rect = detect_grid(sample_photo_path)
    cell_rows = split_into_cells(warped)
    recognized = recognize_grid(cell_rows, is_blank_cell)

    total = 81
    correct = sum(
        1
        for i in range(9)
        for j in range(9)
        if recognized[i][j] == GROUND_TRUTH[i][j]
    )
    accuracy = correct / total

    assert accuracy >= MIN_ACCURACY, (
        f"digit recognition accuracy dropped to {accuracy:.2%} "
        f"(expected >= {MIN_ACCURACY:.0%}); got {recognized}"
    )


def test_recognize_grid_never_misreads_blank_as_wrong_digit(sample_photo_path):
    """空白マスを別の数字と誤読するのは、見逃し（0のまま）より悪い失敗モードなので個別に検証する。"""
    warped, _rect = detect_grid(sample_photo_path)
    cell_rows = split_into_cells(warped)
    recognized = recognize_grid(cell_rows, is_blank_cell)

    for i in range(9):
        for j in range(9):
            if GROUND_TRUTH[i][j] == 0:
                assert recognized[i][j] == 0, f"cell ({i},{j}) should be blank"
