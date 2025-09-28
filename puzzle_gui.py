from __future__ import annotations

import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

import pygame
from tetris.puzzle_game import (
    PuzzleConfig,
    create_puzzle_game,
    move_down,
    move_left,
    move_right,
    move_up,
    place_piece,
    puzzle_state_snapshot,
    select_next_piece,
    select_previous_piece,
)

# 游戏配置
CELL_SIZE = 40
BOARD_WIDTH = 8
BOARD_HEIGHT = 8
WINDOW_WIDTH = CELL_SIZE * (BOARD_WIDTH + 12)  # 额外空间显示信息
WINDOW_HEIGHT = CELL_SIZE * BOARD_HEIGHT + 150

# 颜色定义
COLORS = {
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255),
    'GRAY': (128, 128, 128),
    'LIGHT_GRAY': (200, 200, 200),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'BLUE': (0, 0, 255),
    'YELLOW': (255, 255, 0),
    'ORANGE': (255, 165, 0),
    'PURPLE': (128, 0, 128),
    'CYAN': (0, 255, 255),
}

# 方块颜色映射
PIECE_COLORS = {
    'I001': COLORS['CYAN'],
    'L001': COLORS['ORANGE'],
    'T001': COLORS['PURPLE'],
    'S001': COLORS['GREEN'],
    'O001': COLORS['YELLOW'],
    'Z001': COLORS['RED'],
    'J001': COLORS['BLUE'],
}

logging.basicConfig(level=logging.INFO)


class PuzzleTetrisGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Tetris Puzzle Mode")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # 游戏状态
        config = PuzzleConfig.from_excel(root / "Block.xlsx", random_seed=None)
        self.game_state = create_puzzle_game(config)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    move_left(self.game_state)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    move_right(self.game_state)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    move_down(self.game_state)
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    move_up(self.game_state)
                # 旋转功能已禁用
                # elif event.key == pygame.K_q:
                #     rotate_piece(self.game_state, clockwise=False)
                # elif event.key == pygame.K_e:
                #     rotate_piece(self.game_state, clockwise=True)
                elif event.key == pygame.K_SPACE:
                    place_piece(self.game_state)
                elif event.key == pygame.K_TAB:
                    select_next_piece(self.game_state)
                elif event.key == pygame.K_1:
                    if len(self.game_state.current_round_pieces) > 0:
                        self.game_state.active_piece_index = 0
                        from tetris.puzzle_game import _reset_piece_position
                        _reset_piece_position(self.game_state)
                elif event.key == pygame.K_2:
                    if len(self.game_state.current_round_pieces) > 1:
                        self.game_state.active_piece_index = 1
                        from tetris.puzzle_game import _reset_piece_position
                        _reset_piece_position(self.game_state)
                elif event.key == pygame.K_3:
                    if len(self.game_state.current_round_pieces) > 2:
                        self.game_state.active_piece_index = 2
                        from tetris.puzzle_game import _reset_piece_position
                        _reset_piece_position(self.game_state)
                elif event.key == pygame.K_r and self.game_state.game_over:
                    # 重新开始游戏
                    config = PuzzleConfig.from_excel(root / "Block.xlsx", random_seed=None)
                    self.game_state = create_puzzle_game(config)
        
        return True

    def draw_cell(self, x, y, color, border_color=None):
        rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(self.screen, color, rect)
        border = border_color or COLORS['WHITE']
        pygame.draw.rect(self.screen, border, rect, 1)

    def draw_board(self):
        # 绘制棋盘背景
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                cell = self.game_state.board[y][x]
                if cell is None:
                    color = COLORS['BLACK']
                else:
                    color = PIECE_COLORS.get(cell, COLORS['GRAY'])
                self.draw_cell(x, y, color)

    def draw_ghost_piece(self):
        """绘制当前方块的投影（预览位置）。"""
        if self.game_state.active_piece is None:
            return
        
        ghost_pos = get_ghost_position(self.game_state)
        if ghost_pos is None:
            return
        
        ghost_row, ghost_col = ghost_pos
        piece = self.game_state.active_piece
        
        for r, row in enumerate(piece.matrix):
            for c, value in enumerate(row):
                if value:
                    x = ghost_col + c
                    y = ghost_row + r
                    if 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
                        # 只有当前方块不在这个位置时才绘制投影
                        if (ghost_row, ghost_col) != (self.game_state.active_row, self.game_state.active_col):
                            self.draw_cell(x, y, COLORS['LIGHT_GRAY'], COLORS['GRAY'])

    def draw_active_piece(self):
        if self.game_state.active_piece is None:
            return
        
        piece = self.game_state.active_piece
        base_color = PIECE_COLORS.get(piece.shape_id, COLORS['GRAY'])
        
        for r, row in enumerate(piece.matrix):
            for c, value in enumerate(row):
                if value:
                    x = self.game_state.active_col + c
                    y = self.game_state.active_row + r
                    if 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
                        # 检查当前位置是否与已放置的方块重叠
                        if self.game_state.board[y][x] is not None:
                            # 重叠时使用半透明效果（通过混合颜色实现）
                            existing_color = PIECE_COLORS.get(self.game_state.board[y][x], COLORS['GRAY'])
                            # 简单的颜色混合
                            mixed_color = (
                                (base_color[0] + existing_color[0]) // 2,
                                (base_color[1] + existing_color[1]) // 2,
                                (base_color[2] + existing_color[2]) // 2
                            )
                            self.draw_cell(x, y, mixed_color, COLORS['WHITE'])
                        else:
                            # 正常显示，但使用虚线边框表示虚拟占位
                            self.draw_cell(x, y, base_color, COLORS['LIGHT_GRAY'])

    def draw_round_pieces(self):
        """绘制当前回合的所有方块。"""
        start_x = BOARD_WIDTH + 1
        start_y = 1
        
        # 绘制标题
        title_text = self.font.render(f"Round {self.game_state.round_number} Pieces:", True, COLORS['YELLOW'])
        self.screen.blit(title_text, (start_x * CELL_SIZE, 0))
        
        # 绘制每个方块
        for i, piece in enumerate(self.game_state.current_round_pieces):
            piece_y = start_y + i * 4
            color = PIECE_COLORS.get(piece.shape_id, COLORS['GRAY'])
            
            # 高亮当前选中的方块
            if i == self.game_state.active_piece_index:
                highlight_rect = pygame.Rect(
                    (start_x - 0.2) * CELL_SIZE, 
                    (piece_y - 0.2) * CELL_SIZE, 
                    4 * CELL_SIZE, 
                    3 * CELL_SIZE
                )
                pygame.draw.rect(self.screen, COLORS['WHITE'], highlight_rect, 3)
            
            # 绘制方块编号
            number_text = self.small_font.render(f"{i+1}:", True, COLORS['WHITE'])
            self.screen.blit(number_text, ((start_x - 0.8) * CELL_SIZE, piece_y * CELL_SIZE))
            
            # 绘制方块
            for r, row in enumerate(piece.normalized_matrix):
                for c, value in enumerate(row):
                    if value:
                        self.draw_cell(start_x + c, piece_y + r, color)

    def draw_info(self):
        # 显示得分和其他信息
        info_x = (BOARD_WIDTH + 6) * CELL_SIZE
        
        score_text = self.small_font.render(f"Score: {self.game_state.score}", True, COLORS['WHITE'])
        self.screen.blit(score_text, (info_x, 50))
        
        lines_text = self.small_font.render(f"Lines: {self.game_state.total_lines_cleared}", True, COLORS['WHITE'])
        self.screen.blit(lines_text, (info_x, 80))
        
        pieces_text = self.small_font.render(f"Placed: {self.game_state.total_pieces_placed}", True, COLORS['WHITE'])
        self.screen.blit(pieces_text, (info_x, 110))
        
        round_text = self.small_font.render(f"Round: {self.game_state.round_number}", True, COLORS['WHITE'])
        self.screen.blit(round_text, (info_x, 140))
        
        left_text = self.small_font.render(f"Left: {self.game_state.pieces_left_in_round}", True, COLORS['WHITE'])
        self.screen.blit(left_text, (info_x, 170))
        
        if self.game_state.game_over:
            game_over_text = self.font.render("Game Over!", True, COLORS['RED'])
            self.screen.blit(game_over_text, (info_x, 220))
            
            restart_text = self.small_font.render("Press R to Restart", True, COLORS['WHITE'])
            self.screen.blit(restart_text, (info_x, 260))

    def draw_controls(self):
        # 显示操作说明
        controls = [
            "8x8 Puzzle Mode Controls:",
            "WASD/Arrow Keys: Move (Virtual)",
            "Space: Place Piece (Final)",
            "Tab: Switch Piece",
            "1/2/3: Select Piece",
        ]
        
        start_y = BOARD_HEIGHT * CELL_SIZE + 10
        for i, text in enumerate(controls):
            color = COLORS['YELLOW'] if i == 0 else COLORS['WHITE']
            font = self.font if i == 0 else self.small_font
            rendered = font.render(text, True, color)
            self.screen.blit(rendered, (10, start_y + i * 18))

    def draw(self):
        self.screen.fill(COLORS['BLACK'])
        
        self.draw_board()
        # self.draw_ghost_piece()  # 投影功能已禁用
        self.draw_active_piece()  # 绘制当前方块
        self.draw_round_pieces()  # 绘制当前回合的方块
        self.draw_info()
        self.draw_controls()
        
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            self.clock.tick(60)  # 60 FPS
            
            running = self.handle_events()
            self.draw()
        
        pygame.quit()


def main():
    try:
        game = PuzzleTetrisGUI()
        game.run()
    except Exception as e:
        print(f"Game error: {e}")
        print("Please make sure pygame is installed: pip install pygame")


if __name__ == "__main__":
    main()
