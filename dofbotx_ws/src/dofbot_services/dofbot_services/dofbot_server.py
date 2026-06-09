#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from dofbot_interfaces.srv import GetStatus


class DofbotServServer(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        # Creacion del servidor
        self.__status_server = self.create_service(
            GetStatus,
            '/dofbot_status_srv',
            self._on_status_srv_clbk
        )

        self.get_logger().info(f"{node_name} server inicializado.")

    def _on_status_srv_clbk(self, request:GetStatus.Request, response:GetStatus.Response):
        self.get_logger().info("Recibí una peticion...")
        #Tratamiento de la peticion
        is_active = request.is_robot_active

        # Proceso del servidor
        if is_active:
            response.is_active = is_active
        else:
            response.is_active = False

        # Tratamiento de la respuesta
        response.success = True
        response.string_status_message = "Todo ok"        

        return response


def init_server(args=None):
    rclpy.init(args=args)
    status_server_node = DofbotServServer('dofbot_server_node')
    rclpy.spin(status_server_node)
    rclpy.shutdown()

if __name__ == "__main__":
    init_server()