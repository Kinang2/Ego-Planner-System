#!/bin/bash
# setup_venv.sh
# 一键创建 object_decetion 虚拟环境并安装所有依赖
# 使用方式：bash setup_venv.sh
# 注意：需要先 source ROS2 环境（source /opt/ros/jazzy/setup.bash）

set -e  # 任意命令失败则退出

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PKG_DIR/venv"
REQUIREMENTS="$PKG_DIR/requirements.txt"
YOLO_SRC="$PKG_DIR/third_party/ultralytics"
WEIGHTS_DIR="$PKG_DIR/weights"

echo "=============================================="
echo " object_decetion 虚拟环境安装脚本"
echo " 包目录: $PKG_DIR"
echo "=============================================="

# ── 检查 ROS2 环境 ────────────────────────────────────────────────────
if ! python3 -c "import rclpy" 2>/dev/null; then
    echo "[ERROR] 未检测到 ROS2 环境，请先执行："
    echo "  source /opt/ros/jazzy/setup.bash"
    exit 1
fi
echo "[OK] ROS2 环境正常"

# ── 创建虚拟环境 ──────────────────────────────────────────────────────
if [ -d "$VENV_DIR" ]; then
    echo "[INFO] 虚拟环境已存在：$VENV_DIR，跳过创建"
else
    echo "[INFO] 创建虚拟环境（--system-site-packages 继承 ROS2 库）..."
    python3 -m venv "$VENV_DIR" --system-site-packages
    echo "[OK] 虚拟环境创建完成"
fi

# ── 激活虚拟环境 ──────────────────────────────────────────────────────
source "$VENV_DIR/bin/activate"
echo "[OK] 虚拟环境已激活：$VIRTUAL_ENV"

# ── 安装依赖 ──────────────────────────────────────────────────────────
echo "[INFO] 安装 requirements.txt 中的依赖..."
pip install -r "$REQUIREMENTS"

# ── 强制确认 numpy<2.0（与 cv_bridge 兼容）────────────────────────────
echo "[INFO] 确认 numpy 版本 <2.0..."
pip install "numpy<2.0" --quiet

# ── 卸载 pip 版 opencv（如果误装了）─────────────────────────────────────
if pip show opencv-python &>/dev/null; then
    echo "[WARN] 检测到 pip 版 opencv-python，卸载以避免冲突..."
    pip uninstall opencv-python -y
fi

# ── 验证关键依赖 ──────────────────────────────────────────────────────
echo ""
echo "[INFO] 验证关键依赖..."
python3 -c "
import sys
errors = []

try:
    import rclpy
    print('  [OK] rclpy')
except ImportError as e:
    errors.append(f'  [FAIL] rclpy: {e}')

try:
    import cv_bridge
    print('  [OK] cv_bridge')
except ImportError as e:
    errors.append(f'  [FAIL] cv_bridge: {e}')

try:
    import cv2
    print(f'  [OK] cv2: {cv2.__version__}')
except ImportError as e:
    errors.append(f'  [FAIL] cv2: {e}')

try:
    import torch
    cuda = torch.cuda.is_available()
    print(f'  [OK] torch: {torch.__version__}, CUDA: {cuda}')
except ImportError as e:
    errors.append(f'  [FAIL] torch: {e}')

try:
    import numpy as np
    print(f'  [OK] numpy: {np.__version__}')
    if np.__version__ >= '2.0.0':
        errors.append('  [WARN] numpy >= 2.0，可能与 cv_bridge 冲突，建议降级')
except ImportError as e:
    errors.append(f'  [FAIL] numpy: {e}')

try:
    sys.path.insert(0, '$YOLO_SRC')
    from ultralytics import YOLO
    print('  [OK] ultralytics (YOLOv8 源码)')
except ImportError as e:
    errors.append(f'  [FAIL] ultralytics: {e}')

if errors:
    print('')
    print('[WARNING] 以下问题需要注意：')
    for e in errors:
        print(e)
else:
    print('')
    print('[OK] 所有依赖验证通过')
"

# ── 检查 YOLOv8 源码 ─────────────────────────────────────────────────
echo ""
if [ -d "$YOLO_SRC" ]; then
    VERSION=$(head -5 "$YOLO_SRC/ultralytics/__init__.py" | grep "__version__" | cut -d'"' -f2)
    echo "[OK] YOLOv8 源码存在，版本: $VERSION"
else
    echo "[WARN] YOLOv8 源码不存在，正在克隆..."
    mkdir -p "$PKG_DIR/third_party"
    cd "$PKG_DIR/third_party"
    git clone --depth 1 https://github.com/ultralytics/ultralytics.git
    cd ultralytics
    git fetch --tags
    git checkout v8.2.0
    # 修复 torch 2.6+ 兼容问题
    sed -i 's/torch.load(file, map_location="cpu")/torch.load(file, map_location="cpu", weights_only=False)/g' \
        ultralytics/nn/tasks.py
    echo "[OK] YOLOv8 v8.2.0 克隆完成并已修复兼容性"
fi

# ── 检查权重文件 ──────────────────────────────────────────────────────
echo ""
if [ -f "$WEIGHTS_DIR/yolov8n.pt" ]; then
    echo "[OK] 权重文件存在：$WEIGHTS_DIR/yolov8n.pt"
else
    echo "[WARN] 权重文件不存在，正在下载 yolov8n.pt..."
    mkdir -p "$WEIGHTS_DIR"
    wget -O "$WEIGHTS_DIR/yolov8n.pt" \
        "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt"
    echo "[OK] 权重下载完成"
fi

echo ""
echo "=============================================="
echo " 安装完成！"
echo " 激活虚拟环境：source $VENV_DIR/bin/activate"
echo " 启动检测节点："
echo "   ros2 launch object_decetion detection.launch.py"
echo "=============================================="
