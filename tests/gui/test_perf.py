#!/usr/bin/env python3
"""Rendimiento con un documento grande generado (≈300 secciones con párrafos, listas, tablas y código,
≈9.000 líneas): tiempos de arranque hasta el primer render, de construcción del minimapa, de entrada en
edición, de búsqueda con muchas coincidencias y de salto al final. Umbrales holgados (no es un benchmark:
detectan regresiones groseras); los tiempos medidos salen en el detalle de cada comprobación."""
import pathlib, tempfile, time
from mdlive_test import App, Check

c = Check()
tmp = pathlib.Path(tempfile.mkdtemp(prefix="mdlive-perf-"))
big = tmp / "grande.md"
parts = ["# Documento grande\n\nIntroducción del documento de prueba de rendimiento.\n"]
for i in range(1, 301):
    parts.append("\n## Sección %d\n\nPárrafo de la sección %d con **negrita**, *cursiva*, `código` y un [enlace](https://example.com/%d) "
                 "para dar algo de trabajo al renderizado de cada bloque.\n\n- Elemento uno de la sección %d\n- Elemento dos\n  - Subelemento con `tabla` en el texto\n- Elemento tres\n\n"
                 "| Campo | Descripción | Valor |\n|---|---|---|\n" % (i, i, i, i))
    for j in range(1, 6):
        parts.append("| campo_%d_%d | Descripción del campo %d de la tabla %d | `v%d` |\n" % (i, j, j, i, j))
    parts.append("\n```python\ndef f_%d(x):\n    return x * %d  # tabla %d\n```\n" % (i, i, i))
big.write_text("".join(parts), encoding="utf-8")
lines = sum(1 for _ in open(big, encoding="utf-8"))
t0 = time.time()
app = App(big, size=(1100, 900))
t_start = time.time() - t0
try:
    c.ok("arranque hasta el primer render (%d líneas, %.0f KB): %.1f s" % (lines, big.stat().st_size / 1024, t_start), t_start < 20)
    c.eq("todas las secciones renderizadas", app.js("return document.querySelectorAll('#content h2').length"), 300)
    t0 = time.time(); app.wait_js("return document.querySelectorAll('#minimap-canvas h2').length >= 300", 30); t_mm = time.time() - t0
    c.ok("minimapa construido: %.1f s más" % t_mm, t_mm < 15)
    t0 = time.time(); app.js("document.scrollingElement.scrollTop = document.scrollingElement.scrollHeight; return 1")
    app.wait_js("return document.scrollingElement.scrollTop > 1000 && document.querySelector('#content pre:last-of-type code.hljs')", 15); t_end = time.time() - t0
    c.ok("salto al final con el código del final resaltado: %.1f s" % t_end, t_end < 8)
    app.js("document.scrollingElement.scrollTop = 0; return 1"); time.sleep(0.3)
    app.click(600, 700); app.key("ctrl+f"); time.sleep(0.4)
    t0 = time.time(); app.type("tabla"); app.wait_js("return document.querySelectorAll('#search-results .sr').length > 100", 20); t_search = time.time() - t0
    n = app.js("return document.querySelector('#search-results .search-info').textContent")
    c.ok("búsqueda con muchas coincidencias (%s): %.1f s" % (n, t_search), t_search < 6)
    app.key("Escape"); time.sleep(0.3)
    t0 = time.time(); app.click(600, 700); app.key("e"); app.wait_js("return !!document.querySelector('#editor .cm-editor')", 30); t_edit = time.time() - t0
    c.ok("entrada en edición: %.1f s" % t_edit, t_edit < 12)
    t0 = time.time(); app.js("const v = CM.view.EditorView.findFromDOM(document.querySelector('#editor .cm-editor')); v.dispatch({ selection: { anchor: v.state.doc.length }, effects: CM.view.EditorView.scrollIntoView(v.state.doc.length) }); return 1")
    app.wait_js("return document.querySelector('#editor .cm-editor').getBoundingClientRect().bottom > 0 && document.scrollingElement.scrollTop > 1000", 15); t_cm = time.time() - t0
    c.ok("salto al final en edición: %.1f s" % t_cm, t_cm < 8)
    app.key("Escape"); time.sleep(0.3)
    c.ok("vuelve al visor", not app.js("return document.body.classList.contains('edit-mode')"))
finally:
    app.close()
c.finish()
