import os
import sys
import re
import threading
import flet as ft
import yt_dlp

# --- COLORES CACHYOS ---
COLOR_BG = "#0f111a"
COLOR_CARD = "#1a1d2e"
COLOR_CYAN = "#00f2fe"
COLOR_TEXT_DIM = "#8f9bb3"
COLOR_INPUT_BG = "#121420"
COLOR_BORDER = "#2a2e45"

# --- RUTA DE DESCARGAS UNIVERSAL ---
def obtener_ruta_descargas():
    home = os.path.expanduser("~")
    for posible in [os.path.join(home, "Downloads"), os.path.join(home, "Descargas")]:
        if os.path.exists(posible):
            return posible
    return home

RUTA_DESCARGAS = obtener_ruta_descargas()
DIRECTORIO_APP = os.path.dirname(os.path.abspath(sys.argv[0]))
# ¡AQUÍ ESTÁ EL AJUSTE PARA WINDOWS YA LISTO! 👇
RUTA_FFMPEG = os.path.join(DIRECTORIO_APP, "ffmpeg.exe")

def sanitizar_url(raw_url):
    clean_url = raw_url.split('?')[0].strip()
    tiktok_match = re.search(r'tiktok\.com/.*video/(\d+)', clean_url)
    if tiktok_match:
        return f"https://www.tiktok.com/embed/v2/{tiktok_match.group(1)}"
    return clean_url

# --- INTERFAZ GRÁFICA ---
def main(page: ft.Page):
    page.title = "Cachy Media V2"
    page.window_width = 540
    page.window_height = 560
    page.window_resizable = False
    page.bgcolor = COLOR_BG
    page.padding = 20
    page.theme_mode = ft.ThemeMode.DARK

    lbl_titulo = ft.Text("⚡ CACHY MEDIA V2", size=24, weight=ft.FontWeight.BOLD, color=COLOR_CYAN)
    lbl_sub = ft.Text("Descargas Universales (H.264/MP3) Sin Marca de Agua", size=12, color=COLOR_TEXT_DIM)
    
    txt_url = ft.TextField(
        hint_text="Pega la URL aquí (TikTok, YouTube, Insta...)",
        bgcolor=COLOR_INPUT_BG, border_color=COLOR_BORDER, border_radius=10,
        focused_border_color=COLOR_CYAN, text_size=13, width=450
    )

    opciones = {
        "🎬 Video Universal H.264 - Máxima (1080p)": ("video", "1080"),
        "🎬 Video Universal H.264 - Media (720p)": ("video", "720"),
        "🎬 Video Ligero H.264 - Ahorro (480p)": ("video", "480"),
        "🎵 Audio MP3 - Estudio (320 kbps)": ("audio", "320"),
        "🎵 Audio MP3 - Estándar (192 kbps)": ("audio", "192")
    }

    dd_formato = ft.Dropdown(
        options=[ft.dropdown.Option(k) for k in opciones.keys()],
        value="🎬 Video Universal H.264 - Máxima (1080p)",
        bgcolor=COLOR_INPUT_BG, border_color=COLOR_BORDER, border_radius=10,
        focused_border_color=COLOR_CYAN, width=450
    )

    progress_bar = ft.ProgressBar(width=400, color=COLOR_CYAN, bgcolor=COLOR_INPUT_BG, value=0.0)
    lbl_porcentaje = ft.Text("0%", size=14, weight=ft.FontWeight.BOLD, color=COLOR_CYAN)
    lbl_estado = ft.Text(f"Carpeta: {RUTA_DESCARGAS}", size=11, color=COLOR_TEXT_DIM)

    btn_descargar = ft.ElevatedButton(
        content=ft.Text("INICIAR DESCARGA", weight=ft.FontWeight.BOLD, color="#000000"),
        style=ft.ButtonStyle(bgcolor=COLOR_CYAN, shape=ft.RoundedRectangleBorder(radius=10), padding=15),
        width=250,
    )

    def ejecutar_descarga(e):
        url_raw = txt_url.value
        if not url_raw:
            lbl_estado.value, lbl_estado.color = "❌ Error: Pega un enlace válido", "#ff5555"
            page.update()
            return

        btn_descargar.disabled = True
        progress_bar.value = 0.0
        lbl_porcentaje.value = "0%"
        lbl_estado.value, lbl_estado.color = "Conectando al servidor...", COLOR_CYAN
        page.update()

        def trabajo():
            url = sanitizar_url(url_raw)
            tipo, calidad = opciones[dd_formato.value]

            if tipo == "audio":
                nombre_archivo = '%(title).100s (Audio).%(ext)s'
            else:
                nombre_archivo = f'%(title).100s ({calidad}p).%(ext)s'

            def progreso_hook(d):
                if d['status'] == 'downloading':
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    percent_str = ansi_escape.sub('', d.get('_percent_str', '0.0%')).replace('%', '').strip()
                    try:
                        p = float(percent_str)
                        progress_bar.value = p / 100.0
                        lbl_porcentaje.value = f"{p:.1f}%"
                        page.update()
                    except ValueError:
                        pass
                elif d['status'] == 'finished':
                    progress_bar.value = None
                    lbl_porcentaje.value = "⏳"
                    lbl_estado.value = "Aplicando formato universal H.264/MP3..."
                    page.update()

            opts = {
                'js_runtimes': {'node': {}, 'deno': {}},
                'restrictfilenames': True,
                'outtmpl': os.path.join(RUTA_DESCARGAS, nombre_archivo),
                'extractor_args': {'youtube': {'player_client': ['mweb', 'android', 'web']}},
                'progress_hooks': [progreso_hook],
                'noprogress': True,
                'overwrites': False,
            }

            if os.path.exists(RUTA_FFMPEG):
                opts['ffmpeg_location'] = RUTA_FFMPEG

            if tipo == "audio":
                opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': calidad}]
                })
            else:
                opts.update({
                    'format': f'bestvideo[height<={calidad}][vcodec^=avc1]+bestaudio[acodec^=mp4a]/best[ext=mp4]/best',
                    'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
                    'postprocessor_args': {'video_convertor': ['-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']}
                })

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])

                progress_bar.value = 1.0
                lbl_porcentaje.value = "100%"
                lbl_estado.value, lbl_estado.color = "🎉 ¡Guardado con éxito en Descargas!", "#50fa7b"
                txt_url.value = ""
            except Exception as ex:
                progress_bar.value = 0.0
                lbl_porcentaje.value = "Error"
                lbl_estado.value, lbl_estado.color = "❌ Enlace no soportado o privado", "#ff5555"
                print(ex)
            finally:
                btn_descargar.disabled = False
                page.update()

        threading.Thread(target=trabajo, daemon=True).start()

    btn_descargar.on_click = ejecutar_descarga

    fila_progreso = ft.Row([progress_bar, lbl_porcentaje], alignment=ft.MainAxisAlignment.CENTER, spacing=15)
    
    card = ft.Container(
        content=ft.Column(
            [lbl_titulo, lbl_sub, ft.Container(height=10), txt_url, dd_formato, ft.Container(height=10), fila_progreso, btn_descargar, lbl_estado],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15
        ),
        bgcolor=COLOR_CARD, padding=30, border_radius=16
    )

    page.add(ft.Row([card], alignment=ft.MainAxisAlignment.CENTER))

if __name__ == "__main__":
    ft.run(main)