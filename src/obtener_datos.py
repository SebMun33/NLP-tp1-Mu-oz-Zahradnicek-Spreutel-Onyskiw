"""
obtener_datos.py

Visita la ficha individual de cada libro, extrae sus metadatos y su sinopsis,
y guarda los resultados de forma incremental en un CSV, con soporte de
reanudación (checkpoint) por si el proceso se corta a mitad de camino.

links_para_procesar (list):     lista de URLs de libros a visitar
print_console (bool):           si es True, imprime en consola los datos extraídos de cada libro
categoria_origen (str):         nombre de la categoría de donde se extrajeron los links
archivo_csv (str):              ruta del archivo CSV donde se guardarán los datos extraídos

"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import csv
from pathlib import Path


# --- Función para obtener los datos de los libros ---
def obtener_datos_libros(links_para_procesar, print_console=True, categoria_origen='Ciencia Ficción', archivo_csv='data/libros.csv'):

    """Visita cada link de 'links_para_procesar', extrae los metadatos y guarda todo en 'archivo_csv'."""

    # Creamos la ruta del archivo CSV y nos aseguramos de que el directorio exista
    ruta_csv = Path(archivo_csv)
    ruta_csv.parent.mkdir(parents=True, exist_ok=True)

    # --- 1. LÓGICA DE REANUDACIÓN (CHECKPOINT) ---
    modo_apertura = 'w'
    escribir_cabecera = True

    # Si el archivo ya existe y tiene datos adentro
    if ruta_csv.exists() and ruta_csv.stat().st_size > 0:

        # Cargamos todos los links que ya están en el CSV
        with ruta_csv.open('r', encoding='utf-8') as f:
            links_procesados = {fila['url_libro'] for fila in csv.DictReader(f)}

        # Filtramos la lista original: nos quedamos solo con los links que NO están en el set
        links_restantes = [link for link in links_para_procesar if link not in links_procesados]

        # Si hubo filtrado (es decir, ya había libros procesados), ajustamos el modo de escritura
        if len(links_restantes) < len(links_para_procesar):
            modo_apertura = 'a'                                 # Abrimos en modo append para no sobrescribir
            escribir_cabecera = False                           # No escribimos la cabecera de nuevo
            links_para_procesar = links_restantes
            print(f"Archivo detectado. Ya hay {len(links_procesados)} libros. Retomando los {len(links_para_procesar)} restantes...")

    # Control de seguridad: Si la lista quedó vacía, cortamos la ejecución
    if not links_para_procesar:
        print("¡Todos los links de esta lista ya fueron procesados previamente! No hay datos nuevos que extraer.")
        return str(ruta_csv)

    # --- 2. EXTRACCIÓN DE DATOS ---
    # Abrimos el archivo CSV (dinámicamente en modo 'w' o 'a')
    with ruta_csv.open(modo_apertura, newline='', encoding='utf-8') as f_csv:

        # Definimos las columnas del archivo CSV y creamos un objeto DictWriter
        columnas = ['titulo', 'autores', 'generos', 'serie', 'sinopsis', 'url_portada', 'url_libro', 'fecha_extraccion', 'categoria_origen']
        escritor = csv.DictWriter(f_csv, fieldnames=columnas)

        # Solo escribimos la cabecera si es un archivo nuevo o se reinició
        if escribir_cabecera:
            escritor.writeheader()

        libros_guardados = 0

        # Iniciamos Playwright (Indentado DENTRO de la apertura del archivo)
        with sync_playwright() as p:

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for link in links_para_procesar:
                print(f"Procesando: {link}")

                try:
                    page.goto(link, timeout=60000)
                    time.sleep(2)

                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    contenedor_libro = soup.select_one('#bookWrapper #book')

                    if contenedor_libro:

                        # Extraemos todos los datos
                        contenedor_titulo = contenedor_libro.select_one('#title h1')
                        titulo = contenedor_titulo.get_text(strip=True) if contenedor_titulo else "N/A"

                        contenedor_autor = contenedor_libro.select_one('#autor a')
                        autores = contenedor_autor.get_text(strip=True) if contenedor_autor else "N/A"

                        etiquetas = contenedor_libro.select('#genero a.dinSource')
                        generos_lista = [etiqueta.get_text(strip=True) for etiqueta in etiquetas]
                        generos = ", ".join(generos_lista) if generos_lista else "N/A"

                        contenedor_serie = contenedor_libro.select_one('#serie')
                        serie = contenedor_serie.get_text(strip=True) if contenedor_serie else "N/A"

                        contenedor_sinopsis = contenedor_libro.select_one('#sinopsis')
                        sinopsis = contenedor_sinopsis.get_text(strip=True) if contenedor_sinopsis else "N/A"

                        contenedor_portada = contenedor_libro.select_one('#leftBlock #cover img')
                        url_portada = contenedor_portada.get('src') if contenedor_portada else "N/A"

                        fecha_extraccion = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

                        # Armamos el diccionario
                        registro = {
                            'titulo': titulo,
                            'autores': autores,
                            'generos': generos,
                            'serie': serie,
                            'sinopsis': sinopsis,
                            'url_portada': url_portada,
                            'url_libro': link,
                            'fecha_extraccion': fecha_extraccion,
                            'categoria_origen': categoria_origen
                        }

                        # --- GUARDADO INCREMENTAL ---
                        escritor.writerow(registro)
                        f_csv.flush()  # Obligamos al SO a escribir físicamente en el disco
                        libros_guardados += 1

                        if print_console:
                            print(f"\n    Título: {titulo}")
                            print(f"    Autores: {autores}")
                            print(f"    Géneros: {generos}")
                            print(f"    Serie: {serie}")
                            print(f"    Sinopsis: {sinopsis[:50]}...")
                            print(f"    URL Portada: {url_portada}")
                            print(f"    URL Libro: {link}")
                            print(f"    Fecha de extracción: {fecha_extraccion}")
                            print(f"    Categoría: {categoria_origen}")
                            print("-" * 50)

                except Exception as e:
                    print(f"Error al procesar el link {link}: {e}")

            browser.close()

    print(f"\nProceso finalizado. Se guardaron {libros_guardados} libros nuevos en '{ruta_csv}'.")
    return str(ruta_csv)