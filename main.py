import os
import sys
import threading
import flet as ft
import yt_dlp

# --- COLORES CACHYOS ---
COLOR_BG = "#0d1017"       # Fondo oscuro profundo
COLOR_CARD = "#161b22"     # Panel ligeramente más claro
COLOR_CYAN = "#00f2fe"     # Acento principal
COLOR_GREEN = "#50fa7b"    # Éxito / Terminal
COLOR_RED = "#ff5555"      # Errores
COLOR_TERM_BG = "#000000"  # Fondo de la mini-terminal

# --- DETECCIÓN DE SISTEMA ---
DIRECTORIO_APP = os.path.dirname(os.path.abspath(sys.argv[0]))
# Si es Windows busca .exe, si es Linux/Android busca sin extensión
NOMBRE_FFMPEG = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
RUTA_FFMPEG = os.path.join(DIRECTORIO_APP, NOMBRE_FFMPEG)

def obtener_ruta_descargas():
    home = os.path.expanduser("~")
    for posible in [os.path.join(home, "Downloads"), os.path.join(home, "Descargas")]:
        if os.path.exists(posible): return posible
    return home

RUTA_DESCARGAS = obtener_ruta_descargas()

def main(page: ft.Page):
    page.title = "Cachy Media V3 - Terminal"
    page.window_width = 600
    page.window_height = 700
    page.window_resizable = False
    page.bgcolor = COLOR_BG
    page.padding = 20
    page.theme_mode = ft.ThemeMode.DARK

    # --- ELEMENTOS DE INTERFAZ ---
    lbl_titulo = ft.Text("⚡ CACHY MEDIA", size=28, weight="bold", color=COLOR_CYAN)
    
    txt_url = ft.TextField(
        hint_text="Pega la URL del video aquí...", 
        bgcolor=COLOR_CARD, border_color=COLOR_CYAN, border_radius=5, expand=True
    )
    
    btn_analizar = ft.ElevatedButton(
        "🔍 Analizar", bgcolor=COLOR_CARD, color=COLOR_CYAN, 
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))
    )

    dd_calidad = ft.Dropdown(
        label="Calidades Disponibles", 
        options=[ft.dropdown.Option("Esperando análisis...")], 
        value="Esperando análisis...",
        bgcolor=COLOR_CARD, border_color=COLOR_CYAN, disabled=True
    )

    btn_descargar = ft.ElevatedButton(
        "🎬 INICIAR DESCARGA", bgcolor=COLOR_CYAN, color="#000000", disabled=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5), padding=15), expand=True
    )

    # --- LA MINI-TERMINAL ---
    terminal_lista = ft.ListView(expand=True, spacing=2, auto_scroll=True)
    caja_terminal = ft.Container(
        content=terminal_lista, bgcolor=COLOR_TERM_BG, border_radius=5, 
        padding=10, height=200, border=ft.border.all(1, COLOR_CYAN)
    )

    # Variables globales para guardar los datos del video analizado
    video_data = {"formatos": {}}

    # --- FUNCIONES ---
    def escribir_terminal(texto, color=COLOR_GREEN):
        """Escribe una línea en la mini-terminal al estilo CachyOS"""
        terminal_lista.controls.append(ft.Text(f"[cachy@media]~ $ {texto}", color=color, size=11, font_family="Consolas"))
        page.update()

    # Clase para interceptar los mensajes de yt-dlp y mandarlos a nuestra terminal
    class InterceptorLogger:
        def debug(self, msg): escribir_terminal(msg, COLOR_GREEN)
        def info(self, msg): escribir_terminal(msg, COLOR_CYAN)
        def warning(self, msg): escribir_terminal(msg, "#f1fa8c") # Amarillo
        def error(self, msg): escribir_terminal(msg, COLOR_RED)

    def hook_progreso(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0.0%').replace('\x1b[0;94m', '').replace('\x1b[0m', '').strip()
            escribir_terminal(f"Descargando: {p} ...", COLOR_GREEN)
        elif d['status'] == 'finished':
            escribir_terminal("Descarga completada. Procesando video/audio...", COLOR_CYAN)

    def analizar_enlace(e):
        url = txt_url.value.strip()
        if not url: return
        
        # Bloqueos Anti-Spam
        btn_analizar.disabled = True
        btn_descargar.disabled = True
        dd_calidad.disabled = True
        terminal_lista.controls.clear()
        escribir_terminal("Analizando enlace, buscando calidades reales...", COLOR_CYAN)
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
                    
                    # Ordenar de mayor a menor (Ej: 1080, 720, 480)
                    calidades_ordenadas = sorted(list(calidades_reales), reverse=True)
                    
                    opciones = []
                    video_data["formatos"].clear()
                    
                    for h in calidades_ordenadas:
                        nombre = f"🎬 Video HD - {h}p"
                        opciones.append(ft.dropdown.Option(nombre))
                        video_data["formatos"][nombre] = str(h)
                        
                    # Siempre agregamos la opción de Audio
                    opciones.append(ft.dropdown.Option("🎵 Solo Audio (MP3)"))
                    video_data["formatos"]["🎵 Solo Audio (MP3)"] = "audio"

                    dd_calidad.options = opciones
                    dd_calidad.value = opciones[0].key
                    dd_calidad.disabled = False
                    btn_descargar.disabled = False
                    
                    escribir_terminal(f"¡Análisis completo! Título: {info.get('title', 'Video')}", COLOR_CYAN)

            except Exception as ex:
                escribir_terminal(f"Error al analizar: {ex}", COLOR_RED)
            finally:
                btn_analizar.disabled = False
                page.update()

        threading.Thread(target=trabajo_analisis, daemon=True).start()

    def ejecutar_descarga(e):
        url = txt_url.value.strip()
        seleccion = dd_calidad.value
        if not url or not seleccion: return

        # Bloqueo Anti-Spam
        btn_descargar.disabled = True
        btn_analizar.disabled = True
        txt_url.disabled = True
        dd_calidad.disabled = True
        escribir_terminal(f"Iniciando descarga: {seleccion}", COLOR_CYAN)
        page.update()

        def trabajo_descarga():
            tipo = video_data["formatos"][seleccion]
            
            if tipo == "audio":
                nombre_archivo = '%(title).100s (Audio).%(ext)s'
                formato_ydl = 'bestaudio/best'
                postprocessors = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
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
                escribir_terminal(f"¡ÉXITO! Archivo guardado en: {RUTA_DESCARGAS}", COLOR_GREEN)
            except Exception as ex:
                escribir_terminal(f"Error en descarga: {ex}", COLOR_RED)
            finally:
                # Desbloquear todo al terminar
                btn_descargar.disabled = False
                btn_analizar.disabled = False
                txt_url.disabled = False
                dd_calidad.disabled = False
                txt_url.value = ""
                page.update()

        threading.Thread(target=trabajo_descarga, daemon=True).start()

    # --- ASIGNAR EVENTOS ---
    btn_analizar.on_click = analizar_enlace
    btn_descargar.on_click = ejecutar_descarga

    # --- CONSTRUIR PANTALLA ---
    fila_input = ft.Row([txt_url, btn_analizar], spacing=10)
    
    page.add(
        ft.Row([lbl_titulo], alignment=ft.MainAxisAlignment.CENTER),
        ft.Container(height=10),
        fila_input,
        dd_calidad,
        ft.Row([btn_descargar]),
        ft.Container(height=10),
        ft.Text("TERMINAL DE PROCESOS:", size=12, color=COLOR_TEXT, weight="bold"),
        caja_terminal
    )

if __name__ == "__main__":
    ft.run(main)
