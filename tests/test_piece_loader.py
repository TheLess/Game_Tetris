from __future__ import annotations

import sys
import unittest
from pathlib import Path

# 添加项目根目录到 Python 路径
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from tetris import PieceLoadError, load_pieces_from_excel

DATA_PATH = Path(__file__).resolve().parent.parent / "Block.xlsx"


class PieceLoaderTests(unittest.TestCase):
    def test_load_pieces_from_excel_returns_expected_piece(self) -> None:
        pieces = load_pieces_from_excel(DATA_PATH)
        self.assertGreater(len(pieces), 0)

        pieces_by_id = {piece.shape_id: piece for piece in pieces}
        self.assertIn("I001", pieces_by_id)

        i_piece = pieces_by_id["I001"]
        self.assertEqual(i_piece.display_name, "I型直线(4格)")
        self.assertTrue(i_piece.allow_rotate)
        self.assertTrue(i_piece.allow_mirror)
        self.assertAlmostEqual(i_piece.spawn_weight, 1.0)
        self.assertEqual(i_piece.color_hex, "#1E90FF")

        self.assertEqual(len(i_piece.matrix), 5)
        expected_matrix = [
            [0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0],
            [1, 0, 0, 0, 0],
            [1, 0, 0, 0, 0],
            [1, 0, 0, 0, 0],
        ]
        self.assertEqual(i_piece.matrix, expected_matrix)
        self.assertEqual(i_piece.cell_count, 4)

        expected_normalized = [
            [1],
            [1],
            [1],
            [1],
        ]
        self.assertEqual(i_piece.normalized_matrix, expected_normalized)

    def test_load_pieces_from_excel_missing_file(self) -> None:
        missing_path = DATA_PATH.with_name("missing.xlsx")
        with self.assertRaises(PieceLoadError):
            load_pieces_from_excel(missing_path)


if __name__ == "__main__":
    unittest.main()
