#!/usr/bin/env python3

import rclpy
from dofbot_interfaces.msg import Telemetry
from rclpy.node import Node


class TelemetrySubsNode(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self._telem_sub = self.create_subscription(
            Telemetry, "/telemetry", self._on_telem_clbk, 10
        )
        self.get_logger().info(f"Nodo {node_name} inicializado.")

    def _on_telem_clbk(self, telem_msg: Telemetry):
        msg_str = f"Recibi: [{telem_msg.status}] posicion: [{telem_msg.pos_x}, {telem_msg.pos_y}, {telem_msg.pos_z}]"
        self.get_logger().info(msg_str)


def main(args=None):
    try:
        rclpy.init(args=args)
        telem_sub_node = TelemetrySubsNode("telem_sub_node")
        rclpy.spin(telem_sub_node)
    except KeyboardInterrupt:
        telem_sub_node.get_logger().info("Keyboard interupt received, shutting down.")
    finally:
        telem_sub_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

