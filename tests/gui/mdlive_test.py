#!/usr/bin/env python3
"""Arnes de pruebas de integracion de mdlive.

Lanza la aplicacion DE VERDAD (GTK + WebKit) sobre una copia de un fixture, aislada del
usuario: XDG_DATA_HOME / XDG_CACHE_HOME / XDG_RUNTIME_DIR apuntan a un directorio temporal
(recientes, registro de instancias y localStorage propios). Las teclas y el raton se meten
con xdotool (entrada real), las capturas se hacen con `import` (ImageMagick) y el DOM se
consulta por el canal de pruebas de mdlive.py (MDLIVE_TEST_DIR: ficheros cmd-*.js /
res-*.json, sin sockets).

Requiere: DISPLAY (por defecto :0), xdotool, imagemagick, python3-pil.
Uso en un test:
    app = App('tabla.md'); c = Check()
    app.key('e'); app.wait_js("return !!document.querySelector('#editor .cm-editor')")
    r = app.rect("document.querySelector('#editor td')"); app.click(r['l'] + 10, r['t'] + 10)
    c.eq('...', app.js("return document.title"), '...'); app.close(); c.finish()
Las coordenadas CSS de la pagina coinciden con las de la ventana (el webview ocupa toda la
ventana, zoom 1), asi que un rect del DOM se puede pinchar directamente con xdotool.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"
DISPLAY = os.environ.get("DISPLAY", ":0")


class Check:
    """Acumula comprobaciones; finish() resume y sale con 1 si alguna fallo."""

    def __init__(self):
        self.total = 0
        self.failed = 0

    def ok(self, name, cond, detail=""):
        self.total += 1
        if not cond:
            self.failed += 1
        print(("  ok   " if cond else "  FAIL ") + name + ("" if cond or not detail else "  (%s)" % detail), flush=True)

    def eq(self, name, got, want):
        self.ok(name, got == want, "obtenido %r, esperado %r" % (got, want))

    def close(self, name, got, want, tol=0.5):
        self.ok(name, got is not None and abs(got - want) <= tol, "obtenido %r, esperado %r ±%s" % (got, want, tol))

    def finish(self):
        print(("%d de %d FALLAN" % (self.failed, self.total)) if self.failed else ("%d pruebas, todo ok" % self.total), flush=True)
        sys.exit(1 if self.failed else 0)


class App:
    def __init__(self, fixture, size=(1100, 900)):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="mdlive-test-"))
        for d in ("data", "cache", "run", "cmd"):
            (self.tmp / d).mkdir()
        src = pathlib.Path(fixture) if os.path.isabs(str(fixture)) else FIXTURES / fixture
        self.md = self.tmp / src.name
        shutil.copy(src, self.md)
        env = dict(os.environ, DISPLAY=DISPLAY, XDG_DATA_HOME=str(self.tmp / "data"), XDG_CACHE_HOME=str(self.tmp / "cache"),
                   XDG_RUNTIME_DIR=str(self.tmp / "run"), MDLIVE_TEST_DIR=str(self.tmp / "cmd"))
        self.log = (self.tmp / "app.log").open("w")
        self.proc = subprocess.Popen([sys.executable, str(ROOT / "mdlive.py"), str(self.md)], env=env,
                                     stdout=self.log, stderr=subprocess.STDOUT, start_new_session=True)
        self._cmd_id = 0
        self.win = self._find_window()
        self.xdo("windowsize", "--sync", self.win, str(size[0]), str(size[1]))
        self.activate()
        self.wait_js("return !!window.__mdlive && document.getElementById('content').children.length > 0", 15)
        time.sleep(0.3)

    # ---- proceso / ventana --------------------------------------------------
    def _find_window(self):
        deadline = time.time() + 20
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError("mdlive termino al arrancar; ver " + str(self.tmp / "app.log"))
            try:
                ids = subprocess.run(["xdotool", "search", "--pid", str(self.proc.pid)], env={"DISPLAY": DISPLAY},
                                     capture_output=True, text=True).stdout.split()
            except OSError as e:
                raise RuntimeError("hace falta xdotool: %s" % e)
            for w in ids:
                if self.md.name in self.xdo("getwindowname", w):
                    return w
            time.sleep(0.2)
        raise RuntimeError("no aparece la ventana de mdlive")

    def xdo(self, *args):
        return subprocess.run(["xdotool", *args], env={"DISPLAY": DISPLAY}, capture_output=True, text=True).stdout.strip()

    def activate(self):
        self.xdo("windowactivate", "--sync", self.win)
        time.sleep(0.15)

    def title(self):
        return self.xdo("getwindowname", self.win)

    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.log.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---- entrada real -------------------------------------------------------
    def key(self, *keys, delay=0.15):
        self.xdo("key", "--delay", "40", *keys)
        time.sleep(delay)

    def type(self, text, delay=0.2):
        subprocess.run(["xdotool", "type", "--delay", "25", "--file", "-"], input=text, text=True, env={"DISPLAY": DISPLAY})
        time.sleep(delay)

    def move(self, x, y):
        self.xdo("mousemove", "--window", self.win, str(int(round(x))), str(int(round(y))))

    def click(self, x, y, button=1, mods=(), delay=0.5):
        self.move(x, y)
        for m in mods:
            self.xdo("keydown", m)
        self.xdo("click", str(button))
        for m in mods:
            self.xdo("keyup", m)
        time.sleep(delay)

    # ---- DOM ----------------------------------------------------------------
    def js(self, body, timeout=8):
        """Ejecuta `body` (cuerpo de funcion, con return) en la pagina y devuelve el valor (JSON)."""
        self._cmd_id += 1
        cid = "%d-%d" % (os.getpid(), self._cmd_id)
        code = ("(function(){ try { return JSON.stringify({v: (function(){ " + body + " })()}); }"
                " catch (e) { return JSON.stringify({e: String(e && e.stack || e)}); } })()")
        tmp = self.tmp / "cmd" / ("tmp-%s.js" % cid)
        tmp.write_text(code, encoding="utf-8")
        os.replace(tmp, self.tmp / "cmd" / ("cmd-%s.js" % cid))
        res = self.tmp / "cmd" / ("res-%s.json" % cid)
        deadline = time.time() + timeout
        while not res.exists():
            if time.time() > deadline:
                raise TimeoutError("sin respuesta de la pagina a: " + body[:80])
            time.sleep(0.03)
        out = json.loads(res.read_text(encoding="utf-8"))
        res.unlink()
        if "e" in out:
            raise RuntimeError("JS: " + out["e"])
        return out.get("v")

    def wait_js(self, cond_body, timeout=5):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.js(cond_body):
                return True
            time.sleep(0.1)
        raise TimeoutError("condicion no cumplida: " + cond_body[:80])

    def rect(self, expr):
        """{l, t, r, b, w, h} del elemento que devuelve la expresion JS (coordenadas de ventana)."""
        return self.js("const el = (%s); if (!el) return null; const r = el.getBoundingClientRect();"
                       " return {l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height};" % expr)

    # ---- fichero y capturas -------------------------------------------------
    def text(self, settle=0.8):
        """Contenido del .md. La app guarda 500 ms despues del ultimo cambio: se espera antes de leer."""
        if settle:
            time.sleep(settle)
        return self.md.read_text(encoding="utf-8")

    def line(self, n, settle=0.8):
        return self.text(settle).split("\n")[n - 1]

    def set_text(self, text):
        self.md.write_text(text, encoding="utf-8")
        time.sleep(0.6)

    def shot(self):
        from PIL import Image
        p = self.tmp / "shot.png"
        subprocess.run(["import", "-window", self.win, str(p)], env={"DISPLAY": DISPLAY})
        return Image.open(p).convert("RGB")

    # ---- atajos de alto nivel -----------------------------------------------
    def edit_mode(self):
        self.click(600, 700)   # foco al webview
        self.key("e")
        self.wait_js("return !!document.querySelector('#editor .cm-editor')")
        time.sleep(0.4)


def diff_pixels(a, b, box=None, thresh=40):
    """(n, franjas): pixeles que difieren (algun canal > thresh) entre dos capturas, en el
    recorte box, y las franjas verticales [y0, y1, px] donde estan (para saber que es)."""
    from PIL import ImageChops
    if box:
        a, b = a.crop(box), b.crop(box)
    d = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > thresh else 0)
    w, h = d.size
    px = d.load()
    rows = [sum(1 for x in range(w) if px[x, y]) for y in range(h)]
    bands, start = [], None
    for y, v in enumerate(rows + [0]):
        if v and start is None:
            start = y
        elif not v and start is not None:
            bands.append([start, y - 1, sum(rows[start:y])])
            start = None
    return sum(rows), bands
