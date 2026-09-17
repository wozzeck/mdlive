#!/usr/bin/env python3
"""Operaciones de tabla en edicion: mini-barra sobre la tabla, menu del clic derecho y atajos.
- la mini-barra asoma pegada al borde superior izquierdo de la tabla mientras hay una celda abierta
- realinear anchos, insertar fila (barra), borrar columna (menu), subir fila (Alt+arriba),
  salto de linea en la celda (Ctrl+Intro = <br>), alinear columna (menu), Tab en la ultima celda anade fila
- cada operacion es UN paso de deshacer; Esc con el menu abierto cierra solo el menu
- las operaciones que no proceden (borrar la cabecera) salen deshabilitadas"""
from mdlive_test import App, Check

app, c = App("tabla.md"), Check()
BOX = "document.querySelector('.cm-cell-editor')"
BAR = "document.querySelector('.cm-table-tools')"
MENU = "document.querySelector('.cm-ctxmenu')"
TD = "document.querySelector('#editor table tbody tr:nth-child(%d) td:nth-child(%d)')"
TH = "document.querySelector('#editor table thead th:nth-child(%d)')"
def open_cell(expr):
    r = app.rect(expr)
    app.click(r["l"] + min(12, r["w"] / 3), r["t"] + r["h"] / 2)
    app.wait_js("return !!%s" % BOX)
    return r
def box_over(expr, name):
    b, t = app.rect(BOX), app.rect(expr)
    c.ok(name, b and t and abs(b["l"] - t["l"]) < 1.5 and abs(b["t"] - t["t"]) < 1.5, "cajon %r celda %r" % (b, t))
def bar_click(op):
    r = app.rect("%s.querySelector('button[data-op=\"%s\"]')" % (BAR, op))
    app.click(r["l"] + r["w"] / 2, r["t"] + r["h"] / 2)
def menu_visible():
    return app.js("const m = %s; return !!m && getComputedStyle(m).display !== 'none'" % MENU)
def right_click(expr):
    r = app.rect(expr)
    app.click(r["l"] + min(12, r["w"] / 3), r["t"] + r["h"] / 2, button=3)
    app.wait_js("const m = %s; return !!m && getComputedStyle(m).display !== 'none'" % MENU)
def menu_click(op):
    r = app.rect("%s.querySelector('.item[data-op=\"%s\"]')" % (MENU, op))
    app.click(r["l"] + r["w"] / 2, r["t"] + r["h"] / 2)
F = ["| Épica      | Prio  |   Estado |", "| ---------- | :---: | -------: |", "| **Login**  | alta  | en curso |",
     "| Pagos      | media |          |", "| Corta      |       |          |", "| Con `a\\|b` | baja  |    hecho |"]
try:
    app.edit_mode()
    # 1) mini-barra: visible, sobre la tabla y a su izquierda; la cabecera no se puede borrar
    open_cell(TH % 1)
    bar, tbl = app.rect(BAR), app.rect("document.querySelector('#editor table')")
    c.ok("la mini-barra asoma al abrir una celda", bar is not None and bar["h"] > 10)
    c.ok("justo encima de la tabla", bar and bar["b"] <= tbl["t"] and bar["b"] >= tbl["t"] - 12, "barra %r tabla %r" % (bar, tbl))
    c.close("pegada al borde izquierdo de la tabla", bar and bar["l"], tbl["l"], 1.5)
    c.ok("borrar fila deshabilitado en la cabecera", app.js("return %s.querySelector('button[data-op=\"rowDelete\"]').disabled" % BAR))
    c.eq("alineacion actual marcada (izquierda por defecto)", app.js("return %s.querySelector('button[data-op=\"alignLeft\"]').getAttribute('aria-pressed')" % BAR), "true")
    # 2) realinear anchos (barra): la tabla queda formateada y se sigue en la misma celda
    bar_click("format")
    c.eq("anchos realineados", app.text().split("\n")[4:10], F)
    box_over(TH % 1, "se sigue en la misma celda")
    app.key("Escape"); app.wait_js("return !%s" % BOX)
    c.ok("la mini-barra se esconde al cerrar", app.js("return getComputedStyle(%s).display === 'none'" % BAR))
    # 3) insertar fila debajo (barra) desde Login: fila vacia y el cajon pasa a ella
    open_cell(TD % (1, 1))
    c.ok("borrar fila habilitado en el cuerpo", not app.js("return %s.querySelector('button[data-op=\"rowDelete\"]').disabled" % BAR))
    bar_click("rowBelow")
    c.eq("fila vacia debajo de Login", app.line(8), "|            |       |          |")
    box_over(TD % (2, 1), "el cajon pasa a la fila nueva")
    app.type("Nueva"); app.key("Tab")
    c.eq("se escribe en la fila nueva", app.line(8), "| Nueva |       |          |")
    box_over(TD % (2, 2), "Tab sigue en la fila nueva")
    app.key("Escape"); app.wait_js("return !%s" % BOX)
    # 4) menu del clic derecho sin celda abierta: eliminar columna; Ctrl+Z la devuelve en un paso
    right_click(TD % (3, 3))
    c.eq("menu con todas las operaciones", app.js("return %s.querySelectorAll('.item').length" % MENU), 15)
    c.ok("alineacion actual de la columna marcada", app.js("return %s.querySelector('.item[data-op=\"alignRight\"]').classList.contains('on')" % MENU))
    c.ok("subir fila procede en la fila 3", not app.js("return %s.querySelector('.item[data-op=\"rowUp\"]').classList.contains('off')" % MENU))
    app.key("Escape")
    c.ok("Esc cierra el menu", not menu_visible())
    c.ok("y sigue en edicion", app.js("return !!document.querySelector('#editor .cm-editor')"))
    right_click(TD % (3, 3)); menu_click("colDelete")
    c.eq("columna eliminada (cabecera)", app.line(5), "| Épica      | Prio  |")
    c.eq("columna eliminada (ultima fila)", app.line(11), "| Con `a\\|b` | baja  |")
    c.ok("sin celda abierta no se abre el cajon", not app.js("return !!%s && %s.isConnected" % (BOX, BOX)))
    app.key("ctrl+z")
    c.eq("Ctrl+Z deshace la operacion entera", app.line(5), "| Épica      | Prio  |   Estado |")
    c.eq("y solo esa", app.line(8), "| Nueva |       |          |")
    # 5) atajos en el cajon: Alt+arriba sube la fila (y el cajon con ella); Ctrl+Intro = salto de
    #    linea dentro de la celda: <br> en la fuente, salto visual en el cajon y el caret en la linea de abajo
    open_cell(TD % (3, 1)); app.key("alt+Up")
    c.eq("Alt+arriba: Pagos sube", app.line(8), "| Pagos      | media |          |")
    c.eq("y Nueva baja (re-alineada)", app.line(9), "| Nueva      |       |          |")
    box_over(TD % (2, 1), "el cajon sigue a la fila")
    app.key("End"); app.key("ctrl+Return")
    br = app.js("""const v = CM.view.EditorView.findFromDOM(document.querySelector('.cm-cell-editor .cm-editor')), d = v.state.doc.toString();
      const a = v.coordsAtPos(0), z = v.coordsAtPos(d.length), ln = document.querySelector('.cm-cell-editor .cm-line').getBoundingClientRect().height;
      return { text: d, caret: v.state.selection.main.head, brk: !!document.querySelector('.cm-cell-editor .cm-brk'), down: (z && a) ? z.top - a.top : 0, lineH: ln }""")
    c.ok("Ctrl+Intro: <br> en la fuente de la celda y el caret detras", br["text"] == "Pagos<br>" and br["caret"] == 9, str(br))
    c.ok("y salto visual: el caret ya esta en la linea de abajo", br["brk"] and (br["down"] > 10 or br["lineH"] > 34), str(br))
    app.key("Return")   # confirma y baja a la fila siguiente
    c.eq("el .md lleva el <br> (confirmar una celda no re-alinea: conserva su relleno)", app.line(8), "| Pagos<br>      | media |          |")
    box_over(TD % (3, 1), "y el cajon en la fila de abajo")
    # 6) Esc con el menu abierto (clic derecho en el cajon) cierra solo el menu
    r = app.rect(BOX); app.click(r["l"] + 8, r["t"] + r["h"] / 2, button=3)
    app.wait_js("const m = %s; return !!m && getComputedStyle(m).display !== 'none'" % MENU)
    app.key("Escape")
    c.ok("Esc cierra el menu y deja el cajon", not menu_visible() and app.js("return !!%s && %s.isConnected" % (BOX, BOX)))
    app.key("Escape"); app.wait_js("return !%s" % BOX)
    # 7) alinear la columna desde el menu (cabecera)
    right_click(TH % 1); menu_click("alignCenter")
    c.eq("columna centrada", app.line(6), "| :--------: | :---: | -------: |")
    # 8) Tab en la ultima celda anade una fila y sigue en su primera celda
    n = app.js("return document.querySelectorAll('#editor table tbody tr').length")
    open_cell(TD % (n, 3)); app.key("Tab")
    c.eq("Tab al final: fila nueva", app.js("return document.querySelectorAll('#editor table tbody tr').length"), n + 1)
    box_over(TD % (n + 1, 1), "y el cajon en su primera celda")
    c.eq("la fila nueva esta vacia", app.line(6 + n + 1), "|            |       |          |")
    app.key("Escape"); app.wait_js("return !%s" % BOX)
finally:
    app.close()
c.finish()
