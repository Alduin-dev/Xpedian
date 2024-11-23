# Xpedian

Xpedian es una aplicación de escritorio desarrollada en Python utilizando Tkinter para descargar videos y audios desde YouTube. Permite descargar archivos en formato MP3 y MP4, y gestiona múltiples descargas simultáneamente.

## Características

- Descarga videos en formato MP4.
- Descarga audios en formato MP3.
- Soporte para listas de reproducción de YouTube.
- Interfaz gráfica intuitiva.
- Gestión de múltiples descargas simultáneas.
- Notificaciones al completar todas las descargas.

## Requisitos

- Python 3.x
- Tkinter
- requests
- Pillow
- pytube
- pydub
- plyer

## Instalación

1. Instala las dependencias:
    ```sh
    pip install -r requirements.txt
    ```

## Uso

1. Ejecuta la aplicación:
    ```sh
    python app.py
    ```

2. Selecciona el formato de descarga (MP3 o MP4).

3. Utiliza los botones para descargar desde una URL o un archivo de texto con múltiples URLs.

## Estructura del Proyecto

- `app.py`: Archivo principal que contiene la lógica de la aplicación.
- `requirements.txt`: Lista de dependencias necesarias para ejecutar la aplicación.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Para más información, consulta el archivo LICENSE.