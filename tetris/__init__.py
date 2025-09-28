"""核心游戏数据结构与加载工具包。"""

from .game import GameConfig, GameState, create_game, hard_drop, hold_state_snapshot, move_left, move_right, rotate, soft_drop, tick
from .piece import Piece, PieceMatrix
from .piece_loader import load_pieces_from_excel, PieceLoadError

__all__ = [
    "GameConfig",
    "GameState",
    "create_game",
    "tick",
    "move_left",
    "move_right",
    "soft_drop",
    "hard_drop",
    "rotate",
    "hold_state_snapshot",
    "Piece",
    "PieceMatrix",
    "PieceLoadError",
    "load_pieces_from_excel",
]
