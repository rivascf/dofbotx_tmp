import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    # 1. Encontrar la ruta del paquete dofbot_description
    try:
        dofbot_desc_dir = get_package_share_directory('dofbot_description')
    except Exception:
        dofbot_desc_dir = ''

    # 2. Configurar la ruta por defecto al archivo URDF
    default_urdf_path = os.path.join(dofbot_desc_dir, 'urdf', 'dofbot.urdf')

    # 3. Declarar el argumento de lanzamiento para la ruta del URDF
    urdf_argument = DeclareLaunchArgument(
        'urdf_file',
        default_value=default_urdf_path,
        description='Ruta absoluta al archivo URDF del robot'
    )

    # 4. Leer el contenido del archivo URDF usando el comando 'cat' del sistema de forma nativa en ROS 2
    # ParameterValue con value_type=str asegura que el contenido se pase como una cadena de texto (string)
    robot_description_content = ParameterValue(
        Command(['cat ', LaunchConfiguration('urdf_file')]),
        value_type=str
    )

    # 5. Definición del nodo de cinemática
    kinematics_node = Node(
        package='dofbot_kinematics',
        executable='dofbot_kinematics_node',
        name='dofbot_kinematics_node',
        output='screen',
        parameters=[{
            'robot_description': robot_description_content
        }]
    )

    return LaunchDescription([
        urdf_argument,
        kinematics_node
    ])
