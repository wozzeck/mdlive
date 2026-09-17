#!/usr/bin/env python3
"""Buscador (Ctrl+F): abre el panel con el cajón enfocado; al escribir lista una fila por coincidencia
(número de línea + fragmento) con el contador, y resalta en el visor tantas coincidencias como cuenta;
Intro / Shift+Intro / Ctrl+N / Ctrl+P recorren los resultados marcando la fila activa y llevando la
coincidencia a la vista; clic en una fila salta a ella; Esc cierra. En edición resalta en CodeMirror y
Intro selecciona la coincidencia en el editor."""
import time
from mdlive_test import App, Check

app, c = App("minimapa.md"), Check()
def rows():
    return app.js("return [...document.querySelectorAll('#search-results .sr')].map((r) => ({ ln: r.querySelector('.ln').textContent, active: r.classList.contains('active') }))")
def active():
    return next((i for i, r in enumerate(rows()) if r["active"]), -1)
def marks(host="#content"):
    return app.js("return [...document.querySelectorAll(%r + ' mark.search-hit')].map((m) => m.getBoundingClientRect().top)" % host)
def visible(tops):
    return [t for t in tops if 0 <= t <= app.js("return innerHeight")]
try:
    app.click(600, 700)
    app.key("ctrl+f"); time.sleep(0.5)
    c.ok("Ctrl+F abre el panel con el cajón enfocado", app.js("return document.body.classList.contains('search-open') && document.activeElement && document.activeElement.id === 'search-input'"))
    c.eq("aviso inicial", app.js("return document.querySelector('#search-results .search-info').textContent"), "Escribe para buscar…")
    app.type("notas"); time.sleep(0.9)
    rs = rows()
    info = app.js("return document.querySelector('#search-results .search-info').textContent")
    n = int(info.split()[0])
    c.ok("una fila por coincidencia y contador coherente", len(rs) == n and n >= 10, "%d filas, info %r" % (len(rs), info))
    c.ok("las filas llevan el número de línea en orden", [int(r["ln"]) for r in rs] == sorted(int(r["ln"]) for r in rs) and int(rs[0]["ln"]) >= 1, "%r" % [r["ln"] for r in rs[:5]])
    c.eq("el visor resalta tantas coincidencias como cuenta", len(marks()), n)
    c.eq("sin Intro no hay fila activa", active(), -1)
    app.key("Return"); time.sleep(0.6)
    c.eq("Intro: primera coincidencia activa", active(), 0)
    c.ok("y su coincidencia está a la vista", len(visible(marks())) >= 1)
    app.key("Return"); time.sleep(0.4)
    c.eq("Intro otra vez: la siguiente", active(), 1)
    app.key("shift+Return"); time.sleep(0.4)
    c.eq("Shift+Intro: la anterior", active(), 0)
    app.key("shift+Return"); time.sleep(0.4)
    c.eq("Shift+Intro en la primera: da la vuelta a la última", active(), n - 1)
    app.key("ctrl+n"); time.sleep(0.4)
    c.eq("Ctrl+N: da la vuelta a la primera", active(), 0)
    app.key("ctrl+p"); time.sleep(0.4)
    c.eq("Ctrl+P: la anterior", active(), n - 1)
    # clic en la tercera fila (la lista está al final tras Ctrl+P: se trae a la vista) -> activa y a la vista
    app.js("document.querySelectorAll('#search-results .sr')[2].scrollIntoView({ block: 'center' }); return 1"); time.sleep(0.3)
    r = app.rect("document.querySelectorAll('#search-results .sr')[2]")
    app.click(r["l"] + r["w"] / 2, r["t"] + r["h"] / 2); time.sleep(0.6)
    c.eq("clic en una fila: pasa a ser la activa", active(), 2)
    ln = int(rows()[2]["ln"])
    c.ok("y el visor muestra esa línea", app.js("const el = [...document.querySelectorAll('#content [data-line]')].find((e) => +e.dataset.line <= %d - 1 && +e.dataset.lend >= %d); if (!el) return false; const r = el.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight" % (ln, ln)))
    # el clic en la fila deja el foco fuera del cajón: Ctrl+F vuelve a él (sin cerrar) y Esc cierra
    app.key("ctrl+f"); time.sleep(0.3)
    c.ok("Ctrl+F con el panel abierto: vuelve al cajón sin cerrarlo", app.js("return document.body.classList.contains('search-open') && document.activeElement.id === 'search-input'"))
    app.key("Escape"); time.sleep(0.4)
    c.ok("Esc cierra el panel", not app.js("return document.body.classList.contains('search-open')"))
    c.eq("y quita el resaltado del visor", len(marks()), 0)
    # edición: resaltado en CodeMirror y selección con Intro
    app.edit_mode()
    app.key("ctrl+f"); time.sleep(0.5)
    app.key("ctrl+a"); app.type("texto"); time.sleep(0.9)   # "texto" está en párrafos (texto de CM), no solo en tablas (widgets)
    c.ok("edición: coincidencias resaltadas en el editor", app.js("return document.querySelectorAll('#editor .cm-search-hit, #editor mark.search-hit').length") > 0)
    app.key("Return"); time.sleep(0.6)
    c.eq("edición: Intro selecciona la coincidencia en el editor", app.js("const v = CM.view.EditorView.findFromDOM(document.querySelector('#editor .cm-editor')), s = v.state.selection.main; return v.state.sliceDoc(s.from, s.to).toLowerCase()"), "texto")
    c.ok("y la fila activa es la primera", active() == 0)
    app.key("Escape"); time.sleep(0.3)
    c.ok("Esc cierra sin salir de edición", not app.js("return document.body.classList.contains('search-open')") and app.js("return document.body.classList.contains('edit-mode')"))
finally:
    app.close()
c.finish()
