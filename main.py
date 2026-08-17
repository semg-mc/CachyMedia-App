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

DIRECTORIO_APP = os.path.dirname(os.path.abspath(sys.argv[0]))
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
    lbl_titulo = ft.Text("⚡ CACHY DOWNLOADER", size=24, weight="bold", color=COLOR_CYAN)
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

    spinner_carga = ft.ProgressRing(width=20, height=20, stroke_width=3, color=COLOR_CYAN, visible=False)
    fila_estado = ft.Row([spinner_carga, ft.Text("Terminal de Procesos:", size=12, color=COLOR_TEXT_DIM, weight="bold")], alignment=ft.MainAxisAlignment.START)

    terminal_lista = ft.ListView(expand=True, spacing=2, auto_scroll=True)
    caja_terminal = ft.Container(
        content=terminal_lista, bgcolor=COLOR_TERM_BG, border_radius=10, 
        padding=10, height=150, width=450
    )

    # --- FUNCIONES ---
    def escribir_terminal(texto, color=COLOR_GREEN):
        terminal_lista.controls.append(ft.Text(f"> {texto}", color=color, size=11, font_family="Consolas"))
        page.update()

    class InterceptorLogger:
        def debug(self, msg): pass 
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): escribir_terminal(f"ERROR: {msg}", COLOR_RED)

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
        dd_tipo.disabled = False
        spinner_carga.visible = False
        terminal_lista.controls.clear()
        escribir_terminal("Sistema reiniciado y listo para otro enlace.", COLOR_CYAN)
        page.update()

    def ejecutar_descarga(e):
        url = txt_url.value.strip()
        seleccion = dd_tipo.value
        
        btn_descargar.disabled = True
        btn_descargar.bgcolor = COLOR_BOTON_OFF
        btn_descargar.color = COLOR_TEXT_DIM
        txt_url.disabled = True
        dd_tipo.disabled = True
        
        spinner_carga.visible = True
        
        terminal_lista.controls.clear()
        escribir_terminal(f"Iniciando descarga a MÁXIMA resolución...", COLOR_CYAN)
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
                            escribir_terminal(f"Descargando: {p}% completado...", COLOR_GREEN)
                            estado_ui["ultimo_p"] = p
                    except ValueError: pass
                elif d['status'] == 'finished':
                    escribir_terminal("Descarga terminada. Convirtiendo/Muxing (Esto puede tardar)...", COLOR_CYAN)

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
                # LA MAGIA DE LA MÁXIMA CALIDAD:
                # 1. Agarra el mejor video (sea webm, mp4, mkv) y el mejor audio.
                opts['format'] = 'bestvideo+bestaudio/best'
                # 2. Obliga a FFmpeg a fusionarlo todo dentro de un archivo .mp4 universal.
                opts['merge_output_format'] = 'mp4'

            if os.path.exists(RUTA_FFMPEG):
                opts['ffmpeg_location'] = RUTA_FFMPEG

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                
                escribir_terminal(f"¡ÉXITO TOTAL! Revisa tu carpeta de Descargas.", COLOR_GREEN)
                reiniciar_ui()

            except Exception as ex:
                escribir_terminal(f"Error. Verifica que el enlace sea correcto y público.", COLOR_RED)
                txt_url.disabled = False
                validar_input(None)
                dd_tipo.disabled = False
                spinner_carga.visible = False
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
                ft.Container(content=fila_estado, width=450), 
                caja_terminal,
                ft.Text("Desarrollado por CachyMedia & Gemini © 2026", size=10, color=COLOR_TEXT_DIM)
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
