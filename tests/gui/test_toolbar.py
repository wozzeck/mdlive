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
def widths():
    return app.js("return Object.fromEntries([...%s.children].map((b) => [b.id, Math.round(b.getBoundingClientRect().width)]))" % TB)
def hot_id():
    return app.js("const h = document.querySelector('#toolbar button.hot'); return h && h.id")
def minimap_on():
    return app.js("return document.body.classList.contains('minimap-on')")
def geom():
    """Con la barra desplegada: su borde derecho, su franja vertical, el ancho compacto y el botón
    de rótulo más largo (el que fija el ancho de la zona que extiende los rótulos)."""
    return app.js("""const tb = document.getElementById('toolbar'), r = tb.getBoundingClientRect();
      let wid = null, bw = -1;
      for (const b of tb.children) { const w = b.querySelector('.lbl').scrollWidth; if (w > bw) { bw = w; wid = b.id; } }
      return { right: r.right, top: r.top, bottom: r.bottom, cy: (r.top + r.bottom) / 2, widest: wid,
               compact: Math.min(...[...tb.children].map((b) => b.offsetWidth)) };""")
def hover_width(bid):
    """Ancho real del botón con su rótulo desplegado, posando el ratón encima."""
    r = app.rect("document.getElementById(%r)" % bid)
    app.move(r["l"] + r["w"] / 2, r["t"] + r["h"] / 2); time.sleep(0.45)
    return app.js("return document.getElementById(%r).offsetWidth" % bid)
def away():
    app.move(400, 700); time.sleep(0.95)
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
    w, hot0 = widths(), hot_id()
    rest = [v for k, v in w.items() if k != hot0]
    c.ok("compactos (solo icono) e iguales salvo el de la fila del puntero, que ya sale con su rótulo",
         bool(hot0) and len(set(rest)) == 1 and 26 <= rest[0] <= 34 and w[hot0] > rest[0] + 40, "%r hot=%s" % (w, hot0))
    # 2) posarse sobre otro botón: se extiende hacia la izquierda con su título y su tecla
    b0 = btn('btn-toc')
    app.move(b0["l"] + b0["w"] / 2, b0["t"] + b0["h"] / 2); time.sleep(0.5)
    b1, other = btn('btn-toc'), btn('btn-recent')
    c.ok("el botón bajo el puntero se extiende hacia la izquierda (el borde derecho no se mueve)",
         b1["w"] > b0["w"] + 40 and abs(b1["r"] - b0["r"]) < 1 and b1["l"] < b0["l"] - 40, "%r -> %r" % (b0, b1))
    c.ok("muestra su título y su tecla", b1["lop"] > 0.9 and b1["lw"] > 40 and b1["text"] == "Índicet", "%r" % b1["text"])
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
    # ---- las dos zonas sensibles son más grandes que lo que se ve y se miden solas ----------
    app.toolbar_show()
    g = geom()
    wideW = hover_width(g["widest"])
    compactW = g["compact"]
    c.ok("el botón más ancho con su rótulo mide mucho más que el compacto", wideW > compactW * 3, "%s: %r vs %r" % (g["widest"], wideW, compactW))
    away()
    # 1) desplegar: toda la caja que ocupan los botones compactos, no unos píxeles del borde
    app.move(g["right"] - compactW + 2, g["cy"]); time.sleep(0.5)
    c.ok("el borde izquierdo de los botones compactos ya despliega la barra", tb()["show"])
    away()
    app.move(g["right"] - compactW - 10, g["cy"]); time.sleep(0.5)
    c.ok("a la izquierda de esa caja no se despliega", not tb()["show"])
    # 2) extender el rótulo: la caja del botón MÁS ANCHO, aunque el botón apuntado sea estrecho
    app.move(g["right"] - wideW + 6, g["cy"]); time.sleep(0.5)
    c.ok("la zona ancha no despliega la barra si está escondida", not tb()["show"])
    app.toolbar_show()
    sr = app.rect("document.getElementById('btn-search')")
    app.move(g["right"] - wideW + 6, sr["t"] + sr["h"] / 2); time.sleep(0.6)
    w = app.js("return document.getElementById('btn-search').offsetWidth")
    c.ok("en el borde del botón más ancho ya se extiende el rótulo de uno estrecho", compactW + 30 < w < wideW, "ancho %r (compacto %r, más ancho %r)" % (w, compactW, wideW))
    c.ok("el rótulo se ve entero (el tope se calcula, no es un valor fijo)", app.js("const l = document.querySelector('#btn-search .lbl'); return l.scrollWidth <= l.clientWidth + 1"))
    c.eq("y la barra sigue desplegada en esa zona", tb()["show"], True)
    app.move(g["right"] - wideW - 14, sr["t"] + sr["h"] / 2); time.sleep(0.95)
    c.ok("pasado ese borde se esconde", not tb()["show"])
    # 3) vertical: los huecos entre botones cuentan para el vecino más cercano
    app.toolbar_show()
    a, b = app.rect("document.getElementById('btn-search')"), app.rect("document.getElementById('btn-minimap')")
    app.move(g["right"] - wideW + 6, (a["b"] + b["t"]) / 2); time.sleep(0.6)
    hot = app.js("const h = document.querySelector('#toolbar button.hot'); return h && h.id")
    c.ok("en el hueco entre dos botones se extiende el más cercano", hot in ("btn-search", "btn-minimap"), "%r" % hot)
    # 4) un botón futuro más ancho agranda la zona sin tocar nada
    app.js("""const tb = document.getElementById('toolbar'), b = document.createElement('button');
      b.id = 'btn-futuro'; b.setAttribute('aria-label', 'Futuro');
      b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/></svg>'
        + '<span class="lbl">Un rótulo de un botón futuro mucho más largo<kbd>z</kbd></span>';
      tb.appendChild(b); return 1""")
    time.sleep(0.6)
    wide2 = hover_width("btn-futuro")
    c.ok("el botón nuevo es más ancho que todos", wide2 > wideW + 20, "%r vs %r" % (wide2, wideW))
    away()
    app.toolbar_show()
    app.move(g["right"] - wide2 + 6, sr["t"] + sr["h"] / 2); time.sleep(0.6)
    c.ok("la zona crece con él: el rótulo se extiende ya en el borde nuevo",
         app.js("return document.getElementById('btn-search').offsetWidth") > compactW + 30)
finally:
    app.close()
# el ancho de los rótulos cambia con el idioma: la zona tiene que seguirlo
app = App("toc.md", lang="de")
try:
    app.toolbar_show()
    gd = geom()
    wd = hover_width(gd["widest"])
    lblVar = app.js("return parseFloat(getComputedStyle(document.getElementById('toolbar')).getPropertyValue('--tb-lbl'))")
    c.ok("en alemán la barra se mide con sus propios rótulos (tope publicado = ancho real medido)",
         abs((gd["compact"] + lblVar) - wd) <= 1.5, "medido %r, compacto %r + tope %r" % (wd, gd["compact"], lblVar))
    away()
    app.toolbar_show()
    sd = app.rect("document.getElementById('btn-search')")
    app.move(gd["right"] - wd + 6, sd["t"] + sd["h"] / 2); time.sleep(0.6)
    c.ok("la zona llega hasta donde llega el rótulo alemán", app.js("return document.getElementById('btn-search').offsetWidth") > gd["compact"] + 30)
    app.move(gd["right"] - wd - 14, sd["t"] + sd["h"] / 2); time.sleep(0.95)
    c.ok("y no más allá", not tb()["show"])
finally:
    app.close()
c.finish()
