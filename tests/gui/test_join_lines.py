#!/usr/bin/env python3
"""Unir lineas: boton en la esquina del bloque solo si hay saltos que unir; Ctrl+J el bloque;
Ctrl+Shift+J todo el documento; Ctrl+Z lo deshace de golpe."""
import time
from mdlive_test import App, Check, FIXTURES

app, c = App("join.md"), Check()
try:
    app.edit_mode()
    p = app.rect("document.querySelectorAll('#editor .cm-mdblock')[0]")   # el parrafo partido (el h1 esta en fuente)
    app.click(p["l"] + 40, p["t"] + 10)
    app.wait_js("return !!document.querySelector('#editor .cm-joinbtn')")
    c.ok("boton 'unir lineas' en el bloque partido", True)
    app.key("ctrl+j"); time.sleep(0.8)
    c.eq("Ctrl+J une el bloque", app.line(3), "Este es un párrafo partido a mano en varias líneas, como hacen muchos editores al envolver a ochenta columnas, de modo que en el visor se ve de una pieza pero en la fuente son cuatro líneas distintas.")
    c.ok("y el boton desaparece", not app.js("return !!document.querySelector('#editor .cm-joinbtn')"))
    app.key("ctrl+shift+j"); time.sleep(0.8)
    c.eq("Ctrl+Shift+J respeta el salto duro", app.line(5), "Este otro párrafo tiene un salto duro al final de esta línea  ")
    c.eq("y une el resto del parrafo", app.line(6), "y por tanto la segunda línea debe seguir separada, aunque la tercera sí se puede unir a la segunda.")
    c.eq("cita unida", app.line(8), "> Una cita también partida en dos líneas.")
    c.eq("item unido", app.line(10), "- Un ítem de lista con continuación en la línea siguiente")
    app.key("ctrl+z"); app.key("ctrl+z"); time.sleep(0.8)
    c.ok("Ctrl+Z x2 devuelve el original", app.text() == (FIXTURES / "join.md").read_text(encoding="utf-8"))
finally:
    app.close()
c.finish()
