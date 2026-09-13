"""写真ファイルから数独盤面（9x9の2次元リスト）を読み取るエンドツーエンドの処理。"""

from sudoku_solver.cells import is_blank_cell, split_into_cells
from sudoku_solver.digit_recognition import recognize_grid
from sudoku_solver.grid_detection import detect_grid


def read_sudoku_from_image(image_path: str) -> list[list[int]]:
    """画像ファイルから数独盤面を読み取り、9x9の2次元リスト（空白は0）を返す。"""
    warped, _rect = detect_grid(image_path)
    cell_rows = split_into_cells(warped)
    return recognize_grid(cell_rows, is_blank_cell)
