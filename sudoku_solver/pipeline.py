"""写真ファイルから数独盤面（9x9の2次元リスト）を読み取り、解くエンドツーエンドの処理。"""

from sudoku_solver.cells import is_blank_cell, split_into_cells
from sudoku_solver.digit_recognition import recognize_grid
from sudoku_solver.grid_detection import detect_grid
from sudoku_solver.solver import solve_board


class UnsolvableGridError(RuntimeError):
    """認識した盤面が数独として無効、または解が存在しない場合に送出する。"""


def read_sudoku_from_image(image_path: str) -> list[list[int]]:
    """画像ファイルから数独盤面を読み取り、9x9の2次元リスト（空白は0）を返す。"""
    warped, _rect = detect_grid(image_path)
    cell_rows = split_into_cells(warped)
    return recognize_grid(cell_rows, is_blank_cell)


def solve_sudoku_from_image(image_path: str) -> list[list[int]]:
    """画像ファイルから数独盤面を読み取り、解いた9x9の2次元リストを返す。

    読み取った盤面が矛盾している（OCRの誤読など）か、解が存在しない場合は
    UnsolvableGridError を送出する。
    """
    grid = read_sudoku_from_image(image_path)
    solved = solve_board(grid)
    if solved is None:
        raise UnsolvableGridError(
            "読み取った盤面が無効か、解が存在しません。数字認識の誤りの可能性があります。"
        )
    return solved
