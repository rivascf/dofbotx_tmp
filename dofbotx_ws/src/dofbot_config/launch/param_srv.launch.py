# importa las librerias de acceso a las
# funciones del sistema operativo
import os
import re
# Importa las librerias y funciones necesarias 
# para crear la accion de ros launch
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, EnvironmentVariable
from launch_ros.actions import Node

ROS2_NAMESPACE_PATTERN = re.compile(r"^[a-z0-9_]+$")

def validate_robot_name(context, *args, **kwargs):
    robot_name = LaunchConfiguration("robot_name").perform(context).strip().lower()

    if not robot_name:
        raise ValueError("robot_name cannot be empty")

    if not ROS2_NAMESPACE_PATTERN.fullmatch(robot_name):
        raise ValueError(
            "Invalid robot_name. "
            "Only lowercase letters, numbers, and underscores are allowed."
        )

    param_srv_node = Node(
        package="dofbot_config",
        executable="param_srv",
        namespace=robot_name,
        parameters=[
            {
                "robot_name": robot_name,
            }
        ],
    )

    return [param_srv_node]


def generate_launch_description():
    ld = LaunchDescription()
    # robot_name = EnvironmentVariable('ROBOT_NAME', default_value='VIRTUAL')
    robot_name = os.getenv('ROBOT_NAME', 'VIRTUAL')
    robot_iṕ = os.getenv('IPADDR', '127.0.0.1')

    param_srv_node = Node(
        package='dofbot_config',
        executable='param_srv',
        namespace=robot_name.lower(),
        parameters=[{
            'robot_name': robot_name, 
            'robot_ip': robot_iṕ
        }]
    )

    ld.add_action(param_srv_node)

    return ld


