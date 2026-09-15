"""
obtener_links.py

Recorre las páginas de listado de una categoría de Lectulandia y devuelve
los links a las fichas individuales de cada libro encontrado.

url_base_categoria (str):       URL de la categoría sin el sufijo "/page/N"
total_paginas (int):            Cantidad de páginas a recorrer (cada página tiene ~24 libros)
archivo_links (str):            ruta de un archivo de texto donde se guardan los links ya
                                 extraídos, para no tener que repetir el recorrido de páginas
                                 en corridas posteriores del scraper

"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from pathlib import Path
import time


# --- Función para obtener los links de los libros ---
def obtener_links_libros(url_base_categoria, total_paginas, archivo_links='data/links.txt'):

    """Recorre 'total_paginas' páginas de la categoría y devuelve la lista de URLs de libros.

    Si 'archivo_links' ya existe con contenido, se asume que los links fueron extraídos en una
    corrida anterior y se cargan directamente desde ahí, sin volver a recorrer las páginas.
    """

    ruta_links = Path(archivo_links)

    # --- CHECKPOINT: si ya tenemos los links guardados de una corrida anterior, los reutilizamos ---
    if ruta_links.exists() and ruta_links.stat().st_size > 0:
        with ruta_links.open('r', encoding='utf-8') as f:
            links_guardados = [linea.strip() for linea in f if linea.strip()]
        print(f"Se encontraron {len(links_guardados)} links guardados en '{ruta_links}'. Se reutilizan (no se vuelven a buscar).")
        return links_guardados

    # Lista para almacenar los links extraídos
    links = []

    # Iniciamos Playwright
    with sync_playwright() as p:

        # Abrimos un navegador Chromium
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Bucle de las páginas
        for i in range(1, total_paginas + 1):

            # Construimos la URL de la página actual
            url_actual = f"{url_base_categoria}/page/{i}"
            print(f"Visitando: {url_actual}")

            try:
                # Playwright abre la página
                page.goto(url_actual, timeout=60000)

                # Pequeña pausa para no saturar el servidor
                time.sleep(2)

                # Obtenemos el HTML de la página
                html = page.content()

                # BeautifulSoup analiza el HTML
                soup = BeautifulSoup(html, 'html.parser')

                # Buscamos el contenedor de los libros
                books_grid = soup.find('div', class_='books-grid')

                if books_grid:
                    # Buscamos todos los <a> con la clase 'title'
                    titulos = books_grid.find_all('a', class_='title')

                    for titulo in titulos:
                        # Extraemos el atributo href
                        link = titulo.get('href')

                        # A veces los links son relativos (ej: /libro/it).
                        # Si es así, se concatena con la URL base del sitio.
                        if link.startswith('/'):
                            link_completo = f"https://ww3.lectulandia.co{link}"
                        else:
                            link_completo = link

                        links.append(link_completo)
                else:
                    print(f"No se encontró el grid de libros en la página {i}")

            except Exception as e:
                # Si falla una página, el programa sigue con la otra
                print(f"Error al procesar la página {i}: {e}")

        # Cerramos el navegador
        browser.close()

    # --- Guardamos los links extraídos para no tener que repetir este recorrido en el futuro ---
    ruta_links.parent.mkdir(parents=True, exist_ok=True)
    with ruta_links.open('w', encoding='utf-8') as f:
        f.write("\n".join(links))

    print(f"\nSe extrajeron un total de {len(links)} links. Guardados en '{ruta_links}'.")
    return links