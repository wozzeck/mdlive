#!/usr/bin/env python3
"""Documentos recientes (tecla r): el panel lista el historial (más reciente arriba) con nombre, carpeta y
fecha relativa; el documento actual va marcado, los que no existen también; el botón de copiar deja la
ruta en el portapapeles del sistema (handler nativo); el de quitar borra la fila y la entrada del
historial en disco sin tocar el fichero."""
import json, os, subprocess, time
from mdlive_test import App, Check, DISPLAY

app, c = App("toc.md"), Check()
RECENT = app.tmp / "data" / "mdlive" / "recent.json"
def rows():
    return app.js("return [...document.querySelectorAll('#recent-list .recent-item')].map((r) => ({ nm: r.querySelector('.nm').textContent, rd: r.querySelector('.rd').textContent, rt: r.querySelector('.rt').textContent, title: r.title, cls: r.className }))")
def clip():
    try:
        return subprocess.run(["xclip", "-selection", "clipboard", "-o"], env={"DISPLAY": DISPLAY}, capture_output=True, timeout=5).stdout.decode("utf-8", "replace")
    except Exception as e:
        return "ERROR %s" % e
try:
    time.sleep(0.5)
    hist = json.loads(RECENT.read_text(encoding="utf-8"))
    c.ok("al abrir, el documento entra en el historial en disco", isinstance(hist, list) and hist and hist[0]["path"] == str(app.md), "%r" % hist[:1])
    # se siembran dos entradas más: un fichero que existe (antiguo) y otro que no
    otro = app.tmp / "otro.md"; otro.write_text("# Otro\n", encoding="utf-8")
    now = time.time()
    hist += [{"path": str(otro), "name": "otro.md", "ts": now - 3 * 86400}, {"path": "/no/existe/perdido.md", "name": "perdido.md", "ts": now - 400 * 86400}]
    RECENT.write_text(json.dumps(hist), encoding="utf-8")
    app.click(600, 700); app.key("r"); time.sleep(0.8)
    c.ok("tecla r: panel abierto", app.js("return document.body.classList.contains('recent-open')"))
    rs = rows()
    c.eq("tres filas, más reciente arriba", [r["nm"] for r in rs], ["toc.md", "otro.md", "perdido.md"])
    c.ok("el actual va marcado", "current" in rs[0]["cls"] and "open" in rs[0]["cls"], rs[0]["cls"])
    c.ok("fecha relativa y absoluta", rs[0]["rt"].startswith("hace un momento · ") and rs[1]["rt"].startswith("hace 3 días · ") and rs[2]["rt"].startswith("hace 1 año · "), "%r" % [r["rt"] for r in rs])
    c.ok("carpeta abreviada", rs[0]["rd"].endswith("/") and rs[0]["rd"] in rs[0]["title"] or str(app.tmp) in rs[0]["title"], "%r" % rs[0])
    c.ok("el que no existe va marcado y lo dice el tooltip", "missing" in rs[2]["cls"] and rs[2]["title"].endswith("(no encontrado)"), rs[2]["title"])
    # copiar ruta (handler nativo -> portapapeles del sistema)
    subprocess.run(["xclip", "-selection", "clipboard"], input=b"vacio", env={"DISPLAY": DISPLAY}, timeout=5)
    # los botones de la fila solo se despliegan con la fila bajo el ratón
    r = app.rect("document.querySelector('#recent-list .recent-item')")
    app.move(r["l"] + r["w"] / 2, r["t"] + r["h"] / 2); time.sleep(0.4)
    r = app.rect("document.querySelector('#recent-list .recent-item .rc')")
    c.ok("los botones de la fila asoman al pasar el ratón", r["w"] > 10, "%r" % r)
    app.click(r["l"] + r["w"] / 2, r["t"] + r["h"] / 2, delay=0.05)
    # la confirmación dura 1,2 s: se espera sin dormir (el canal de pruebas tiene su latencia)
    try:
        app.wait_js("const b = document.querySelector('#recent-list .recent-item .rc'); return b.classList.contains('copied') && b.title === 'Ruta copiada'", 1.5); confirmed = True
    except TimeoutError:
        confirmed = False
    c.ok("copiar: el botón confirma (icono de visto 1,2 s)", confirmed)
    c.eq("copiar: la ruta está en el portapapeles del sistema", clip(), str(app.md))
    time.sleep(1.2)
    c.eq("y el botón vuelve a su estado", app.js("return document.querySelector('#recent-list .recent-item .rc').title"), "Copiar ruta")
    # quitar del historial el que no existe
    r = app.rect("document.querySelectorAll('#recent-list .recent-item')[2]")
    app.move(r["l"] + r["w"] / 2, r["t"] + r["h"] / 2); time.sleep(0.4)
    r = app.rect("document.querySelectorAll('#recent-list .recent-item')[2].querySelector('.rx')")
    app.click(r["l"] + r["w"] / 2, r["t"] + r["h"] / 2); time.sleep(0.8)
    c.eq("quitar: la fila desaparece", [r["nm"] for r in rows()], ["toc.md", "otro.md"])
    hist = json.loads(RECENT.read_text(encoding="utf-8"))
    c.ok("quitar: sale del historial en disco y los demás siguen", [h["path"] for h in hist] == [str(app.md), str(otro)], "%r" % [h["path"] for h in hist])
    c.ok("quitar no borra ficheros", otro.exists() and app.md.exists())
    app.click(600, 700); app.key("r"); time.sleep(0.4)   # (Esc no cierra los paneles laterales: se alternan con su tecla)
    c.ok("r de nuevo: cierra el panel", not app.js("return document.body.classList.contains('recent-open')"))
finally:
    app.close()
c.finish()
