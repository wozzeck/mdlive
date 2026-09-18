#!/usr/bin/env python3
"""El fichero cambia en disco mientras está abierto. En el visor se recarga solo (live reload de
siempre). En modo edición, si aquí no hay nada que perder el editor adopta lo del disco sin molestar;
si se ha escrito algo, sale el aviso «El fichero ha cambiado fuera del editor» con «Recargar» (trae el
disco y descarta lo escrito) y «Seguir editando» (no toca nada), y hasta entonces el buffer se queda
como está. Al salir de edición sin haber tocado nada vale lo del disco: antes la ventana se quedaba
enseñando una versión que ya no existía y nada la refrescaba."""
import time
from mdlive_test import App, Check

app, c = App("join.md"), Check()
VIEW = "Párrafo del visor."
def bar():
    return app.js("const b = document.getElementById('extbar');"
                  " return { open: document.body.classList.contains('ext-open'), txt: b.querySelector('span').textContent,"
                  " vis: b.getBoundingClientRect().height > 10 }")
def doc():
    return app.js("const e = document.querySelector('#editor .cm-editor'), v = e && CM.view.EditorView.findFromDOM(e); return v ? v.state.doc.toString() : null")
def wait_for(cond, t=6):
    try:
        app.wait_js(cond, t); return True
    except TimeoutError:
        return False
def click_el(sel):
    r = app.rect("document.querySelector(%r)" % sel)
    app.click(r["l"] + r["w"] / 2, r["t"] + r["h"] / 2)
def type_in_editor(txt):
    app.js("const v = CM.view.EditorView.findFromDOM(document.querySelector('#editor .cm-editor'));"
           " v.dispatch({ changes: { from: v.state.doc.length, insert: %r } }); return 1" % ("\n\n" + txt + "\n"))
    time.sleep(1.0)   # el guardado va con 500 ms de retardo
def outside(marker):
    """Reescribe el fichero desde fuera (como haría otro editor u otra sesión)."""
    app.set_text(base.replace(VIEW, marker))
try:
    # 1) visor: el live reload de siempre
    app.set_text(app.text(0).rstrip("\n") + "\n\n" + VIEW + "\n")
    c.ok("visor: el cambio en disco se recarga solo", wait_for("return document.getElementById('content').textContent.includes(%r)" % VIEW))
    base = app.text(0)
    # 2) en edición sin tocar nada: se adopta el disco sin molestar
    app.edit_mode()
    c.ok("al entrar en edición el buffer es el del disco", VIEW in (doc() or ""))
    outside("Cambiado desde fuera.")
    c.ok("edición sin tocar nada: el editor adopta lo del disco", wait_for("const e = document.querySelector('#editor .cm-editor'), v = CM.view.EditorView.findFromDOM(e); return v.state.doc.toString().includes('Cambiado desde fuera.')"))
    c.ok("y no molesta con ningún aviso", not bar()["open"])
    # 3) con algo escrito: aviso, y el buffer intacto
    type_in_editor("Lo que estoy escribiendo.")
    c.ok("lo escrito se guarda en disco", "Lo que estoy escribiendo." in app.text(0))
    outside("Otro cambio de fuera.")
    c.ok("con algo escrito sale el aviso", wait_for("return document.body.classList.contains('ext-open')"))
    b = bar()
    c.eq("el aviso dice lo que pasa", b["txt"], "El fichero ha cambiado fuera del editor")
    c.ok("y se ve de verdad", b["vis"])
    d = doc()
    c.ok("el buffer NO se toca hasta que se decida", "Lo que estoy escribiendo." in d and "Otro cambio de fuera." not in d)
    # 4) «Seguir editando»: quita el aviso y deja el buffer como está
    click_el("#ext-keep"); time.sleep(0.4)
    c.ok("«Seguir editando» quita el aviso sin tocar el buffer", not bar()["open"] and "Lo que estoy escribiendo." in doc())
    # 5) salir de edición sin tocar nada más: manda el disco (y no se pisa el fichero)
    app.key("Escape"); time.sleep(0.8)
    c.ok("sale de edición", not app.js("return document.body.classList.contains('edit-mode')"))
    c.ok("el visor enseña lo que hay en disco, no la versión vieja",
         app.js("return document.getElementById('content').textContent.includes('Otro cambio de fuera.')"))
    c.ok("y el fichero conserva el cambio de fuera (no se ha pisado)", "Otro cambio de fuera." in app.text() and "Lo que estoy escribiendo." not in app.text(0))
    # 6) «Recargar»: trae el disco y descarta lo escrito
    app.edit_mode()
    type_in_editor("Esto se va a descartar.")
    outside("Versión del disco.")
    c.ok("vuelve a avisar", wait_for("return document.body.classList.contains('ext-open')"))
    click_el("#ext-reload"); time.sleep(0.8)
    d = doc()
    c.ok("«Recargar» trae el disco y descarta lo escrito", "Versión del disco." in d and "Esto se va a descartar." not in d)
    c.ok("y quita el aviso", not bar()["open"])
    time.sleep(1.2)
    c.ok("recargar no reescribe el fichero", "Esto se va a descartar." not in app.text(0) and "Versión del disco." in app.text(0))
    # 7) Esc quita el aviso si está a la vista (y no sale de edición)
    outside("Un cambio más.")
    type_in_editor("Escrito otra vez.")
    outside("Y otro cambio más.")
    if wait_for("return document.body.classList.contains('ext-open')"):
        app.key("Escape"); time.sleep(0.5)
        c.ok("Esc quita el aviso sin salir de edición", not bar()["open"] and app.js("return document.body.classList.contains('edit-mode')"))
    else:
        c.ok("Esc quita el aviso sin salir de edición", False, "no salió el aviso")
finally:
    app.close()
c.finish()
