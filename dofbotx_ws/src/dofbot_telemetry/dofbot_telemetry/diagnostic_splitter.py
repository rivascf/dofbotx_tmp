#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from diagnostic_msgs.msg import DiagnosticArray
from std_msgs.msg import Float32, Float32MultiArray

class DiagnosticSplitter(Node):
    def __init__(self):
        super().__init__('diagnostic_splitter')
        
        # Create subscribers and publishers
        self.sub = self.create_subscription(DiagnosticArray, '/diagnostics', self._on_diagnostics_callback, 10)
        # self.pub_cpu0 = self.create_publisher(Float32, '/graph/cpu0_usage', 10)
        self.pub_cpu = self.create_publisher(Float32MultiArray, '/graph/cpu_usage', 10)
        # self.pub_cpu1 = self.create_publisher(Float32, '/graph/cpu1_usage', 10)
        self.pub_ram = self.create_publisher(Float32, '/graph/ram_used', 10)
        self.pub_disk = self.create_publisher(Float32, '/graph/disk_used', 10)
        self.get_logger().info(f"'diagnostic_splitter' initialized, listening '/diagnostics' topic.")

    def _on_diagnostics_callback(self, msg):
        cpu_data = Float32MultiArray()
        cpu_vals = []
        disk_value = Float32()
        ram_value = Float32()

        for status in msg.status:
            # Check for CPU 0
            if 'cpu_core_' in status.name:
                for kv in status.values:
                    if kv.key == 'usage':
                        cpu_vals.append(float(kv.value))
            
            # Check for RAM info
            elif status.name == 'hardware_disk':
                for kv in status.values:
                    if kv.key == 'used':
                        disk_value.data=float(kv.value)
                        
            # Check for Disk info
            elif status.name == 'hardware_ram':
                for kv in status.values:
                    if kv.key == 'used':
                        ram_value.data = float(kv.value)

        cpu_data.data = cpu_vals
        self.pub_cpu.publish(cpu_data)
        self.pub_ram.publish(ram_value)
        self.pub_disk.publish(disk_value)


    def _on_diagnostics_old_callback(self, msg):
        for status in msg.status:
            # Check for CPU 0
            if status.name == 'System Hardware: CPU: cpu0':
                for kv in status.values:
                    if kv.key == 'usage':
                        self.pub_cpu0.publish(Float32(data=float(kv.value)))
            
            # Check for CPU 1
            elif status.name == 'System Hardware: CPU: cpu1':
                for kv in status.values:
                    if kv.key == 'usage':
                        self.pub_cpu1.publish(Float32(data=float(kv.value)))
            
            # Check for RAM info
            elif status.name == 'System Hardware: RAM Info':
                for kv in status.values:
                    if kv.key == 'used':
                        self.pub_ram.publish(Float32(data=float(kv.value)))
                        
            # Check for Disk info
            elif status.name == 'System Hardware: Disk Info':
                for kv in status.values:
                    if kv.key == 'used':
                        self.pub_disk.publish(Float32(data=float(kv.value)))
                                    

def init_node(args=None):
    rclpy.init(args=args)
    node = DiagnosticSplitter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    init_node()
