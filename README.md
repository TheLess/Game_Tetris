# Tetris 俄罗斯方块游戏引擎

一个基于 Python 的俄罗斯方块游戏核心引擎，支持从 Excel 配置文件加载自定义方块。

## 功能特性

- **方块数据结构**：完整的方块类，支持旋转、镜像、归一化等操作
- **Excel 配置加载**：从 `Block.xlsx` 读取方块配置，包括形状、颜色、权重等
- **游戏状态管理**：完整的游戏状态跟踪，包括棋盘、得分、消行等
- **游戏操作接口**：移动、旋转、软降、硬降等标准操作
- **日志系统**：详细的调试和错误日志
- **单元测试**：全面的测试覆盖

## 项目结构

```
Tetris/
├── Block.xlsx              # 方块配置文件
├── tetris/                 # 核心模块
│   ├── __init__.py        # 模块导出
│   ├── piece.py           # 方块数据结构
│   ├── piece_loader.py    # Excel 加载器
│   └── game.py            # 游戏主逻辑
├── tests/                  # 单元测试
│   ├── test_piece_loader.py
│   └── test_game.py
└── examples/              # 示例代码
    ├── show_pieces.py     # 展示方块信息
    └── run_basic_game.py  # 基础游戏演示
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
# 或者单独安装
pip install openpyxl pygame
```

### 2. 查看方块配置

```bash
python examples/show_pieces.py
```

### 3. 运行图形化游戏

```bash
python gui_game.py
```

### 4. 运行基础游戏示例

```bash
python examples/run_basic_game.py
```

### 5. 运行测试

```bash
python -m unittest tests/test_piece_loader.py
python -m unittest tests/test_game.py
```

## 使用示例

### 基础用法

```python
import logging
from tetris import GameConfig, create_game, tick, move_left, rotate

# 启用日志
logging.basicConfig(level=logging.INFO)

# 从 Excel 创建游戏配置
config = GameConfig.from_excel("Block.xlsx", random_seed=42)

# 创建游戏状态
state = create_game(config)

# 游戏操作
move_left(state)
rotate(state)
tick(state)  # 向下移动一格

print(f"当前得分: {state.score}")
print(f"游戏结束: {state.game_over}")
```

### 自定义配置

```python
from tetris import GameConfig, Piece

# 创建自定义方块
custom_piece = Piece(
    shape_id="CUSTOM",
    display_name="自定义方块",
    matrix=[[1, 1], [1, 0]],
    allow_rotate=True,
    allow_mirror=False,
    color_hex="#FF0000"
)

# 创建自定义配置
config = GameConfig(
    pieces=[custom_piece],
    board_width=8,
    board_height=16
)

state = create_game(config)
```

## Excel 配置格式

`Block.xlsx` 文件应包含以下列：

| 列名 | 类型 | 说明 |
|------|------|------|
| ShapeID | 文本 | 方块唯一标识 |
| DisplayName | 文本 | 显示名称 |
| Cells | 数字 | 有效格子数（用于验证） |
| AllowRotate | 布尔 | 是否允许旋转 |
| AllowMirror | 布尔 | 是否允许镜像 |
| SpawnWeight | 数字 | 生成权重 |
| ColorHex | 文本 | 十六进制颜色代码 |
| MatrixSize | 数字 | 矩阵大小 |
| Row1-Row5 | 文本 | 矩阵行数据（如 "110" 表示前两格填充） |
| Notes | 文本 | 备注信息 |

## API 参考

### 核心类

- `Piece`: 方块数据结构
- `GameConfig`: 游戏配置
- `GameState`: 游戏状态

### 主要函数

- `create_game(config)`: 创建新游戏
- `tick(state)`: 游戏时钟（向下移动）
- `move_left(state)` / `move_right(state)`: 左右移动
- `rotate(state, clockwise=True)`: 旋转方块
- `soft_drop(state)`: 软降（加速下落）
- `hard_drop(state)`: 硬降（瞬间落地）
- `hold_state_snapshot(state)`: 获取状态快照

## 开发说明

### 日志配置

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,  # 详细调试信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 扩展方块类型

1. 在 `Block.xlsx` 中添加新行
2. 设置相应的矩阵数据和属性
3. 重新加载配置即可使用

### 自定义游戏规则

继承或修改 `game.py` 中的相关函数来实现自定义规则，如：
- 修改消行得分算法
- 添加特殊方块效果
- 实现不同的旋转规则

## 许可证

本项目采用 MIT 许可证。
