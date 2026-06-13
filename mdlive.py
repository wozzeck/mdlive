#!/usr/bin/env python3
"""mdlive - visor/editor de Markdown nativo (GTK3 + WebKit2). Sin servidor.

Uso: mdlive.py <archivo.md>

- Renderiza con el WebKit del sistema (ligero).
- Esquema interno app:// para servir el HTML/CSS/JS/markdown (sin sockets TCP).
- Live reload: vigila el .md, el style.css y el index.html y refresca al vuelo.
- Modo edicion (lapicero): live-preview por bloques; guarda al .md en disco.
- Enlaces externos -> navegador del sistema. Sin menu contextual.
"""
import os
import sys
import pathlib
import subprocess
import urllib.parse
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gtk, WebKit2, Gio, GLib  # noqa: E402

APP_DIR = pathlib.Path(__file__).resolve().parent

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".ico": "image/x-icon",
    ".avif": "image/avif",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
}


class MdLive(Gtk.Window):
    def __init__(self, md_path):
        super().__init__()
        self.md_path = pathlib.Path(md_path).resolve()
        self.set_default_size(1100, 900)
        self.set_title(self.md_path.name + " - mdlive")

        # icono de markdown (para barra de tareas / alt-tab)
        for name in ("icon.png", "icon.svg"):
            p = APP_DIR / name
            if p.exists():
                try:
                    self.set_icon_from_file(str(p))
                    break
                except Exception:
                    pass
        try:
            self.set_wmclass("mdlive", "mdlive")
        except Exception:
            pass

        # esquema propio app:// (en el contexto por defecto)
        ctx = WebKit2.WebContext.get_default()
        ctx.register_uri_scheme("app", self.on_app_request)
        ctx.get_security_manager().register_uri_scheme_as_cors_enabled("app")

        # canal JS -> nativo para guardar lo editado
        self.ucm = WebKit2.UserContentManager()
        self.ucm.register_script_message_handler("mdliveSave")
        self.ucm.connect("script-message-received::mdliveSave", self.on_save_message)

        self.webview = WebKit2.WebView.new_with_user_content_manager(self.ucm)
        st = self.webview.get_settings()
        st.set_enable_developer_extras(True)
        st.set_enable_write_console_messages_to_stdout(True)
        st.set_enable_smooth_scrolling(False)  # scroll directo
        self.webview.connect("decide-policy", self.on_decide_policy)
        self.webview.connect("context-menu", self.on_context_menu)  # solo "copiar enlace" en enlaces
        self.add(self.webview)
        self.webview.load_uri("app://local/index.html")

        # vigilancia por polling de mtime (robusto ante editores que renombran)
        self._mtimes = {}
        GLib.timeout_add(150, self._poll)

        self.connect("destroy", Gtk.main_quit)

    # ---- guardado de lo editado ----------------------------------------
    def on_save_message(self, ucm, js_result):
        try:
            text = js_result.get_js_value().to_string()
        except Exception:
            try:
                text = js_result.get_value().to_string()
            except Exception:
                return
        try:
            self.md_path.write_text(text, encoding="utf-8")
            # marca el mtime como propio para que el watcher NO recargue encima
            self._mtimes["md"] = os.stat(self.md_path).st_mtime_ns
        except OSError as e:
            print("mdlive: no se pudo guardar %s: %s" % (self.md_path, e), file=sys.stderr)

    # ---- handler del esquema app:// -------------------------------------
    def on_app_request(self, request, *user_data):
        uri = request.get_uri()
        path = uri.split("app://local/", 1)[-1].split("?", 1)[0].split("#", 1)[0]

        if path in ("", "index.html"):
            data, mime = self._read(APP_DIR / "index.html", b"<h1>falta index.html</h1>"), MIME[".html"]
        elif path == "style.css":
            data, mime = self._read(APP_DIR / "style.css", b"/* falta style.css */"), MIME[".css"]
        elif path == "raw":
            data, mime = self._read(self.md_path, b"# No se pudo leer el fichero"), "text/plain; charset=utf-8"
        elif path == "title":
            data, mime = self.md_path.name.encode("utf-8"), "text/plain; charset=utf-8"
        elif path.startswith("vendor/") and ".." not in path:
            f = APP_DIR / path
            data, mime = self._read(f, b""), MIME.get(f.suffix.lower(), "application/octet-stream")
        elif path.startswith("_abs/"):
            # imagen por ruta absoluta o file:// (la reescribe el frontend)
            f = pathlib.Path(urllib.parse.unquote(path[len("_abs/"):]))
            data, mime = self._read(f, b""), MIME.get(f.suffix.lower(), "application/octet-stream")
        else:
            # cualquier otra cosa = recurso (imagen, etc.) relativo al directorio del .md
            rel = urllib.parse.unquote(path)
            f = (self.md_path.parent / rel)
            data, mime = self._read(f, b""), MIME.get(f.suffix.lower(), "application/octet-stream")

        stream = Gio.MemoryInputStream.new_from_data(data)
        request.finish(stream, len(data), mime)

    @staticmethod
    def _read(p, fallback):
        try:
            return pathlib.Path(p).read_bytes()
        except OSError:
            return fallback

    # ---- menu contextual: solo "copiar enlace" cuando se pulsa sobre un enlace ----
    def on_context_menu(self, webview, context_menu, event, hit_test_result):
        if hit_test_result.context_is_link():
            context_menu.remove_all()
            try:
                item = WebKit2.ContextMenuItem.new_from_stock_action(
                    WebKit2.ContextMenuAction.COPY_LINK_TO_CLIPBOARD)
                context_menu.append(item)
            except Exception:
                return True
            return False  # mostrar nuestro menu minimo
        return True  # resto: sin menu contextual

    # ---- enlaces externos al navegador del sistema ----------------------
    def on_decide_policy(self, webview, decision, decision_type):
        T = WebKit2.PolicyDecisionType
        if decision_type == T.NAVIGATION_ACTION:
            nav = decision.get_navigation_action()
            uri = nav.get_request().get_uri()
            if nav.get_navigation_type() == WebKit2.NavigationType.LINK_CLICKED and not uri.startswith("app://"):
                decision.ignore()
                self._open_external(uri)
                return True
        elif decision_type == T.NEW_WINDOW_ACTION:
            nav = decision.get_navigation_action()
            uri = nav.get_request().get_uri()
            decision.ignore()
            if not uri.startswith("app://"):
                self._open_external(uri)
            return True
        return False

    @staticmethod
    def _open_external(uri):
        try:
            Gtk.show_uri_on_window(None, uri, 0)
        except Exception:
            try:
                Gio.AppInfo.launch_default_for_uri(uri, None)
            except Exception:
                try:
                    subprocess.Popen(["xdg-open", uri])
                except Exception:
                    pass

    # ---- live reload ----------------------------------------------------
    def _poll(self):
        for key, p in (("md", self.md_path), ("css", APP_DIR / "style.css"), ("html", APP_DIR / "index.html")):
            try:
                m = os.stat(p).st_mtime_ns
            except OSError:
                continue
            prev = self._mtimes.get(key)
            self._mtimes[key] = m
            if prev is not None and prev != m:
                if key == "html":
                    self.webview.reload()
                else:
                    fn = "reloadMd" if key == "md" else "reloadCss"
                    self._js("window.__mdlive && window.__mdlive.%s()" % fn)
        return True

    def _js(self, script):
        try:
            self.webview.run_javascript(script, None, None, None)
        except Exception:
            pass


def main():
    GLib.set_prgname("mdlive")
    GLib.set_application_name("mdlive")
    if len(sys.argv) < 2:
        print("Uso: mdlive <archivo.md>", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(sys.argv[1]):
        print("No existe: %s" % sys.argv[1], file=sys.stderr)
        sys.exit(1)
    win = MdLive(sys.argv[1])
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
