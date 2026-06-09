#!/usr/bin/env python3

import rclpy
from dofbot_interfaces.msg import Telemetry
from rclpy.node import Node


class TelemetryNode(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self._telemetry_pub = self.create_publisher(Telemetry, "/telemetry", 10)
        self._telemetry_timer = self.create_timer(1.0, self._on_telemetry_clbk)
        self.get_logger().info(f"Nodo [{node_name}] inicializado")

    def _on_telemetry_clbk(self):
        telemetry_msg = Telemetry()
        telemetry_msg.status = "Active"
        telemetry_msg.pos_x = 0.0
        telemetry_msg.pos_y = 0.0
        telemetry_msg.pos_z = 0.0

        self._telemetry_pub.publish(telemetry_msg)


def main(args=None):
    try:
        rclpy.init(args=args)
        telemetry_node = TelemetryNode("telemetry_node")
        rclpy.spin(telemetry_node)
    except KeyboardInterrupt as e:
        pass
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()

