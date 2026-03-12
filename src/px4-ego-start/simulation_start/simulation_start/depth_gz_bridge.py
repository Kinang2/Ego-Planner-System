#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
from std_msgs.msg import Header
from rclpy.qos import qos_profile_sensor_data

class DepthPublisher(Node):
    def __init__(self):
        super().__init__('depth_img_transfer')
        self.subscription = self.create_subscription(
            Image,
            '/depth_camera',
            self.depth_callback,
            10
        )
        self.publisher = self.create_publisher(
            Image,
            '/depth_camera_bestef',
            qos_profile_sensor_data
        )
        self.bridge = CvBridge()
        self.background_depth = 10.0
        self.saved = False

    def depth_callback(self, msg):
        height = int(msg.height)
        width = int(msg.width)
        depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
        depth_data = msg.data
        depth_array = np.frombuffer(depth_data, dtype=np.float32).reshape((height, width))
        depth_msg = self.bridge.cv2_to_imgmsg(depth_array, encoding="32FC1")
        depth_msg.header = Header()
        depth_msg.header.stamp = self.get_clock().now().to_msg()
        depth_msg.header.frame_id = "camera_link"
        self.publisher.publish(depth_msg)
        # if not self.saved:
        #     print(depth_msg.data)
        #     self.saved = True

def main(args=None):
    rclpy.init(args=args)
    node = DepthPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
