#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue

import jtop
from telem_utils.jtop_utils import(
    other_status,
    board_status,
    disk_status,
    cpu_status,
    fan_status,
    gpu_status,
    ram_status,
    swap_status,
    power_status,
    temp_status,
    emc_status
)

class JTOPUtilsNode(Node):
    def __init__(self, node_name):
        super().__init__(node_name)

        self.declare_parameter('interval', 0.5)  # Default interval 0.5
        self.declare_parameter('level_error', 60)
        self.declare_parameter('level_warning', 40)
        self.declare_parameter('level_ok', 20)
        self.level_options = {
            self.get_parameter('level_error')._value: DiagnosticStatus.ERROR,
            self.get_parameter('level_warning')._value: DiagnosticStatus.WARN,
            self.get_parameter('level_ok')._value: DiagnosticStatus.OK,
        }
        # Create diagnostics publisher
        self._publisher = self.create_publisher(
            DiagnosticArray,
            'nv_diagnostics',
            1
        )

        timer_period = self.get_parameter('interval')._value
        self.timer = self.create_timer(timer_period, self.jetson_callback)
        self.i = 0
        self.jetson = jtop.jtop(interval=0.5)
        self.arr = DiagnosticArray()
        # self.get_logger().info("Jetson Stats has started with interval : {}\n You can run following:\n  1. $ros2 run rqt_topic rqt_topic \n  2. Services for controlling fan_speed, power_mode, jetson_clocks\n".format(timer_period))
        self.get_logger().info("Jetson Stats has started with interval : {}".format(timer_period))

    def start(self):
        self.jetson.start()
        # Extract board information
        board = self.jetson.board
        # Define hardware name
        self.hardware = board["platform"]["Machine"]
        self.board_status = board_status(self.hardware, board, 'board')
        # Set callback
        # self.jetson.attach(self.jetson_callback)

    def jetson_callback(self):
        # Add timestamp
        self.arr.header.stamp = self.get_clock().now().to_msg()
        # Status board and board info
        self.arr.status = [other_status(
            self.hardware, self.jetson, jtop.__version__)]
        # Make diagnostic message for each cpu
        self.arr.status += [cpu_status(self.hardware, name, cpu)
                            for name, cpu in enumerate(self.jetson.cpu['cpu'])]
        # Make diagnostic message for each gpu
        self.arr.status += [gpu_status(self.hardware, name, self.jetson.gpu[name])
                            for name in self.jetson.gpu]
        # Merge all other diagnostics
        self.arr.status += [ram_status(self.hardware,
                                       self.jetson.memory['RAM'], 'mem')]
        self.arr.status += [swap_status(self.hardware,
                                        self.jetson.memory['SWAP'], 'mem')]
        self.arr.status += [emc_status(self.hardware,
                                       self.jetson.memory['EMC'], 'mem')]
        # Temperature
        self.arr.status += [temp_status(self.hardware,
                                        self.jetson.temperature, self.level_options)]
        # Read power
        self.arr.status += [power_status(self.hardware, self.jetson.power)]
        # Fan controller
        if self.jetson.fan is not None:
            self.arr.status += [fan_status(self.hardware, key, value)
                                for key, value in self.jetson.fan.items()]
        # Status board and board info
        self.arr.status += [self.board_status]
        # Add disk status
        self.arr.status += [disk_status(self.hardware,
                                        self.jetson.disk, 'board')]
        # Update status jtop
        # rospy.logdebug("jtop message %s" % rospy.get_time())
        self.publisher_.publish(self.arr)


def init_node(args=None):
    rclpy.init(args=args)
    jtop_node = JTOPUtilsNode('jtop_node')
    jtop_node.start()
    rclpy.spin(jtop_node)
    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    jtop_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    init_node()
