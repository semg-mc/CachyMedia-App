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

# LA SOLUCIÓN MAESTRA AL PROBLEMA DE CALIDAD (Rutas en .exe)
if getattr(sys, 'frozen', False):
    # Si es un .exe compilado, busca exactamente donde está el .exe
    DIRECTORIO_APP = os.path.dirname(sys.executable)
else:
    # Si es el script de python normal
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
    page.title = "Cachy Media Downloader"
    page.window_width = 540
    page.window_height = 650
    page.window_resizable = False
    page.bgcolor = COLOR_BG
    page.padding = 20
    page.theme_mode = ft.ThemeMode.DARK

    # --- ELEMENTOS DE UI ---
    lbl_titulo = ft.Text("⚡Cachy Media V10", size=24, weight="bold", color=COLOR_CYAN)
    lbl_compatibles = ft.Text("✅ Universal: YouTube, TikTok, Facebook, X, Instagram, etc.", size=12, color=COLOR_GREEN)
    
    txt_url = ft.TextField(
        hint_text="Pega la URL del video aquí...", 
        bgcolor=COLOR_TERM_BG, border_color=COLOR_CYAN, border_radius=10, width=450, text_size=13
    )

    dd_tipo = ft.Dropdown(
        label="Formato de Descarga", 
        options=[
            ft.dropdown.Option("🎬 Video MP4 (Máxima Calidad Posible)"),
            ft.dropdown.Option("🎵 Audio MP3 (Máxima Calidad Posible)")
        ], 
        value="🎬 Video MP4 (Máxima Calidad Posible)",
        bgcolor=COLOR_TERM_BG, border_color=COLOR_CYAN, border_radius=10, width=450
    )
    
    btn_descargar = ft.ElevatedButton(
        "INICIAR DESCARGA", bgcolor=COLOR_BOTON_OFF, color=COLOR_TEXT_DIM, disabled=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=15), width=250
    )

    # LA SOLUCIÓN AL BUG DE LA VENTANA (Usar TextField en lugar de ListView)
    terminal_texto = ft.TextField(
        multiline=True,
        read_only=True,
        value="[cachy@media]~ $ Sistema listo.\n",
        bgcolor=COLOR_TERM_BG,
        color=COLOR_GREEN,
        border_color=COLOR_CYAN,
        border_radius=10,
        text_size=11,
        width=450,
        height=150
    )

    # --- FUNCIONES ---
    def escribir_terminal(texto):
        # En lugar de agregar cajas visuales, solo sumamos texto (Cero lag)
        terminal_texto.value += f"> {texto}\n"
        page.update()

    class InterceptorLogger:
        def debug(self, msg): pass 
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): escribir_terminal(f"ERROR: {msg}")

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
        time.sleep(3)
        txt_url.value = ""
        validar_input(None)
        txt_url.disabled = False
        dd_tipo.disabled = False
        terminal_texto.value = "[cachy@media]~ $ Sistema reiniciado.\n"
        page.update()

    def ejecutar_descarga(e):
        url = txt_url.value.strip()
        seleccion = dd_tipo.value
        
        btn_descargar.disabled = True
        btn_descargar.bgcolor = COLOR_BOTON_OFF
        btn_descargar.color = COLOR_TEXT_DIM
        txt_url.disabled = True
        dd_tipo.disabled = True
        
        terminal_texto.value = "[cachy@media]~ $ Iniciando motor de descarga...\n"
        page.update()

        def trabajo_descarga():
            estado_ui = {"ultimo_p": -10} 

            def hook_progreso(d):
                if d['status'] == 'downloading':
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    percent_str = ansi_escape.sub('', d.get('_percent_str', '0.0%')).replace('%', '').strip()
                    try:
                        p = int(float(percent_str))
                        if p - estado_ui["ultimo_p"] >= 10:
                            escribir_terminal(f"Descargando... {p}%")
                            estado_ui["ultimo_p"] = p
                    except ValueError: pass
                elif d['status'] == 'finished':
                    escribir_terminal("Descarga terminada. Fusionando alta calidad...")

            opts = {
                'progress_hooks': [hook_progreso],
                'logger': InterceptorLogger(),
                'nocheckcertificate': True,
                'geo_bypass': True,
                'extractor_args': {'youtube': {'player_client': ['mweb', 'android', 'web']}}
            }

            if "Audio" in seleccion:
                opts['outtmpl'] = os.path.join(RUTA_DESCARGAS, '%(title).100s (Audio).%(ext)s')
                opts['format'] = 'bestaudio/best'
                opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}]
            else:
                opts['outtmpl'] = os.path.join(RUTA_DESCARGAS, '%(title).100s (Video).%(ext)s')
                # MÁXIMA CALIDAD GARANTIZADA:
                opts['format'] = 'bestvideo+bestaudio/best'
                opts['merge_output_format'] = 'mp4'

            # VINCULACIÓN CON FFMPEG (AQUÍ ESTABA LA FALLA DE CALIDAD)
            if os.path.exists(RUTA_FFMPEG):
                opts['ffmpeg_location'] = RUTA_FFMPEG
                escribir_terminal("Motor FFmpeg detectado. Calidad 1080p+ desbloqueada.")
            else:
                escribir_terminal("AVISO: ffmpeg.exe no encontrado. Calidad limitada a 720p.")

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                
                escribir_terminal(f"¡ÉXITO TOTAL! Guardado en Descargas.")
                reiniciar_ui()

            except Exception as ex:
                escribir_terminal(f"Error o video bloqueado.")
                txt_url.disabled = False
                validar_input(None)
                dd_tipo.disabled = False
                page.update()

        threading.Thread(target=trabajo_descarga, daemon=True).start()

    btn_descargar.on_click = ejecutar_descarga

    # --- CONSTRUIR TARJETA CENTRAL ---
    card = ft.Container(
        content=ft.Column(
            [
                lbl_titulo, 
                lbl_compatibles,
                ft.Container(height=10), 
                txt_url, 
                dd_tipo, 
                ft.Container(height=10),
                btn_descargar,
                ft.Container(height=10),
                ft.Text("Terminal de Procesos:", size=12, color=COLOR_TEXT_DIM, weight="bold"),
                terminal_texto,
                ft.Text("Desarrollado por semg_mc © 2026", size=10, color=COLOR_TEXT_DIM)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        ),
        bgcolor=COLOR_CARD,
        padding=30,
        border_radius=16,
        width=500
    )

    page.add(ft.Row([card], alignment=ft.MainAxisAlignment.CENTER))

if __name__ == "__main__":
    ft.run(main)
