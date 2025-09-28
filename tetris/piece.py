from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence

PieceMatrix = List[List[int]]


@dataclass(frozen=True, slots=True)
class Piece:
    """拼图方块的数据结构。"""

    shape_id: str
    display_name: str
    matrix: PieceMatrix
    allow_rotate: bool
    allow_mirror: bool
    spawn_weight: float = 1.0
    color_hex: str | None = None
    notes: str | None = None
    _normalized_matrix: PieceMatrix | None = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "matrix", self._copy_matrix(self.matrix))
        if not self.matrix:
            raise ValueError("matrix 不能为空")
        size = len(self.matrix)
        if any(len(row) != size for row in self.matrix):
            raise ValueError("matrix 必须是方阵")
        if size == 0:
            raise ValueError("matrix 大小必须大于 0")
        for r, row in enumerate(self.matrix):
            for c, value in enumerate(row):
                if value not in (0, 1):
                    raise ValueError(f"matrix[{r}][{c}] = {value}，应为 0 或 1")

    @property
    def matrix_size(self) -> int:
        return len(self.matrix)

    @property
    def cell_count(self) -> int:
        return sum(value for row in self.matrix for value in row)

    @property
    def normalized_matrix(self) -> PieceMatrix:
        cached = self._normalized_matrix
        if cached is not None:
            return self._copy_matrix(cached)
        matrix = self._trim_empty_edges(self.matrix)
        object.__setattr__(self, "_normalized_matrix", matrix)
        return self._copy_matrix(matrix)

    def rotated(self, clockwise: bool = True, *, enforce_rule: bool = True) -> "Piece":
        if enforce_rule and not self.allow_rotate:
            raise ValueError(f"方块 {self.shape_id} 不允许旋转")
        m = self.matrix
        size = len(m)
        if clockwise:
            rotated_matrix = [[m[size - 1 - r][c] for r in range(size)] for c in range(size)]
        else:
            rotated_matrix = [[m[r][size - 1 - c] for r in range(size)] for c in range(size)]
        return Piece(
            shape_id=self.shape_id,
            display_name=self.display_name,
            matrix=rotated_matrix,
            allow_rotate=self.allow_rotate,
            allow_mirror=self.allow_mirror,
            spawn_weight=self.spawn_weight,
            color_hex=self.color_hex,
            notes=self.notes,
        )

    def mirrored(self, *, enforce_rule: bool = True) -> "Piece":
        if enforce_rule and not self.allow_mirror:
            raise ValueError(f"方块 {self.shape_id} 不允许镜像")
        mirrored_matrix = [list(reversed(row)) for row in self.matrix]
        return Piece(
            shape_id=self.shape_id,
            display_name=self.display_name,
            matrix=mirrored_matrix,
            allow_rotate=self.allow_rotate,
            allow_mirror=self.allow_mirror,
            spawn_weight=self.spawn_weight,
            color_hex=self.color_hex,
            notes=self.notes,
        )

    def iter_cells(self) -> Iterable[tuple[int, int]]:
        """遍历矩阵中为 1 的坐标。"""
        for r, row in enumerate(self.matrix):
            for c, value in enumerate(row):
                if value:
                    yield r, c

    @staticmethod
    def _copy_matrix(matrix: Sequence[Sequence[int]]) -> PieceMatrix:
        return [list(row) for row in matrix]

    @staticmethod
    def _trim_empty_edges(matrix: PieceMatrix) -> PieceMatrix:
        def is_empty_row(row: Sequence[int]) -> bool:
            return all(value == 0 for value in row)

        def is_empty_col(mat: PieceMatrix, col_index: int) -> bool:
            return all(row[col_index] == 0 for row in mat)

        top = 0
        bottom = len(matrix)
        while top < bottom and is_empty_row(matrix[top]):
            top += 1
        while bottom > top and is_empty_row(matrix[bottom - 1]):
            bottom -= 1

        left = 0
        right = len(matrix[0])
        while left < right and is_empty_col(matrix, left):
            left += 1
        while right > left and is_empty_col(matrix, right - 1):
            right -= 1

        if top >= bottom or left >= right:
            return [[0]]

        return [row[left:right] for row in matrix[top:bottom]]


def build_matrix_from_rows(rows: Sequence[str], matrix_size: int) -> PieceMatrix:
    if matrix_size <= 0:
        raise ValueError("matrix_size 必须大于 0")
    normalized_rows: List[str] = []
    for row in rows:
        text = (row or "").strip().replace(" ", "")
        if not text:
            text = "0" * matrix_size
        if set(text) - {"0", "1"}:
            raise ValueError(f"行数据 {text} 包含非法字符")
        if len(text) < matrix_size:
            text = text.ljust(matrix_size, "0")
        elif len(text) > matrix_size:
            raise ValueError(f"行数据 {text} 长度超过 matrix_size={matrix_size}")
        normalized_rows.append(text)

    if len(normalized_rows) < matrix_size:
        normalized_rows.extend(["0" * matrix_size] * (matrix_size - len(normalized_rows)))
    elif len(normalized_rows) > matrix_size:
        normalized_rows = normalized_rows[:matrix_size]

    matrix: PieceMatrix = []
    for text in normalized_rows:
        matrix.append([1 if ch == "1" else 0 for ch in text])
    return matrix
