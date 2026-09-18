# mdlive

Visor y editor de Markdown **nativo** para Linux (GTK3 + WebKit2GTK), *standalone* y **sin servidor**: no levanta ningún puerto HTTP, renderiza con el WebKit del sistema a través de un esquema interno `app://`.

Pensado para abrir un `.md` y verlo actualizarse al vuelo mientras lo editas con otra herramienta — o editarlo en el propio mdlive con vista previa en vivo.

## Características

- **Live reload**: si el `.md` cambia en disco, la vista se refresca al instante (también recarga `style.css` e `index.html` en caliente). En modo edición, si no hay nada escrito sin guardar el editor adopta lo del disco sin molestar; si lo hay, avisa («el fichero ha cambiado fuera del editor») y deja elegir entre recargar o seguir editando, sin tocar el buffer mientras tanto.
- **Título de la ventana**: `nombre.md - dd/mm/aaaa HH:MM - mdlive`, con la fecha de la última modificación del fichero; se actualiza al guardar desde el editor y cuando el `.md` cambia en disco.
- **Edición WYSIWYG por bloques** (CodeMirror 6): todo el documento se ve renderizado salvo el bloque donde está el cursor (en una lista, solo su ítem), que se muestra como fuente y se resalta. Guarda directo al fichero. Si el bloque tiene saltos de línea que al leer no se ven (texto partido a mano), un botón en su esquina —o `Ctrl`+`J`— los quita. En las tablas, un clic sobre una celda edita solo esa celda (su fuente) con el resto de la tabla renderizado; `Tab` e `Intro` saltan de celda, y con el clic derecho (o la mini-barra que asoma sobre la tabla) se insertan, mueven y eliminan filas y columnas, se alinea la columna y se realinean los anchos de la fuente.
- **Índice/árbol del documento**: panel lateral con la jerarquía de encabezados, colapsable, redimensionable y con *scroll-spy* (resalta el apartado visible), tanto en visor como en editor.
- **Minimapa** (`m`): miniatura a escala de todo el documento en la parte derecha (estilo Sublime Text), con un recuadro que marca la ventana visible y se mueve con el scroll; haz clic o arrastra sobre la miniatura para navegar. Ancho ajustable con un tirador en su borde izquierdo (se recuerda). Las coincidencias de la búsqueda se marcan sobre el minimapa; con el minimapa apagado, aparecen en una franja fina a la derecha (esta franja, solo en el visor). Funciona igual en el visor y en el editor.
- **Imágenes como miniaturas** (`i`): las imágenes del documento se muestran pequeñas (también en edición y en el minimapa) y un clic las abre a tamaño completo ajustadas a la ventana; otro clic sobre la imagen la muestra a tamaño real con scroll, `←`/`→` pasan de una a otra y `Esc` o un clic fuera cierra. En edición, para llevar el bloque a fuente se hace clic fuera de la miniatura.
- **Exportar** (`x`): **PDF** y **HTML autocontenido** (un solo fichero con CSS, código resaltado, diagramas e imágenes locales embebidas), y texto para pegar en **Jira** (wiki markup), **Confluence** (storage format, o «copiar con formato» para el editor visual), **Slack** (mrkdwn, o con formato para el cuadro de mensaje) y **Teams** (con formato: títulos, listas, tablas y código). Si hay algo seleccionado, en el visor o en el editor, se exporta solo la selección (ampliada a bloques enteros).
- **Buscador** (`Ctrl`+`F`): comparte el panel lateral con el índice, resalta las coincidencias en visor y editor y las lista con su número de línea; `Intro` (o `Ctrl`+`N`/`Ctrl`+`P`) navega por todas las ocurrencias con un breve halo de localización.
- **Documentos recientes** (`r`): panel lateral con los últimos 50 documentos abiertos (más reciente arriba). Un clic abre el documento en una **ventana nueva** o, si ya está abierto, **enfoca** su ventana (punto azul = abierto ahora). Comparte el panel con el índice y el buscador (secciones apilables y redimensionables). El historial es común a todas las ventanas.
- **Botonera oculta**: los botones (índice, chincheta, buscar, minimapa, miniaturas, exportar, recientes y edición) asoman por el borde derecho; al acercar el ratón se despliegan y el que queda bajo el puntero se extiende con su nombre y su tecla. Las zonas sensibles son más amplias que lo que se ve y se miden solas: la que despliega la barra ocupa toda la caja de los botones, y la que extiende el rótulo, la del botón más ancho; así valen igual con otros idiomas o con botones nuevos.
- **Chincheta** (`p`): fija en la parte superior la jerarquía de títulos de la sección visible (sticky), como la cabecera de una tabla. Con la chincheta activa, las cabeceras de las tablas largas también quedan fijas bajo la barra mientras se recorre la tabla (en visor y editor).
- **Enlaces**: se abren en el navegador del sistema; al pasar el ratón por encima, su destino aparece abajo a la izquierda (como un navegador); con el botón derecho, «Copiar enlace».
- **Rendimiento en ficheros grandes**: resaltado de código y diagramas perezosos (IntersectionObserver), scroll directo.
- **Idioma**: la interfaz sigue el idioma del sistema (`LANGUAGE`, `LC_ALL`, `LC_MESSAGES`, `LANG`; `MDLIVE_LANG=en` lo fuerza). Español (fuente), inglés, alemán, francés, italiano y portugués; un idioma sin diccionario cae al inglés. Para añadir uno: copiar `i18n/en.json` a `i18n/<código>.json` y traducir los valores (las claves son el texto en español); `node tests/unit/run.js` comprueba que no falte ni sobre ninguna clave.
- **Offline**: todas las dependencias están vendorizadas en `vendor/` (markdown-it, highlight.js, mermaid, CodeMirror).
- **Mermaid** y resaltado de sintaxis integrados.
- **Zoom de solo texto** (`Ctrl`+rueda) que conserva el punto de lectura.
- Los **enlaces** se abren en el navegador del sistema, no dentro de la ventana.

## Requisitos

- Python 3
- PyGObject (`python3-gi`), GTK 3 y **WebKit2GTK 4.1** (`gir1.2-webkit2-4.1`)

En Debian/Ubuntu/Mint:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1
```

## Uso

```bash
./mdlive documento.md
```

### Atajos

#### Generales

| Tecla | Acción |
|-------|--------|
| `t` | Mostrar/ocultar el índice del documento |
| `m` | Mostrar/ocultar el minimapa del documento |
| `x` | Exportar: PDF, HTML autocontenido, Jira, Confluence, Slack o Teams (con selección, solo lo seleccionado) |
| `i` | Imágenes como miniaturas (clic: tamaño completo; otro clic: tamaño real; `←`/`→` siguiente/anterior; `Esc` cierra) |
| `r` | Documentos recientes (abrir en ventana nueva o enfocar la existente) |
| `p` | Fijar (chincheta) los títulos de sección al hacer scroll |
| `Ctrl`+`F` | Buscador |
| `Ctrl`+`N` / `Ctrl`+`P` | Ir a la siguiente / anterior coincidencia |
| `Intro` / `Shift`+`Intro` | En el cajón de búsqueda: a la primera coincidencia y, repitiendo, a la siguiente / anterior |
| `e` | Entrar/salir del modo edición |
| `Ctrl`+rueda | Zoom de solo texto |
| `Ctrl`+`0` | Restablecer el zoom |
| `Ctrl`+`H` | Ayuda con todos los atajos |
| `Esc` | Cerrar lo que esté abierto (ayuda, menús, visor de imágenes, paneles laterales de uno en uno) y, cuando no queda nada, salir del modo edición |

#### Formato (solo en modo edición)

| Tecla | Acción |
|-------|--------|
| `Ctrl`+`B` | Negrita |
| `Ctrl`+`K` | Cursiva |
| `Ctrl`+`U` | Subrayado |
| `Ctrl`+`E` | Código en línea |
| `Ctrl`+`Shift`+`X` | Tachado |
| `Ctrl`+`Shift`+`K` | Enlace |
| `Ctrl`+`Shift`+`.` | Cita |
| `Ctrl`+`1`…`6` | Encabezado de nivel 1–6 (alterna) |
| `Ctrl`+`J` | Unir las líneas del bloque: quita los saltos de línea que al leer no se ven (también con el botón de la esquina del bloque) |
| `Ctrl`+`Shift`+`J` | Lo mismo en todo el documento |
| clic en una celda | Tablas: edita esa celda en su sitio (su fuente); `Tab`/`Shift`+`Tab` celda siguiente/anterior, `Intro`/`Shift`+`Intro` abajo/arriba, `Esc` cancela; `Ctrl`+clic abre la tabla entera en fuente |
| clic derecho en una celda | Tablas: menú con las operaciones (insertar, mover y eliminar filas y columnas, alinear la columna, realinear los anchos de la fuente). Mientras se edita una celda, las más usadas asoman en una mini-barra sobre la tabla |
| `Tab` en la última celda | Tablas: añade una fila |
| `Ctrl`+`Intro` | Tablas (en la celda): salto de línea dentro de la celda (un `<br>` en el .md; el cajón lo muestra como salto) |
| `Alt`+`↑`/`↓`, `Alt`+`←`/`→` | Tablas (en la celda): mover la fila / la columna |

Cada atajo de formato actúa sobre la selección o, si no hay nada seleccionado, sobre la palabra bajo el cursor.

## Instalación como aplicación

```bash
# comando global
ln -s "$PWD/mdlive" ~/.local/bin/mdlive

# entrada de menú + asociación de ficheros .md
cp mdlive.desktop ~/.local/share/applications/
xdg-mime default mdlive.desktop text/markdown
```

## Tests

```bash
tests/run.sh          # toda la suite
tests/run.sh unit     # solo los unitarios
```

- **Unitarios** (`tests/unit/*.test.js`, node sin dependencias): las funciones puras del editor —unir líneas, troceado en unidades (listas ítem a ítem), celdas y operaciones de tabla, exportación a texto— van marcadas en `index.html` con `// @test-begin <nombre>` … `// @test-end`; el runner las extrae y las ejecuta con el markdown-it vendorizado. Otro test comprueba las traducciones: toda clave de la interfaz (marcado, atributos, script y `mdlive.py`) está en cada `i18n/*.json`, sin huérfanas y con sus marcadores.
- **Integración** (`tests/gui/test_*.py`): lanza la aplicación real sobre una copia de `tests/fixtures/*.md`, aislada (`XDG_*` a un directorio temporal: recientes, instancias y `localStorage` propios), con teclado y ratón reales (`xdotool`), capturas (`import`) y consulta del DOM por el canal de pruebas de `mdlive.py` (`MDLIVE_TEST_DIR`, ficheros `cmd-*.js`/`res-*.json`). Necesita `DISPLAY`, `xdotool`, `imagemagick` y `python3-pil`. Cubre el título de la ventana, unir líneas, el tooltip del índice, las celdas y operaciones de tabla, el código monoespaciado, el minimapa, las miniaturas, la exportación, la botonera oculta, el idioma de la interfaz, el buscador, la chincheta, los recientes, el visor frente al editor con listas y un test de rendimiento con un documento grande generado (umbrales holgados).

## Estructura

- `mdlive.py` — la aplicación GTK3/WebKit2 (sin servidor; esquema `app://`, live reload, guardado).
- `index.html` — frontend (render, modo edición CodeMirror, índice).
- `style.css` — estilos del contenido, **editables en caliente**.
- `tests/` — suite (ver arriba).
- `vendor/` — dependencias vendorizadas (offline).
- `icon.svg` / `icon.png` — icono.
- `mdlive` — lanzador; `mdlive.desktop` — entrada de escritorio.

## Notas

Los iconos de la barra de botones son [Lucide](https://lucide.dev) (licencia ISC), incrustados como SVG en `index.html`; los atributos de trazo se declaran una vez en CSS.

El bundle de CodeMirror (`vendor/codemirror.js`) se construye con esbuild a partir de `@codemirror/{state,view,commands,language,lang-markdown}` exponiendo `window.CM`; el directorio de build (`.cmbuild/`) no se versiona, pero el bundle final sí.

El historial de **documentos recientes** se guarda en `$XDG_DATA_HOME/mdlive/recent.json` (por defecto `~/.local/share/mdlive/recent.json`). Cada ventana publica además su existencia en `$XDG_RUNTIME_DIR/mdlive/instances/` (efímero) para poder enfocar la ventana ya abierta en lugar de duplicarla; ese enfoque usa `wmctrl` (o `xdotool` como alternativa) en X11.
