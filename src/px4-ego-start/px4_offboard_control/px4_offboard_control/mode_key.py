#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class KeyPublisher(Node):
    def __init__(self):
        super().__init__('key_publisher')

        # 创建发布者
        self.pub = self.create_publisher(String, '/mode_key', 10)

        self.get_logger().info("键盘指令发布节点启动，等待输入字母...")

    def run(self):
        while rclpy.ok():
            key = input("请输入字母并回车 >>> ").strip()

            if not key:
                continue

            # 发布消息
            msg = String()
            msg.data = key
            self.pub.publish(msg)

            # 打印 info
            self.get_logger().info(f"已发布字母：{key}")

            # 可选：对不同字母打印不同提示
            if key == 'm':
                self.get_logger().info("manual control command sent")
            elif key == 'p':
                self.get_logger().info("position control command sent")
            elif key == 'o':
                self.get_logger().info("offboard control command sent")
            elif key == 'l':
                self.get_logger().info("land control command sent")
            else:
                self.get_logger().info(f"unknown command: {key}")


def main(args=None):
    rclpy.init(args=args)
    node = KeyPublisher()

    try:
        node.run()
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
