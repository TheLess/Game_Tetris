from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from .piece import Piece
from .piece_loader import load_pieces_from_excel

logger = logging.getLogger(__name__)

BoardCell = Optional[str]
BoardMatrix = List[List[BoardCell]]


@dataclass(slots=True)
class PuzzleConfig:
    """拼图模式游戏配置。"""

    pieces: Sequence[Piece]
    board_width: int = 8
    board_height: int = 8
    spawn_row: int = 0
    spawn_col: Optional[int] = None
    random_seed: Optional[int] = None
    pieces_per_round: int = 3

    @classmethod
    def from_excel(
        cls,
        path: str | Path,
        *,
        sheet_name: str | None = None,
        board_width: int = 8,
        board_height: int = 8,
        spawn_row: int = 0,
        spawn_col: Optional[int] = None,
        random_seed: Optional[int] = None,
    ) -> "PuzzleConfig":
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
class PuzzleState:
    """拼图游戏运行时状态。"""

    config: PuzzleConfig
    board: BoardMatrix
    rng: random.Random
    current_round_pieces: List[Piece]  # 当前回合的3个方块
    active_piece_index: int = 0  # 当前选中的方块索引
    active_row: int = 0
    active_col: int = 0
    score: int = 0
    total_lines_cleared: int = 0
    total_pieces_placed: int = 0
    round_number: int = 1
    game_over: bool = False

    @property
    def active_piece(self) -> Optional[Piece]:
        if 0 <= self.active_piece_index < len(self.current_round_pieces):
            return self.current_round_pieces[self.active_piece_index]
        return None

    @property
    def pieces_left_in_round(self) -> int:
        return len(self.current_round_pieces)

    def clone_board(self) -> BoardMatrix:
        return [row[:] for row in self.board]


def create_puzzle_game(config: PuzzleConfig) -> PuzzleState:
    """创建拼图模式游戏。"""
    if not config.pieces:
        raise ValueError("pieces 不能为空")

    board: BoardMatrix = [[None for _ in range(config.board_width)] for _ in range(config.board_height)]
    rng = random.Random(config.random_seed)
    
    # 生成第一回合的方块
    round_pieces = _generate_round_pieces(config, rng)
    
    state = PuzzleState(
        config=config, 
        board=board, 
        rng=rng, 
        current_round_pieces=round_pieces,
        active_piece_index=0
    )
    _reset_piece_position(state)
    return state


def move_left(state: PuzzleState) -> bool:
    """向左移动当前方块。"""
    return _try_move(state, delta_row=0, delta_col=-1)


def move_right(state: PuzzleState) -> bool:
    """向右移动当前方块。"""
    return _try_move(state, delta_row=0, delta_col=1)


def move_up(state: PuzzleState) -> bool:
    """向上移动当前方块。"""
    return _try_move(state, delta_row=-1, delta_col=0)


def move_down(state: PuzzleState) -> bool:
    """向下移动当前方块。"""
    return _try_move(state, delta_row=1, delta_col=0)


def rotate_piece(state: PuzzleState, clockwise: bool = True) -> bool:
    """旋转当前方块。"""
    if state.game_over or state.active_piece is None:
        return False
    piece = state.active_piece
    if not piece.allow_rotate:
        return False
    rotated_piece = piece.rotated(clockwise=clockwise)
    # 旋转时只检查边界，不检查与已放置方块的碰撞
    if _can_move_to(state, rotated_piece, state.active_row, state.active_col):
        # 更新列表中的方块而不是设置属性
        state.current_round_pieces[state.active_piece_index] = rotated_piece
        return True
    return False


def place_piece(state: PuzzleState) -> bool:
    """在当前位置放置方块。"""
    if state.game_over or state.active_piece is None:
        return False
    
    if not _can_place(state, state.active_piece, state.active_row, state.active_col):
        return False
    
    _lock_piece(state)
    return True


def select_next_piece(state: PuzzleState) -> bool:
    """选择下一个方块。"""
    if state.game_over or state.pieces_left_in_round == 0:
        return False
    
    state.active_piece_index = (state.active_piece_index + 1) % len(state.current_round_pieces)
    _reset_piece_position(state)
    logger.debug("Selected next piece: %s", state.active_piece.shape_id if state.active_piece else "None")
    return True


def select_previous_piece(state: PuzzleState) -> bool:
    """选择上一个方块。"""
    if state.game_over or state.pieces_left_in_round == 0:
        return False
    
    state.active_piece_index = (state.active_piece_index - 1) % len(state.current_round_pieces)
    _reset_piece_position(state)
    logger.debug("Selected previous piece: %s", state.active_piece.shape_id if state.active_piece else "None")
    return True


def can_place_any_piece(state: PuzzleState) -> bool:
    """检查是否还能放置任何方块。"""
    for piece in state.current_round_pieces:
        for row in range(state.config.board_height):
            for col in range(state.config.board_width):
                if _can_place(state, piece, row, col):
                    return True
    return False


def get_ghost_position(state: PuzzleState) -> tuple[int, int] | None:
    """获取当前方块的投影位置（如果直接下降到底部）。"""
    if state.active_piece is None:
        return None
    
    ghost_row = state.active_row
    ghost_col = state.active_col
    
    # 向下寻找可放置的最低位置
    while _can_place(state, state.active_piece, ghost_row + 1, ghost_col):
        ghost_row += 1
    
    return ghost_row, ghost_col


def puzzle_state_snapshot(state: PuzzleState) -> dict:
    """获取用于调试或保存的简单快照。"""
    return {
        "board": state.clone_board(),
        "active_piece": state.active_piece.shape_id if state.active_piece else None,
        "active_position": (state.active_row, state.active_col),
        "current_round_pieces": [p.shape_id for p in state.current_round_pieces],
        "active_piece_index": state.active_piece_index,
        "pieces_left_in_round": state.pieces_left_in_round,
        "round_number": state.round_number,
        "score": state.score,
        "total_lines_cleared": state.total_lines_cleared,
        "total_pieces_placed": state.total_pieces_placed,
        "game_over": state.game_over,
    }


def _generate_round_pieces(config: PuzzleConfig, rng: random.Random) -> List[Piece]:
    """生成一回合的方块。"""
    pieces = config.pieces
    weights = [piece.spawn_weight for piece in pieces]
    round_pieces = rng.choices(pieces, weights=weights, k=config.pieces_per_round)
    logger.info("Generated new round pieces: %s", [p.shape_id for p in round_pieces])
    return round_pieces


def _reset_piece_position(state: PuzzleState) -> None:
    """重置当前方块到安全位置。"""
    if state.active_piece is None:
        return
    
    # 首先尝试默认位置
    default_row = state.config.spawn_row
    default_col = state.config.resolve_spawn_col(state.active_piece)
    
    # 重置位置时只检查边界，允许与已放置方块重叠（虚拟占位）
    if _can_move_to(state, state.active_piece, default_row, default_col):
        state.active_row = default_row
        state.active_col = default_col
        return
    
    # 如果默认位置超出边界，寻找第一个在边界内的位置
    for row in range(state.config.board_height):
        for col in range(state.config.board_width):
            if _can_move_to(state, state.active_piece, row, col):
                state.active_row = row
                state.active_col = col
                logger.debug("Piece %s reset to safe position: (%d, %d)", state.active_piece.shape_id, row, col)
                return
    
    # 如果找不到任何可用位置，保持在默认位置（这种情况下游戏应该结束）
    state.active_row = default_row
    state.active_col = default_col
    logger.warning("Piece %s cannot find safe position, keeping at default", state.active_piece.shape_id)


def _try_move(state: PuzzleState, *, delta_row: int, delta_col: int) -> bool:
    if state.game_over or state.active_piece is None:
        return False
    new_row = state.active_row + delta_row
    new_col = state.active_col + delta_col
    # 移动时只检查边界，不检查与已放置方块的碰撞
    if not _can_move_to(state, state.active_piece, new_row, new_col):
        return False
    state.active_row = new_row
    state.active_col = new_col
    return True


def _can_move_to(state: PuzzleState, piece: Piece, base_row: int, base_col: int) -> bool:
    """检查方块是否可以移动到指定位置（只检查边界，不检查与已放置方块的碰撞）。"""
    matrix = piece.matrix
    height = len(matrix)
    width = len(matrix[0])
    for r in range(height):
        for c in range(width):
            if not matrix[r][c]:
                continue
            board_row = base_row + r
            board_col = base_col + c
            # 只检查边界，不检查已放置的方块
            if board_row < 0 or board_row >= state.config.board_height:
                return False
            if board_col < 0 or board_col >= state.config.board_width:
                return False
    return True


def _can_place(state: PuzzleState, piece: Piece, base_row: int, base_col: int) -> bool:
    """检查方块是否可以放置到指定位置（检查边界和与已放置方块的碰撞）。"""
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


def _lock_piece(state: PuzzleState) -> None:
    if state.active_piece is None:
        return

    # 放置方块到棋盘
    matrix = state.active_piece.matrix
    for r, row in enumerate(matrix):
        for c, value in enumerate(row):
            if not value:
                continue
            board_row = state.active_row + r
            board_col = state.active_col + c
            if 0 <= board_row < state.config.board_height and 0 <= board_col < state.config.board_width:
                state.board[board_row][board_col] = state.active_piece.shape_id

    state.total_pieces_placed += 1
    logger.info("Placed piece: %s, total placed: %s", state.active_piece.shape_id, state.total_pieces_placed)

    # 从当前回合移除已放置的方块
    state.current_round_pieces.pop(state.active_piece_index)
    
    # 调整当前选中的方块索引
    if state.active_piece_index >= len(state.current_round_pieces):
        state.active_piece_index = max(0, len(state.current_round_pieces) - 1)
    
    # 检查消行
    cleared = _clear_full_lines(state)
    if cleared:
        state.total_lines_cleared += cleared
        state.score += (cleared ** 2) * 100
        logger.info("Cleared %s lines, current score %s", cleared, state.score)

    # 检查回合是否结束
    if len(state.current_round_pieces) == 0:
        # 开始新回合
        state.round_number += 1
        state.current_round_pieces = _generate_round_pieces(state.config, state.rng)
        state.active_piece_index = 0
        logger.info("Starting round %s", state.round_number)
    
    # 检查游戏是否结束
    if not can_place_any_piece(state):
        state.game_over = True
        logger.info("Game Over! Cannot place any piece")
        return
    
    # 重置当前方块位置
    _reset_piece_position(state)


def _clear_full_lines(state: PuzzleState) -> int:
    """清除满行，但不移动其他方块（就地清除）。"""
    cleared = 0
    for row_index in range(state.config.board_height):
        row = state.board[row_index]
        if all(cell is not None for cell in row):
            # 清除这一行，变成空行
            for col_index in range(state.config.board_width):
                state.board[row_index][col_index] = None
            cleared += 1
            logger.debug("Cleared row %d", row_index)
    
    return cleared
