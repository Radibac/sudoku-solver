from sudoku_solver.solver import is_valid_board, solve_board

VALID_PUZZLE = [
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

EXPECTED_SOLUTION = [
    [8, 1, 2, 7, 5, 3, 6, 4, 9],
    [9, 4, 3, 6, 8, 2, 1, 7, 5],
    [6, 7, 5, 4, 9, 1, 2, 8, 3],
    [1, 5, 4, 2, 3, 7, 8, 9, 6],
    [3, 6, 9, 8, 4, 5, 7, 2, 1],
    [2, 8, 7, 1, 6, 9, 5, 3, 4],
    [5, 2, 1, 9, 7, 4, 3, 6, 8],
    [4, 3, 8, 5, 2, 6, 9, 1, 7],
    [7, 9, 6, 3, 1, 8, 4, 5, 2],
]


def test_is_valid_board_true_for_valid_puzzle():
    assert is_valid_board(VALID_PUZZLE) is True


def test_is_valid_board_false_for_duplicate_in_row():
    board = [row.copy() for row in VALID_PUZZLE]
    board[0][1] = 8  # 行0にすでに8があるのに重複させる
    assert is_valid_board(board) is False


def test_is_valid_board_false_for_duplicate_in_box():
    board = [row.copy() for row in VALID_PUZZLE]
    board[1][0] = 8  # 左上の3x3ブロックに8が重複
    assert is_valid_board(board) is False


def test_solve_board_returns_expected_solution():
    solved = solve_board(VALID_PUZZLE)
    assert solved == EXPECTED_SOLUTION


def test_solve_board_does_not_mutate_input():
    original = [row.copy() for row in VALID_PUZZLE]
    solve_board(VALID_PUZZLE)
    assert VALID_PUZZLE == original


def test_solve_board_returns_none_for_invalid_board():
    board = [row.copy() for row in VALID_PUZZLE]
    board[0][1] = 8
    assert solve_board(board) is None


def test_solve_board_returns_none_for_unsolvable_board():
    # 2箇所に矛盾を作り、行・列・ブロックのどの重複チェックにも引っかからないが
    # 解が存在しない盤面を用意する代わりに、埋めた数字だけで手詰まりになる盤面を使う。
    board = [[0] * 9 for _ in range(9)]
    board[0][0] = 1
    board[0][1] = 2
    board[0][2] = 3
    board[0][3] = 4
    board[0][4] = 5
    board[0][5] = 6
    board[0][6] = 7
    board[0][7] = 8
    # 残り1マスに置けるのは9だけだが、同じ列に9を強制的に置いて手詰まりにする
    board[1][8] = 9
    board[2][8] = 1
    board[3][8] = 2
    board[4][8] = 3
    board[5][8] = 4
    board[6][8] = 5
    board[7][8] = 6
    board[8][8] = 7
    assert solve_board(board) is None
