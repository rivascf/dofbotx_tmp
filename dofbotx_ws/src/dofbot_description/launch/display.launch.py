from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
  ld = LaunchDescription()

  default_urdf_path = FindPackageShare('dofbot_description')
  default_model_path = PathJoinSubstitution(['urdf', 'dofbot.urdf'])
  default_rviz_config_path = PathJoinSubstitution([default_urdf_path, 'config', 'urdf_show.rviz'])

  # These parameters are maintained for backwards compatibility
  gui_arg = DeclareLaunchArgument(name='gui', default_value='true', choices=['true', 'false'],
                                  description='Flag to enable joint_state_publisher_gui')
  ld.add_action(gui_arg)

  # This parameter has changed its meaning slightly from previous versions
  ld.add_action(DeclareLaunchArgument(name='model', default_value=default_model_path,
                                      description='Path to robot urdf file relative to omnicar_description package'))

  # This parameter has changed its meaning slightly from previous versions
  ld.add_action(DeclareLaunchArgument(name='rviz_config', default_value=default_rviz_config_path,
                                      description='Absolute path to rviz config file'))

  ld.add_action(IncludeLaunchDescription(
    PathJoinSubstitution([FindPackageShare('urdf_launch'), 'launch', 'display.launch.py']),
    launch_arguments={
      'urdf_package': 'dofbot_description',
      'urdf_package_path': LaunchConfiguration('model'),
      'jsp_gui': LaunchConfiguration('gui'),
      'rviz_config': LaunchConfiguration('rviz_config')
      }.items()
  ))

  return ld
