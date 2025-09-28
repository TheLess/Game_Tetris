from __future__ import annotations

import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

import pygame
from tetris import GameConfig, create_game, hard_drop, move_left, move_right, rotate, soft_drop, tick

# 游戏配置
CELL_SIZE = 30
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
WINDOW_WIDTH = CELL_SIZE * (BOARD_WIDTH + 6)  # 额外空间显示信息
WINDOW_HEIGHT = CELL_SIZE * BOARD_HEIGHT + 100

# 颜色定义
COLORS = {
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255),
    'GRAY': (128, 128, 128),
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


class TetrisGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("俄罗斯方块")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        # 游戏状态
        config = GameConfig.from_excel(root / "Block.xlsx", random_seed=None)
        self.game_state = create_game(config)
        
        # 游戏计时
        self.fall_time = 0
        self.fall_speed = 500  # 毫秒

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    move_left(self.game_state)
                elif event.key == pygame.K_RIGHT:
                    move_right(self.game_state)
                elif event.key == pygame.K_DOWN:
                    soft_drop(self.game_state)
                elif event.key == pygame.K_UP:
                    rotate(self.game_state)
                elif event.key == pygame.K_SPACE:
                    hard_drop(self.game_state)
                elif event.key == pygame.K_r and self.game_state.game_over:
                    # 重新开始游戏
                    config = GameConfig.from_excel(root / "Block.xlsx", random_seed=None)
                    self.game_state = create_game(config)
        
        return True

    def update(self, dt):
        if not self.game_state.game_over:
            self.fall_time += dt
            if self.fall_time >= self.fall_speed:
                tick(self.game_state)
                self.fall_time = 0

    def draw_cell(self, x, y, color):
        rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, COLORS['WHITE'], rect, 1)

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

    def draw_active_piece(self):
        if self.game_state.active_piece is None:
            return
        
        piece = self.game_state.active_piece
        color = PIECE_COLORS.get(piece.shape_id, COLORS['GRAY'])
        
        for r, row in enumerate(piece.matrix):
            for c, value in enumerate(row):
                if value:
                    x = self.game_state.active_col + c
                    y = self.game_state.active_row + r
                    if 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
                        self.draw_cell(x, y, color)

    def draw_next_piece(self):
        if self.game_state.next_piece is None:
            return
        
        # 在右侧显示下一个方块
        start_x = BOARD_WIDTH + 1
        start_y = 2
        
        piece = self.game_state.next_piece
        color = PIECE_COLORS.get(piece.shape_id, COLORS['GRAY'])
        
        # 绘制标题
        text = self.font.render("下一个:", True, COLORS['WHITE'])
        self.screen.blit(text, (start_x * CELL_SIZE, 0))
        
        # 绘制方块
        for r, row in enumerate(piece.normalized_matrix):
            for c, value in enumerate(row):
                if value:
                    self.draw_cell(start_x + c, start_y + r, color)

    def draw_info(self):
        # 显示得分和其他信息
        info_x = (BOARD_WIDTH + 1) * CELL_SIZE
        
        score_text = self.font.render(f"得分: {self.game_state.score}", True, COLORS['WHITE'])
        self.screen.blit(score_text, (info_x, 150))
        
        lines_text = self.font.render(f"消行: {self.game_state.total_lines_cleared}", True, COLORS['WHITE'])
        self.screen.blit(lines_text, (info_x, 190))
        
        if self.game_state.game_over:
            game_over_text = self.font.render("游戏结束!", True, COLORS['RED'])
            self.screen.blit(game_over_text, (info_x, 250))
            
            restart_text = self.font.render("按 R 重新开始", True, COLORS['WHITE'])
            self.screen.blit(restart_text, (info_x, 290))

    def draw_controls(self):
        # 显示操作说明
        controls = [
            "操作说明:",
            "← → 移动",
            "↓ 软降",
            "↑ 旋转", 
            "空格 硬降",
        ]
        
        start_y = BOARD_HEIGHT * CELL_SIZE + 10
        for i, text in enumerate(controls):
            color = COLORS['YELLOW'] if i == 0 else COLORS['WHITE']
            rendered = self.font.render(text, True, color)
            self.screen.blit(rendered, (10, start_y + i * 20))

    def draw(self):
        self.screen.fill(COLORS['BLACK'])
        
        self.draw_board()
        self.draw_active_piece()
        self.draw_next_piece()
        self.draw_info()
        self.draw_controls()
        
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60)  # 60 FPS
            
            running = self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()


def main():
    try:
        game = TetrisGUI()
        game.run()
    except Exception as e:
        print(f"游戏运行出错: {e}")
        print("请确保已安装 pygame: pip install pygame")


if __name__ == "__main__":
    main()
