#!/usr/bin/env python3
"""Minimapa: el recuadro marca exactamente la zona visible, en el visor y en edicion.
Invariante: un h2 visible a d px del borde superior de la ventana tiene su copia en el lienzo a
(recuadro.top + d*escala) px del borde superior del panel. En edicion el bloque en fuente (una
tabla con Ctrl+clic, mucho mas alta en fuente) corre todo lo de debajo y el recuadro debe seguir
al contenido sin esperar a un scroll; y el clic en el minimapa centra lo pulsado.
(Bug del 17-sep-2026: el recuadro se calculaba con el scroll de la pagina como si el lienzo
fuera la pagina.)"""
import time
from mdlive_test import App, Check

app, c = App("minimapa.md"), Check()
MM = "document.getElementById('minimap')"
# estado para el primer bloque (h2 o parrafo) renderizado por debajo del borde superior de la
# ventana: distancia d al borde, y de su copia en el lienzo respecto al panel, recuadro y escala.
# (h2 o p: en edicion el h2 de la seccion visible puede ser justo el bloque en fuente)
def state(host_sel):
    return app.js("""const mm = %s, mr = mm.getBoundingClientRect(), host = document.querySelector(%r);
      const scale = mm.clientWidth / host.getBoundingClientRect().width;
      const vp = document.getElementById('minimap-viewport').getBoundingClientRect();
      const el = [...host.querySelectorAll('h2, p')].find((x) => x.getBoundingClientRect().top >= 0);
      if (!el) return null;
      const ce = [...document.querySelectorAll('#minimap-canvas h2, #minimap-canvas p')].find((x) => x.textContent === el.textContent);
      if (!ce) return null;
      return { scale, vpTop: vp.top - mr.top, vpH: vp.height, d: el.getBoundingClientRect().top, cy: ce.getBoundingClientRect().top - mr.top,
               vh: document.scrollingElement.clientHeight, text: el.textContent.slice(0, 24) };""" % (MM, host_sel))
def check(name, s, tol=2.5):
    if not s:
        c.ok(name, False, "sin bloque renderizado visible"); return
    want = s["vpTop"] + s["d"] * s["scale"]
    c.ok(name, abs(s["cy"] - want) <= tol, "%r: en el lienzo a %.1f, esperado %.1f (recuadro %.1f + %.1f*%.3f)" % (s["text"], s["cy"], want, s["vpTop"], s["d"], s["scale"]))
def scroll_to(frac, host_sel):
    """salta al frac del documento y espera a que haya un h2 renderizado por debajo del borde superior
    (en edicion CodeMirror mide y repinta la ventana unos fotogramas despues del salto)"""
    app.js("const sc = document.scrollingElement; sc.scrollTop = %s * (sc.scrollHeight - sc.clientHeight); return sc.scrollTop" % frac)
    for _ in range(12):
        time.sleep(0.25)
        if app.js("return [...document.querySelectorAll(%r + ' h2')].some((h) => h.getBoundingClientRect().top >= 0)" % host_sel):
            break
        app.js("const sc = document.scrollingElement; sc.scrollTop += 1; return 1")   # un empujon: que CM vuelva a medir y repinte
    time.sleep(0.3)
PICK = """const mr = %s.getBoundingClientRect(), goal = mr.top + mr.height * .7;
      const src = [...document.querySelectorAll('#editor .cm-line')].map((l) => l.textContent);
      let best = null;
      for (const h of document.querySelectorAll('#minimap-canvas h2')) { const r = h.getBoundingClientRect();
        if (r.top < mr.top + 4 || r.bottom > mr.bottom - 4 || src.some((t) => t.includes(h.textContent))) continue;
        const d = Math.abs(r.top + r.height / 2 - goal); if (!best || d < best.d) best = { d, y: r.top + r.height / 2, x: mr.left + mr.width / 2, text: h.textContent }; }
      return best;""" % MM
def click_canvas_h2(synthetic=False):
    """clic en el minimapa sobre la copia de un h2 del lienzo (dentro del panel, cerca del 70%% de su alto,
    y que no sea el bloque en fuente). Real con xdotool (coordenadas enteras: 1 px del panel son ~5 px de
    pagina) o sintetico con clientY exacto (mide el mapeo sin esa cuantizacion). Devuelve el texto del h2."""
    t = app.js(PICK)
    if not t:
        return None
    if synthetic:
        app.js("""const mm = %s; const ev = (type, tgt) => tgt.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, button: 0, clientX: %r, clientY: %r }));
          ev('mousedown', mm); ev('mouseup', document); return 1""" % (MM, t["x"], t["y"]))
    else:
        app.click(t["x"], t["y"])
    time.sleep(0.6)
    return t["text"]
def centered(name, host_sel, text, tol):
    mid = app.js("const h = [...document.querySelectorAll(%r + ' h2')].find((x) => x.textContent === %r); if (!h) return null;"
                 " const r = h.getBoundingClientRect(); return { c: r.top + r.height / 2, vh: document.scrollingElement.clientHeight }" % (host_sel, text))
    c.ok(name, mid is not None and abs(mid["c"] - mid["vh"] / 2) <= tol, "centro %r, ventana/2 %r" % (mid and mid["c"], mid and mid["vh"] / 2))
try:
    # ---- visor ----
    app.click(600, 700)   # foco al webview; el minimapa viene activado por defecto (perfil nuevo): solo si no, tecla m
    if not app.js("return document.body.classList.contains('minimap-on')"):
        app.key("m")
    app.wait_js("return document.body.classList.contains('minimap-on') && !!document.querySelector('#minimap-canvas h2')")
    scroll_to(0.4, "#content")
    s = state("#content")
    check("visor: recuadro alineado con el contenido", s)
    c.close("visor: alto del recuadro = ventana a escala", s["vpH"], s["vh"] * s["scale"], 2.5)
    text = click_canvas_h2()
    c.ok("visor: copia del h2 dentro del panel", text is not None)
    if text:
        centered("visor: clic real en el minimapa centra lo pulsado", "#content", text, 15)
    text = click_canvas_h2(synthetic=True)
    if text:
        centered("visor: clic exacto en el minimapa centra lo pulsado", "#content", text, 6)
    # ---- edicion ----
    app.edit_mode()
    app.wait_js("return !!document.querySelector('#minimap-canvas h2')")
    time.sleep(0.5)
    scroll_to(0.4, "#editor")
    s = state("#editor")
    check("edicion: recuadro alineado con el contenido", s, 3)
    # la tabla de la primera celda visible pasa a fuente (Ctrl+clic): cambia de alto (en fuente sus filas
    # largas miden distinto) y con ella todo lo de debajo; sin scroll, el recuadro debe actualizarse
    # una tabla que EMPIECE dentro de la ventana: asi su fuente (mas corta) queda a la vista y cambia lo
    # visible. Si empezara muy arriba, en fuente podria quedar entera por encima del borde superior.
    target = app.js("""const tb = [...document.querySelectorAll('#editor table')].find((t) => { const r = t.getBoundingClientRect(); return r.top >= 0 && r.top <= innerHeight - 120; });
      const td = tb && [...tb.querySelectorAll('td')].find((t) => { const r = t.getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight - 10; });
      if (!td) return null;
      const r = td.getBoundingClientRect();
      return { x: r.left + 10, y: r.top + r.height / 2, h: tb.getBoundingClientRect().height, top: tb.getBoundingClientRect().top };""")
    c.ok("hay una celda visible para el Ctrl+clic", target is not None)
    if target:
        before = state("#editor")
        app.click(target["x"], target["y"], mods=("ctrl",))
        app.wait_js("return [...document.querySelectorAll('#editor .cm-line')].some((l) => l.textContent.startsWith('| campo_'))")
        time.sleep(0.5)
        srcH = app.js("const ls = [...document.querySelectorAll('#editor .cm-line')].filter((l) => l.textContent.startsWith('| ')); return ls.length ? ls[ls.length - 1].getBoundingClientRect().bottom - ls[0].getBoundingClientRect().top : 0")
        c.ok("la tabla en fuente mide distinto que renderizada", abs(srcH - target["h"]) > 60, "fuente %.0f px, renderizada %.0f" % (srcH, target["h"]))
        vp1 = app.rect("document.getElementById('minimap-viewport')")
        # fuerza una actualizacion (el recuadro se recalcula con el evento scroll de window; un
        # scrollTop +1/-1 en el mismo tick no dispara ninguno)
        app.js("window.dispatchEvent(new Event('scroll')); return 1"); time.sleep(0.4)
        vp2 = app.rect("document.getElementById('minimap-viewport')")
        geo = app.js("""const sc = document.scrollingElement, ls = [...document.querySelectorAll('#editor .cm-line')];
          const r0 = ls.length && ls[0].getBoundingClientRect(), r1 = ls.length && ls[ls.length - 1].getBoundingClientRect();
          return 'scrollTop ' + sc.scrollTop + ', ' + ls.length + ' lineas en fuente en [' + (ls.length ? r0.top.toFixed(0) + ', ' + r1.bottom.toFixed(0) : '') + '] de la ventana'""")
        c.ok("sin scroll, el recuadro ya reflejaba el cambio", abs(vp1["t"] - vp2["t"]) < 0.6 and abs(vp1["h"] - vp2["h"]) < 0.6,
             "top %.1f/%.1f alto %.1f/%.1f (antes del Ctrl+clic: alto %.1f); %s" % (vp1["t"], vp2["t"], vp1["h"], vp2["h"], before["vpH"] if before else -1, geo))
        c.ok("y el alto del recuadro ha cambiado con la tabla en fuente", before is not None and abs(vp2["h"] - before["vpH"]) > 2,
             "alto %.1f -> %.1f; %s" % (before["vpH"] if before else -1, vp2["h"], geo))
        # el borde superior de la ventana pasa por debajo del bloque en fuente: todo lo de arriba
        # difiere entre pagina y lienzo, y el recuadro tiene que seguir clavado en lo visible
        app.js("const ls = [...document.querySelectorAll('#editor .cm-line')].filter((l) => l.textContent.startsWith('| '));"
               " document.scrollingElement.scrollTop += ls[ls.length - 1].getBoundingClientRect().bottom + 30; return 1")
        time.sleep(0.5)
        check("edicion: recuadro alineado con el bloque en fuente por encima de la ventana", state("#editor"), 3)
    text = click_canvas_h2()
    c.ok("edicion: copia del h2 dentro del panel", text is not None)
    if text:
        centered("edicion: clic real en el minimapa centra lo pulsado", "#editor", text, 15)
    text = click_canvas_h2(synthetic=True)
    if text:
        centered("edicion: clic exacto en el minimapa centra lo pulsado", "#editor", text, 6)
finally:
    app.close()
c.finish()
