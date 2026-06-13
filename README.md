# mdlive

Visor y editor de Markdown **nativo** para Linux (GTK3 + WebKit2GTK), *standalone* y **sin servidor**: no levanta ningún puerto HTTP, renderiza con el WebKit del sistema a través de un esquema interno `app://`.

Pensado para abrir un `.md` y verlo actualizarse al vuelo mientras lo editas con otra herramienta — o editarlo en el propio mdlive con vista previa en vivo.

## Características

- **Live reload**: si el `.md` cambia en disco, la vista se refresca al instante (también recarga `style.css` e `index.html` en caliente).
- **Edición WYSIWYG por bloques** (CodeMirror 6): todo el documento se ve renderizado salvo el bloque donde está el cursor, que se muestra como fuente y se resalta. Guarda directo al fichero.
- **Índice/árbol del documento**: panel lateral con la jerarquía de encabezados, colapsable, redimensionable y con *scroll-spy* (resalta el apartado visible), tanto en visor como en editor.
- **Buscador** (`Ctrl`+`F`): comparte el panel lateral con el índice, resalta las coincidencias en visor y editor y las lista con su número de línea; `Ctrl`+`N`/`Ctrl`+`P` navegan por todas las ocurrencias con un breve halo de localización.
- **Chincheta** (`p`): fija en la parte superior la jerarquía de títulos de la sección visible (sticky), como la cabecera de una tabla. Con la chincheta activa, las cabeceras de las tablas largas también quedan fijas bajo la barra mientras se recorre la tabla (en el visor).
- **Rendimiento en ficheros grandes**: resaltado de código y diagramas perezosos (IntersectionObserver), scroll directo.
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
| `p` | Fijar (chincheta) los títulos de sección al hacer scroll |
| `Ctrl`+`F` | Buscador |
| `Ctrl`+`N` / `Ctrl`+`P` | Ir a la siguiente / anterior coincidencia |
| `e` | Entrar/salir del modo edición |
| `Ctrl`+rueda | Zoom de solo texto |
| `Ctrl`+`0` | Restablecer el zoom |
| `Ctrl`+`H` | Ayuda con todos los atajos |
| `Esc` | Cerrar la ayuda / salir del modo edición |

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

Cada atajo de formato actúa sobre la selección o, si no hay nada seleccionado, sobre la palabra bajo el cursor.

## Instalación como aplicación

```bash
# comando global
ln -s "$PWD/mdlive" ~/.local/bin/mdlive

# entrada de menú + asociación de ficheros .md
cp mdlive.desktop ~/.local/share/applications/
xdg-mime default mdlive.desktop text/markdown
```

## Estructura

- `mdlive.py` — la aplicación GTK3/WebKit2 (sin servidor; esquema `app://`, live reload, guardado).
- `index.html` — frontend (render, modo edición CodeMirror, índice).
- `style.css` — estilos del contenido, **editables en caliente**.
- `vendor/` — dependencias vendorizadas (offline).
- `icon.svg` / `icon.png` — icono.
- `mdlive` — lanzador; `mdlive.desktop` — entrada de escritorio.

## Notas

El bundle de CodeMirror (`vendor/codemirror.js`) se construye con esbuild a partir de `@codemirror/{state,view,commands,language,lang-markdown}` exponiendo `window.CM`; el directorio de build (`.cmbuild/`) no se versiona, pero el bundle final sí.
