import signal
import sys
import threading
import time

import Adafruit_SSD1306
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel
from sysinfo import SysInfo

# --- CONFIGURACIÓN DEL DISPLAY ---
RST = None
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, i2c_bus=1, gpio=1)
disp.begin()
disp.clear()
disp.display()

width = disp.width
height = disp.height
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)
# font = ImageFont.load_default()
font = ImageFont.truetype("RobotoMonoNerdFontMono-Regular.ttf", 9)


# --- VARIABLES DE CONTROL ---
refresh_duration = 2.0
custom_message_active = False
custom_msg_text = ""
custom_msg_priority = "info"
custom_msg_end_time = 0.0

# Variable para apagar el hilo de forma segura
program_running = True

# --- FUNCIÓN DESTROY ---


def destroy():
    """
    Limpia por completo la pantalla OLED y apaga el programa.
    Evita que la pantalla se quede con texto congelado al salir.
    """
    print("\n[INFO] Limpiando pantalla OLED y cerrando sistema...")
    try:
        # Dibujar un rectángulo negro en todo el tamaño de la pantalla
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        disp.image(image)
        disp.display()
        disp.clear()
        disp.display()
        print("[OK] Pantalla apagada correctamente.")
    except Exception as e:
        print(f"[ERROR] No se pudo limpiar la pantalla: {e}")


def signal_handler(sig, frame):
    """Manejador para capturar Ctrl+C (SIGINT) desde la terminal."""
    global program_running
    program_running = False
    destroy()
    sys.exit(0)


# Registrar el manejador de Ctrl+C en el sistema
signal.signal(signal.SIGINT, signal_handler)

# --- FUNCIONES DE VALIDACIÓN Y DIBUJO ---


def validate_and_truncate(text, max_chars=21):
    if len(text) > max_chars:
        print(f"[ALERTA] El texto '{text}' es muy largo. Será recortado.")
        return text[:max_chars]
    return text


def draw_text_lines(line1, line2, line3, line4):
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    l1 = validate_and_truncate(line1)
    l2 = validate_and_truncate(line2)
    l3 = validate_and_truncate(line3)
    l4 = validate_and_truncate(line4)

    draw.text((0, 0), l1, font=font, fill=255)
    draw.text((0, 8), l2, font=font, fill=255)
    draw.text((0, 16), l3, font=font, fill=255)
    draw.text((0, 24), l4, font=font, fill=255)

    disp.image(image)
    disp.display()


def handle_custom_message(message: str, priority: str, duration: float):
    global custom_message_active, custom_msg_text, custom_msg_priority, custom_msg_end_time
    current_time = time.time()

    if custom_message_active:
        if priority == "info" and custom_msg_priority in ["error", "warning"]:
            print("[INFO] Mensaje ignorado: Hay una alerta más importante en pantalla.")
            return False
        if priority == "warning" and custom_msg_priority == "error":
            print("[INFO] Mensaje ignorado: Hay un error crítico en pantalla.")
            return False

    custom_message_active = True
    custom_msg_text = message
    custom_msg_priority = priority
    custom_msg_end_time = current_time + duration
    return True


# --- HILO PRINCIPAL DEL DISPLAY ---


def oled_loop():
    """Ciclo infinito que actualiza la pantalla OLED."""
    global custom_message_active, program_running
    info_provider = SysInfo()

    # El ciclo ahora depende de la variable de control program_running
    while program_running:
        current_time = time.time()

        if custom_message_active:
            if current_time < custom_msg_end_time:
                prefix = f"[{custom_msg_priority.upper()}]"
                draw_text_lines(prefix, custom_msg_text, "", "")
                time.sleep(0.5)
                continue
            else:
                custom_message_active = False

        stats = info_provider.get_snapshot()

        line1 = f"IP: {stats.get('ip', 'No IP')}"
        line2 = f"CPU: {stats.get('cpu', '0')}% RAM: {stats.get('ram', '0')}%"
        line3 = f"Disk: {stats.get('disk', '0')}%"
        line4 = f"Time: {stats.get('time', '')}"

        # Solo dibuja si el programa sigue activo (evita conflictos al cerrar)
        if program_running:
            draw_text_lines(line1, line2, line3, line4)

        time.sleep(refresh_duration)


display_thread = threading.Thread(target=oled_loop, daemon=True)
display_thread.start()

# --- CONFIGURACIÓN DE LA API (FASTAPI) ---

app = FastAPI(title="Dofbot OLED API")


# Evento de FastAPI que se ejecuta cuando la API se apaga de forma controlada
@app.on_event("shutdown")
def shutdown_event():
    global program_running
    program_running = False
    destroy()


class MessageModel(BaseModel):
    message: str
    priority: str = "info"
    duration: float = 3.0


class ConfigModel(BaseModel):
    duration: float


@app.post("/message")
def send_message(data: MessageModel):
    if data.priority not in ["info", "warning", "error"]:
        raise HTTPException(
            status_code=400, detail="Prioridad no válida. Usa: info, warning o error."
        )

    success = handle_custom_message(data.message, data.priority, data.duration)
    if success:
        return {
            "status": "success",
            "detail": f"Mensaje [{data.priority}] enviado a la pantalla.",
        }
    else:
        return {
            "status": "ignored",
            "detail": "El mensaje no se mostró debido a las reglas de prioridad.",
        }


@app.put("/config/refresh")
def update_refresh_duration(data: ConfigModel):
    global refresh_duration
    if data.duration <= 0:
        raise HTTPException(
            status_code=400, detail="La duración debe ser mayor a 0 segundos."
        )

    refresh_duration = data.duration
    return {"status": "success", "new_refresh_duration": refresh_duration}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
