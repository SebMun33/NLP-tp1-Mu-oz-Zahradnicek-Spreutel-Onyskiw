"""
limpiar_datos.py

Toma el CSV crudo generado por obtener_datos_libros, aplica los controles
mínimos pedidos en la consigna (duplicados, títulos, URLs, espacios, valores
ausentes y cantidad final) y guarda el resultado en un CSV limpio.

valor_faltante (str):          valor que se asigna a los campos ausentes o inválidos
patron_url (re.Pattern):       patrón regex para validar URLs de libros
archivo_entrada (str):         ruta del CSV crudo a limpiar
archivo_salida (str):          ruta del CSV limpio a generar (si es None, sobrescribe el archivo de entrada)
min_libros (int):              cantidad mínima de libros esperada en el CSV final
max_libros (int):              cantidad máxima de libros esperada en el CSV

"""

import re
from pathlib import Path
import pandas as pd

VALOR_FALTANTE = "N/A"
PATRON_URL = re.compile(r"^https?://", re.IGNORECASE)


# --- Función para normalizar un valor de texto ---
def _limpiar_texto(valor):
    """Recorta espacios, colapsa saltos de línea y unifica los valores ausentes en 'N/A'."""

    texto = str(valor) if valor is not None else ""

    if texto.strip().lower() in ("", "nan", "none", "n/a", "na"):
        return VALOR_FALTANTE

    # Reemplazamos cualquier secuencia de espacios, tabs o saltos de línea por un solo espacio
    return re.sub(r"\s+", " ", texto).strip()


# --- Función para limpiar y validar los datos ---
def limpiar_datos(archivo_entrada='data/libros_raw.csv', archivo_salida=None, min_libros=100, max_libros=200):

    """Limpia y valida 'archivo_entrada' según los controles mínimos del TP y guarda 'archivo_salida'."""

    # Creamos las rutas de entrada y salida, y nos aseguramos de que el directorio de salida exista
    ruta_entrada = Path(archivo_entrada)
    # Si archivo_salida es None, sobrescribimos el archivo de entrada
    ruta_salida = Path(archivo_salida) if archivo_salida else ruta_entrada
    # Nos aseguramos de que el directorio de salida exista
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    # Control de seguridad: si no hay datos crudos, no hay nada para limpiar
    if not ruta_entrada.exists() or ruta_entrada.stat().st_size == 0:
        print(f"No se encontró el archivo '{ruta_entrada}' o está vacío.")
        return None

    df = pd.read_csv(ruta_entrada, dtype=str)
    total_crudo = len(df)

    # --- 1. LIMPIEZA DE TEXTO (espacios, saltos de línea y valores ausentes) ---
    for columna in df.columns:
        df[columna] = df[columna].apply(_limpiar_texto)

    # --- 2. DESCARTAR REGISTROS SIN TÍTULO ---
    sin_titulo = (df['titulo'] == VALOR_FALTANTE).sum()
    df = df[df['titulo'] != VALOR_FALTANTE]

    # --- 3. DESCARTAR REGISTROS CON URL INVÁLIDA ---
    url_valida = df['url_libro'].str.match(PATRON_URL)
    url_invalida = (~url_valida).sum()
    df = df[url_valida]

    # --- 4. ELIMINAR LIBROS DUPLICADOS (mismo url_libro, se conserva el primero) ---
    duplicados = df.duplicated(subset='url_libro').sum()
    df = df.drop_duplicates(subset='url_libro', keep='first')

    # --- 5. ACOTAR AL MÁXIMO PEDIDO (si sobran libros, nos quedamos con los 'max_libros' primeros) ---
    sobrantes = max(0, len(df) - max_libros)
    if sobrantes:
        df = df.iloc[:max_libros]

    # --- 6. ESTADÍSTICAS FINALES ---
    total_final = len(df)
    con_sinopsis = (df['sinopsis'] != VALOR_FALTANTE).sum()
    porcentaje_sinopsis = (con_sinopsis / total_final * 100) if total_final else 0

    sinopsis_validas = (df['sinopsis'].str.len() > 200).sum()
    porcentaje_sinopsis_valida = (sinopsis_validas / total_final * 100) if total_final else 0

    # Guardamos el CSV limpio (sobrescribe si archivo_salida == archivo_entrada)
    df.to_csv(ruta_salida, index=False, encoding='utf-8')

    # --- REPORTE DE CONTROLES MÍNIMOS ---
    print("\n" + "=" * 60)
    print("REPORTE DE LIMPIEZA Y VALIDACIÓN")
    print("=" * 60)
    print(f"Registros crudos leídos:           {total_crudo}")
    print(f"Descartados por falta de título:   {sin_titulo}")
    print(f"Descartados por URL inválida:      {url_invalida}")
    print(f"Duplicados eliminados (url_libro): {duplicados}")
    print(f"Recortados por exceder el máximo:  {sobrantes} (se conservan los primeros {max_libros})" if sobrantes else "Recortados por exceder el máximo:  0")
    print(f"Registros finales:                 {total_final}")
    print(f"Con sinopsis:                      {con_sinopsis} ({porcentaje_sinopsis:.1f}%)")
    print(f"Con sinopsis > 200 caracteres:     {sinopsis_validas} ({porcentaje_sinopsis_valida:.1f}%)")
    print("-" * 60)
    print("OK  - Sin registros duplicados por url_libro." if total_final == df['url_libro'].nunique()
          else "FALLO - Aún hay url_libro duplicadas.")
    print("OK  - Todos los registros tienen título." if total_final and (df['titulo'] != VALOR_FALTANTE).all()
          else "FALLO - Hay registros sin título.")
    print("OK  - Todos los registros tienen una URL válida." if total_final and df['url_libro'].str.match(PATRON_URL).all()
          else "FALLO - Hay registros con URL inválida.")
    print(f"OK  - La mayoría de los registros tiene sinopsis ({porcentaje_sinopsis:.1f}%)." if porcentaje_sinopsis >= 50
          else f"ADVERTENCIA - Menos de la mitad tiene sinopsis ({porcentaje_sinopsis:.1f}%).")
    print(f"OK  - La cantidad final ({total_final}) está dentro del rango esperado [{min_libros}-{max_libros}]." if min_libros <= total_final <= max_libros
          else f"ADVERTENCIA - La cantidad final ({total_final}) no está en el rango esperado [{min_libros}-{max_libros}].")
    print("=" * 60)
    print(f"Archivo final guardado en: {ruta_salida}")

    return str(ruta_salida)


if __name__ == "__main__":
    limpiar_datos()