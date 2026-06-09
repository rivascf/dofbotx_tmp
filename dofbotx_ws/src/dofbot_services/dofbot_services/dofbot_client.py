#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from dofbot_interfaces.srv import GetStatus


class DofbotServiceClient(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.__status_client = self.create_client(
            GetStatus,
            '/dofbot_status_srv',
        )
        self.__wait_count = 3
        self.get_logger().info("Service Client inicializado...")

    def call_service(self, is_active: bool):
        self.get_logger().info("Waiting for service...")
        while not self.__status_client.wait_for_service(timeout_sec=1.0):
            if self.__wait_count == 0:
                self.get_logger().info("Excedido el número de reintentos. Bye.")
                return None
            self.get_logger().info(f"Intento {self.__wait_count}: esperando por el servicio 1 seg.")
            self.__wait_count = self.__wait_count - 1

        self.__wait_count = 3
        peticion = GetStatus.Request()
        peticion.is_robot_active = is_active
        self.future = self.__status_client.call_async(peticion)
        rclpy.spin_until_future_complete(self, future=self.future)
        return self.future.result()


def init_client(args=None):
    rclpy.init(args=args)
    service_client = DofbotServiceClient('service_client_node')
    resultado = service_client.call_service(True)
    if resultado:
        service_client.get_logger().info(f"Resultado de la llamada: {resultado.is_active}")
        service_client.get_logger().info(f"Resultado del proceso: {resultado.success}")
        service_client.get_logger().info(f"Mensaje del proceso: {resultado.string_status_message}")

    rclpy.shutdown()

if __name__ == "__main__":
    init_client()