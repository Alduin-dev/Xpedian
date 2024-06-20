import tkinter as tk
from tkinter import Button, ttk, filedialog, messagebox, Menu, Scrollbar, Label, Radiobutton, simpledialog
import threading
import re
import os
import requests
from io import BytesIO
from PIL import Image, ImageTk
from pytube import YouTube, Playlist
from concurrent.futures import ThreadPoolExecutor
from pydub import AudioSegment
from plyer import notification

PRIMARY_COLOR = "#007aff"
SECONDARY_COLOR = "#34c759"
BACKGROUND_COLOR = "#f5f5f5"
TEXT_COLOR = "#1c1c1e"

class DownloadManager:
    def __init__(self, root, file_extension):
        self.root = root
        self.file_extension = file_extension
        self.downloads = []
        self.completed_count = 0
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.listbox = None
    def set_listbox(self, listbox):
        self.listbox = listbox

    def add_download(self, url, output_folder):
        download = {
            "url": url,
            "progress": 0,
            "status": "En progreso",
            "output_folder": output_folder,
            "filename": None,
            "title": None,
            "thumbnail": None,
            "file_extension": self.file_extension
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
        self.listbox.delete(0, tk.END)
        for download in self.downloads:
            item_text = f"{download['title']} - {download['url']} - {download['progress']:.2f}% - {download['status']}"
            self.listbox.insert(tk.END, item_text)
            if download['thumbnail']:
                self.listbox.itemconfig(tk.END, {'bg': 'lightgrey'})
                
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
            self.show_notification("Descargas Completadas", "Todas las descargas se han completado con éxito.")

        self.root.after(10000, self.clear_completed_downloads)

    def show_notification(self, title, message):
        notification.notify(
            title=title,
            message=message,
            app_name="Xpedian Downloader",
            timeout=10
        )

    def download_from_url(self, url, output_folder):
        if 'playlist' in url.lower():
            try:
                playlist = Playlist(url)
                for video_url in playlist.video_urls:
                    self.executor.submit(self.download_file, video_url, output_folder)
            except Exception as e:
                messagebox.showerror("Error", f"Error al descargar la lista de reproducción: {e}")
        else:
            self.executor.submit(self.download_file, url, output_folder)

    def download_file(self, url, output_folder):
        if self.file_extension == 'mp4':
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

            audio = AudioSegment.from_file(temp_filename)
            audio.export(filename, format="mp3", bitrate="128k")
            os.remove(temp_filename)

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

def download_from_url(download_manager):
    video_url = simpledialog.askstring("Descargar desde URL", "Introduce la URL del video de YouTube o de la playlist:")
    if video_url and is_valid_youtube_url(video_url):
        output_folder = filedialog.askdirectory(title="Seleccionar carpeta para guardar")
        if not output_folder:
            output_folder = None
        threading.Thread(target=download_manager.download_from_url, args=(video_url, output_folder)).start()
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
        try:
            with open(file_path, 'r') as file:
                urls = [url.strip() for url in file if is_valid_youtube_url(url.strip())]

            if not urls:
                messagebox.showerror("Error", "El archivo de texto no contiene URLs válidas.")
                return

            for url in urls:
                threading.Thread(target=download_manager.download_from_url, args=(url, output_folder)).start()
        except Exception as e:
            messagebox.showerror("Error al procesar el archivo", f"{e}")

def on_right_click(event, download_manager):
    try:
        selection = download_manager.listbox.curselection()
        if selection:
            index = selection[0]
            download = download_manager.downloads[index]
            if download["status"] == "Error":
                context_menu = Menu(download_manager.listbox, tearoff=0)
                context_menu.add_command(
                    label="Eliminar",
                    command=lambda: download_manager.remove_download(download)
                )
                context_menu.post(event.x_root, event.y_root)
    except IndexError:
        pass

def main():
    root = tk.Tk()
    root.title("Xpedian Downloader")

    window_width = 800
    window_height = 500
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

    root.configure(bg=BACKGROUND_COLOR)

    file_extension = simpledialog.askstring("Formato de descarga", "Elija el formato de descarga (mp3 o mp4):")
    if file_extension not in ['mp3', 'mp4']:
        messagebox.showerror("Error", "Por favor, ingresa un formato válido (mp3 o mp4).")
        return

    download_manager = DownloadManager(root, file_extension)

    frame = tk.Frame(root, bg=BACKGROUND_COLOR)
    frame.pack(pady=20, padx=20, fill="both", expand=True)

    listbox_frame = tk.Frame(frame)
    listbox_frame.pack(pady=10, padx=10, fill="both", expand=True)

    scrollbar = Scrollbar(listbox_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    listbox = tk.Listbox(
        listbox_frame,
        bg=BACKGROUND_COLOR,
        fg=TEXT_COLOR,
        font=("Helvetica", 12),
        selectbackground=PRIMARY_COLOR,
        activestyle="none",
        yscrollcommand=scrollbar.set
    )
    listbox.pack(side=tk.LEFT, fill="both", expand=True)
    scrollbar.config(command=listbox.yview)
    
    download_manager.set_listbox(listbox)

    button_frame = tk.Frame(frame, bg=BACKGROUND_COLOR)
    button_frame.pack(pady=10)

    url_button = Button(
        button_frame,
        text="Descargar desde URL",
        bg=PRIMARY_COLOR,
        fg="white",
        font=("Helvetica", 14),
        command=lambda: download_from_url(download_manager)
    )
    url_button.pack(side="left", padx=20)

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
