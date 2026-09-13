import numpy as np

from sudoku_solver.cells import is_blank_cell, split_into_cells


def test_split_into_cells_returns_9x9_grid():
    warped = np.zeros((90, 90), dtype=np.uint8)
    rows = split_into_cells(warped)

    assert len(rows) == 9
    assert all(len(row) == 9 for row in rows)
    assert rows[0][0].shape == (10, 10)


def test_is_blank_cell_true_for_white_cell():
    white_cell = np.full((60, 60), 255, dtype=np.uint8)
    assert is_blank_cell(white_cell) is True


def test_is_blank_cell_false_for_cell_with_digit():
    cell = np.full((60, 60), 255, dtype=np.uint8)
    cell[20:40, 20:40] = 0  # 中央に大きな黒い塊＝数字を模す
    assert is_blank_cell(cell) is False
