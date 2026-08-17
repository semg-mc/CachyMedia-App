import os
import sys
import re
import time
import threading
import urllib.request
import flet as ft
import yt_dlp

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

    # --- EL DESFIBRILADOR GRÁFICO (Mantiene despierta la ventana) ---
    pixel_fantasma = ft.Text("", size=1) 
    page.add(pixel_fantasma)

    def latido_cardiaco():
        while True:
            time.sleep(0.5)
            pixel_fantasma.value = " " if pixel_fantasma.value == "" else ""
            page.update()

    threading.Thread(target=latido_cardiaco, daemon=True).start()

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

    def actualizar_terminal(texto):
        terminal_texto.value += f"> {texto}\n"
        page.update()

    # --- LA MAGIA CONTRA EL TARTAMUDEO ---
    def actualizar_progreso_fluido(p_str, p_float):
        lineas = terminal_texto.value.strip().split('\n')
        if lineas and "Descargando:" in lineas[-1]:
            lineas[-1] = f"> Descargando: {p_str}%"
            terminal_texto.value = "\n".join(lineas) + "\n"
        else:
            terminal_texto.value += f"> Descargando: {p_str}%\n"
        
        progress_bar.value = p_float
        page.update()

    def verificar_motor():
        if sys.platform == "win32" and not os.path.exists(RUTA_FFMPEG):
            actualizar_terminal("⚙️ Configurando FFmpeg por primera vez...")
            try:
                url = "https://github.com/imageio/imageio-binaries/raw/master/ffmpeg/ffmpeg-win32-v4.2.2.exe"
                urllib.request.urlretrieve(url, RUTA_FFMPEG)
                actualizar_terminal("✅ Motor HD instalado. ¡1080p+ Desbloqueado!")
            except Exception as e:
                actualizar_terminal(f"❌ Error instalando el motor: {e}")
        elif os.path.exists(RUTA_FFMPEG):
            actualizar_terminal("✅ Motor HD listo y operativo.")

    threading.Thread(target=verificar_motor, daemon=True).start()

    def resetear_interfaz():
        txt_url.disabled = False
        dd_calidad.disabled = False
        progress_bar.value = 0.0
        
        if len(txt_url.value.strip()) > 0:
            btn_descargar.disabled = False
            btn_descargar.bgcolor = COLOR_CYAN
            btn_descargar.color = "#000000"
        else:
            btn_descargar.disabled = True
            btn_descargar.bgcolor = COLOR_BOTON_OFF
            btn_descargar.color = COLOR_TEXT_DIM
            
        page.update()

    def validar_input(e):
        resetear_interfaz()

    txt_url.on_change = validar_input

    def ejecutar_descarga(e):
        url = txt_url.value.strip()
        seleccion = dd_calidad.value
        
        btn_descargar.disabled = True
        btn_descargar.bgcolor = COLOR_BOTON_OFF
        btn_descargar.color = COLOR_TEXT_DIM
        txt_url.disabled = True
        dd_calidad.disabled = True
        terminal_texto.value = ""
        progress_bar.value = 0.0
        page.update()
        
        actualizar_terminal("Iniciando secuencia de descarga...")

        def trabajo_descarga():
            max_intentos = 4
            intento_actual = 1
            descarga_exitosa = False

            while intento_actual <= max_intentos and not descarga_exitosa:
                try:
                    estado_ui = {"ultimo_tiempo": 0.0} 

                    def hook_progreso(d):
                        if d['status'] == 'downloading':
                            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                            p_str = ansi_escape.sub('', d.get('_percent_str', '0.0%')).replace('%', '').strip()
                            try:
                                p = float(p_str)
                                ahora = time.time()
                                if ahora - estado_ui["ultimo_tiempo"] >= 0.3:
                                    actualizar_progreso_fluido(p_str, p / 100.0)
                                    estado_ui["ultimo_tiempo"] = ahora
                            except ValueError: pass
                            
                        elif d['status'] == 'finished':
                            progress_bar.value = None
                            actualizar_terminal("Ensamblando Video MP4 Universal...")
                            page.update()

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
                    progress_bar.value = 1.0
                    actualizar_terminal(f"✅ ¡Video Guardado en Descargas!")
                    time.sleep(3)
                    txt_url.value = ""
                    actualizar_terminal("✅ Listo para un nuevo enlace.")

                except Exception as ex:
                    # EL BUCLE TERCO INTACTO
                    if intento_actual < max_intentos:
                        actualizar_terminal(f"⚠️ El servidor rechazó la conexión.")
                        actualizar_terminal(f"🔄 Reintentando... (Intento {intento_actual}/{max_intentos})")
                        time.sleep(2) 
                        intento_actual += 1
                        progress_bar.value = 0.0
                        page.update()
                    else:
                        actualizar_terminal("❌ El servidor está muy estricto hoy o el enlace no jala.")
                        actualizar_terminal("Vuelve a picarle al botón o intenta con otro enlace. Ni modo, andamos haciendo milagros. xd")
                        break

            resetear_interfaz()

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
