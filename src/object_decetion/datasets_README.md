# 训练数据集说明

## 目录结构（标准YOLOv8格式）

```
datasets/
└── my_dataset/
    ├── images/
    │   ├── train/   ← 训练图像
    │   └── val/     ← 验证图像
    ├── labels/
    │   ├── train/   ← 对应的标注文件（.txt）
    │   └── val/
    └── data.yaml    ← 数据集配置文件
```

## data.yaml 示例

```yaml
path: /home/guo/ego-planner-stystem/src/object_decetion/datasets/my_dataset
train: images/train
val:   images/val

nc: 3  # 类别数量
names: ['person', 'car', 'obstacle']
```

## 训练命令

```bash
cd ~/ego-planner-stystem/src/object_decetion/third_party/ultralytics
python3 train.py \
    --data ../../datasets/my_dataset/data.yaml \
    --model yolov8n.pt \
    --epochs 100 \
    --imgsz 640 \
    --batch 16 \
    --project ../../weights/runs \
    --name my_model
```

训练完成后权重在：
`weights/runs/my_model/weights/best.pt`

修改 detection.launch.py 中的 weights_path 参数指向新权重即可。
