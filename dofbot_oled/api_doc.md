# En ralación a la API

## ¿Cómo usar la API?

Una vez que ejecutes el script, la API estará disponible en el puerto 8000. Puedes probarla desde tu navegador entrando a http://localhost:8000/docs para ver la interfaz interactiva.

## Ejemplos de peticiones (usando comandos cURL):

   1. Enviar un mensaje de error prioritario por 5 segundos:
   
   `curl -X POST "http://localhost:8000/message" -H "Content-Type: application/json" -d '{"message": "Fallo de Motor", "priority": "error", "duration": 5.0}'`
   
   2. Cambiar el tiempo de actualización de la pantalla del sistema a 5 segundos:
   
   `curl -X PUT "http://localhost:8000/config/refresh" -H "Content-Type: application/json" -d '{"duration": 5.0}'`


Para ejecutar este script como un servicio de Linux (systemd) en tu Jetson Nano 4GB, necesitas organizar los archivos en una carpeta dedicada, crear un entorno virtual de Python para aislar las librerías y configurar un archivo de servicio del sistema. [1, 2] 

Aquí tienes la estructura de carpetas, los archivos necesarios y el paso a paso detallado para lograrlo.

## Estructura de carpetas recomendada

Te sugiero guardar todo dentro de la carpeta del usuario principal (jetson) o en /opt. Usaremos /home/jetson/dofbot_oled/ como base:

```text
/home/jetson/dofbot_oled/
├── venv/                 # Entorno virtual de Python (se creará con comandos)
├── sysinfo.py            # Tu script secundario de recopilación de datos
├── dofbot_oled.py        # Tu script principal modificado con FastAPI y destroy()
└── requirements.txt      # Archivo con las librerías necesarias
```

## Archivos Necesarios

### 1. Archivo requirements.txt

Crea este archivo para instalar las dependencias exactas dentro del entorno virtual.

```text
Adafruit-SSD1306
Pillow
fastapi
pydantic
uvicorn
psutil
```

### 2. Modificación en dofbot_oled.py (Línea final de ejecución)

Asegúrate de que la última línea de tu archivo dofbot_oled.py use la ruta absoluta o el host correcto para producción. Al final de tu script, debe verse así:

```python
if __name__ == "__main__":
    # Usamos host 0.0.0.0 para que acepte conexiones desde cualquier IP de tu red local
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
### 3. Archivo del Servicio: dofbot_oled.service

Este archivo le dice a Linux cómo, cuándo y con qué permisos ejecutar tu script.

```text
[Unit]
Description=Servicio de Pantalla OLED y API para Dofbot
After=network.target

[Service]
Type=simple
User=jetson
WorkingDirectory=/home/jetson/dofbot_oled
# Ejecuta el script usando el Python del entorno virtual
ExecStart=/home/jetson/dofbot_oled/venv/bin/python dofbot_oled.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Paso a Paso para la Configuración en Jetson Nano

Abre una terminal en tu Jetson Nano y ejecuta los siguientes comandos:

## Paso 1: Crear la carpeta y mover tus archivos

```console
# Crear el directorio del proyecto

mkdir -p /home/jetson/dofbot_oled
cd /home/jetson/dofbot_oled
# (Aquí debes copiar o crear tus archivos dofbot_oled.py, sysinfo.py y requirements.txt)
```

## Paso 2: Crear el Entorno Virtual e instalar librerías

La Jetson Nano suele usar Python 3.6 o 3.8 por defecto. Crearemos un entorno limpio para evitar conflictos globales: [3, 4] 

```bash
# Instalar la herramienta de entornos virtuales si no la tienes

sudo apt-get update
sudo apt-get install -y python3-venv python3-pip

# Crear el entorno virtual llamado 'venv'

python3 -m venv venv

# Activar el entorno virtual temporalmente para instalar las dependencias

source venv/bin/activate

# Instalar los paquetes necesarios

pip install --upgrade pip
pip install -r requirements.txt
# Salir del entorno virtual
deactivate
```

### Paso 3: Registrar el Servicio en Linux (systemd) [5] 

Debes copiar el archivo de configuración del servicio a la carpeta del sistema y darle de alta:

```bash
# Crear el archivo del servicio directamente en la ruta del sistema
sudo nano /etc/systemd/system/dofbot_oled.service
```

(Pega aquí el contenido del bloque dofbot_oled.service que te mostré arriba. Guarda con Ctrl+O, presiona Enter y sal con Ctrl+X).

## Paso 4: Iniciar y Activar el Servicio

```bash
# Recargar el sistema para que reconozca el nuevo servicio
sudo systemctl daemon-reload

# Habilitar el servicio para que arranque automáticamente al encender la Jetson Nano
sudo systemctl enable dofbot_oled.service

# Iniciar el servicio en este momento
sudo systemctl start dofbot_oled.service
```

### Comandos útiles de Administración

Una vez instalado, puedes controlar el estado de tu pantalla y API con estos comandos desde cualquier terminal:

* Ver si el servicio está corriendo o tiene errores:

`sudo systemctl status dofbot_oled.service`

* Ver las impresiones de consola (logs) en tiempo real (útil para ver alertas de texto largo o peticiones API):

`journalctl -u dofbot_oled.service -f`

* Detener el servicio manualmente (esto activará tu función destroy() y apagará el OLED):

`sudo systemctl stop dofbot_oled.service`

* Reiniciar el servicio:

`sudo systemctl restart dofbot_oled.service`


Dime si tienes alguna duda con las rutas de los archivos o si te gustaría añadir un script de instalación automatizada (.sh) para configurar todo con un solo comando.

[1] [https://hoyo.tech](https://hoyo.tech/article/coding-essentials-python-installation-ubuntu-service-setup-and-bitbucket-pipeline-configuration-walkthrough)
[2] [https://community.hpe.com](https://community.hpe.com/t5/software-general/how-i-turned-my-python-script-into-a-linux-service-and-why-you/td-p/7245402)
[3] [https://docs.donkeycar.com](https://docs.donkeycar.com/guide/robot_sbc/setup_jetson_nano/)
[4] [https://github.com](https://github.com/dusty-nv/jetson-containers/issues/1084)
[5] [https://community.hpe.com](https://community.hpe.com/t5/software-general/how-i-turned-my-python-script-into-a-linux-service-and-why-you/td-p/7245402)


