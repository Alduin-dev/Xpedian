import os
import re
import threading
from tkinter import Tk, Frame, Listbox, Button, Menu, simpledialog, filedialog, messagebox
from yt_dlp import YoutubeDL

PRIMARY_COLOR = "#007aff"
SECONDARY_COLOR = "#34c759"
BACKGROUND_COLOR = "#f5f5f5"
TEXT_COLOR = "#1c1c1e"

# Clase para gestionar descargas
class DownloadManager:
    def __init__(self, root):
        self.root = root
        self.downloads = []

    def add_download(self, url, output_folder, file_extension):
        download = {
            "url": url,
            "progress": 0,
            "status": "Pendiente",
            "output_folder": output_folder,
            "file_extension": file_extension,
        }
        self.downloads.append(download)
        return download

    def update_progress(self, download, percent_complete):
        download["progress"] = percent_complete
        self.update_list()

    def update_list(self):
        listbox.delete(0, "end")
        for download in self.downloads:
            listbox.insert(
                "end", f"{download['url']} - {download['progress']:.2f}% - {download['status']}"
            )

    def download_playlist(self, url, output_folder, file_extension):
        try:
            with YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                urls = [entry['url'] for entry in info.get('entries', [])]
                for video_url in urls:
                    threading.Thread(target=self.download_file, args=(video_url, output_folder, file_extension)).start()
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar la lista: {e}")

    def download_file(self, url, output_folder, file_extension):
        download = self.add_download(url, output_folder, file_extension)
        download["status"] = "En progreso"
        self.update_list()

        try:
            ydl_opts = {
                'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
                'format': 'bestaudio/best' if file_extension == 'mp3' else 'bestvideo+bestaudio',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}] if file_extension == 'mp3' else [],
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            download["status"] = "Completado"
            download["progress"] = 100
            notify_download_completed(download)
        except Exception as e:
            download["status"] = "Error"
            messagebox.showerror("Error", f"Error al descargar {url}: {e}")
        finally:
            self.update_list()

    def download_from_url(self, url, output_folder, file_extension):
        if "playlist" in url.lower():
            threading.Thread(target=self.download_playlist, args=(url, output_folder, file_extension)).start()
        else:
            threading.Thread(target=self.download_file, args=(url, output_folder, file_extension)).start()

    def remove_download(self, index):
        if 0 <= index < len(self.downloads):
            del self.downloads[index]
            self.update_list()


# Validación de URL
def is_valid_url(url):
    youtube_pattern = r"(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+"
    return re.match(youtube_pattern, url) is not None


# Pedir formato
def ask_file_extension():
    file_extension = simpledialog.askstring("Formato", "Elija el formato de descarga (mp3 o mp4):")
    if file_extension and file_extension.lower() in ['mp3', 'mp4']:
        return file_extension.lower()
    else:
        messagebox.showerror("Error", "Por favor, ingresa un formato válido (mp3 o mp4).")
        return None


# Notificación de finalización
def notify_download_completed(download):
    messagebox.showinfo("Descarga Completada", f"La descarga de {download['url']} se completó correctamente.")


# Descargar desde una URL
def download_from_url(download_manager):
    video_url = simpledialog.askstring("Descargar desde URL", "Introduce la URL del video o la playlist:")
    if video_url and is_valid_url(video_url):
        output_folder = filedialog.askdirectory(title="Seleccionar carpeta para guardar")
        if not output_folder:
            return

        file_extension = ask_file_extension()
        if file_extension:
            download_manager.download_from_url(video_url, output_folder, file_extension)
    else:
        messagebox.showerror("Error", "Por favor, ingresa una URL válida.")


# Cargar un archivo TXT
def load_txt_file(download_manager):
    file_path = filedialog.askopenfilename(
        title="Seleccionar archivo .txt",
        filetypes=[("Archivos de texto", "*.txt")]
    )
    if not file_path:
        return

    with open(file_path, "r") as file:
        urls = file.readlines()

    if urls:
        output_folder = filedialog.askdirectory(title="Seleccionar carpeta para guardar")
        if not output_folder:
            return

        file_extension = ask_file_extension()
        if file_extension:
            for url in urls:
                url = url.strip()
                if is_valid_url(url):
                    download_manager.download_from_url(url, output_folder, file_extension)
                else:
                    messagebox.showerror("Error", f"URL inválida: {url}")


# Menú contextual
def on_right_click(event, download_manager):
    selection = listbox.curselection()
    if selection:
        index = selection[0]
        context_menu = Menu(listbox, tearoff=0)
        context_menu.add_command(label="Eliminar", command=lambda: download_manager.remove_download(index))
        context_menu.post(event.x_root, event.y_root)


# Interfaz principal
def main():
    global listbox
    root = Tk()
    root.title("Xpedian Downloader")

    window_width = 800
    window_height = 400
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

    root.configure(bg=BACKGROUND_COLOR)
    download_manager = DownloadManager(root)

    frame = Frame(root, bg=BACKGROUND_COLOR)
    frame.pack(pady=20, padx=20, fill="both", expand=True)

    listbox = Listbox(
        frame,
        bg=BACKGROUND_COLOR,
        fg=TEXT_COLOR,
        font=("Helvetica", 12),
        selectbackground=PRIMARY_COLOR,
        activestyle="none"
    )
    listbox.pack(pady=10, padx=10, fill="both", expand=True)
    listbox.bind("<Button-3>", lambda event: on_right_click(event, download_manager))

    button_frame = Frame(root, bg=BACKGROUND_COLOR)
    button_frame.pack(pady=10)

    download_button = Button(
        button_frame,
        text="Descargar desde URL",
        bg=PRIMARY_COLOR,
        fg="white",
        font=("Helvetica", 14),
        command=lambda: download_from_url(download_manager)
    )
    download_button.pack(side="left", padx=10)

    load_txt_button = Button(
        button_frame,
        text="Cargar archivo .txt",
        bg=SECONDARY_COLOR,
        fg="white",
        font=("Helvetica", 14),
        command=lambda: load_txt_file(download_manager)
    )
    load_txt_button.pack(side="left", padx=10)

    root.mainloop()


if __name__ == "__main__":
    main()
