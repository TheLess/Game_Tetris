from __future__ import annotations

import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from tetris import GameConfig, create_game, hard_drop, hold_state_snapshot, move_left, move_right, rotate, soft_drop, tick

logging.basicConfig(level=logging.INFO)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    config = GameConfig.from_excel(root / "Block.xlsx", random_seed=42)
    state = create_game(config)

    logging.info("初始状态: %s", hold_state_snapshot(state))

    # 示例操作序列
    move_left(state)
    move_right(state)
    rotate(state)
    soft_drop(state)
    tick(state)
    hard_drop(state)

    logging.info("最终状态: %s", hold_state_snapshot(state))


if __name__ == "__main__":
    main()
