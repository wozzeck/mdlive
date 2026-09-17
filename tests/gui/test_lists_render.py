#!/usr/bin/env python3
"""Editor con todo renderizado = visor, pixel a pixel (listas anidadas, numeradas, tareas,
titulo pegado a parrafo...). El caret va al final del documento y se vuelve arriba."""
from mdlive_test import App, Check, diff_pixels

app, c = App("listas.md"), Check()
try:
    view = app.shot()
    app.edit_mode()
    app.key("ctrl+End")
    app.js("document.scrollingElement.scrollTop = 0; return true")
    import time; time.sleep(0.6)
    edit = app.shot()
    w = app.js("return document.getElementById('editor').getBoundingClientRect().right")
    box = (0, 0, int(w) - 10, 860)
    n, bands = diff_pixels(view, edit, box)
    # el ruido de antialiasing son unas decenas de px sueltos; un desfase de maquetacion son miles
    c.ok("primera pantalla identica en visor y editor", n <= 150, "%d px distintos en %s" % (n, bands[:8]))
finally:
    app.close()
c.finish()
