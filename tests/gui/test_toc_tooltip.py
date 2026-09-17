#!/usr/bin/env python3
"""Indice: el titulo completo de una fila cortada se despliega SOBRE la propia fila, con su
misma tipografia y en la misma posicion (el texto cae justo encima del cortado)."""
from mdlive_test import App, Check

app, c = App("toc.md"), Check()
A = "[...document.querySelectorAll('#toc-list a')].find((a) => a.scrollWidth > a.clientWidth + 1)"
try:
    if not app.js("return document.body.classList.contains('toc-open')"):
        app.click(600, 700); app.key("t")
    app.wait_js("return document.body.classList.contains('toc-open') && !!%s" % A)
    r = app.rect(A)
    app.move(r["l"] + 30, r["t"] + r["h"] / 2)
    app.wait_js("return !!document.querySelector('.mdlive-tip.show')")
    m = app.js("""const a = %s, tip = document.querySelector('.mdlive-tip.show'), sp = tip.firstElementChild;
      const ra = a.getBoundingClientRect(), rt = tip.getBoundingClientRect();
      const ca = getComputedStyle(a), ct = getComputedStyle(sp), cb = getComputedStyle(tip);
      return { text: sp.textContent === a.textContent, family: ca.fontFamily === ct.fontFamily, size: ca.fontSize === ct.fontSize,
               weight: ca.fontWeight === ct.fontWeight,
               dx: (rt.left + parseFloat(cb.borderLeftWidth) + parseFloat(ct.paddingLeft)) - (ra.left + parseFloat(ca.paddingLeft)),
               dy: (rt.top + parseFloat(cb.borderTopWidth) + parseFloat(ct.paddingTop)) - (ra.top + parseFloat(ca.paddingTop)),
               wider: rt.right > ra.right };""" % A)
    c.ok("texto completo", m["text"])
    c.ok("misma familia / tamano / peso", m["family"] and m["size"] and m["weight"])
    c.close("el texto empieza donde el de la fila (x)", m["dx"], 0, 0.5)
    c.close("y a la misma altura (y)", m["dy"], 0, 0.5)
    c.ok("asoma por la derecha del panel", m["wider"])
finally:
    app.close()
c.finish()
