#!/usr/bin/env python3
"""Botonera oculta: los botones asoman 7 px por el borde derecho; se despliegan al acercar el ratón al borde
a su altura (o al posarse sobre ellos) y se esconden al alejarse; el botón bajo el puntero se extiende hacia
la izquierda con su título y su tecla (los demás siguen compactos, todos alineados por la derecha). Un clic
real en un botón desplegado funciona. El menú de exportar mantiene la barra desplegada (sin rótulos) y se
coloca a su izquierda sin solaparla."""
import time
from mdlive_test import App, Check

app, c = App("toc.md"), Check()
TB = "document.getElementById('toolbar')"
def tb():
    return app.js("const t = %s, r = t.getBoundingClientRect(); return { show: t.classList.contains('show'), hold: t.classList.contains('hold'),"
                  " l: r.left, r: r.right, t: r.top, b: r.bottom, cw: document.documentElement.clientWidth, n: t.children.length }" % TB)
def btn(bid):
    return app.js("const b = document.getElementById(%r), r = b.getBoundingClientRect(), l = b.querySelector('.lbl'), lr = l.getBoundingClientRect();"
                  " return { l: r.left, r: r.right, w: r.width, t: r.top, h: r.height, lw: lr.width, lop: parseFloat(getComputedStyle(l).opacity), text: l.textContent }" % bid)
def minimap_on():
    return app.js("return document.body.classList.contains('minimap-on')")
try:
    app.wait_js("return document.getElementById('content').children.length > 0")
    app.move(400, 700); time.sleep(0.5)
    s = tb()
    c.ok("al arrancar la barra está escondida: asoma ≤ 8 px por el borde derecho", not s["show"] and s["cw"] - s["l"] <= 8 and s["r"] > s["cw"], "%r" % s)
    c.eq("ocho botones", s["n"], 8)
    REM = app.js("return parseFloat(getComputedStyle(document.documentElement).fontSize)")
    # 1) acercar el ratón al borde a la altura de la barra: se despliega
    app.move(s["cw"] - 4, (s["t"] + s["b"]) / 2)
    app.wait_js("return %s.classList.contains('show')" % TB); time.sleep(0.45)
    s = tb()
    c.close("desplegada: pegada al borde a .9rem", s["cw"] - s["r"], 0.9 * REM, 1.5)
    ws = app.js("return [...%s.children].map((b) => Math.round(b.getBoundingClientRect().width))" % TB)
    c.ok("botones compactos (solo icono) y del mismo ancho", len(set(ws)) == 1 and 26 <= ws[0] <= 34, "%r" % ws)
    # 2) posarse sobre un botón: se extiende hacia la izquierda con su título y su tecla
    b0 = btn('btn-minimap')
    app.move(b0["l"] + b0["w"] / 2, b0["t"] + b0["h"] / 2); time.sleep(0.5)
    b1, other = btn('btn-minimap'), btn('btn-recent')
    c.ok("el botón bajo el puntero se extiende hacia la izquierda (el borde derecho no se mueve)",
         b1["w"] > b0["w"] + 40 and abs(b1["r"] - b0["r"]) < 1 and b1["l"] < b0["l"] - 40, "%r -> %r" % (b0, b1))
    c.ok("muestra su título y su tecla", b1["lop"] > 0.9 and b1["lw"] > 40 and b1["text"] == "Minimapam", "%r" % b1["text"])
    c.ok("los demás siguen compactos y alineados por la derecha", abs(other["w"] - b0["w"]) < 1 and abs(other["r"] - b1["r"]) < 1, "%r" % other)
    # 3) alejar el ratón: se esconde
    app.move(400, 700); time.sleep(0.9)
    s = tb()
    c.ok("al alejar el ratón se esconde de nuevo", not s["show"] and s["cw"] - s["l"] <= 8, "%r" % s)
    # 4) clic real en un botón (el helper despliega la barra antes)
    on0 = minimap_on()
    app.toolbar_click('btn-minimap'); time.sleep(0.4)
    c.ok("clic en el botón desplegado: el minimapa cambia de estado", minimap_on() != on0)
    app.toolbar_click('btn-minimap'); time.sleep(0.4)
    c.ok("segundo clic: vuelve al estado inicial", minimap_on() == on0)
    # 5) menú de exportar por teclado con la barra escondida
    app.move(400, 700); time.sleep(0.9)
    c.ok("tras el clic la barra se esconde al alejarse", not tb()["show"])
    app.click(400, 700)   # foco al webview
    app.key("x"); time.sleep(0.6)
    s, m, bx = tb(), app.rect("document.getElementById('export-menu')"), btn('btn-export')
    c.ok("tecla x: la barra se despliega y queda fija mientras el menú está abierto", s["show"] and s["hold"], "%r" % s)
    c.ok("el menú queda a la izquierda de la barra, sin solaparla y a la altura del botón",
         m is not None and m["r"] <= s["l"] - 2 and m["l"] >= 0 and abs(m["t"] - bx["t"]) < 12, "%r vs %r / %r" % (m, s, bx))
    app.move(bx["l"] + bx["w"] / 2, bx["t"] + bx["h"] / 2); time.sleep(0.5)
    c.ok("con el menú abierto los rótulos no se extienden", abs(btn('btn-export')["w"] - bx["w"]) < 1, "%r" % btn('btn-export'))
    app.key("Escape"); time.sleep(0.3)
    c.ok("Esc cierra el menú y suelta la barra (sigue desplegada mientras el ratón está encima)",
         not app.js("return document.getElementById('export-menu').style.display === 'block'") and not tb()["hold"] and tb()["show"])
    app.move(400, 700); time.sleep(0.9)
    c.ok("al alejarse se esconde", not tb()["show"])
finally:
    app.close()
c.finish()
