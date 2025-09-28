from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence

from .piece import Piece
from .piece_loader import load_pieces_from_excel

logger = logging.getLogger(__name__)

BoardCell = Optional[str]
BoardMatrix = List[List[BoardCell]]


@dataclass(slots=True)
class GameConfig:
    """俄罗斯方块游戏的配置。"""

    pieces: Sequence[Piece]
    board_width: int = 10
    board_height: int = 20
    spawn_row: int = 0
    spawn_col: Optional[int] = None
    random_seed: Optional[int] = None

    @classmethod
    def from_excel(
        cls,
        path: str | Path,
        *,
        sheet_name: str | None = None,
        board_width: int = 10,
        board_height: int = 20,
        spawn_row: int = 0,
        spawn_col: Optional[int] = None,
        random_seed: Optional[int] = None,
    ) -> "GameConfig":
        pieces = load_pieces_from_excel(path, sheet_name=sheet_name)
        return cls(
            pieces=pieces,
            board_width=board_width,
            board_height=board_height,
            spawn_row=spawn_row,
            spawn_col=spawn_col,
            random_seed=random_seed,
        )

    def resolve_spawn_col(self, piece: Piece) -> int:
        if self.spawn_col is not None:
            return self.spawn_col
        return max(0, (self.board_width - piece.matrix_size) // 2)


@dataclass(slots=True)
class GameState:
    """游戏运行时状态。"""

    config: GameConfig
    board: BoardMatrix
    rng: random.Random
    active_piece: Optional[Piece] = None
    active_row: int = 0
    active_col: int = 0
    next_piece: Optional[Piece] = None
    score: int = 0
    total_lines_cleared: int = 0
    game_over: bool = False

    def clone_board(self) -> BoardMatrix:
        return [row[:] for row in self.board]


def create_game(config: GameConfig) -> GameState:
    if not config.pieces:
        raise ValueError("pieces 不能为空")

    board: BoardMatrix = [[None for _ in range(config.board_width)] for _ in range(config.board_height)]
    rng = random.Random(config.random_seed)
    state = GameState(config=config, board=board, rng=rng)
    state.next_piece = _choose_piece(state)
    _spawn_next_piece(state)
    return state


def tick(state: GameState) -> None:
    """向下移动一步，无法移动则锁定当前方块。"""

    if state.game_over or state.active_piece is None:
        return

    if _try_move(state, delta_row=1, delta_col=0):
        return
    _lock_piece(state)


def move_left(state: GameState) -> bool:
    return _try_move(state, delta_row=0, delta_col=-1)


def move_right(state: GameState) -> bool:
    return _try_move(state, delta_row=0, delta_col=1)


def soft_drop(state: GameState) -> bool:
    """尝试向下移动一格。成功返回 True，失败则锁定方块。"""

    if state.game_over or state.active_piece is None:
        return False
    if _try_move(state, delta_row=1, delta_col=0):
        state.score += 1
        return True
    _lock_piece(state)
    return False


def hard_drop(state: GameState) -> None:
    if state.game_over or state.active_piece is None:
        return
    distance = 0
    while _try_move(state, delta_row=1, delta_col=0):
        distance += 1
    if distance:
        state.score += distance * 2
    _lock_piece(state)


def rotate(state: GameState, clockwise: bool = True) -> bool:
    if state.game_over or state.active_piece is None:
        return False
    piece = state.active_piece
    if not piece.allow_rotate:
        return False
    rotated_piece = piece.rotated(clockwise=clockwise)
    if _can_place(state, rotated_piece, state.active_row, state.active_col):
        state.active_piece = rotated_piece
        return True
    return False


def hold_state_snapshot(state: GameState) -> dict:
    """获取用于调试或保存的简单快照。"""

    return {
        "board": state.clone_board(),
        "active_piece": state.active_piece.shape_id if state.active_piece else None,
        "active_position": (state.active_row, state.active_col),
        "next_piece": state.next_piece.shape_id if state.next_piece else None,
        "score": state.score,
        "total_lines_cleared": state.total_lines_cleared,
        "game_over": state.game_over,
    }


def _choose_piece(state: GameState) -> Piece:
    pieces = state.config.pieces
    weights = [piece.spawn_weight for piece in pieces]
    choice = state.rng.choices(pieces, weights=weights, k=1)[0]
    logger.debug("随机选择方块: %s", choice.shape_id)
    return choice


def _spawn_next_piece(state: GameState) -> None:
    if state.game_over:
        state.active_piece = None
        return

    next_piece = state.next_piece or _choose_piece(state)
    spawn_row = state.config.spawn_row
    spawn_col = state.config.resolve_spawn_col(next_piece)
    if not _can_place(state, next_piece, spawn_row, spawn_col):
        logger.info("无法放置新方块 %s，游戏结束", next_piece.shape_id)
        state.game_over = True
        state.active_piece = None
        return

    state.active_piece = next_piece
    state.active_row = spawn_row
    state.active_col = spawn_col
    state.next_piece = _choose_piece(state)
    logger.debug(
        "生成方块: %s at row=%s col=%s", state.active_piece.shape_id, state.active_row, state.active_col
    )


def _try_move(state: GameState, *, delta_row: int, delta_col: int) -> bool:
    if state.game_over or state.active_piece is None:
        return False
    new_row = state.active_row + delta_row
    new_col = state.active_col + delta_col
    if not _can_place(state, state.active_piece, new_row, new_col):
        return False
    state.active_row = new_row
    state.active_col = new_col
    return True


def _can_place(state: GameState, piece: Piece, base_row: int, base_col: int) -> bool:
    matrix = piece.matrix
    height = len(matrix)
    width = len(matrix[0])
    for r in range(height):
        for c in range(width):
            if not matrix[r][c]:
                continue
            board_row = base_row + r
            board_col = base_col + c
            if board_row < 0 or board_row >= state.config.board_height:
                return False
            if board_col < 0 or board_col >= state.config.board_width:
                return False
            if state.board[board_row][board_col] is not None:
                return False
    return True


def _lock_piece(state: GameState) -> None:
    if state.active_piece is None:
        return

    matrix = state.active_piece.matrix
    for r, row in enumerate(matrix):
        for c, value in enumerate(row):
            if not value:
                continue
            board_row = state.active_row + r
            board_col = state.active_col + c
            if 0 <= board_row < state.config.board_height and 0 <= board_col < state.config.board_width:
                state.board[board_row][board_col] = state.active_piece.shape_id

    cleared = _clear_full_lines(state)
    if cleared:
        state.total_lines_cleared += cleared
        state.score += (cleared ** 2) * 100
        logger.info("消除 %s 行，当前得分 %s", cleared, state.score)

    state.active_piece = None
    _spawn_next_piece(state)


def _clear_full_lines(state: GameState) -> int:
    rows_to_keep: List[List[BoardCell]] = []
    cleared = 0
    for row in state.board:
        if all(cell is not None for cell in row):
            cleared += 1
        else:
            rows_to_keep.append(row)

    for _ in range(cleared):
        rows_to_keep.insert(0, [None for _ in range(state.config.board_width)])

    if cleared:
        state.board[:] = rows_to_keep
    return cleared
