#!/usr/bin/env python3
"""Titulo de la ventana: 'nombre - dd/mm/aaaa HH:MM - mdlive', y se refresca al cambiar el .md."""
import datetime
import os
import time
from mdlive_test import App, Check

app, c = App("join.md"), Check()
try:
    stamp = datetime.datetime.fromtimestamp(app.md.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
    c.eq("titulo al abrir", app.title(), "%s - %s - mdlive" % (app.md.name, stamp))
    t = time.mktime((2024, 3, 4, 9, 7, 0, 0, 0, -1))
    os.utime(app.md, (t, t))
    time.sleep(1)
    c.eq("titulo tras cambio externo", app.title(), "%s - 04/03/2024 09:07 - mdlive" % app.md.name)
finally:
    app.close()
c.finish()
