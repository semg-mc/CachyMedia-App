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
    page.window_height = 750
    page.window_resizable = False
    page.bgcolor = COLOR_BG
    page.padding = 20
    page.theme_mode = ft.ThemeMode.DARK

    # --- ELEMENTOS DE UI ---
    lbl_titulo = ft.Text("⚡ CACHY DOWNLOADER", size=24, weight="bold", color=COLOR_CYAN)
    lbl_sub = ft.Text("Descargador Universal de Audio & Video", size=12, color=COLOR_TEXT_DIM)
    
    txt_url = ft.TextField(
        hint_text="Pega la URL del video aquí...", 
        bgcolor=COLOR_TERM_BG, border_color=COLOR_CYAN, border_radius=10, expand=True, text_size=13
    )
    
    btn_analizar = ft.ElevatedButton(
        "🔍 Analizar", bgcolor=COLOR_CARD, color=COLOR_CYAN, disabled=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    dd_calidad = ft.Dropdown(
        label="Selecciona una Calidad", 
        options=[ft.dropdown.Option("Esperando enlace...")], 
        value="Esperando enlace...",
        bgcolor=COLOR_TERM_BG, border_color=COLOR_CYAN, border_radius=10, disabled=True, width=450
    )

    progress_bar = ft.ProgressBar(width=450, color=COLOR_CYAN, bgcolor=COLOR_TERM_BG, value=0.0)
    
    btn_descargar = ft.ElevatedButton(
        "INICIAR DESCARGA", bgcolor=COLOR_CYAN, color="#000000", disabled=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=15), width=250
    )

    # Mini-Terminal
    terminal_lista = ft.ListView(expand=True, spacing=2, auto_scroll=True)
    caja_terminal = ft.Container(
        content=terminal_lista, bgcolor=COLOR_TERM_BG, border_radius=10, 
        padding=10, height=120, width=450
    )

    lbl_creditos = ft.Text("Desarrollado por CachyMedia © 2026", size=10, color=COLOR_TEXT_DIM)

    # Variables globales
    video_data = {"formatos": {}}

    # --- FUNCIONES ---
    def escribir_terminal(texto, color=COLOR_GREEN):
        terminal_lista.controls.append(ft.Text(f"[cachy@media]~ $ {texto}", color=color, size=11, font_family="Consolas"))
        page.update()

    class InterceptorLogger:
        def debug(self, msg): escribir_terminal(msg, COLOR_GREEN)
        def info(self, msg): escribir_terminal(msg, COLOR_CYAN)
        def warning(self, msg): escribir_terminal(msg, "#f1fa8c")
        def error(self, msg): escribir_terminal(msg, COLOR_RED)

    def hook_progreso(d):
        if d['status'] == 'downloading':
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            percent_str = ansi_escape.sub('', d.get('_percent_str', '0.0%')).replace('%', '').strip()
            try:
                p = float(percent_str)
                progress_bar.value = p / 100.0
                escribir_terminal(f"Descargando: {p}% ...", COLOR_GREEN)
            except ValueError: pass
            page.update()
        elif d['status'] == 'finished':
            progress_bar.value = None
            escribir_terminal("Descarga completada. Procesando/Fusión...", COLOR_CYAN)
            page.update()

    def validar_input(e):
        # Solo enciende "Analizar" si hay texto escrito
        btn_analizar.disabled = len(txt_url.value.strip()) == 0
        page.update()

    txt_url.on_change = validar_input

    def reiniciar_ui():
        """Regresa la app a su estado original para el siguiente video"""
        time.sleep(3) # Espera 3 segundos para que el usuario lea el éxito
        txt_url.value = ""
        txt_url.disabled = False
        btn_analizar.disabled = True
        dd_calidad.options = [ft.dropdown.Option("Esperando enlace...")]
        dd_calidad.value = "Esperando enlace..."
        dd_calidad.disabled = True
        btn_descargar.disabled = True
        progress_bar.value = 0.0
        terminal_lista.controls.clear()
        escribir_terminal("Sistema reiniciado y listo.", COLOR_CYAN)
        page.update()

    def analizar_enlace(e):
        url = txt_url.value.strip()
        if not url: return
        
        # Bloqueo total anti-spam
        btn_analizar.disabled = True
        txt_url.disabled = True
        dd_calidad.disabled = True
        btn_descargar.disabled = True
        terminal_lista.controls.clear()
        progress_bar.value = 0.0
        escribir_terminal("Analizando resoluciones disponibles...", COLOR_CYAN)
        page.update()

        def trabajo_analisis():
            try:
                opts = {'quiet': True, 'logger': InterceptorLogger()}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    calidades_reales = set()
                    for f in info.get('formats', []):
                        if f.get('vcodec') != 'none' and f.get('height'):
                            calidades_reales.add(f.get('height'))
                    
                    calidades_ordenadas = sorted(list(calidades_reales), reverse=True)
                    opciones = []
                    video_data["formatos"].clear()
                    
                    for h in calidades_ordenadas:
                        nombre = f"🎬 MP4 - Alta Calidad ({h}p)"
                        opciones.append(ft.dropdown.Option(nombre))
                        video_data["formatos"][nombre] = str(h)
                        
                    # Audio a máxima calidad siempre
                    opciones.append(ft.dropdown.Option("🎵 MP3 - Máxima Calidad (320kbps)"))
                    video_data["formatos"]["🎵 MP3 - Máxima Calidad (320kbps)"] = "audio"

                    dd_calidad.options = opciones
                    dd_calidad.value = opciones[0].key
                    dd_calidad.disabled = False
                    
                    btn_descargar.disabled = False
                    txt_url.disabled = False # Liberamos para que pueda corregir
                    escribir_terminal(f"Análisis exitoso. Selecciona formato.", COLOR_CYAN)

            except Exception as ex:
                escribir_terminal(f"Error al analizar el enlace.", COLOR_RED)
                txt_url.disabled = False
            finally:
                btn_analizar.disabled = len(txt_url.value.strip()) == 0
                page.update()

        threading.Thread(target=trabajo_analisis, daemon=True).start()

    def ejecutar_descarga(e):
        url = txt_url.value.strip()
        seleccion = dd_calidad.value
        
        # SÚPER BLOQUEO ANTI-SPAM
        btn_descargar.disabled = True
        btn_analizar.disabled = True
        txt_url.disabled = True
        dd_calidad.disabled = True
        progress_bar.value = 0.0
        escribir_terminal(f"Iniciando descarga...", COLOR_CYAN)
        page.update()

        def trabajo_descarga():
            tipo = video_data["formatos"][seleccion]
            
            if tipo == "audio":
                nombre_archivo = '%(title).100s (Audio).%(ext)s'
                formato_ydl = 'bestaudio/best'
                # 320 es la máxima calidad real en MP3
                postprocessors = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}]
            else:
                nombre_archivo = f'%(title).100s ({tipo}p).%(ext)s'
                formato_ydl = f'bestvideo[height<={tipo}]+bestaudio/best'
                postprocessors = [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]

            opts = {
                'outtmpl': os.path.join(RUTA_DESCARGAS, nombre_archivo),
                'format': formato_ydl,
                'progress_hooks': [hook_progreso],
                'logger': InterceptorLogger(),
                'postprocessors': postprocessors,
            }

            if os.path.exists(RUTA_FFMPEG):
                opts['ffmpeg_location'] = RUTA_FFMPEG

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                
                progress_bar.value = 1.0
                escribir_terminal(f"¡ÉXITO TOTAL! Guardado en Descargas.", COLOR_GREEN)
                page.update()
                reiniciar_ui() # Llama al auto-reinicio

            except Exception as ex:
                escribir_terminal(f"Falló la descarga. Intenta de nuevo.", COLOR_RED)
                progress_bar.value = 0.0
                # Si falla, liberamos botones manualmente
                btn_analizar.disabled = False
                txt_url.disabled = False
                dd_calidad.disabled = False
                btn_descargar.disabled = False
                page.update()

        threading.Thread(target=trabajo_descarga, daemon=True).start()

    # --- ASIGNAR EVENTOS ---
    btn_analizar.on_click = analizar_enlace
    btn_descargar.on_click = ejecutar_descarga

    # --- CONSTRUIR TARJETA CENTRAL ---
    fila_input = ft.Row([txt_url, btn_analizar], spacing=10)
    
    card = ft.Container(
        content=ft.Column(
            [
                lbl_titulo, 
                lbl_sub, 
                ft.Container(height=10), 
                fila_input, 
                dd_calidad, 
                ft.Container(height=5),
                progress_bar,
                ft.Container(height=5),
                btn_descargar,
                ft.Container(height=10),
                caja_terminal,
                ft.Container(height=5),
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
