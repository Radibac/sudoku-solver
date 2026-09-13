import numpy as np

from sudoku_solver.cells import is_blank_cell, remove_grid_lines, split_into_cells


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


def test_remove_grid_lines_clears_border_but_keeps_center():
    cell = np.full((60, 60), 255, dtype=np.uint8)
    cell[0:4, :] = 0  # 上端に太い罫線
    cell[:, 0:2] = 0  # 左端に細い罫線
    cell[25:35, 25:35] = 0  # 中央の数字を模した塊（辺には接していない）

    cleaned = remove_grid_lines(cell)

    assert np.all(cleaned[0:4, :] == 255)
    assert np.all(cleaned[:, 0:2] == 255)
    assert np.any(cleaned[25:35, 25:35] == 0)


def test_is_blank_cell_true_when_only_grid_line_is_present():
    # 罫線しかない（数字がない）セルは、罫線除去後に空白と判定されるべき
    cell = np.full((60, 60), 255, dtype=np.uint8)
    cell[0:5, :] = 0
    assert is_blank_cell(cell) is True
