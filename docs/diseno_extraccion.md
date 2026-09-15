# Universidad Nacional de Rosario
### Facultad de Ciencias Exactas, Ingeniería y Agrimensura
### T.U.I.A — Procesamiento del Lenguaje Natural

# Trabajo Unidad 1

**Integrantes del grupo:**

| Nombre y Apellido    | Legajo |
| --------------------- | ------ |
| Sebastian Muñoz       |        |
| Manuel Spreutels      |        |
| Lara Onyskiw          |        |
| Ezequiel Zahradnicek  |        |
| Erica                 |        |

---

## Entrega número 1 NLP

### 1. Categoría seleccionada

- **Nombre de la categoría:** Ciencia Ficción
- **URL de la categoría:** https://ww3.lectulandia.co/genero/ciencia-ficcion/
- **Cantidad de libros que se propone extraer:** 200
- **Criterio utilizado para seleccionar las páginas:** se recorrerán los libros que aparezcan
  en cada página del género "Ciencia Ficción" de Lectulandia, tomando cada elemento listado
  hasta llegar a los 200 libros.

### 2. Datos que se extraerán

El dataset deberá contener, como mínimo:

| Campo | Descripción |
| --- | --- |
| `titulo` | Título del libro |
| `autores` | Autor o autores |
| `generos` | Género o géneros |
| `serie` | Serie a la que pertenece, si corresponde |
| `sinopsis` | Texto completo de la sinopsis |
| `url_libro` | Dirección de la ficha |
| `categoria_origen` | Categoría seleccionada por el grupo |
| `portada` | Url de la imagen mostrada como portada en la web |
| `fecha_extraccion` | Fecha en que se obtuvo el registro |

### 3. Localización de los datos

Para cada campo se indica dónde se encuentra y cómo se extrae:

| Dato | Tipo de página | Etiqueta HTML | Selector propuesto |
| --- | --- | --- | --- |
| Título | Ficha individual | `<h1>` | `#title h1` |
| Autores | Ficha individual | `<a>` | `#autor a.dinSource` |
| Géneros | Ficha individual | `<a>` | `#genero a.dinSource` |
| Sinopsis | Ficha individual | `<div>` | `#sinopsis` |
| Serie | Ficha individual | `<div>` | `#serie` |
| categoría | Ficha individual | - | - (parámetro fijo pasado por el grupo, no se extrae del HTML) |
| portada | Ficha individual | `<img>` | `#leftBlock #cover img` |

Los selectores se obtuvieron inspeccionando el HTML del sitio desde las herramientas de
desarrollo del navegador.

### 4. Estrategia de extracción

El proceso se implementó en tres módulos independientes (`obtener_links.py`,
`obtener_datos.py`, `limpiar_datos.py`), orquestados por `scraper.py`. Se optó por esta
separación —en lugar de un único script— porque cada etapa tiene una responsabilidad y un
punto de posible falla distintos (recorrido de listados, visita de fichas, y validación de
datos), y así cada una puede ejecutarse, probarse o reanudarse de forma independiente.

**Paso 1-2. Abrir la categoría con Playwright y recorrer las páginas necesarias
(`obtener_links_libros`)**

Se abre un navegador Chromium en modo headless y se visita `URL_CATEGORIA/page/N` para
`N = 1..TOTAL_PAGINAS` (`TOTAL_PAGINAS = 10`, a razón de ~24 libros por página). Se usa
Playwright en lugar de una librería de requests simple porque el listado de la categoría
depende de contenido cargado dinámicamente por el sitio, y Playwright permite esperar a que
el HTML final esté disponible antes de analizarlo.

`TOTAL_PAGINAS` se fijó deliberadamente por encima del mínimo estrictamente necesario para
llegar a los 100 libros pedidos por la consigna: la cantidad de fichas que finalmente quedan
en `data/libros.csv` depende de cuántos duplicados y registros inválidos se descarten en
`limpiar_datos` (ver Paso 8-9), algo que no se puede saber de antemano sin visitar las
fichas. Extraer algunos links de más es barato (son requests livianos a páginas de listado,
no a las fichas individuales) y funciona como margen de seguridad: si en el proceso aparecen
duplicados o URLs inválidas, igual queda margen para llegar cómodamente al rango pedido sin
tener que volver a recorrer páginas de la categoría.

**Sobre el supuesto de configuración fija.** El diseño da por sentado que los parámetros de
configuración (`URL_CATEGORIA`, `TOTAL_PAGINAS`, y en general las constantes definidas al
principio de `scraper.py`) se fijan una vez, antes de arrancar la extracción, y se mantienen
sin cambios durante todo el proceso —incluso si este se corre en varias corridas separadas
por cortes o interrupciones—. No se valida en ningún punto que esos parámetros no hayan
cambiado entre una corrida y la siguiente porque el programa no está pensado para que se
edite la configuración a mitad de una extracción, sino para configurarse una sola vez y
correrse las veces que haga falta hasta terminar. Esto es relevante en particular para
`data/links.txt` (ver Paso 5): si se quisiera correr el scraper de nuevo con un
`TOTAL_PAGINAS` distinto, hay que borrar ese archivo a mano, ya que el script no tiene forma
de detectar que la cantidad de páginas pedida cambió respecto de la corrida que generó el
archivo.

**Paso 3-4. Obtener el HTML y analizarlo con BeautifulSoup**

En cada página se toma `page.content()` (HTML ya renderizado) y se lo analiza con
BeautifulSoup, buscando el contenedor `div.books-grid` y, dentro de él, los enlaces
`a.title`.

**Paso 5. Extraer las URLs de las fichas de los libros**

Se arma la URL completa de cada ficha (resolviendo links relativos contra el dominio base) y
se acumulan en una lista. Para no tener que repetir este recorrido de páginas en cada corrida
del scraper, la lista final de links se guarda en `data/links.txt`; si ese archivo ya existe
con contenido, `obtener_links_libros` lo carga directamente y omite el recorrido por completo,
sin volver a abrir el navegador.

Esta decisión trae aparejado un supuesto que vale la pena dejar explícito: `obtener_links_libros`
no verifica que la cantidad de links guardados en `data/links.txt` sea consistente con el
`TOTAL_PAGINAS` que se le pasa en la corrida actual. Si `data/links.txt` fue generado con, por
ejemplo, 7 páginas y luego se decide correr el scraper con `TOTAL_PAGINAS = 10`, el archivo
existente se toma tal cual y las 3 páginas nuevas no se llegan a recorrer. No se agregó una
validación para este caso (por ejemplo, comparar la cantidad de links guardados contra una
estimación esperada) porque, como se explicó en el paso anterior, el flujo de trabajo asume
que la configuración se define antes de la primera corrida y no cambia entre corridas; agregar
esa validación sería resolver un problema que el propio uso previsto del script ya evita, a
costa de sumar complejidad innecesaria al código.

**Paso 6-7. Visitar cada ficha y extraer metadatos y sinopsis con BeautifulSoup
(`obtener_datos_libros`)**

Se visita cada URL de la lista de links con Playwright y se extraen título, autores, géneros,
serie, sinopsis y portada con los selectores de la sección 3. Esta etapa es la que más tiempo
toma (una visita por libro) y la más expuesta a cortes de red o a que el usuario interrumpa
manualmente la ejecución (`Ctrl+C` / `KeyboardInterrupt`), por lo que se implementó un
checkpoint: cada registro se escribe en `data/libros_raw.csv` apenas se extrae (con `flush()`
incluido, para forzar la escritura a disco en el momento y no perderla si el proceso se corta
inmediatamente después) y, si el proceso se reinicia, se lee el conjunto de URLs (`url_libro`)
ya presentes en `data/libros_raw.csv` y se filtra la lista original de links, quedándonos
únicamente con los que todavía no fueron procesados.

Esta forma de reanudar la ejecución se apoya en dos supuestos concretos sobre cómo funciona
el resto del programa:

1. **`data/links.txt` no cambia entre una corrida y la siguiente** (ver el supuesto de
   configuración fija del Paso 1-2 y del Paso 5): si la lista de links fuera distinta en cada
   corrida, comparar contra "las URLs ya presentes en el CSV" dejaría de tener sentido, porque
   ya no habría una única lista de referencia contra la cual completar lo que falta.
2. **El recorrido es secuencial**, es decir, `obtener_datos_libros` procesa la lista de links
   siempre en el mismo orden (de principio a fin). Gracias a esto alcanza con calcular la
   diferencia entre conjuntos (links totales menos links ya procesados) para saber qué falta:
   no hace falta guardar un índice, un cursor de posición, ni ningún estado adicional aparte
   del propio `data/libros_raw.csv` ya escrito.

Bajo estos dos supuestos, el checkpoint es simple y robusto: no importa en qué punto exacto se
cortó la ejecución anterior, la próxima corrida va a retomar exactamente donde quedó. Los
errores al procesar un link individual (timeout, ficha con una estructura distinta a la
esperada, etc.) se capturan con `try/except` y se registran en consola sin interrumpir el
resto del recorrido, cumpliendo con el requisito de "controlar errores sin detener
completamente la ejecución". Entre ficha y ficha se agrega además una pausa (`time.sleep(2)`)
para no saturar el servidor.

**Paso 8-9. Limpiar y validar los datos, eliminar duplicados (`limpiar_datos`)**

A diferencia de las etapas anteriores, acá no hay decisiones de diseño demasiado complejas:
`limpiar_datos` esencialmente recorre el CSV crudo y comprueba, campo por campo y registro por
registro, que los datos cumplan lo que pide la consigna. Aun así, hay algunos criterios
puntuales que vale la pena dejar documentados porque no son arbitrarios:

1. **Normalización de texto y valores ausentes.** Se recortan espacios y se colapsan saltos de
   línea/tabs en todos los campos (con una expresión regular, `re.sub(r"\s+", " ", texto)`), y
   se unifican los valores ausentes o inválidos (celda vacía, `nan`, `none`, `n/a`, `na`, sin
   distinguir mayúsculas/minúsculas) en un único valor consistente: el string `"N/A"`. Se eligió
   representar los faltantes como string y no dejarlos como `NaN`/`None` por una razón muy
   concreta: este dataset va a usarse después en actividades de procesamiento de texto (por
   ejemplo, para generar embeddings a partir de la sinopsis), y trabajar con un único tipo de
   dato consistente en todas las columnas evita tener que manejar valores nulos como caso
   especial en cada script que lea el CSV más adelante.
2. **Descarte de registros sin título.** Un libro sin título no aporta información útil al
   corpus, así que se descarta directamente en vez de conservarlo con un placeholder.
3. **Validación de URL con expresión regular.** Se define `PATRON_URL = re.compile(r"^https?://", re.IGNORECASE)`
   y se descartan los registros cuya `url_libro` no matchea ese patrón. Es una validación
   deliberadamente simple (no se intenta validar que la URL exista o resuelva, solo que tenga
   una forma mínimamente válida), porque alcanza para detectar los casos reales que puede
   producir el scraper (por ejemplo, un campo vacío si `obtener_datos_libros` no llegó a
   completar el registro).
4. **Eliminación de duplicados por `url_libro`.** Se conserva la primera ocurrencia de cada URL
   y se descartan las repeticiones. Se usa `url_libro` como clave (y no `titulo`, por ejemplo)
   porque es el único campo que identifica unívocamente a cada ficha.
5. **Recorte al máximo pedido, después de deduplicar.** Si tras eliminar los duplicados la
   cantidad de libros sigue superando el máximo pedido (`max_libros = 200`), recién ahí se
   recorta el resultado a los primeros `max_libros` registros, dejando explícito en el reporte
   cuántos se descartaron por ese motivo. Este orden es intencional: el `TOTAL_PAGINAS` con el
   que se corre `obtener_links_libros` se fija con cierto margen por encima del mínimo pedido
   (ver Paso 1-2) precisamente para que, si aparecen duplicados o registros inválidos durante la
   limpieza, siempre quede margen suficiente para llegar al rango pedido. Si en cambio se
   acotara la cantidad de libros *antes* de extraer los datos (por ejemplo, cortando la lista de
   links a los primeros 200 ni bien se obtiene), cualquier duplicado o registro inválido que
   apareciera después nos dejaría por debajo del mínimo sin ninguna forma de recuperarlos sin
   volver a correr todo el proceso de scraping. Recortar al final, en cambio, es una operación
   inmediata sobre datos que ya están en memoria.

Como indicador de calidad adicional (no exigido explícitamente por la consigna, pero útil para
las etapas posteriores de NLP), se calcula qué porcentaje de los registros tiene sinopsis y qué
porcentaje tiene una sinopsis de más de 200 caracteres. Se eligió ese umbral como proxy de que
la sinopsis extraída es un texto real y con información relevante sobre el libro, y no
simplemente un campo con una palabra suelta o un fragmento cortado que técnicamente "tiene
contenido" pero no sirve como sinopsis.

**Paso 10. Guardar el resultado en un archivo CSV**

El resultado final se guarda en `data/libros.csv` (el entregable pedido por la consigna).
Además, `limpiar_datos` imprime un reporte con el detalle de cada control (OK/ADVERTENCIA)
para poder verificar de un vistazo que el dataset cumple lo pedido antes de la entrega.

**Orquestación (`scraper.py`)**

`scraper.py` simplemente ejecuta las tres etapas en orden (links → datos → limpieza) con la
configuración de la categoría elegida y las rutas de los archivos intermedios. Al mantener la
configuración (`CATEGORIA`, `URL_CATEGORIA`, `TOTAL_PAGINAS`, rutas de archivos,
`MIN_LIBROS_ESPERADOS`, `MAX_LIBROS_ESPERADOS`) como constantes al principio del archivo,
ejecutar el scraper para otra categoría o ajustar el rango de libros no requiere tocar el
resto del código.

### Consideraciones y supuestos de diseño

A modo de síntesis, todo el esquema de checkpoints del scraper (`data/links.txt` en el Paso 5 y
`data/libros_raw.csv` en el Paso 6-7) descansa sobre una única premisa de uso: la configuración
se fija **una sola vez, antes de arrancar la extracción**, y no cambia durante el proceso, aun
si este termina corriéndose en varias sesiones por cortes de red o interrupciones manuales. Esa
premisa es la que permite que el código de reanudación sea tan simple —comparar qué falta contra
lo ya guardado, sin validar ni versionar la configuración de cada corrida— y es también,
justamente por eso, su principal limitación conocida: si algún día se necesitara cambiar la
configuración a mitad de una extracción (por ejemplo, ampliar `TOTAL_PAGINAS`), el mecanismo
previsto no es agregar una validación al código, sino simplemente borrar `data/links.txt` (y, si
corresponde, `data/libros_raw.csv`) y volver a correr `scraper.py` desde cero. Se prefirió esta
solución operativa, más simple, a sumarle al código comprobaciones adicionales para un escenario
que queda fuera del uso previsto del script.

---