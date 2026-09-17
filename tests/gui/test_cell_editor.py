#!/usr/bin/env python3
"""Tablas en edicion: clic en una celda abre el cajon con la fuente de la celda.
- el cajon no se sale del ancho de la celda (crece hacia abajo si la fuente no cabe)
- una celda cuyo texto cabe justo no se parte (una sola linea)
- la fuente se colorea como en el bloque en fuente (**negrita** con los asteriscos, en negrita)
- Tab / Intro / Esc / clic fuera; fila corta; cabecera; Ctrl+Z; Ctrl+clic = tabla en fuente"""
import time
from mdlive_test import App, Check

app, c = App("tabla.md"), Check()
BOX = "document.querySelector('.cm-cell-editor')"
TD = "document.querySelector('#editor table tbody tr:nth-child(%d) td:nth-child(%d)')"
TH = "document.querySelector('#editor table thead th:nth-child(%d)')"
def box_text():
    return app.js("const b = %s; return b ? b.querySelector('.cm-content').textContent : null" % BOX)
def open_cell(expr):
    r = app.rect(expr)
    app.click(r["l"] + min(12, r["w"] / 3), r["t"] + r["h"] / 2)
    app.wait_js("return !!%s" % BOX)
    return r
try:
    app.edit_mode()
    # 1) **Login**: la fuente es mas ancha que la celda -> el cajon se queda en su ancho y crece hacia abajo
    td = open_cell(TD % (1, 1))
    info = app.js("""const b = %s, r = b.getBoundingClientRect(), spans = [...b.querySelectorAll('.cm-line span')];
      const tok = spans.find((s) => s.textContent.includes('Login'));
      return { l: r.left, r: r.right, h: r.height, weight: tok ? getComputedStyle(tok).fontWeight : null,
               markers: b.querySelector('.cm-content').textContent };""" % BOX)
    c.eq("fuente de la celda", info["markers"], "**Login**")
    c.ok("no se sale por la izquierda", info["l"] >= td["l"] - 0.5, "cajon %.1f celda %.1f" % (info["l"], td["l"]))
    c.ok("no se sale por la derecha", info["r"] <= td["r"] + 0.5, "cajon %.1f celda %.1f" % (info["r"], td["r"]))
    c.ok("crece hacia abajo al partirse", info["h"] > td["h"] + 5, "alto cajon %.1f celda %.1f" % (info["h"], td["h"]))
    c.ok("negrita con los asteriscos a la vista", info["weight"] is not None and int(info["weight"]) >= 600, "font-weight %s" % info["weight"])
    app.key("Escape")
    app.wait_js("return !%s" % BOX)
    c.ok("Esc devuelve el foco al editor", app.js("return !!document.activeElement.closest('#editor')"))
    # 2) 'media' cabe justo: una sola linea
    td = open_cell(TD % (2, 2))
    h = app.rect(BOX)["h"]
    c.close("celda que cabe justa: una linea", h, td["h"], 1.5)
    c.eq("texto", box_text(), "media")
    # codigo en linea: misma familia que en el bloque en fuente (se compara mas abajo)
    app.key("Escape"); app.wait_js("return !%s" % BOX)
    # 3) escribir + Tab: confirma y pasa a la celda siguiente
    open_cell(TD % (1, 1)); app.type(" ok"); app.key("Tab")
    app.wait_js("return (%s) && %s.querySelector('.cm-content').textContent === 'alta'" % (BOX, BOX))
    c.eq("Tab confirma la celda", app.line(7), "| **Login** ok | alta | en curso |")
    # 4) Ctrl+A + texto + Intro: sustituye y baja
    app.key("ctrl+a"); app.type("baja"); app.key("Return")
    app.wait_js("return (%s) && %s.querySelector('.cm-content').textContent === 'media'" % (BOX, BOX))
    c.eq("Intro confirma y baja", app.line(7), "| **Login** ok | baja | en curso |")
    # 5) Esc cancela
    app.type("ZZZ"); app.key("Escape"); app.wait_js("return !%s" % BOX)
    c.eq("Esc no toca la fila", app.line(8), "| Pagos | media | |")
    # 6) celda vacia + clic fuera (en el parrafo de despues) confirma
    open_cell(TD % (2, 3)); app.type("pendiente")
    p = app.rect("[...document.querySelectorAll('#editor .cm-mdblock')].pop()")
    app.click(p["l"] + 30, p["t"] + p["h"] / 2); app.wait_js("return !%s" % BOX)
    c.eq("clic fuera confirma", app.line(8), "| Pagos | media | pendiente |")
    # 7) fila corta: celda que la fila no tiene; Tab en la ultima columna salta a la fila siguiente
    open_cell(TD % (3, 3)); app.type("x"); app.key("Tab")
    app.wait_js("return (%s) && %s.querySelector('.cm-content').textContent.startsWith('Con')" % (BOX, BOX))
    c.eq("fila corta: se anaden las celdas que faltan", app.line(9), "| Corta | | x |")
    c.eq("Tab al final de fila: primera celda de la siguiente, con el pipe escapado", box_text(), "Con `a\\|b`")
    mono = app.js("const s = [...%s.querySelectorAll('.cm-line span')].find((s) => s.textContent.includes('a'));"
                  " return s ? getComputedStyle(s).fontFamily : null" % BOX)
    app.key("Escape"); app.wait_js("return !%s" % BOX)
    # 8) cabecera + Intro baja a la fila 1; Ctrl+Z en el editor deshace la celda
    open_cell(TH % 2); app.type("ridad"); app.key("Return")
    app.wait_js("return (%s) && %s.querySelector('.cm-content').textContent === 'baja'" % (BOX, BOX))
    c.eq("cabecera editable", app.line(5), "| Épica | Prioridad | Estado |")
    app.key("Escape"); app.wait_js("return !%s" % BOX)
    app.key("ctrl+z"); time.sleep(0.8)
    c.eq("Ctrl+Z deshace la celda", app.line(5), "| Épica | Prio | Estado |")
    # 9) Ctrl+clic: la tabla entera en fuente, coloreada igual que el cajon
    td = app.rect(TD % (1, 1))
    app.click(td["l"] + 12, td["t"] + td["h"] / 2, mods=("ctrl",))
    app.wait_js("return [...document.querySelectorAll('#editor .cm-line')].some((l) => l.textContent.includes('| Épica'))")
    src = app.js("""const ln = [...document.querySelectorAll('#editor .cm-line')].find((l) => l.textContent.includes('**Login**'));
      const tok = ln && [...ln.querySelectorAll('span')].find((s) => s.textContent.includes('Login'));
      const lc = [...document.querySelectorAll('#editor .cm-line')].find((l) => l.textContent.includes('a\\\\|b'));
      const code = lc && [...lc.querySelectorAll('span')].find((s) => s.textContent.includes('a'));
      return { weight: tok ? getComputedStyle(tok).fontWeight : null, mono: code ? getComputedStyle(code).fontFamily : null };""")
    c.eq("Ctrl+clic: tabla en fuente y misma negrita que en el cajon", src["weight"], info["weight"])
    c.eq("codigo en linea: misma fuente que en el bloque en fuente", mono, src["mono"])
finally:
    app.close()
c.finish()
