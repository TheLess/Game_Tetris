from __future__ import annotations

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from tetris import load_pieces_from_excel


def main() -> None:
    excel_path = Path(__file__).resolve().parent.parent / "Block.xlsx"
    pieces = load_pieces_from_excel(excel_path)
    print(f"从 {excel_path.name} 读取到 {len(pieces)} 个方块:\n")
    for piece in pieces:
        print(f"ID: {piece.shape_id}")
        print(f"名称: {piece.display_name}")
        print(f"可旋转: {piece.allow_rotate} | 可镜像: {piece.allow_mirror}")
        print(f"权重: {piece.spawn_weight}")
        print(f"颜色: {piece.color_hex or '未设置'}")
        print("矩阵:")
        for row in piece.matrix:
            print(" ".join(str(cell) for cell in row))
        print(f"有效格子数: {piece.cell_count}")
        print(f"备注: {piece.notes or '无'}")
        print("-" * 40)


if __name__ == "__main__":
    main()
