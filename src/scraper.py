"""
scraper.py

Script principal del TP. Orquesta el proceso completo: obtiene los links de
la categoría elegida, extrae los metadatos y la sinopsis de cada libro, y
limpia los datos crudos para generar el archivo final data/libros.csv.
"""

from obtener_links import obtener_links_libros
from obtener_datos import obtener_datos_libros
from limpiar_datos import limpiar_datos


# --- Configuración ---
CATEGORIA = "Ciencia Ficción"
URL_CATEGORIA = "https://ww3.lectulandia.co/genero/ciencia-ficcion"  # sin el sufijo "/page/N"
TOTAL_PAGINAS = 10  # ~24 libros por página -> aprox. 240 libros

ARCHIVO_LINKS = "data/links.txt"       # checkpoint con los links ya extraídos de la categoría
ARCHIVO_CRUDO = "data/libros_raw.csv"  # checkpoint incremental con los datos sin procesar
ARCHIVO_FINAL = "data/libros.csv"      # entregable final pedido por la consigna

MIN_LIBROS_ESPERADOS = 100
MAX_LIBROS_ESPERADOS = 200


# --- Función principal ---
def main():
    print("=" * 60)
    print(f"Categoría seleccionada: {CATEGORIA}")
    print(f"URL de categoría:       {URL_CATEGORIA}")
    print(f"Páginas a recorrer:     {TOTAL_PAGINAS}")
    print("=" * 60)

    # 1. Obtenemos los links de todos los libros de la categoría
    print("\n[1/3] Obteniendo links de los libros...")
    links = obtener_links_libros(URL_CATEGORIA, TOTAL_PAGINAS, archivo_links=ARCHIVO_LINKS)

    if not links:
        print("No se obtuvo ningún link. Se aborta el proceso.")
        return

    # 2. Visitamos cada ficha y extraemos los datos crudos (con checkpoint)
    print("\n[2/3] Extrayendo metadatos y sinopsis de cada libro...")
    obtener_datos_libros(
        links_para_procesar=links,
        print_console=False,
        categoria_origen=CATEGORIA,
        archivo_csv=ARCHIVO_CRUDO,
    )

    # 3. Limpiamos, validamos y generamos el archivo final
    print("\n[3/3] Limpiando y validando los datos...")
    limpiar_datos(
        archivo_entrada=ARCHIVO_CRUDO,
        archivo_salida=ARCHIVO_FINAL,
        min_libros=MIN_LIBROS_ESPERADOS,
        max_libros=MAX_LIBROS_ESPERADOS,
    )

    print(f"\nProceso completo. Archivo final disponible en: {ARCHIVO_FINAL}")


if __name__ == "__main__":
    main()