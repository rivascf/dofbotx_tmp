import time
import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont
from sysinfo import SysInfo
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uvicorn
import threading

# --- CONFIGURACIÓN DEL DISPLAY ---
# Configura el OLED de 128x32

RST = None
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)
disp.begin()
disp.clear()
disp.display()

# Crear imagen en blanco para dibujar
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# Cargar fuente por defecto
font = ImageFont.load_default()

# --- VARIABLES DE CONTROL ---
# Duración por defecto en segundos para refrescar la pantalla
refresh_duration = 2.0

# Variables para mensajes personalizados
custom_message_active = False
custom_msg_text = ""
custom_msg_priority = "info"
custom_msg_end_time = 0.0

# --- FUNCIONES DE VALIDACIÓN Y DIBUJO ---

def validate_and_truncate(text, max_chars=21):
    """
    Revisa si el texto cabe en la pantalla.
    Si es muy largo, manda una alerta en consola y lo corta.
    """
    if len(text) > max_chars:
        print(f"[ALERTA] El texto '{text}' es muy largo, será recortado.")
        return text[:max_chars]
    return text

def draw_text_lines(line1, line2, line3, line4):
    """Limpia la pantalla y dibuja 4 líneas de texto."""
    # Limpiar pantalla interna
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    
    # Validar y recortar cada línea
    l1 = validate_and_truncate(line1)
    l2 = validate_and_truncate(line2)
    l3 = validate_and_truncate(line3)
    l4 = validate_and_truncate(line4)
    
    # Dibujar las líneas en la imagen
    draw.text((0, 0),  l1, font=font, fill=255)
    draw.text((0, 8),  l2, font=font, fill=255)
    draw.text((0, 16), l3, font=font, fill=255)
    draw.text((0, 24), l4, font=font, fill=255)
    
    # Mostrar en el OLED
    disp.image(image)
    disp.display()

def handle_custom_message(message: str, priority: str, duration: float):
    """
    Maneja la lógica de interrupción por mensajes personalizados.
    Aplica reglas según la prioridad (error, warning, info).
    """
    global custom_message_active, custom_msg_text, custom_msg_priority, custom_msg_end_time
    
    current_time = time.time()
    
    # Reglas de prioridad:
    # 'error' interrumpe todo.
    # 'warning' interrumpe a 'info' y a otros 'warning'.
    # 'info' solo se muestra si no hay un mensaje más importante activo.
    if custom_message_active:
        if priority == "info" and custom_msg_priority in ["error", "warning"]:
            print("[INFO] Mensaje ignorado: Hay una alerta más importante en pantalla.")
            return False
        if priority == "warning" and custom_msg_priority == "error":
            print("[INFO] Mensaje ignorado: Hay un error crítico en pantalla.")
            return False

    # Configurar el nuevo mensaje activo
    custom_message_active = True
    custom_msg_text = message
    custom_msg_priority = priority
    custom_msg_end_time = current_time + duration
    return True

# --- HILO PRINCIPAL DEL DISPLAY ---

def oled_loop():
    """Ciclo infinito que actualiza la pantalla OLED."""
    global custom_message_active
    info_provider = SysInfo()
    
    while True:
        current_time = time.time()
        
        # 1. Verificar si hay un mensaje personalizado activo
        if custom_message_active:
            if current_time < custom_msg_end_time:
                # Mostrar el mensaje personalizado con su etiqueta de prioridad
                prefix = f"[{custom_msg_priority.upper()}]"
                draw_text_lines(prefix, custom_msg_text, "", "")
                time.sleep(0.5)
                continue
            else:
                # El tiempo del mensaje terminó
                custom_message_active = False
        
        # 2. Si no hay mensaje personalizado, mostrar info del sistema
        stats = info_provider.get_snapshot()
        
        line1 = f"IP: {stats.get('ip', 'No IP')}"
        line2 = f"CPU: {stats.get('cpu', '0')}% RAM: {stats.get('ram', '0')}%"
        line3 = f"Disk: {stats.get('disk', '0')}%"
        line4 = f"Time: {stats.get('time', '')}"
        
        draw_text_lines(line1, line2, line3, line4)
        
        # Esperar el tiempo configurado en la variable de duración
        time.sleep(refresh_duration)

# Iniciar el hilo del OLED para que no bloquee la API
display_thread = threading.Thread(target=oled_loop, daemon=True)
display_thread.start()

# --- CONFIGURACIÓN DE LA API (FASTAPI) ---

app = FastAPI(title="Dofbot OLED API")

class MessageModel(BaseModel):
    message: str
    priority: str = "info"  # opciones: info, warning, error
    duration: float = 3.0   # tiempo en segundos

class ConfigModel(BaseModel):
    duration: float

@app.post("/message")
def send_message(data: MessageModel):
    """Envía un mensaje personalizado a la pantalla OLED."""
    if data.priority not in ["info", "warning", "error"]:
        raise HTTPException(status_code=400, detail="Prioridad no válida. Usa: info, warning o error.")
    
    success = handle_custom_message(data.message, data.priority, data.duration)
    
    if success:
        return {"status": "success", "detail": f"Mensaje [{data.priority}] enviado a la pantalla."}
    else:
        return {"status": "ignored", "detail": "El mensaje no se mostró debido a las reglas de prioridad."}

@app.put("/config/refresh")
def update_refresh_duration(data: ConfigModel):
    """Cambia el tiempo de refresco del hilo principal."""
    global refresh_duration
    if data.duration <= 0:
        raise HTTPException(status_code=400, detail="La duración debe ser mayor a 0 segundos.")
    
    refresh_duration = data.duration
    return {"status": "success", "new_refresh_duration": refresh_duration}

# Para ejecutar la API directamente si se corre este script
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
