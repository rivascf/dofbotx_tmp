from setuptools import find_packages, setup

package_name = 'dofbot_oled_bridge'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Felpe Rivas',
    maintainer_email='rivascf@gmail.com',
    description='Dofbot OLED Bridge Package.',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'oled_bridge = dofbot_oled_bridge.oled_bridge_node:init_node'
        ],
    },
)
