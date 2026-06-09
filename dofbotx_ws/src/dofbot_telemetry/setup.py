from setuptools import find_packages, setup

package_name = 'dofbot_telemetry'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name, f"{package_name}.telem_utils"], #find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Felipe Rivas',
    maintainer_email='rivascf@gmail.com',
    description='Dofbot telemetry package',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'telemetry = dofbot_telemetry.Telemetry:main',
            'telem_sub = dofbot_telemetry.TelemetrySubs:main',
            'robot_telem = dofbot_telemetry.robot_telem:init_node',
            'jtop_telem = dofbot_telemetry.jtop_node:init_node',
            'diag_splitter = dofbot_telemetry.diagnostic_splitter:init_node',
        ],
    },
)
