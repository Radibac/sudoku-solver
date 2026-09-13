from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_photo_path() -> str:
    """既知の数独盤面が写ったサンプル写真（old/sudoku.jpg）へのパス。"""
    return str(REPO_ROOT / "old" / "sudoku.jpg")
