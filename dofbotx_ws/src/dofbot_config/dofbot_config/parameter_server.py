#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rcl_interfaces.msg import ParameterDescriptor, SetParametersResult

import re

IPV4_REGEX = r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"


class DofbotParamSrv(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        # Para declarar un parametro se utiliza 
        # el metodo 'declare_aparameter'
        self.declare_parameter(
            name='time_period',
            value=0.01,   # parameter type is double
            descriptor=ParameterDescriptor(description="telemetry sampling time in secs.")
        )

        # Para declara varios parametros utilizamos 
        # el metodo 'declare_parameters'
        self.declare_parameters(
            namespace="",
            parameters=[
                ('vel_lin', 0.0),
                ('vel_ang', 0.0),
                ('joint_names', rclpy.Parameter.Type.STRING_ARRAY),
                ('robot_ip', rclpy.Parameter.Type.STRING),
                ('robot_name', rclpy.Parameter.Type.STRING)
            ]
        )


        # para leer un parametro se utiliza el 
        # metodo 'get_parameter'
        self.__time_period = self.get_parameter("time_period").get_parameter_value().double_value

        # Para validar un parámetro antes de cambiar su valo
        # utilizamos una funcion asincrona asociada al evento
        # 'on_set_parameter'
        self.add_on_set_parameters_callback(self._on_parameter_change)

        self.get_logger().info(f"{node_name} inicializado.")

    def _on_parameter_change(self, params:list[Parameter]):
        success = True
        # Validacion por cada parametro dentro del arreglo de
        # parametros
        for param in params:
            if param.name == 'time_period':
                if param.value < 0.0:
                    self.get_logger().warning(f"Parameter {param.name} debe ser mayor o igual a cero.")
                    success = False
            if param.name == 'robot_ip':
                success = self._validate_ip(param.value)
                if not success:
                    self.get_logger().warning(f"Parameter {param.name} no parece ser una ip valida {param.value}.")

        # Generamos el mensaje de resultado del proceso
        result_msg = SetParametersResult()
        result_msg.successful = success
        result_msg.reason = "Error en la validación de parametros."

        return result_msg
    
    def _validate_ip(self, ip):
        return bool(re.match(IPV4_REGEX, ip))

def init_srv(args=None):
    rclpy.init(args=args)
    param_srv = DofbotParamSrv("dofbot_config")
    try:
        rclpy.spin(param_srv)
    except KeyboardInterrupt:
        param_srv.get_logger().info('Keyboard Interrupt (SIGINT) received. Shutting down...')
    finally:
        # param_srv.destroy_node()
        rclpy.shutdown()

if __name__ == "__main_":
    init_srv()