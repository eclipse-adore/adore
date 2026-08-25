from setuptools import setup

package_name = 'weather_service_interface'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', [
            'config/weather_service_config.yaml',
        ]),
        ('share/' + package_name + '/launch', [
            'launch/weather_service.launch.py',
            'launch/weather_service_and_visualizer.launch.py',
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='maintainer',
    description='ROS 2 weather forecast service interface',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'weather_service_node = weather_service_interface.weather_service_node:main',
            'weather_visualizer_node = weather_service_interface.weather_visualizer_node:main',
        ],
    },
)
