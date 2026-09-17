#!/usr/bin/env python3
"""Codigo en FUENTE (bloque en edicion): `codigo` sale en la letra monoespaciada del visor, con
los acentos graves a la vista, y el texto de un bloque de codigo tambien; la negrita del mismo
parrafo sigue en negrita. (Correccion del 17-sep-2026: el estilo por defecto de CodeMirror no
trae nada para `monospace`.)"""
from mdlive_test import App, Check

app, c = App("codigo.md"), Check()
def source_of(block_expr):
    r = app.rect(block_expr)
    app.click(r["l"] + 20, r["t"] + r["h"] / 2)
try:
    app.edit_mode()
    body = app.js("return getComputedStyle(document.body).fontFamily")
    # parrafo con codigo en linea y negrita -> a fuente
    source_of("[...document.querySelectorAll('#editor .cm-mdblock')].find((d) => d.querySelector('p > code'))")
    app.wait_js("return !!document.querySelector('#editor .cm-mdcode')")
    info = app.js("""const code = document.querySelector('#editor .cm-mdcode');
      const strong = [...document.querySelectorAll('#editor .cm-line span')].find((s) => s.textContent === 'negrita');
      return { text: code.textContent, font: getComputedStyle(code).fontFamily, weight: strong ? getComputedStyle(strong).fontWeight : null };""")
    c.eq("codigo en linea entero, con los acentos graves", info["text"], "`código en línea`")
    c.ok("en monoespaciada", "mono" in info["font"].lower(), "font-family %s" % info["font"])
    c.ok("distinta de la letra del texto", info["font"] != body, "%s vs %s" % (info["font"], body))
    c.ok("la negrita del parrafo sigue en negrita", info["weight"] is not None and int(info["weight"]) >= 600, "font-weight %s" % info["weight"])
    # bloque de codigo -> a fuente: su texto en monoespaciada
    source_of("[...document.querySelectorAll('#editor .cm-mdblock')].find((d) => d.querySelector('pre'))")
    app.wait_js("return !!document.querySelector('#editor .cm-mdcodetext')")
    blk = app.js("const t = document.querySelector('#editor .cm-mdcodetext'); return { text: t.textContent, font: getComputedStyle(t).fontFamily }")
    c.eq("texto del bloque de codigo", blk["text"], "const x = 1;")
    c.ok("en monoespaciada", "mono" in blk["font"].lower(), "font-family %s" % blk["font"])
finally:
    app.close()
c.finish()
