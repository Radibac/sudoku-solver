from sudoku_solver.pipeline import solve_sudoku_from_image


def _is_valid_completed_board(board: list[list[int]]) -> bool:
    for i in range(9):
        row = board[i]
        col = [board[r][i] for r in range(9)]
        if sorted(row) != list(range(1, 10)) or sorted(col) != list(range(1, 10)):
            return False

    for br in range(3):
        for bc in range(3):
            box = [
                board[br * 3 + i][bc * 3 + j]
                for i in range(3)
                for j in range(3)
            ]
            if sorted(box) != list(range(1, 10)):
                return False

    return True


def test_solve_sudoku_from_image_produces_valid_completed_board(sample_photo_path):
    solved = solve_sudoku_from_image(sample_photo_path)
    assert _is_valid_completed_board(solved)
