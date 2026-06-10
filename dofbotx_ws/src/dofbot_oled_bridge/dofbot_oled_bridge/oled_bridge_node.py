import rclpy
from rclpy.node import Node
import requests
from dofbot_interfaces.srv import SetOledMessage

class OledBridgeNode(Node):
    def __init__(self):
        super().__init__('oled_bridge_node')
        
        # Declarar parámetro para la URL de la API (por si cambia la IP del host en Docker)
        # En Docker para Linux, 'http://172.17.0.1:8000' suele ser la IP del host.
        self.declare_parameter('api_url', 'http://172.17.0')
        self.api_url = self.get_parameter('api_url').get_parameter_value().string_value
        
        # Crear el servicio de ROS2
        self.srv = self.create_service(
            SetOledMessage, 
            'set_oled_message', 
            self.handle_oled_request
        )
        self.get_logger().info('Servicio ROS2 /set_oled_message listo.')

    def handle_oled_request(self, request, response):
        self.get_logger().info(f"Petición recibida: '{request.message}' [{request.priority}]")
        
        # Estructura de datos para la API de FastAPI del host
        payload = {
            "message": request.message,
            "priority": request.priority,
            "duration": float(request.duration)
        }
        
        try:
            # Enviar la petición HTTP POST al servicio del host
            res = requests.post(self.api_url, json=payload, timeout=2.0)
            
            if res.status_code == 200:
                data = res.json()
                # La API regresa 'success' si se puso en pantalla, o 'ignored' por prioridad
                if data.get("status") == "success":
                    response.success = True
                    response.string_status_message = "info: Mensaje colocado en pantalla correctamente."
                else:
                    response.success = False
                    response.string_status_message = f"warning: {data.get('detail')}"
            else:
                response.success = False
                response.string_status_message = f"error: API del host respondió con código {res.status_code}."
                
        except requests.exceptions.RequestException as e:
            # Captura si el servicio del host está caído o no hay ruta de red
            self.get_logger().error(f"Error de conexión con la API: {e}")
            response.success = False
            response.string_status_message = f"error: No se pudo conectar con el host. {str(e)}"
            
        return response

def init_node(args=None):
    rclpy.init(args=args)
    node = OledBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    init_node()
