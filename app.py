import os
from tkinter import Tk, Label, Entry, Button, StringVar, filedialog, messagebox, Radiobutton
from yt_dlp import YoutubeDL
from flask import Flask, request, jsonify, render_template
import threading

# Descargar audio
def download_audio(url, output_folder):
    try:
        options = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_folder, '%(playlist_title)s/%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': True,
        }
        with YoutubeDL(options) as ydl:
            ydl.download([url])
        return "El audio se descargó correctamente."
    except Exception as e:
        return f"Error al descargar audio: {e}"


# Descargar video
def download_video(url, output_folder):
    try:
        options = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(output_folder, '%(playlist_title)s/%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': True,
        }
        with YoutubeDL(options) as ydl:
            ydl.download([url])
        return "El video se descargó correctamente."
    except Exception as e:
        return f"Error al descargar video: {e}"


# Opción de consola
def console_mode():
    print("Bienvenido al modo consola")
    file_extension = input("Selecciona el formato (mp3 o mp4): ").strip().lower()
    output_folder = input("Introduce la carpeta de salida: ").strip()
    url = input("Introduce la URL del video o playlist: ").strip()
    
    if file_extension == "mp3":
        result = download_audio(url, output_folder)
    elif file_extension == "mp4":
        result = download_video(url, output_folder)
    else:
        result = "Formato no válido."
    
    print(result)


# Opción de escritorio con tkinter
def desktop_mode():
    def select_output_folder():
        folder = filedialog.askdirectory(title="Selecciona la carpeta de salida")
        if folder:
            output_folder.set(folder)

    def start_download():
        url = url_var.get().strip()
        folder = output_folder.get()
        format_choice = format_var.get()

        if not url or not folder:
            messagebox.showerror("Error", "Por favor, completa todos los campos.")
            return

        if format_choice == "mp3":
            result = download_audio(url, folder)
        elif format_choice == "mp4":
            result = download_video(url, folder)
        else:
            result = "Formato no válido."

        messagebox.showinfo("Resultado", result)

    root = Tk()
    root.title("Xpedian Downloader")
    root.geometry("500x400")

    url_var = StringVar()
    output_folder = StringVar()
    format_var = StringVar(value="mp3")

    Label(root, text="Introduce la URL:").pack(pady=5)
    Entry(root, textvariable=url_var, width=50).pack(pady=5)

    Label(root, text="Formato de descarga:").pack(pady=5)
    Radiobutton(root, text="MP3 (Audio)", variable=format_var, value="mp3").pack()
    Radiobutton(root, text="MP4 (Video)", variable=format_var, value="mp4").pack()

    Label(root, text="Selecciona la carpeta de salida:").pack(pady=5)
    Button(root, text="Seleccionar Carpeta", command=select_output_folder).pack(pady=5)

    Button(root, text="Iniciar Descarga", command=start_download).pack(pady=20)

    root.mainloop()


# Opción de web con Flask
def web_mode():
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template("index.html")  # Crear un archivo `templates/index.html`

    @app.route("/download", methods=["POST"])
    def download():
        url = request.form.get("url")
        format_choice = request.form.get("format")
        output_folder = request.form.get("folder")

        if not url or not output_folder:
            return jsonify({"error": "Faltan datos."}), 400

        if format_choice == "mp3":
            result = download_audio(url, output_folder)
        elif format_choice == "mp4":
            result = download_video(url, output_folder)
        else:
            result = "Formato no válido."

        return jsonify({"message": result})

    threading.Thread(target=lambda: app.run(debug=True, use_reloader=False)).start()


# Menú principal
def main_menu():
    print("Bienvenido a Xpedian Downloader")
    print("Selecciona un modo de uso:")
    print("1. Modo Consola")
    print("2. Modo Escritorio (GUI)")
    print("3. Modo Web")
    choice = input("Elige una opción (1/2/3): ").strip()

    if choice == "1":
        console_mode()
    elif choice == "2":
        desktop_mode()
    elif choice == "3":
        web_mode()
        print("Abre tu navegador en http://127.0.0.1:5000")
    else:
        print("Opción no válida.")


if __name__ == "__main__":
    main_menu()
