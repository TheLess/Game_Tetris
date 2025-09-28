from __future__ import annotations

import sys
import unittest
from pathlib import Path

# 添加项目根目录到 Python 路径
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from tetris import GameConfig, GameState, create_game, hard_drop, move_left, move_right, rotate, soft_drop, tick
from tetris.piece import Piece

DATA_PATH = Path(__file__).resolve().parent.parent / "Block.xlsx"


class GameTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = GameConfig.from_excel(DATA_PATH, random_seed=42, board_width=10, board_height=20)
        self.state = create_game(self.config)

    def test_create_game_initializes_correctly(self) -> None:
        self.assertIsInstance(self.state, GameState)
        self.assertEqual(len(self.state.board), 20)
        self.assertEqual(len(self.state.board[0]), 10)
        self.assertIsNotNone(self.state.active_piece)
        self.assertIsNotNone(self.state.next_piece)
        self.assertEqual(self.state.score, 0)
        self.assertEqual(self.state.total_lines_cleared, 0)
        self.assertFalse(self.state.game_over)

    def test_tick_moves_piece_down(self) -> None:
        initial_row = self.state.active_row
        tick(self.state)
        self.assertEqual(self.state.active_row, initial_row + 1)

    def test_move_left_and_right(self) -> None:
        initial_col = self.state.active_col
        
        # 测试向左移动
        success = move_left(self.state)
        if success:
            self.assertEqual(self.state.active_col, initial_col - 1)
        
        # 测试向右移动
        success = move_right(self.state)
        if success:
            self.assertEqual(self.state.active_col, initial_col)

    def test_soft_drop_increases_score(self) -> None:
        initial_score = self.state.score
        success = soft_drop(self.state)
        if success:
            self.assertEqual(self.state.score, initial_score + 1)

    def test_hard_drop_locks_piece(self) -> None:
        initial_piece = self.state.active_piece
        hard_drop(self.state)
        # 硬降落后应该生成新方块
        self.assertNotEqual(self.state.active_piece, initial_piece)

    def test_rotate_piece(self) -> None:
        # 找到一个可旋转的方块进行测试
        if self.state.active_piece and self.state.active_piece.allow_rotate:
            initial_matrix = self.state.active_piece.matrix
            success = rotate(self.state)
            if success:
                self.assertNotEqual(self.state.active_piece.matrix, initial_matrix)

    def test_game_over_when_no_space(self) -> None:
        # 填满顶部行来触发游戏结束
        for col in range(self.config.board_width):
            self.state.board[0][col] = "TEST"
        
        # 强制生成新方块应该触发游戏结束
        from tetris.game import _spawn_next_piece
        _spawn_next_piece(self.state)
        self.assertTrue(self.state.game_over)

    def test_line_clearing(self) -> None:
        # 手动填满一行（除了最后一个位置）
        test_row = self.config.board_height - 1
        for col in range(self.config.board_width - 1):
            self.state.board[test_row][col] = "TEST"
        
        # 放置一个方块来完成这一行
        self.state.board[test_row][self.config.board_width - 1] = "TEST"
        
        from tetris.game import _clear_full_lines
        cleared = _clear_full_lines(self.state)
        self.assertEqual(cleared, 1)
        
        # 检查该行是否被清除（应该全为 None）
        self.assertTrue(all(cell is None for cell in self.state.board[test_row]))

    def test_config_from_excel(self) -> None:
        config = GameConfig.from_excel(DATA_PATH)
        self.assertGreater(len(config.pieces), 0)
        self.assertEqual(config.board_width, 10)
        self.assertEqual(config.board_height, 20)

    def test_spawn_col_resolution(self) -> None:
        # 创建一个小方块测试生成位置
        small_piece = Piece(
            shape_id="TEST",
            display_name="Test",
            matrix=[[1]],
            allow_rotate=False,
            allow_mirror=False,
        )
        
        # 测试默认居中
        spawn_col = self.config.resolve_spawn_col(small_piece)
        expected_col = (self.config.board_width - 1) // 2
        self.assertEqual(spawn_col, expected_col)
        
        # 测试指定位置
        config_with_spawn = GameConfig(
            pieces=[small_piece],
            spawn_col=3,
        )
        spawn_col = config_with_spawn.resolve_spawn_col(small_piece)
        self.assertEqual(spawn_col, 3)


if __name__ == "__main__":
    unittest.main()
