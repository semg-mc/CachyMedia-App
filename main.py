import os
import sys
import re
import time
import threading
import urllib.request
import queue
import flet as ft
import yt_dlp

# --- EL SILENCIADOR DE WINDOWS ---
if sys.platform == "win32" and getattr(sys, 'frozen', False):
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

COLOR_BG = "#0d1017"       
COLOR_CARD = "#161b22"     
COLOR_CYAN = "#00f2fe"     
COLOR_GREEN = "#50fa7b"    
COLOR_RED = "#ff5555"      
COLOR_TERM_BG = "#000000"  
COLOR_TEXT_DIM = "#8f9bb3"
COLOR_BOTON_OFF = "#2a2e45"

CARPETA_APPDATA = os.path.join(os.getenv('APPDATA'), 'CachyMedia')
os.makedirs(CARPETA_APPDATA, exist_ok=True)
RUTA_FFMPEG = os.path.join(CARPETA_APPDATA, 'ffmpeg.exe')

def obtener_ruta_descargas():
    home = os.path.expanduser("~")
    for p in [os.path.join(home, "Downloads"), os.path.join(home, "Descargas")]:
        if os.path.exists(p): return p
    return home

RUTA_DESCARGAS = obtener_ruta_descargas()

def main(page: ft.Page):
    page.title = "🎬 CachyVIDEOS 🎬"
    page.window_width = 450
    page.window_height = 700
    page.window_resizable = False
    page.bgcolor = COLOR_BG
    page.padding = 20
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # --- EL BUZÓN DE MENSAJES (LA CURA AL CONGELAMIENTO) ---
    cola_ui = queue.Queue()

    lbl_titulo = ft.Text("🎬 CachyVIDEOS 🎬", size=26, weight="bold", color=COLOR_CYAN)
    lbl_sub = ft.Text("Descargador de Video Universal", size=12, color=COLOR_TEXT_DIM)
    
    iconos_redes = ft.Text(
        "▶️ YouTube  |  📘 Facebook  |  📸 Instagram  |  🎵 TikTok  |  ✖️ X",
        size=11, color=COLOR_TEXT_DIM, weight="bold"
    )

    txt_url = ft.TextField(
        hint_text="🔗 Pega un enlace de video aquí...", 
        bgcolor=COLOR_TERM_BG, border_color=COLOR_CYAN, border_radius=20, width=380, text_size=13
    )

    dd_calidad = ft.Dropdown(
        label="Calidad del Video", 
        options=[
            ft.dropdown.Option("🎬 Video HD (Máxima Calidad)"),
            ft.dropdown.Option("📱 Video Ligero (Ahorro de Datos)")
        ], 
        value="🎬 Video HD (Máxima Calidad)",
        bgcolor=COLOR_TERM_BG, border_color=COLOR_CYAN, border_radius=15, width=380
    )
    
    btn_descargar = ft.ElevatedButton(
        "📥 DESCARGAR VIDEO", bgcolor=COLOR_BOTON_OFF, color=COLOR_TEXT_DIM, disabled=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), padding=18), width=380
    )

    progress_bar = ft.ProgressBar(width=380, color=COLOR_CYAN, bgcolor=COLOR_TERM_BG, value=0.0)

    terminal_texto = ft.TextField(
        multiline=True, read_only=True, value="[cachy@video]~ $ Motor de video iniciado.\n",
        bgcolor=COLOR_TERM_BG, color=COLOR_GREEN, border_color="transparent",
        border_radius=10, text_size=10, width=380, height=140
    )

    # --- EL REPARTIDOR DE MENSAJES (DIBUJA SIN TRABARSE) ---
    def actualizador_interfaz():
        while True:
            try:
                mensaje = cola_ui.get()
                accion = mensaje[0]
                
                if accion == "terminal":
                    terminal_texto.value += f"> {mensaje[1]}\n"
                elif accion == "progreso":
                    progress_bar.value = mensaje[1]
                    terminal_texto.value += f"> {mensaje[2]}\n"
                elif accion == "limpiar_barra":
                    progress_bar.value = mensaje[1]
                elif accion == "limpiar_terminal":
                    terminal_texto.value = ""
                elif accion == "limpiar_url":
                    txt_url.value = ""
                elif accion == "estado_botones":
                    bloqueado = mensaje[1]
                    btn_descargar.disabled = bloqueado
                    txt_url.disabled = bloqueado
                    dd_calidad.disabled = bloqueado
                    if not bloqueado and txt_url.value.strip():
                        btn_descargar.bgcolor = COLOR_CYAN
                        btn_descargar.color = "#000000"
                    else:
                        btn_descargar.bgcolor = COLOR_BOTON_OFF
                        btn_descargar.color = COLOR_TEXT_DIM
                
                page.update()
                cola_ui.task_done()
            except Exception:
                pass

    # Iniciamos al repartidor en las sombras
    threading.Thread(target=actualizador_interfaz, daemon=True).start()

    def verificar_motor():
        if sys.platform == "win32" and not os.path.exists(RUTA_FFMPEG):
            cola_ui.put(("terminal", "⚙️ Configurando FFmpeg por primera vez..."))
            try:
                url = "https://github.com/imageio/imageio-binaries/raw/master/ffmpeg/ffmpeg-win32-v4.2.2.exe"
                urllib.request.urlretrieve(url, RUTA_FFMPEG)
                cola_ui.put(("terminal", "✅ Motor HD instalado. ¡1080p+ Desbloqueado!"))
            except Exception as e:
                cola_ui.put(("terminal", f"❌ Error instalando el motor: {e}"))
        elif os.path.exists(RUTA_FFMPEG):
            cola_ui.put(("terminal", "✅ Motor HD listo y operativo."))

    threading.Thread(target=verificar_motor, daemon=True).start()

    def validar_input(e):
        if len(txt_url.value.strip()) > 0:
            cola_ui.put(("estado_botones", False))
        else:
            cola_ui.put(("estado_botones", True))

    txt_url.on_change = validar_input

    def ejecutar_descarga(e):
        url = txt_url.value.strip()
        seleccion = dd_calidad.value
        
        # Mandamos cartas al buzón para bloquear la interfaz visual
        cola_ui.put(("estado_botones", True))
        cola_ui.put(("limpiar_terminal", None))
        cola_ui.put(("limpiar_barra", 0.0))
        cola_ui.put(("terminal", "Iniciando secuencia de descarga..."))

        def trabajo_descarga():
            max_intentos = 4
            intento_actual = 1
            descarga_exitosa = False

            while intento_actual <= max_intentos and not descarga_exitosa:
                try:
                    estado_ui = {"ultimo_p": -5} 

                    def hook_progreso(d):
                        if d['status'] == 'downloading':
                            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                            p_str = ansi_escape.sub('', d.get('_percent_str', '0.0%')).replace('%', '').strip()
                            try:
                                p = float(p_str)
                                if p - estado_ui["ultimo_p"] >= 5:
                                    # En vez de tocar Flet, dejamos una carta en el buzón
                                    cola_ui.put(("progreso", p / 100.0, f"Descargando: {p_str}%"))
                                    estado_ui["ultimo_p"] = p
                            except ValueError: pass
                            
                        elif d['status'] == 'finished':
                            cola_ui.put(("limpiar_barra", None))
                            cola_ui.put(("terminal", "Ensamblando Video MP4 Universal..."))

                    class InterceptorLogger:
                        def debug(self, msg): pass 
                        def info(self, msg): pass
                        def warning(self, msg): pass
                        def error(self, msg): pass

                    opts = {
                        'quiet': True, 
                        'progress_hooks': [hook_progreso],
                        'logger': InterceptorLogger(),
                        'nocheckcertificate': True,
                        'geo_bypass': True
                    }

                    if "Ligero" in seleccion:
                        opts['outtmpl'] = os.path.join(RUTA_DESCARGAS, '%(title).100s (Ligero).%(ext)s')
                        opts['format'] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                        opts['merge_output_format'] = 'mp4' 
                    else:
                        opts['outtmpl'] = os.path.join(RUTA_DESCARGAS, '%(title).100s (HD).%(ext)s')
                        opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                        opts['merge_output_format'] = 'mp4'

                    if os.path.exists(RUTA_FFMPEG):
                        opts['ffmpeg_location'] = RUTA_FFMPEG

                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.download([url])
                    
                    descarga_exitosa = True
                    cola_ui.put(("limpiar_barra", 1.0))
                    cola_ui.put(("terminal", "✅ ¡Video Guardado en Descargas!"))
                    time.sleep(3)
                    cola_ui.put(("limpiar_url", None))
                    cola_ui.put(("terminal", "✅ Listo para un nuevo enlace."))

                except Exception as ex:
                    if intento_actual < max_intentos:
                        cola_ui.put(("terminal", "⚠️ El servidor rechazó la conexión."))
                        cola_ui.put(("terminal", f"🔄 Reintentando... (Intento {intento_actual}/{max_intentos})"))
                        time.sleep(2) 
                        intento_actual += 1
                        cola_ui.put(("limpiar_barra", 0.0))
                    else:
                        cola_ui.put(("terminal", "❌ El servidor está muy estricto hoy o el enlace no jala."))
                        cola_ui.put(("terminal", "Vuelve a picarle al botón o intenta con otro enlace. Ni modo, andamos haciendo milagros. xd"))
                        break

            # Desbloqueamos los botones mandando la última carta al buzón
            cola_ui.put(("estado_botones", False))

        threading.Thread(target=trabajo_descarga, daemon=True).start()

    btn_descargar.on_click = ejecutar_descarga

    card = ft.Container(
        content=ft.Column(
            [
                lbl_titulo, 
                lbl_sub,
                ft.Container(height=10),
                iconos_redes,
                ft.Container(height=20), 
                txt_url, 
                dd_calidad,
                ft.Container(height=10),
                progress_bar,
                btn_descargar,
                ft.Container(height=15),
                terminal_texto,
                ft.Text("Desarrollado por semg_mc © 2026", size=10, color=COLOR_TEXT_DIM)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5
        ),
        bgcolor=COLOR_CARD,
        padding=30,
        border_radius=25,
        width=450
    )

    page.add(card)

if __name__ == "__main__":
    ft.run(main)
