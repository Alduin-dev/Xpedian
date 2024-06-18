import tkinter as tk
from tkinter import Button, ttk, filedialog, messagebox, simpledialog, Menu
import threading
import re
import os
import requests
from io import BytesIO
from PIL import Image, ImageTk
from pytube import YouTube, Playlist
from concurrent.futures import ThreadPoolExecutor
from pydub import AudioSegment

# Definición de colores y tema
PRIMARY_COLOR = "#007aff"
SECONDARY_COLOR = "#34c759"
BACKGROUND_COLOR = "#f5f5f5"
TEXT_COLOR = "#1c1c1e"

class DownloadManager:
    def __init__(self, root):
        self.root = root
        self.downloads = []
        self.completed_count = 0
        self.executor = ThreadPoolExecutor(max_workers=5)

    def add_download(self, url, output_folder, file_extension='mp3'):
        download = {
            "url": url,
            "progress": 0,
            "status": "En progreso",
            "output_folder": output_folder,
            "filename": None,
            "title": None,
            "thumbnail": None,
            "file_extension": file_extension
        }
        self.downloads.append(download)
        return download

    def on_progress(self, download, stream, chunk, bytes_remaining):
        try:
            total_size = stream.filesize
            bytes_downloaded = total_size - bytes_remaining
            percent_complete = (bytes_downloaded / total_size) * 100
            download["progress"] = percent_complete
            self.root.after(100, self.update_list)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error al calcular el progreso: {e}"))

    def update_list(self):
        listbox.delete(0, tk.END)
        for download in self.downloads:
            listbox.insert(
                tk.END, f"{download['title']} - {download['url']} - {download['progress']:.2f}% - {download['status']}"
            )

    def clear_completed_downloads(self):
        self.downloads = [d for d in self.downloads if d["status"] != "Completado"]
        self.update_list()

    def on_complete(self, download):
        download["status"] = "Completado"
        download["progress"] = 100
        self.completed_count += 1
        self.root.after(100, self.update_list)

        if self.completed_count == len(self.downloads):
            self.root.after(0, lambda: messagebox.showinfo("Éxito", "Todas las descargas se han completado."))

        # Limpiar la lista después de 10 segundos
        self.root.after(10000, self.clear_completed_downloads)

    def download_from_url(self, url, output_folder, file_extension='mp3'):
        if 'playlist' in url.lower():
            try:
                playlist = Playlist(url)
                for video_url in playlist.video_urls:
                    self.executor.submit(self.download_file, video_url, output_folder, file_extension)
            except Exception as e:
                messagebox.showerror("Error", f"Error al descargar la lista de reproducción: {e}")
        else:
            self.executor.submit(self.download_file, url, output_folder, file_extension)

    def download_file(self, url, output_folder, file_extension='mp3'):
        if file_extension == 'mp4':
            self.download_video_mp4_single(url, output_folder)
        else:
            self.download_mp3_single(url, output_folder)

    def download_mp3_single(self, url, output_folder):
        download = self.add_download(url, output_folder)
        try:
            yt = YouTube(url, on_progress_callback=lambda s, c, b: self.on_progress(download, s, c, b))
            stream = yt.streams.filter(only_audio=True).first()

            if not stream:
                messagebox.showerror("Error", "No se encontró ningún flujo de audio.")
                return

            filename = re.sub(r'[^\w\s-]', '', yt.title) + ".mp3"
            download["title"] = yt.title
            if output_folder:
                filename = os.path.join(output_folder, filename)
                download["filename"] = filename

            temp_filename = filename.replace(".mp3", "_temp.mp4")
            stream.download(output_path=output_folder, filename=temp_filename)

            # Convertir a mp3 con 128kbps usando pydub
            audio = AudioSegment.from_file(temp_filename)
            audio.export(filename, format="mp3", bitrate="128k")
            os.remove(temp_filename)  # Eliminar el archivo temporal

            thumbnail_url = yt.thumbnail_url
            self.download_thumbnail(thumbnail_url, download)

            self.on_complete(download)
        except Exception as e:
            download["status"] = "Error"
            self.update_list()
            messagebox.showerror("Error", f"Error al descargar el archivo: {e}")

    def download_video_mp4_single(self, url, output_folder):
        download = self.add_download(url, output_folder, file_extension='mp4')
        try:
            yt = YouTube(url, on_progress_callback=lambda s, c, b: self.on_progress(download, s, c, b))
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

            if not stream:
                messagebox.showerror("Error", "No se encontró ningún flujo de video MP4 disponible.")
                return

            filename = re.sub(r'[^\w\s-]', '', yt.title) + ".mp4"
            download["title"] = yt.title
            if output_folder:
                filename = os.path.join(output_folder, filename)
                download["filename"] = filename

            stream.download(output_path=output_folder, filename=filename)

            thumbnail_url = yt.thumbnail_url
            self.download_thumbnail(thumbnail_url, download)

            self.on_complete(download)
        except Exception as e:
            download["status"] = "Error"
            self.update_list()
            messagebox.showerror("Error", f"Error al descargar el archivo: {e}")

    def download_thumbnail(self, thumbnail_url, download):
        try:
            response = requests.get(thumbnail_url)
            if response.status_code == 200:
                img_data = BytesIO(response.content)
                image = Image.open(img_data)
                thumbnail = ImageTk.PhotoImage(image)
                download["thumbnail"] = thumbnail
                self.root.after(100, self.update_list)
        except Exception as e:
            messagebox.showerror("Error", f"Error al descargar la portada: {e}")

    def remove_download(self, download):
        if download in self.downloads:
            self.downloads.remove(download)
            self.update_list()

def is_valid_youtube_url(url):
    youtube_pattern = r"(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+"
    return re.match(youtube_pattern, url) is not None

def ask_file_extension():
    file_extension = simpledialog.askstring("Formato de descarga", "Elija el formato de descarga (mp3 o mp4):")
    if file_extension and file_extension.lower() in ['mp3', 'mp4']:
        return file_extension.lower()
    else:
        messagebox.showerror("Error", "Por favor, ingresa un formato válido (mp3 o mp4).")
        return None

def download_from_url(download_manager):
    video_url = simpledialog.askstring("Descargar desde URL", "Introduce la URL del video de YouTube o de la playlist:")
    if video_url and is_valid_youtube_url(video_url):
        output_folder = filedialog.askdirectory(title="Seleccionar carpeta para guardar")
        if not output_folder:
            output_folder = None

        file_extension = ask_file_extension()
        if file_extension:
            threading.Thread(target=download_manager.download_from_url, args=(video_url, output_folder, file_extension)).start()
    else:
        messagebox.showerror("Error", "Por favor, ingresa una URL de YouTube o playlist válida.")

def download_from_file(download_manager):
    file_path = filedialog.askopenfilename(
        title="Seleccionar archivo de texto",
        filetypes=[("Archivos de texto", "*.txt")]
    )
    if file_path:
        output_folder = filedialog.askdirectory(title="Seleccionar carpeta para guardar")
        if not output_folder:
            output_folder = None

        file_extension = ask_file_extension()
        if file_extension:
            try:
                with open(file_path, 'r') as file:
                    urls = [url.strip() for url in file if is_valid_youtube_url(url.strip())]

                if not urls:
                    messagebox.showerror("Error", "El archivo de texto no contiene URLs válidas.")
                    return

                for url in urls:
                    threading.Thread(target=download_manager.download_from_url, args=(url, output_folder, file_extension)).start()
            except Exception as e:
                messagebox.showerror("Error al procesar el archivo", f"{e}")

def on_right_click(event, download_manager):
    try:
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            download = download_manager.downloads[index]
            if download["status"] == "Error":
                context_menu = Menu(listbox, tearoff=0)
                context_menu.add_command(
                    label="Eliminar",
                    command=lambda: download_manager.remove_download(download)
                )
                context_menu.post(event.x_root, event.y_root)
    except IndexError:
        pass

def main():
    global listbox
    root = tk.Tk()
    root.title("Xpedian")

    window_width = 800
    window_height = 400
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

    root.configure(bg=BACKGROUND_COLOR)
    download_manager = DownloadManager(root)

    frame = tk.Frame(root, bg=BACKGROUND_COLOR)
    frame.pack(pady=20, padx=20, fill="both", expand=True)

    listbox = tk.Listbox(
        frame,
        bg=BACKGROUND_COLOR,
        fg=TEXT_COLOR,
        font=("Helvetica", 12),
        selectbackground=PRIMARY_COLOR,
        activestyle="none"
    )
    listbox.pack(pady=10, padx=10, fill="both", expand=True)
    listbox.bind("<Button-3>", lambda event: on_right_click(event, download_manager))

    button_frame = tk.Frame(root, bg=BACKGROUND_COLOR)
    button_frame.pack(pady=10)

    download_button = Button(
        button_frame,
        text="Descargar desde URL",
        bg=PRIMARY_COLOR,
        fg="white",
        font=("Helvetica", 14),
        command=lambda: download_from_url(download_manager)
    )
    download_button.pack(side="left", padx=20)

    file_button = Button(
        button_frame,
        text="Descargar desde archivo",
        bg=SECONDARY_COLOR,
        fg="white",
        font=("Helvetica", 14),
        command=lambda: download_from_file(download_manager)
    )
    file_button.pack(side="left", padx=20)

    root.mainloop()

if __name__ == "__main__":
    main()
