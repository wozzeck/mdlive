#!/usr/bin/env python3
"""Chincheta (tecla p): fija arriba la cadena de títulos de la sección visible (h1 > h2) mientras se hace
scroll; el título fijado es el último encabezado que ha pasado por encima del borde; clic en una fila lleva
a esa sección; se recuerda en localStorage; funciona también en edición; al apagarla desaparece."""
import time
from mdlive_test import App, Check

app, c = App("minimapa.md"), Check()
def bar():
    return app.js("const b = document.getElementById('pin-bar'), r = b.getBoundingClientRect(); return { show: b.classList.contains('show'), rows: [...b.querySelectorAll('.pin-row')].map((x) => ({ t: x.textContent, l: [...x.classList].find((k) => /^pin-h\\d$/.test(k)) })), h: r.height, b: r.bottom }")
def last_h2_above(host):
    # mismo criterio que la app (curHeadingFrom): el h2 cuenta si su borde superior queda a <= 8 px + la fila del h1
    return app.js("const r1 = document.querySelector('#pin-bar .pin-h1'), lim = 8 + (r1 ? r1.getBoundingClientRect().height : 0) + 0.5;"
                  " const hs = [...document.querySelectorAll(%r + ' h2')].filter((h) => h.getBoundingClientRect().top <= lim); return hs.length ? hs[hs.length - 1].textContent : null" % host)
def scroll(y):
    app.js("document.scrollingElement.scrollTop = %d; return 1" % y); time.sleep(0.6)
try:
    c.ok("empieza apagada", not app.js("return document.body.classList.contains('pin-on')") and not bar()["show"])
    app.click(600, 700); app.key("p"); time.sleep(0.5)
    c.ok("tecla p: activa, botón resaltado y guardada", app.js("return document.body.classList.contains('pin-on') && document.getElementById('btn-pin').classList.contains('active') && localStorage.getItem('mdlive-pin') === '1'"))
    scroll(1800)
    b = bar()
    c.ok("con scroll la barra se muestra con la cadena h1 > h2", b["show"] and [r["l"] for r in b["rows"]] == ["pin-h1", "pin-h2"] and b["rows"][0]["t"] == "Minimapa", "%r" % b)
    c.eq("el h2 fijado es el último que ha pasado por encima de la barra", b["rows"][1]["t"], last_h2_above("#content"))
    c.ok("la barra reserva su altura para los thead pegajosos (--pin-h)", abs(float(app.js("return parseFloat(document.documentElement.style.getPropertyValue('--pin-h'))")) - b["h"]) < 1.5)
    scroll(4200)
    b2 = bar()
    c.ok("al seguir bajando cambia de sección", b2["show"] and b2["rows"][1]["t"] != b["rows"][1]["t"] and b2["rows"][1]["t"] == last_h2_above("#content"), "%r" % b2)
    # clic en la fila del h2 -> esa sección arriba
    r = app.rect("document.querySelectorAll('#pin-bar .pin-row')[1]")
    title = b2["rows"][1]["t"]
    app.click(r["l"] + 30, r["t"] + r["h"] / 2); time.sleep(0.8)
    top = app.js("const h = [...document.querySelectorAll('#content h2')].find((x) => x.textContent === %r); return h && h.getBoundingClientRect().top" % title)
    c.ok("clic en la fila: la sección queda arriba", top is not None and -2 <= top <= bar()["h"] + 40, "top %r" % top)
    scroll(0)
    c.ok("en la cabecera del documento la barra se esconde o solo lleva el h1", not bar()["show"] or all(r["l"] == "pin-h1" for r in bar()["rows"]), "%r" % bar())
    # edición
    app.edit_mode()
    scroll(2600)
    b3 = bar()
    c.ok("en edición también fija la sección visible", b3["show"] and len(b3["rows"]) == 2 and b3["rows"][1]["t"] == last_h2_above("#editor"), "%r vs %r" % (b3, last_h2_above("#editor")))
    app.key("Escape"); time.sleep(0.5)
    app.js("document.getElementById('btn-pin').click(); return 1"); time.sleep(0.4)
    c.ok("apagada: sin barra, sin reserva de altura y guardada", not app.js("return document.body.classList.contains('pin-on')") and not bar()["show"]
         and app.js("return document.documentElement.style.getPropertyValue('--pin-h')") == "0px" and app.js("return localStorage.getItem('mdlive-pin')") == "0")
finally:
    app.close()
c.finish()
