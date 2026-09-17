#!/usr/bin/env python3
"""Imágenes como miniaturas (tecla i): con el modo activo las imágenes salen pequeñas (visor, edición y
minimapa) y un clic las abre a tamaño completo ajustadas a la ventana; otro clic sobre la imagen, a tamaño
real; flechas para pasar de imagen; Esc cierra. En edición el clic en la miniatura NO lleva el bloque a
fuente. Fixture imagenes.md + imagenes/ (SVG de 1600x1000 y 300x200)."""
import time
from mdlive_test import App, Check

app, c = App("imagenes.md"), Check()
def IMG(host, name):
    return "[...document.querySelectorAll(%r + ' img')].find((i) => i.src.includes(%r))" % (host, name)
def size(host, name):
    return app.js("const i = %s; if (!i) return null; const r = i.getBoundingClientRect();"
                  " return { w: r.width, h: r.height, nw: i.naturalWidth, nh: i.naturalHeight, x: r.left + r.width / 2, y: r.top + r.height / 2 }" % IMG(host, name))
def lb():
    return app.js("""const lb = document.getElementById('lightbox'), i = lb.querySelector('img'), r = i.getBoundingClientRect();
      return { open: document.body.classList.contains('lightbox-open'), natural: lb.classList.contains('natural'), src: i.getAttribute('src') || '',
               w: r.width, h: r.height, cap: document.getElementById('lightbox-cap').textContent, vw: innerWidth, vh: innerHeight }""")
try:
    app.wait_js("const i = %s; return !!i && i.complete && i.naturalWidth > 0" % IMG('#content', 'grande.svg'))
    g = size('#content', 'grande.svg')
    # (naturalWidth no sirve de referencia: en WebKit, para un <img> SVG maquetado es su tamaño actual)
    c.ok("sin miniaturas: la imagen grande ocupa el ancho disponible", g is not None and g["w"] > 500, "ancho %r" % (g and g["w"]))
    REM = app.js("return parseFloat(getComputedStyle(document.documentElement).fontSize)")
    MAXW, MAXH = 12 * REM + 1, 8 * REM + 1   # miniatura: max-width 12rem, max-height 8rem
    c.ok("el modo empieza apagado", not app.js("return document.body.classList.contains('thumbs-on')"))
    app.click(600, 860)   # foco al webview, en zona vacía
    app.key("i"); time.sleep(0.5)
    c.ok("tecla i: modo miniaturas y botón activo", app.js("return document.body.classList.contains('thumbs-on') && document.getElementById('btn-thumbs').classList.contains('active')"))
    g, p = size('#content', 'grande.svg'), size('#content', 'pequena.svg')
    c.ok("la grande queda como miniatura (<= 12rem x 8rem)", g["w"] <= MAXW and g["h"] <= MAXH, "%.0fx%.0f (rem %s)" % (g["w"], g["h"], REM))
    c.ok("la pequeña también, sin deformarse", p["w"] <= MAXW and p["h"] <= MAXH and abs(p["w"] / p["h"] - 1.5) < 0.02, "%.0fx%.0f" % (p["w"], p["h"]))
    c.ok("en el minimapa la imagen mide lo mismo que en la página", app.js("const a = %s, b = %s; return !!a && !!b && Math.abs(a.offsetHeight - b.offsetHeight) < 1"
         % (IMG('#minimap-canvas', 'grande.svg'), IMG('#content', 'grande.svg'))))
    # clic en la miniatura grande: visor a tamaño completo, ajustado a la ventana
    app.click(g["x"], g["y"]); time.sleep(0.6)
    s = lb()
    c.ok("clic en la miniatura: se abre el visor con esa imagen", s["open"] and "grande.svg" in s["src"], s["src"][-40:])
    c.ok("ajustada a la ventana", s["w"] <= s["vw"] and s["h"] <= s["vh"] and s["w"] > 600, "%.0fx%.0f en %dx%d" % (s["w"], s["h"], s["vw"], s["vh"]))
    c.ok("pie con nombre y tamaño real", "Grande" in s["cap"] and "1600×1000" in s["cap"], s["cap"])
    app.click(s["vw"] / 2, s["vh"] / 2); time.sleep(0.5)   # sobre la imagen: es mayor que la ventana -> tamaño real
    s = lb()
    c.ok("clic sobre la imagen: tamaño real", s["open"] and s["natural"] and abs(s["w"] - 1600) < 1, "natural %r, ancho %.0f" % (s["natural"], s["w"]))
    app.key("Right"); time.sleep(0.5)
    s = lb()
    c.ok("flecha derecha: siguiente imagen, ajustada", s["open"] and "pequena.svg" in s["src"] and not s["natural"] and s["cap"].startswith("2/2"), s["cap"])
    app.key("Escape"); time.sleep(0.4)
    c.ok("Esc cierra el visor", not lb()["open"])
    # edición: miniaturas también en los widgets; el clic abre el visor y NO lleva el bloque a fuente
    app.edit_mode()
    app.wait_js("const i = %s; return !!i && i.complete" % IMG('#editor', 'grande.svg'))
    g = size('#editor', 'grande.svg')
    c.ok("edición: miniatura también en el widget", g is not None and g["w"] <= MAXW and g["h"] <= MAXH, g and "%.0fx%.0f" % (g["w"], g["h"]))
    app.click(g["x"], g["y"]); time.sleep(0.6)
    s = lb()
    c.ok("edición: clic en la miniatura abre el visor", s["open"] and "grande.svg" in s["src"])
    c.ok("y el bloque de la imagen NO pasa a fuente", not app.js("return [...document.querySelectorAll('#editor .cm-line')].some((l) => l.textContent.includes('grande.svg'))"))
    app.key("Escape"); time.sleep(0.4)
    c.ok("Esc cierra el visor sin salir de edición", not lb()["open"] and app.js("return document.body.classList.contains('edit-mode')"))
    app.js("document.getElementById('btn-thumbs').click(); return 1"); time.sleep(0.6)   # en edición la tecla i es del editor: botón
    g = size('#editor', 'grande.svg')
    c.ok("botón: modo apagado, la imagen recupera su tamaño en el widget y se guarda la preferencia",
         g is not None and g["w"] > 500 and app.js("return localStorage.getItem('mdlive-thumbs') === '0'"), g and "ancho %.0f" % g["w"])
finally:
    app.close()
c.finish()
