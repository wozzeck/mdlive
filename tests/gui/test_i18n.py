#!/usr/bin/env python3
"""Idioma de la interfaz: con MDLIVE_LANG=en todo el marcado estático (rótulos de la botonera, cabeceras,
atributos title/placeholder, ayuda), las cadenas del script (menú de exportar, tablas, recientes, buscador)
y el atributo lang salen en inglés; pt_BR cae a pt.json; un idioma sin diccionario cae al inglés; el
harness arranca en español por defecto (el resto de la suite depende de ello)."""
import re
import time
from mdlive_test import App, Check

c = Check()
def attr(app, sel, name):
    return app.js("const e = document.querySelector(%r); return e && e.getAttribute(%r)" % (sel, name))
app = App("tabla.md", lang="en")
try:
    c.eq("lang del documento", app.js("return document.documentElement.lang"), "en")
    c.eq("rótulo de la botonera", app.js("return document.querySelector('#btn-toc .lbl').innerHTML"), "Contents<kbd>t</kbd>")
    c.eq("aria-label traducido", attr(app, "#btn-recent", "aria-label"), "Recent documents")
    c.eq("title traducido", attr(app, "#pin-bar", "title"), "Go to section")
    c.eq("placeholder traducido", attr(app, "#search-input", "placeholder"), "Search…")
    c.eq("cabecera del panel", app.js("return document.querySelector('#recent-sec .side-head').textContent"), "Recent")
    app.click(600, 700); app.key("ctrl+h"); time.sleep(0.4)
    c.eq("ayuda: título", app.js("return document.querySelector('#help-modal h2').textContent"), "Keyboard shortcuts")
    c.ok("ayuda: la tecla Intro se llama Enter", app.js("return [...document.querySelectorAll('#help-modal td')].some((td) => td.innerHTML === '<kbd>Ctrl</kbd>+<kbd>Enter</kbd>')"))
    c.ok("ayuda: sin celdas en español", not app.js("return [...document.querySelectorAll('#help-modal td')].some((td) => /Tablas|celda|Buscar|Intro/.test(td.textContent))"))
    app.key("Escape"); time.sleep(0.3)
    app.key("x"); time.sleep(0.5)
    c.eq("menú de exportar (cadena del script con {scope})", app.js("return document.querySelector('#export-menu .hdr').textContent"), "Export the whole document")
    c.eq("menú de exportar: ítem estático", app.js("return document.querySelector('#export-menu .item[data-kind=html]').textContent"), "Self-contained HTML…")
    app.key("Escape"); time.sleep(0.3)
    app.key("ctrl+f"); time.sleep(0.5)
    c.eq("buscador: aviso inicial", app.js("return document.querySelector('#search-results .search-info').textContent"), "Type to search…")
    app.type("Pagos"); time.sleep(0.8)
    c.eq("buscador: contador", app.js("return document.querySelector('#search-results .search-info').textContent"), "1 match")
    app.key("Escape"); time.sleep(0.3)
    app.click(600, 700); app.key("r"); time.sleep(0.6)
    rt = app.js("return document.querySelector('#recent-list .rt').textContent")
    c.ok("recientes: fecha relativa y fecha absoluta en el locale del idioma", re.match(r"a moment ago · [A-Z][a-z]{2} \d{1,2}, \d{4}, ", rt) is not None, rt)
    c.eq("recientes: title del botón generado", app.js("return document.querySelector('#recent-list .rc').title"), "Copy path")
    app.key("Escape"); time.sleep(0.3)
    # edición: literales evaluados al arrancar el script (operaciones de tabla)
    app.edit_mode()
    r = app.rect("document.querySelector('#editor td')")
    app.click(r["l"] + r["w"] / 2, r["t"] + r["h"] / 2); time.sleep(0.6)
    c.eq("tablas: mini-barra en inglés (literal evaluado al arrancar el script)", app.js("const b = document.querySelector('.cm-table-tools button[data-op=rowBelow]'); return b && b.title"), "Insert row below")
finally:
    app.close()
app = App("toc.md", lang="pt_BR")
try:
    c.ok("pt_BR cae a pt.json", app.js("return document.documentElement.lang === 'pt' && document.getElementById('pin-bar').title !== 'Ir a la sección' && document.getElementById('pin-bar').title !== 'Go to section'"), app.js("return document.getElementById('pin-bar').title"))
finally:
    app.close()
app = App("toc.md", lang="xx_YY")
try:
    c.eq("idioma sin diccionario: inglés", app.js("return document.documentElement.lang + '|' + document.getElementById('pin-bar').title"), "en|Go to section")
finally:
    app.close()
app = App("toc.md")
try:
    c.eq("por defecto en el harness: español", app.js("return document.documentElement.lang + '|' + document.getElementById('pin-bar').title"), "es|Ir a la sección")
finally:
    app.close()
c.finish()
