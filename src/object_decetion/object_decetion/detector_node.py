#!/home/guo/Ego-planner-stystem/src/object_decetion/venv/bin/python3
"""
detector_node.py
ROS2 节点：订阅 /rgb_image，调用 YOLOv8 推理，发布检测结果。
本文件用虚拟环境 Python 直接运行，不经过 colcon install。

订阅：/rgb_image          sensor_msgs/Image
发布：/detection_image    sensor_msgs/Image        标注框图像
      /detected_objects   vision_msgs/Detection2DArray
"""

import os
import sys

# ── 虚拟环境路径（保证 torch 等可用）────────────────────────────────
_VENV = os.path.expanduser(
    '~/Ego-planner-stystem/src/object_decetion/venv'
)
_VENV_SITE = os.path.join(_VENV, 'lib', 'python3.12', 'site-packages')
if _VENV_SITE not in sys.path:
    sys.path.insert(0, _VENV_SITE)

# ── YOLOv8 源码路径 ───────────────────────────────────────────────
_PKG_ROOT = os.path.expanduser(
    '~/Ego-planner-stystem/src/object_decetion'
)
_YOLO_SRC = os.path.join(_PKG_ROOT, 'third_party', 'ultralytics')
if _YOLO_SRC not in sys.path:
    sys.path.insert(0, _YOLO_SRC)

# ── detector.py 与本文件同目录 ────────────────────────────────────
_THIS_DIR = os.path.dirname(os.path.realpath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy

from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection2D, \
    ObjectHypothesisWithPose, BoundingBox2D

import cv2
import numpy as np
from cv_bridge import CvBridge

from detector import YOLODetector


class DetectorNode(Node):

    def __init__(self):
        super().__init__('detector_node')

        # ── 参数 ──────────────────────────────────────────────────
        self.declare_parameter(
            'weights_path',
            os.path.join(_PKG_ROOT, 'weights', 'yolov8n.pt'))
        self.declare_parameter('conf_threshold', 0.5)
        self.declare_parameter('device', 'cpu')
        self.declare_parameter('image_topic', '/rgb_image')

        weights   = self.get_parameter('weights_path') \
                        .get_parameter_value().string_value
        conf      = self.get_parameter('conf_threshold') \
                        .get_parameter_value().double_value
        device    = self.get_parameter('device') \
                        .get_parameter_value().string_value
        img_topic = self.get_parameter('image_topic') \
                        .get_parameter_value().string_value

        # ── 初始化检测器 ──────────────────────────────────────────
        # 将cuda:0转换为YOLOv8格式的'0'
        yolo_device = device.replace('cuda:', '') if 'cuda:' in device else device
        self.detector = YOLODetector(weights, conf, yolo_device)
        self.bridge   = CvBridge()

        # ── QoS：匹配 Gazebo bridge 的 best_effort ────────────────
        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        # ── 订阅 /rgb_image ───────────────────────────────────────
        self.sub = self.create_subscription(
            Image, img_topic, self.image_callback, qos)

        # ── 发布 ─────────────────────────────────────────────────
        self.pub_img = self.create_publisher(
            Image, '/detection_image', 10)
        self.pub_det = self.create_publisher(
            Detection2DArray, '/detected_objects', 10)

        self.get_logger().info(
            f'\n  订阅: {img_topic}'
            f'\n  权重: {weights}'
            f'\n  设备: {device}, 置信度: {conf}'
        )

    def image_callback(self, msg: Image):
        # ROS Image → OpenCV BGR
        try:
            bgr = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'cv_bridge 转换失败: {e}')
            return

        # ── 推理 ─────────────────────────────────────────────────
        detections, annotated = self.detector.infer(bgr)

        # ── 发布标注图像 ──────────────────────────────────────────
        ann_msg = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
        ann_msg.header = msg.header
        self.pub_img.publish(ann_msg)

        # ── 发布检测结果 ──────────────────────────────────────────
        det_array = Detection2DArray()
        det_array.header = msg.header

        for d in detections:
            det = Detection2D()
            det.header = msg.header

            x1, y1, x2, y2 = d['bbox']
            bbox = BoundingBox2D()
            bbox.center.position.x = float((x1 + x2) / 2)
            bbox.center.position.y = float((y1 + y2) / 2)
            bbox.size_x = float(x2 - x1)
            bbox.size_y = float(y2 - y1)
            det.bbox = bbox

            hyp = ObjectHypothesisWithPose()
            hyp.hypothesis.class_id = str(d['class_id'])
            hyp.hypothesis.score    = d['conf']
            det.results.append(hyp)

            det_array.detections.append(det)

        self.pub_det.publish(det_array)

        if detections:
            labels = [f"{d['label']}({d['conf']:.2f})"
                      for d in detections]
            self.get_logger().info(f'检测到: {", ".join(labels)}')


def main():
    rclpy.init()
    node = DetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
