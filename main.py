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
COLOR_TEXT = "#c9d1d9"     
COLOR_TEXT_DIM = "#8f9bb3"
COLOR_BOTON_OFF = "#2a2e45"

DIRECTORIO_APP = os.path.dirname(os.path.abspath(sys.argv[0]))
NOMBRE_FFMPEG = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
RUTA_FFMPEG = os.path.join(DIRECTORIO_APP, NOMBRE_FFMPEG)

def obtener_ruta_descargas():
    home = os.path.expanduser("~")
    for posible in [os.path.join(home, "Downloads"), os.path.join(home, "Descargas")]:
        if os.path.exists(posible): return posible
    return home

RUTA_DESCARGAS = obtener_ruta_descargas()

def main(page: ft.Page):
    page.title = "Cachy Media Downloader"
    page.window_width = 540
    page.window_height = 700
    page.window_resizable = False
    page.bgcolor = COLOR_BG
    page.padding = 20
    page.theme_mode = ft.ThemeMode.DARK

    # --- ELEMENTOS DE UI ---
    lbl_titulo = ft.Text("⚡ CACHY DOWNLOADER", size=24, weight="bold", color=COLOR_CYAN)
    lbl_sub = ft.Text("Descargador Universal de Audio & Video", size=12, color=COLOR_TEXT_DIM)
    lbl_compatibles = ft.Text("✅ Compatible con: YouTube, TikTok, Instagram, X (Twitter), Facebook y Twitch.", size=10, color=COLOR_GREEN)
    
    txt_url = ft.TextField(
        hint_text="Pega la URL del video aquí...", 
        bgcolor=COLOR_TERM_BG, border_color=COLOR_CYAN, border_radius=10, width=450, text_size=13
    )

    # Menú fijo y simplificado a prueba de fallos
    dd_calidad = ft.Dropdown(
        label="Selecciona la Calidad", 
        options=[
            ft.dropdown.Option("🎬 Video MP4 - Alta Calidad (1080p)"),
            ft.dropdown.Option("🎬 Video MP4 - Calidad Media (720p)"),
            ft.dropdown.Option("🎵 Audio MP3 - Máxima Calidad (320kbps)")
        ], 
        value="🎬 Video MP4 - Alta Calidad (1080p)",
        bgcolor=COLOR_TERM_BG, border_color=COLOR_CYAN, border_radius=10, width=450
    )

    progress_bar = ft.ProgressBar(width=450, color=COLOR_CYAN, bgcolor=COLOR_TERM_BG, value=0.0)
    
    btn_descargar = ft.ElevatedButton(
        "INICIAR DESCARGA", bgcolor=COLOR_BOTON_OFF, color=COLOR_TEXT_DIM, disabled=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=15), width=250
    )

    # Mini-Terminal
    terminal_lista = ft.ListView(expand=True, spacing=2, auto_scroll=True)
    caja_terminal = ft.Container(
        content=terminal_lista, bgcolor=COLOR_TERM_BG, border_radius=10, 
        padding=10, height=120, width=450
    )

    lbl_creditos = ft.Text("Desarrollado por CachyMedia & Gemini © 2026", size=10, color=COLOR_TEXT_DIM)

    # --- FUNCIONES ---
    def escribir_terminal(texto, color=COLOR_GREEN):
        terminal_lista.controls.append(ft.Text(f"[cachy@media]~ $ {texto}", color=color, size=11, font_family="Consolas"))
        page.update()

    class InterceptorLogger:
        def debug(self, msg): escribir_terminal(msg, COLOR_GREEN)
        def info(self, msg): escribir_terminal(msg, COLOR_CYAN)
        def warning(self, msg): pass # Ocultamos warnings innecesarios
        def error(self, msg): escribir_terminal(msg, COLOR_RED)

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
        txt_url.disabled = False
        validar_input(None)
        dd_calidad.disabled = False
        progress_bar.value = 0.0
        terminal_lista.controls.clear()
        escribir_terminal("Sistema reiniciado y listo.", COLOR_CYAN)
        page.update()

    def ejecutar_descarga(e):
        url = txt_url.value.strip()
        seleccion = dd_calidad.value
        
        # Bloqueo de UI
        btn_descargar.disabled = True
        btn_descargar.bgcolor = COLOR_BOTON_OFF
        btn_descargar.color = COLOR_TEXT_DIM
        txt_url.disabled = True
        dd_calidad.disabled = True
        progress_bar.value = 0.0
        terminal_lista.controls.clear()
        escribir_terminal(f"Conectando al servidor...", COLOR_CYAN)
        page.update()

        def trabajo_descarga():
            estado_ui = {"ultimo_update": 0.0}

            def hook_progreso(d):
                if d['status'] == 'downloading':
                    ahora = time.time()
                    if ahora - estado_ui["ultimo_update"] > 0.5:
                        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                        percent_str = ansi_escape.sub('', d.get('_percent_str', '0.0%')).replace('%', '').strip()
                        try:
                            p = float(percent_str)
                            progress_bar.value = p / 100.0
                            escribir_terminal(f"Descargando: {p}% ...", COLOR_GREEN)
                            page.update()
                            estado_ui["ultimo_update"] = ahora
                        except ValueError: pass
                elif d['status'] == 'finished':
                    progress_bar.value = None
                    escribir_terminal("Descarga completada. Procesando/Fusión...", COLOR_CYAN)
                    page.update()

            opts = {
                'outtmpl': os.path.join(RUTA_DESCARGAS, '%(title).100s.%(ext)s'),
                'progress_hooks': [hook_progreso],
                'logger': InterceptorLogger(),
                'nocheckcertificate': True, # Ayuda a evitar errores de red
            }

            # Lógica inteligente basada en tu selección
            if "Audio" in seleccion:
                opts['format'] = 'bestaudio/best'
                opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}]
            elif "1080" in seleccion:
                opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                opts['postprocessors'] = [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]
            else: # 720p
                opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                opts['postprocessors'] = [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]

            if os.path.exists(RUTA_FFMPEG):
                opts['ffmpeg_location'] = RUTA_FFMPEG

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                
                progress_bar.value = 1.0
                escribir_terminal(f"¡ÉXITO TOTAL! Guardado en Descargas.", COLOR_GREEN)
                page.update()
                reiniciar_ui()

            except Exception as ex:
                escribir_terminal(f"Error de red o video no disponible.", COLOR_RED)
                progress_bar.value = 0.0
                txt_url.disabled = False
                validar_input(None)
                dd_calidad.disabled = False
                page.update()

        threading.Thread(target=trabajo_descarga, daemon=True).start()

    btn_descargar.on_click = ejecutar_descarga

    # --- CONSTRUIR TARJETA CENTRAL ---
    card = ft.Container(
        content=ft.Column(
            [
                lbl_titulo, 
                lbl_sub, 
                lbl_compatibles,
                ft.Container(height=5), 
                txt_url, 
                dd_calidad, 
                ft.Container(height=5),
                progress_bar,
                btn_descargar,
                ft.Container(height=5),
                caja_terminal,
                lbl_creditos
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
