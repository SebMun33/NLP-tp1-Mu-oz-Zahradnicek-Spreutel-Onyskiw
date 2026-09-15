# Trabajo Unidad 1 — Procesamiento del Lenguaje Natural

Scraper de [Lectulandia](https://ww3.lectulandia.co) que arma un corpus de libros (metadatos +
sinopsis) para usarlo más adelante en actividades de procesamiento de texto y en un
recomendador de libros.

## 1) Integrantes del grupo

| Nombre y Apellido | Legajo |
| ------------------ | ------ |
| Sebastian Muñoz    |        |
| Manuel Spreutels   |        |
| Lara Onyskiw       |        |
| Ezequiel Zahradnicek |      |
| Erica              |        |

## 2) Categoría seleccionada

**Ciencia Ficción** — https://ww3.lectulandia.co/genero/ciencia-ficcion/

Se recorrieron 10 páginas de listado (~24 libros por página) para cubrir el rango de entre
100 y 200 libros pedido por la consigna.

## 3) Cantidad de libros extraídos

**200 libros**, dentro del rango [100-200] solicitado. El detalle final está en `data/libros.csv`.

## 4) Instrucciones de instalación

1. Clonar el repositorio y ubicarse en la carpeta del proyecto.
2. Crear y activar un entorno virtual (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate      # En Windows: venv\Scripts\activate
   ```
3. Instalar las dependencias del proyecto:
   ```bash
   pip install -r requirements.txt
   ```
4. Instalar el navegador que usa Playwright (solo la primera vez):
   ```bash
   playwright install chromium
   ```

## 5) Instrucciones para ejecutar el programa

1. Pararse en la carpeta `src/` (o ajustar los imports/paths si se ejecuta desde la raíz).
2. Ejecutar el script principal:
   ```bash
   python scraper.py
   ```
3. El proceso corre en tres etapas y genera archivos intermedios dentro de `data/`, todos con
   soporte de reanudación (si se corta a mitad de camino, al volver a ejecutarlo continúa
   donde quedó en lugar de empezar de cero):
   - `data/links.txt`: links a las fichas de cada libro (se recorren las páginas de la
     categoría una sola vez; en corridas posteriores se reutiliza este archivo).
   - `data/libros_raw.csv`: metadatos y sinopsis crudos, uno por libro, guardados de forma
     incremental a medida que se visita cada ficha.
   - `data/libros.csv`: archivo final, ya limpio y validado (es el entregable pedido por la
     consigna).
4. Si se quiere volver a extraer todo desde cero, basta con borrar los archivos de `data/`
   antes de ejecutar `scraper.py`.

## 6) Principales dificultades encontradas

- El sitio carga el listado de libros con contenido dinámico, por lo que fue necesario usar
  Playwright (en lugar de un simple `requests`) para poder renderizar la página antes de
  analizarla con BeautifulSoup.
- Al recorrer ~170 fichas individuales, cualquier corte de conexión o timeout obligaba a
  reiniciar todo el proceso desde el principio. Se resolvió agregando guardado incremental y
  checkpoints tanto para los links de la categoría (`data/links.txt`) como para los datos de
  cada libro (`data/libros_raw.csv`), de forma que el scraper pueda retomarse sin repetir
  trabajo ya hecho.
- No todos los libros tienen todos los campos completos (por ejemplo, algunos no pertenecen
  a ninguna serie), por lo que hubo que definir un valor consistente (`"N/A"`) para los
  campos ausentes en lugar de dejarlos vacíos o con `NaN`.
- Se detectó una inconsistencia en la consigna: la Parte 2 menciona un rango de "entre 50 y
  100 fichas de libros", mientras que la Parte 1 pide extraer "entre 100 y 200 libros". Se
  tomó como válido el rango de 100 a 200, y `limpiar_datos.py` recorta automáticamente el
  resultado a lo sumo a `max_libros` si el scraping trajo de más.
- Se agregaron pausas entre requests (`time.sleep`) para no saturar el servidor y evitar ser
  bloqueados durante el recorrido de las ~170 fichas.
- Como los duplicados y las URLs inválidas solo se detectan durante la limpieza (no antes de
  visitar las fichas), `TOTAL_PAGINAS` en `scraper.py` se fijó con cierto margen por encima del
  mínimo pedido: es más barato extraer algunos links de más que arriesgarse a terminar por
  debajo de los 100 libros pedidos por culpa de duplicados. `limpiar_datos.py` recién recorta al
  máximo (`max_libros`) una vez eliminados los duplicados, nunca antes.

## 7) Notas de diseño

Los checkpoints (`data/links.txt` y `data/libros_raw.csv`) asumen que la configuración del
scraper (categoría, URL, `TOTAL_PAGINAS`) se define una sola vez, antes de la primera corrida, y
no cambia entre corridas. Bajo ese supuesto no hace falta validar que un `data/links.txt`
existente corresponda a la configuración actual, ni llevar un cursor de progreso aparte del
propio CSV ya escrito: alcanza con comparar qué falta contra lo ya guardado. El detalle completo
de esta decisión, junto con el resto de las decisiones de diseño del scraper, está documentado
en [`docs/diseno_extraccion.md`](docs/diseno_extraccion.md).
