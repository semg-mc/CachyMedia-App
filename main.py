import os
import sys
import re
import time
import threading
import urllib.request
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
    page.title = "💻 Cachy Media🗿"
    page.window_width = 450
    page.window_height = 700
    page.window_resizable = False
    page.bgcolor = COLOR_BG
    page.padding = 20
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    lbl_titulo = ft.Text("💻 Cachy Media🗿", size=26, weight="bold", color=COLOR_CYAN)
    lbl_sub = ft.Text("Descargador PRO (Sin Anuncios)", size=12, color=COLOR_TEXT_DIM)
    
    iconos_redes = ft.Text(
        "▶️ YouTube  |  📘 Facebook  |  📸 Instagram  |  🎵 TikTok  |  ✖️ X",
        size=11, color=COLOR_TEXT_DIM, weight="bold"
    )

    txt_url = ft.TextField(
        hint_text="🔗 Pega un enlace de video válido...", 
        bgcolor=COLOR_TERM_BG, border_color=COLOR_CYAN, border_radius=20, width=380, text_size=13
    )

    dd_tipo = ft.Dropdown(
        label="Elegir Tipo de Archivo", 
        options=[
            ft.dropdown.Option("🎬 Video HD (Máxima Calidad)"),
            ft.dropdown.Option("📺 Video SD (Ahorro de Datos)"),
            ft.dropdown.Option("🎵 Audio MP3 (Alta Calidad)")
        ], 
        value="🎬 Video HD (Máxima Calidad)",
        bgcolor=COLOR_TERM_BG, border_color=COLOR_CYAN, border_radius=15, width=380
    )
    
    btn_descargar = ft.ElevatedButton(
        "📥 DESCARGAR ARCHIVO", bgcolor=COLOR_BOTON_OFF, color=COLOR_TEXT_DIM, disabled=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), padding=18), width=380
    )

    progress_bar = ft.ProgressBar(width=380, color=COLOR_CYAN, bgcolor=COLOR_TERM_BG, value=0.0)

    terminal_texto = ft.TextField(
        multiline=True, read_only=True, value="[cachy@media]~ $ Sistema iniciado.\n",
        bgcolor=COLOR_TERM_BG, color=COLOR_GREEN, border_color="transparent",
        border_radius=10, text_size=10, width=380, height=120
    )

    def actualizar_terminal(texto):
        terminal_texto.value += f"> {texto}\n"
        page.update()

    def verificar_motor():
        if sys.platform == "win32" and not os.path.exists(RUTA_FFMPEG):
            actualizar_terminal("⚙️ Configurando el núcleo por primera vez...")
            try:
                url = "https://github.com/imageio/imageio-binaries/raw/master/ffmpeg/ffmpeg-win32-v4.2.2.exe"
                urllib.request.urlretrieve(url, RUTA_FFMPEG)
                actualizar_terminal("✅ Núcleo HD instalado en AppData. ¡1080p+ Desbloqueado!")
            except Exception as e:
                actualizar_terminal(f"❌ Error instalando el núcleo: {e}")
        elif os.path.exists(RUTA_FFMPEG):
            actualizar_terminal("✅ Núcleo HD operativo.")

    threading.Thread(target=verificar_motor, daemon=True).start()

    def resetear_interfaz():
        # ESTA FUNCIÓN ES EL BLINDAJE DEL BOTÓN
        txt_url.disabled = False
        dd_tipo.disabled = False
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
        seleccion = dd_tipo.value
        
        btn_descargar.disabled = True
        btn_descargar.bgcolor = COLOR_BOTON_OFF
        btn_descargar.color = COLOR_TEXT_DIM
        txt_url.disabled = True
        dd_tipo.disabled = True
        terminal_texto.value = ""
        progress_bar.value = 0.0
        page.update()
        
        actualizar_terminal("Estableciendo conexión...")

        def trabajo_descarga():
            try:
                estado_ui = {"ultimo_p": -5} 

                def hook_progreso(d):
                    if d['status'] == 'downloading':
                        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                        p_str = ansi_escape.sub('', d.get('_percent_str', '0.0%')).replace('%', '').strip()
                        try:
                            p = float(p_str)
                            if p - estado_ui["ultimo_p"] >= 5:
                                progress_bar.value = p / 100.0
                                actualizar_terminal(f"Descargando: {p_str}%")
                                estado_ui["ultimo_p"] = p
                        except ValueError: pass
                        
                    elif d['status'] == 'finished':
                        progress_bar.value = None
                        actualizar_terminal("Fusionando calidad suprema...")
                        page.update()

                class InterceptorLogger:
                    def debug(self, msg): pass 
                    def info(self, msg): pass
                    def warning(self, msg): pass
                    def error(self, msg): actualizar_terminal(f"ERR: {msg}")

                # AJUSTE ANTI-403: Relajamos YT, Mantenemos TikTok
                opts = {
                    'quiet': True, 
                    'progress_hooks': [hook_progreso],
                    'logger': InterceptorLogger(),
                    'nocheckcertificate': True,
                    'geo_bypass': True,
                    'extractor_args': {
                        'tiktok': {'api_hostname': 'api16-normal-c-useast1a.tiktokv.com'} 
                    }
                }

                # MKV ES EL REY: Evita que crashee al unir audios raros
                if "Audio" in seleccion:
                    opts['outtmpl'] = os.path.join(RUTA_DESCARGAS, '%(title).100s (Audio).%(ext)s')
                    opts['format'] = 'bestaudio/best'
                    opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}]
                elif "SD" in seleccion:
                    opts['outtmpl'] = os.path.join(RUTA_DESCARGAS, '%(title).100s (SD).%(ext)s')
                    opts['format'] = 'bestvideo[height<=480]+bestaudio/best'
                    opts['merge_output_format'] = 'mkv'
                else: 
                    opts['outtmpl'] = os.path.join(RUTA_DESCARGAS, '%(title).100s (HD).%(ext)s')
                    opts['format'] = 'bestvideo+bestaudio/best'
                    opts['merge_output_format'] = 'mkv'

                if os.path.exists(RUTA_FFMPEG):
                    opts['ffmpeg_location'] = RUTA_FFMPEG

                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                
                progress_bar.value = 1.0
                actualizar_terminal(f"✅ ¡Éxito! Guardado en Descargas.")
                time.sleep(3)
                txt_url.value = ""
                actualizar_terminal("✅ Listo para un nuevo enlace.")

            except Exception as ex:
                actualizar_terminal(f"❌ Error en la descarga (Verifica que no sea un link privado).")
                
            finally:
                # PASE LO QUE PASE, EL BOTÓN SE DESBLOQUEA AQUÍ
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
                dd_tipo, 
                ft.Container(height=10),
                progress_bar,
                btn_descargar,
                ft.Container(height=15),
                terminal_texto,
                ft.Text("Desarrollado por CachyMedia © 2026", size=10, color=COLOR_TEXT_DIM)
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
