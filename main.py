import os
import sys
import re
import time
import threading
import flet as ft
import yt_dlp

# --- COLORES CACHYOS ---
COLOR_BG = "#0d1017"       
COLOR_CARD = "#161b22"     
COLOR_CYAN = "#00f2fe"     
COLOR_GREEN = "#50fa7b"    
COLOR_RED = "#ff5555"      
COLOR_TERM_BG = "#000000"  
COLOR_TEXT_DIM = "#8f9bb3"
COLOR_BOTON_OFF = "#2a2e45"

# RUTA ABSOLUTA PARA FFMPEG (La clave del HD)
if getattr(sys, 'frozen', False):
    DIRECTORIO_APP = os.path.dirname(os.path.abspath(sys.argv[0]))
else:
    DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))

NOMBRE_FFMPEG = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
RUTA_FFMPEG = os.path.join(DIRECTORIO_APP, NOMBRE_FFMPEG)

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

    # --- LA PIZARRA INVISIBLE (Para evitar congelamientos) ---
    pizarra = {"texto": "", "porcentaje": 0.0, "impreso": ""}

    # --- ELEMENTOS DE UI ---
    lbl_titulo = ft.Text("💻 Cachy Media🗿", size=26, weight="bold", color=COLOR_CYAN)
    lbl_sub = ft.Text("Descargador PRO (Sin Anuncios)", size=12, color=COLOR_TEXT_DIM)
    
    # Iconos de redes compatibles (Blindados contra crashes)
    iconos_redes = ft.Row(
        [
            ft.Icon("play_arrow", color="#ff0000", size=20),        # YouTube
            ft.Icon("facebook", color="#1877f2", size=20),          # Facebook
            ft.Icon("camera_alt", color="#e1306c", size=20),        # Instagram
            ft.Icon("music_note", color="#ffffff", size=20),        # TikTok
            ft.Icon("alternate_email", color="#1da1f2", size=20)    # X / Twitter
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=15
    )

    txt_url = ft.TextField(
        hint_text="Pega un enlace de video válido...", 
        bgcolor=COLOR_TERM_BG, border_color=COLOR_CYAN, border_radius=20, width=380, text_size=13,
        prefix_icon=ft.icons.LINK
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
        "Descargar Archivo", bgcolor=COLOR_BOTON_OFF, color=COLOR_TEXT_DIM, disabled=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), padding=18), width=380,
        icon=ft.icons.DOWNLOAD_ROUNDED
    )

    progress_bar = ft.ProgressBar(width=380, color=COLOR_CYAN, bgcolor=COLOR_TERM_BG, value=0.0)

    terminal_texto = ft.TextField(
        multiline=True, read_only=True, value="[cachy@media]~ $ Sistema seguro iniciado.\n",
        bgcolor=COLOR_TERM_BG, color=COLOR_GREEN, border_color="transparent",
        border_radius=10, text_size=10, width=380, height=100
    )

    # --- EL MARCAPASOS ---
    def marcapasos():
        while True:
            if pizarra["texto"] != "" and pizarra["texto"] != pizarra["impreso"]:
                terminal_texto.value += f"> {pizarra['texto']}\n"
                pizarra["impreso"] = pizarra["texto"]
                page.update()
            
            if progress_bar.value != pizarra["porcentaje"]:
                progress_bar.value = pizarra["porcentaje"]
                page.update()
            
            time.sleep(0.2)

    threading.Thread(target=marcapasos, daemon=True).start()

    # --- FUNCIONES ---
    def anotar(texto):
        pizarra["texto"] = texto

    def validar_input(e):
        if len(txt_url.value.strip()) > 0:
            btn_descargar.disabled = False
            btn_descargar.bgcolor = COLOR_CYAN
            btn_descargar.color = "#000000"
        else:
            btn_descargar.disabled = True
            btn_descargar.bgcolor = COLOR_BOTON_OFF
            btn_descargar.color = COLOR_TEXT_DIM
        page.update()

    txt_url.on_change = validar_input

    def reiniciar_ui():
        time.sleep(4)
        txt_url.value = ""
        validar_input(None)
        txt_url.disabled = False
        dd_tipo.disabled = False
        pizarra["porcentaje"] = 0.0
        anotar("Listo para un nuevo enlace.")

    def ejecutar_descarga(e):
        url = txt_url.value.strip()
        seleccion = dd_tipo.value
        
        btn_descargar.disabled = True
        btn_descargar.bgcolor = COLOR_BOTON_OFF
        btn_descargar.color = COLOR_TEXT_DIM
        txt_url.disabled = True
        dd_tipo.disabled = True
        terminal_texto.value = ""
        pizarra["porcentaje"] = 0.0
        
        anotar("Camuflando conexión como Dispositivo Móvil...")

        def trabajo_descarga():
            def hook_progreso(d):
                if d['status'] == 'downloading':
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    p_str = ansi_escape.sub('', d.get('_percent_str', '0.0%')).replace('%', '').strip()
                    try:
                        p = float(p_str)
                        pizarra["porcentaje"] = p / 100.0
                        anotar(f"Descargando: {p_str}%")
                    except ValueError: pass
                elif d['status'] == 'finished':
                    pizarra["porcentaje"] = None
                    anotar("Procesando archivo final (No cierre la app)...")

            class InterceptorLogger:
                def debug(self, msg): pass 
                def info(self, msg): pass
                def warning(self, msg): pass
                def error(self, msg): anotar(f"ERR: {msg}")

            # LA MÁSCARA ANTI-BLOQUEOS (El Bypass Maestro)
            opts = {
                'progress_hooks': [hook_progreso],
                'logger': InterceptorLogger(),
                'nocheckcertificate': True,
                'geo_bypass': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36'
                },
                'extractor_args': {
                    'youtube': {'player_client': ['android', 'ios']},
                    'tiktok': {'api_hostname': 'api16-normal-c-useast1a.tiktokv.com'} # Fuerza API sin marca de agua
                }
            }

            # LÓGICA DE CALIDADES
            if "Audio" in seleccion:
                opts['outtmpl'] = os.path.join(RUTA_DESCARGAS, '%(title).100s (Audio).%(ext)s')
                opts['format'] = 'bestaudio/best'
                opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}]
            elif "SD" in seleccion:
                opts['outtmpl'] = os.path.join(RUTA_DESCARGAS, '%(title).100s (SD).%(ext)s')
                opts['format'] = 'bestvideo[height<=480]+bestaudio/best'
                opts['merge_output_format'] = 'mp4'
            else: # Video HD
                opts['outtmpl'] = os.path.join(RUTA_DESCARGAS, '%(title).100s (HD).%(ext)s')
                opts['format'] = 'bestvideo+bestaudio/best'
                opts['merge_output_format'] = 'mp4'

            if os.path.exists(RUTA_FFMPEG):
                opts['ffmpeg_location'] = RUTA_FFMPEG
                anotar("Motor FFmpeg listo. Procesamiento pesado habilitado.")
            else:
                anotar("ADVERTENCIA: FFmpeg no encontrado. Calidad reducida.")

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                
                pizarra["porcentaje"] = 1.0
                anotar(f"✅ ¡Completado! Guardado en Descargas.")
                reiniciar_ui()

            except Exception as ex:
                anotar(f"❌ Enlace bloqueado o inválido.")
                pizarra["porcentaje"] = 0.0
                txt_url.disabled = False
                validar_input(None)
                dd_tipo.disabled = False

        threading.Thread(target=trabajo_descarga, daemon=True).start()

    btn_descargar.on_click = ejecutar_descarga

    # --- CONSTRUIR TARJETA ---
    card = ft.Container(
        content=ft.Column(
            [
                lbl_titulo, 
                lbl_sub,
                ft.Container(height=10),
                ft.Text("Plataformas Soportadas:", size=11, color=COLOR_TEXT_DIM),
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
