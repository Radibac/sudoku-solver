"""数独ソルバー。generate_sudoku.ipynb のバックトラッキングロジックを移植したもの。"""

Board = list[list[int]]


def _is_valid_placement(board: Board, row: int, col: int, num: int) -> bool:
    for i in range(9):
        if i != col and board[row][i] == num:
            return False
        if i != row and board[i][col] == num:
            return False

    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            r, c = start_row + i, start_col + j
            if (r, c) != (row, col) and board[r][c] == num:
                return False
    return True


def is_valid_board(board: Board) -> bool:
    """事前に埋まっているマス同士に重複がないか（行・列・3x3ブロック）を確認する。

    OCRの誤読でありえない盤面が渡された場合に、solve()を無駄に走らせず早期検出するために使う。
    """
    for row in range(9):
        for col in range(9):
            num = board[row][col]
            if num != 0 and not _is_valid_placement(board, row, col, num):
                return False
    return True


def solve(board: Board) -> bool:
    """boardを破壊的に解く。解けたらTrueを返し、boardは解に更新される。解なしならFalse。"""
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                for num in range(1, 10):
                    if _is_valid_placement(board, row, col, num):
                        board[row][col] = num
                        if solve(board):
                            return True
                        board[row][col] = 0
                return False
    return True


def solve_board(board: Board) -> Board | None:
    """boardを変更せず、解けたコピーを返す。無効な盤面や解なしの場合はNoneを返す。"""
    if not is_valid_board(board):
        return None

    candidate = [row.copy() for row in board]
    if solve(candidate):
        return candidate
    return None
