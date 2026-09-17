#!/usr/bin/env python3
"""Exportar (tecla x / botón): menú con PDF, HTML autocontenido, Jira, Confluence, Slack y Teams; con
algo seleccionado solo se exporta la selección (bloques enteros), en el visor y en edición. Jira y
compañía abren un popup con el texto (copiar texto / copiar con formato = HTML en el portapapeles);
HTML y PDF generan un fichero (aquí por el canal de pruebas, sin diálogo de guardar)."""
import re
import subprocess
import time
from mdlive_test import App, Check, DISPLAY

app, c = App("exportar.md"), Check()
MENU = "document.getElementById('export-menu')"
def menu_open():
    return app.js("return %s.style.display === 'block'" % MENU)
def click_item(kind):
    r = app.rect('%s.querySelector(".item[data-kind=%s]")' % (MENU, kind))
    app.click(r["l"] + 20, r["t"] + r["h"] / 2)
def click_el(sel):
    r = app.rect("document.querySelector(%r)" % sel)
    app.click(r["l"] + r["w"] / 2, r["t"] + r["h"] / 2)
def modal():
    return app.js("return { open: document.body.classList.contains('export-open'), title: document.getElementById('export-title').textContent,"
                  " text: document.getElementById('export-text').value, status: document.getElementById('export-status').textContent }")
def clip(target="UTF8_STRING"):
    try:
        return subprocess.run(["xclip", "-selection", "clipboard", "-o", "-t", target], env={"DISPLAY": DISPLAY}, capture_output=True, timeout=5).stdout.decode("utf-8", "replace")
    except Exception as e:
        return "ERROR %s" % e
def wait_file(path, timeout):
    for _ in range(int(timeout * 4)):
        if path.exists() and path.stat().st_size > 0:
            time.sleep(0.3); return True
        time.sleep(0.25)
    return False
try:
    app.click(600, 860)   # foco al webview, zona vacía
    app.key("x"); time.sleep(0.4)
    c.ok("tecla x: se abre el menú de exportar", menu_open())
    c.eq("seis destinos", app.js("return %s.querySelectorAll('.item').length" % MENU), 6)
    c.eq("sin selección: todo el documento", app.js("return %s.querySelector('.hdr').textContent" % MENU), "Exportar todo el documento")
    click_item("jira"); time.sleep(0.5)
    m = modal()
    c.ok("Jira: popup con el wiki markup", m["open"] and m["text"].startswith("h1. Exportar") and "||C1||C2||" in m["text"] and "{code:js}" in m["text"], m["text"][:120])
    c.ok("título del popup", "todo el documento" in m["title"] and "Jira" in m["title"], m["title"])
    c.ok("el menú se ha cerrado", not menu_open())
    click_el("#export-copy"); time.sleep(0.5)
    c.ok("Copiar texto: el portapapeles tiene el wiki markup", clip().strip() == m["text"].strip(), clip()[:80])
    click_el("#export-copy-rich"); time.sleep(0.5)
    html = clip("text/html")
    # (WebKit re-serializa el HTML del portapapeles con estilos inline: se busca la estructura, no el literal)
    c.ok("Copiar con formato: HTML en el portapapeles", re.search(r"<h1[^>]*>Exportar</h1>", html) is not None and "<table" in html and "<code" in html, html[:160])
    c.ok("y el texto plano sigue siendo el wiki markup", clip().strip() == m["text"].strip())
    c.ok("estado del popup", "Copiado con formato" in modal()["status"], modal()["status"])
    app.key("Escape"); time.sleep(0.3)
    c.ok("Esc cierra el popup", not modal()["open"])
    # selección en el visor: solo ese bloque
    app.js("const p = document.querySelectorAll('#content p')[1], s = getSelection(), r = document.createRange(); r.selectNodeContents(p); s.removeAllRanges(); s.addRange(r); return s.toString()")
    app.key("x"); time.sleep(0.4)
    c.eq("con selección: cabecera con las líneas", app.js("return %s.querySelector('.hdr').textContent" % MENU), "Exportar la selección (líneas 5–5)")
    click_item("slack"); time.sleep(0.5)
    m = modal()
    c.eq("Slack: solo el párrafo seleccionado", m["text"], "Párrafo dos para seleccionar.")
    app.key("Escape"); time.sleep(0.3)
    app.js("getSelection().removeAllRanges(); return 1")
    # HTML autocontenido por el canal de pruebas (sin diálogo)
    out_html = app.tmp / "salida.html"
    app.js("window.__mdliveExportPath = %r; return 1" % str(out_html))
    app.key("x"); time.sleep(0.4); click_item("html")
    c.ok("HTML: se genera el fichero", wait_file(out_html, 15))
    doc = out_html.read_text(encoding="utf-8") if out_html.exists() else ""
    conds = { "doctype": doc.startswith("<!DOCTYPE html>"), "css": "<style>" in doc and ".markdown-body" in doc, "articulo": '<article class="markdown-body">' in doc,
              "imagen data:": "data:image/svg+xml" in doc, "hljs": "hljs" in doc, "titulo": "<title>exportar</title>" in doc }
    c.ok("HTML: autocontenido (doctype, CSS, artículo, imagen embebida, código resaltado)", all(conds.values()), "fallan: %s (len %d)" % ([k for k, v in conds.items() if not v], len(doc)))
    c.ok("HTML: sin data-line", "data-line" not in doc)
    c.ok("aviso de exportado", "Exportado a" in app.js("return document.getElementById('toast').textContent"))
    # PDF: impresión del HTML en una vista aparte
    out_pdf = app.tmp / "salida.pdf"
    app.js("window.__mdliveExportPath = %r; return 1" % str(out_pdf))
    app.key("x"); time.sleep(0.4); click_item("pdf")
    ok = wait_file(out_pdf, 40)
    head = out_pdf.read_bytes()[:5] if ok else b""
    c.ok("PDF: se genera el fichero", ok and head == b"%PDF-" and out_pdf.stat().st_size > 2000, "%r %s" % (head, app.js("return document.getElementById('toast').textContent")))
    # edición: la selección de CM (bloques enteros) y el botón (la tecla x es del editor)
    app.edit_mode()
    app.js("const v = CM.view.EditorView.findFromDOM(document.querySelector('#editor .cm-editor')), l = v.state.doc.line(3); v.dispatch({ selection: { anchor: l.from + 3, head: l.to - 2 } }); return l.text")
    time.sleep(0.4)
    click_el("#btn-export"); time.sleep(0.4)
    c.eq("edición: la selección de CM se amplía al bloque", app.js("return %s.querySelector('.hdr').textContent" % MENU), "Exportar la selección (líneas 3–3)")
    click_item("teams"); time.sleep(0.5)
    m = modal()
    c.eq("Teams: el bloque en su markdown", m["text"], "Párrafo **uno** con `código`.")
    app.key("Escape"); time.sleep(0.3)
    c.ok("Esc cierra el popup sin salir de edición", not modal()["open"] and app.js("return document.body.classList.contains('edit-mode')"))
finally:
    app.close()
c.finish()
