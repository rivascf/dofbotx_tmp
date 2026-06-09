#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
# importamos la libreria de mensajes
# de ROS2 diagnistic_msgs: KeyValue, DiagnosticArray
from diagnostic_msgs.msg import KeyValue, DiagnosticStatus, DiagnosticArray
# importamos la(s) librerias externas
from .telem_utils.sysinfo import SysInfo
import os

class DofbotTelemNode(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        # definimos el publicador
        self.__diag_pub = self.create_publisher(
            DiagnosticArray, 
            "/diagnostics",
            10
        )
        self.declare_parameter('interval', 0.5)  # Default interval 0.5
        self.__robot_name = robot_name = os.getenv('ROBOT_NAME', 'VIRTUAL')
        self._telem_report = SysInfo()
        self.__diag_arr = DiagnosticArray()
        self.__timer_period = self.get_parameter('interval').get_parameter_value().double_value
        self.__diag_timer = self.create_timer(self.__timer_period, self._on_diag_timer)

        self.get_logger().info(f"{node_name} initialized: System diagnostics has started with interval : {self.__timer_period} secs.")

    def _find_key_recursive(self, data, target_key):
        """
        Busca una clave de forma recursiva dentro de diccionarios o listas anidadas.
        Devuelve el valor si lo encuentra, o None si no existe.
        """
        if isinstance(data, dict):
            if target_key in data:
                return data[target_key]
            for key, value in data.items():
                result = self._find_key_recursive(value, target_key)
                if result is not None:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._find_key_recursive(item, target_key)
                if result is not None:
                    return result
        return None    

    def _on_diag_timer(self):
        # 0. Obtención del reporte real de telem_utils.sysinfo
        # from telem_utils.sysinfo import get_system_report
        # raw_report = get_system_report()
        raw_report = self._telem_report.get_system_report()

        # Extraer secciones usando la función de búsqueda recursiva tolerante
        cpu_stats = self._find_key_recursive(raw_report, 'cpu_stats')
        disk = self._find_key_recursive(raw_report, 'disk')
        ram = self._find_key_recursive(raw_report, 'ram')
        ip = self._find_key_recursive(raw_report, 'ip')
        rosinfo = self._find_key_recursive(raw_report, 'ros')

        # Crear contenedor del mensaje ROS 2
        self.__diag_arr.header.stamp = self.get_clock().now().to_msg()
        status_list = []

        # 1. Procesar CPU Stats (solo si es una lista y type == 'core')
        if isinstance(cpu_stats, list):
            for core in cpu_stats:
                if isinstance(core, dict) and core.get('type') == 'core':
                    label = core.get('label', 'Unknown_Core')
                    usage = core.get('usaged')  # Mantiene tu especificación exacta 'usaged'
                    
                    if usage is not None:
                        cpu_status = DiagnosticStatus()
                        cpu_status.level = DiagnosticStatus.OK
                        # cpu_status.name = f"System Hardware: CPU: {label}"
                        cpu_status.name = f"cpu_core_{label}"
                        cpu_status.message = "System Hardware [CPU]: Métricas por núcleo de CPU"
                        cpu_status.hardware_id = f"{label}"
                        cpu_status.values.append(KeyValue(key='usage', value=str(usage)))
                        status_list.append(cpu_status)

        # 2. Procesar Disk
        if isinstance(disk, dict):
            disk_status = DiagnosticStatus()
            disk_status.level = DiagnosticStatus.OK
            disk_status.name = "hardware_disk"
            disk_status.message = "System Hardware [Disk Info]: Estado del almacenamiento"
            disk_status.hardware_id = "disk_drive"
            
            # Obtener de forma segura cada campo solicitado
            for key in ['size', 'used', 'available']:
                if key in disk:
                    disk_status.values.append(KeyValue(key=key, value=str(disk[key])))
            
            if disk_status.values: # Solo añadir si se extrajo al menos un valor
                status_list.append(disk_status)

        # 3. Procesar RAM
        if isinstance(ram, dict):
            ram_status = DiagnosticStatus()
            ram_status.level = DiagnosticStatus.OK
            ram_status.name = "hardware_ram"
            ram_status.message = "System Hardware [RAM Info]: Estado de la memoria de sistema"
            ram_status.hardware_id = "ram_memory"
            
            # Obtener de forma segura cada campo solicitado
            for key in ['total', 'used', 'free', 'available']:
                if key in ram:
                    ram_status.values.append(KeyValue(key=key, value=str(ram[key])))
            
            if ram_status.values:
                status_list.append(ram_status)

        # 4. Procesar IP
        if ip is not None:
            ip_status = DiagnosticStatus()
            ip_status.level = DiagnosticStatus.OK
            ip_status.name = "network_interface"
            ip_status.message = "System Network [IP Address]: Dirección IP activa"
            ip_status.hardware_id = "ip_address"
            ip_status.values.append(KeyValue(key='ip', value=str(ip)))
            status_list.append(ip_status)

        # 5. Procesar ROS Info
        if isinstance(rosinfo, dict):
            robotsys_status = DiagnosticStatus()
            robotsys_status.level = DiagnosticStatus.OK
            robotsys_status.name = "robot_system"
            robotsys_status.message = "Robot System: Nombre asignado al robot y versión de ROS utilizada."
            robotsys_status.hardware_id = "robot_system"
            
            # Obtener de forma segura cada campo solicitado
            for key in ['version', 'distro', 'domain_id']:
                if key in rosinfo:
                    robotsys_status.values.append(KeyValue(key=key, value=str(rosinfo[key])))
            
            if robotsys_status.values:
                robotsys_status.values.append(KeyValue(key='robot_name', value=self.__robot_name))
                status_list.append(robotsys_status)

        # Asignar los estados recolectados al arreglo y publicar
        self.__diag_arr.status = status_list
        self.__diag_pub.publish(self.__diag_arr)

def init_node(args=None):
    rclpy.init(args=args)
    try:
        telem_node = DofbotTelemNode('telemetry_node')
        rclpy.spin(telem_node)
    except KeyboardInterrupt:
        telem_node.get_logger().info("Keyboard interrupt signal receive, shutting down node.")
    finally:
        rclpy.shutdown()

if __name__ == "__main__":
    init_node()