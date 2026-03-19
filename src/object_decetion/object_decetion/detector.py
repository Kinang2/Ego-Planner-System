"""
detector.py
封装 YOLOv8 推理，与 ROS2 无关，可单独测试。
使用 third_party/ultralytics 源码，不依赖 pip install。
"""

import sys
import os

# ── 加载 YOLOv8 源码路径 ──────────────────────────────────────────────
_PKG_ROOT = os.path.expanduser(
    '~/Ego-planner-stystem/src/object_decetion'
)
_YOLO_SRC = os.path.join(_PKG_ROOT, 'third_party', 'ultralytics')

if _YOLO_SRC not in sys.path:
    sys.path.insert(0, _YOLO_SRC)

from ultralytics import YOLO   # noqa: E402
import numpy as np
import cv2


class YOLODetector:
    """
    封装 YOLOv8 推理。

    参数
    ----
    weights_path : str   .pt 权重文件路径
    conf         : float 置信度阈值，默认 0.5
    device       : str   推理设备，'cpu' 或 '0'（GPU 0）
    """

    def __init__(self,
                 weights_path: str = None,
                 conf: float = 0.5,
                 device: str = 'cpu'):

        if weights_path is None:
            weights_path = os.path.join(_PKG_ROOT, 'weights', 'yolov8n.pt')

        weights_path = os.path.realpath(os.path.expanduser(weights_path))

        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"权重文件不存在: {weights_path}")

        self.conf   = conf
        self.device = device
        self.model  = YOLO(weights_path)
        self.model.to('cuda:' + device if device.isdigit() else device)
        print(f"[YOLODetector] 权重: {weights_path}")
        print(f"[YOLODetector] 设备: {device}, 置信度: {conf}")
        print(f"[YOLODetector] 类别数: {len(self.model.names)}")

    def infer(self, bgr_image: np.ndarray):
        """
        对一帧图像做推理。

        参数
        ----
        bgr_image : np.ndarray  OpenCV BGR 格式 (H, W, 3)

        返回
        ----
        detections : list[dict]
            每项包含:
              'label'    : str   类别名
              'class_id' : int   类别ID
              'conf'     : float 置信度
              'bbox'     : [x1, y1, x2, y2]  像素坐标
        annotated : np.ndarray
            画好检测框的 BGR 图像
        """
        results = self.model.predict(
            source=bgr_image,
            conf=self.conf,
            device=self.device,
            verbose=False
        )

        detections = []
        result = results[0]

        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf     = float(box.conf[0])
            cls_id   = int(box.cls[0])
            label    = self.model.names[cls_id]

            detections.append({
                'label':    label,
                'class_id': cls_id,
                'conf':     conf,
                'bbox':     [int(x1), int(y1), int(x2), int(y2)]
            })

        annotated = result.plot()   # BGR，已画好框和标签

        return detections, annotated


# ── 单独测试入口（不依赖ROS2）────────────────────────────────────────
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='YOLOv8 单帧推理测试')
    parser.add_argument('--weights', type=str, default=None,
                        help='权重路径，默认使用 weights/yolov8n.pt')
    parser.add_argument('--image',   type=str, required=True,
                        help='测试图像路径')
    parser.add_argument('--conf',    type=float, default=0.5)
    parser.add_argument('--device',  type=str,   default='cpu')
    args = parser.parse_args()

    detector = YOLODetector(args.weights, args.conf, args.device)

    img = cv2.imread(args.image)
    if img is None:
        print(f"无法读取图像: {args.image}")
        sys.exit(1)

    dets, annotated = detector.infer(img)
    print(f"\n检测到 {len(dets)} 个目标:")
    for d in dets:
        print(f"  [{d['class_id']:2d}] {d['label']:15s} "
              f"conf={d['conf']:.2f}  bbox={d['bbox']}")

    out_path = '/tmp/yolov8_result.jpg'
    cv2.imwrite(out_path, annotated)
    print(f"\n结果已保存: {out_path}")
    cv2.imshow('YOLOv8', annotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
