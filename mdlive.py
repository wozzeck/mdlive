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
import json
import time
import pathlib
import subprocess
import urllib.parse
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gtk, WebKit2, Gio, GLib, Gdk  # noqa: E402

APP_DIR = pathlib.Path(__file__).resolve().parent

# Historial persistente de documentos abiertos (MRU) y registro de ventanas vivas.
_DATA_HOME = pathlib.Path(os.environ.get("XDG_DATA_HOME") or (pathlib.Path.home() / ".local/share"))
RECENT_FILE = _DATA_HOME / "mdlive" / "recent.json"
RECENT_MAX = 50
# Instancias vivas (efimero): cada ventana publica {path,pid,xid} para "enfocar si ya esta abierto".
_RUN_HOME = pathlib.Path(os.environ.get("XDG_RUNTIME_DIR")
                         or os.environ.get("XDG_CACHE_HOME")
                         or (pathlib.Path.home() / ".cache"))
INSTANCES_DIR = _RUN_HOME / "mdlive" / "instances"


def _pid_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # existe pero de otro usuario
    except OSError:
        return False
    return True


def record_recent(md_path):
    """Inserta md_path al frente del MRU (dedup por ruta, recorta a RECENT_MAX). Best-effort."""
    p = str(md_path)
    try:
        RECENT_FILE.parent.mkdir(parents=True, exist_ok=True)
        items = []
        if RECENT_FILE.exists():
            try:
                items = json.loads(RECENT_FILE.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                items = []
        if not isinstance(items, list):
            items = []
        items = [it for it in items if isinstance(it, dict) and it.get("path") != p]
        items.insert(0, {"path": p, "name": md_path.name, "ts": time.time()})
        items = items[:RECENT_MAX]
        tmp = RECENT_FILE.with_name("recent.json.%d.tmp" % os.getpid())
        tmp.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, RECENT_FILE)
    except OSError:
        pass


def forget_recent(md_path):
    """Elimina md_path del MRU (no toca el fichero en disco). Best-effort."""
    p = str(md_path)
    try:
        if not RECENT_FILE.exists():
            return
        items = json.loads(RECENT_FILE.read_text(encoding="utf-8"))
        if not isinstance(items, list):
            return
        items = [it for it in items if isinstance(it, dict) and it.get("path") != p]
        tmp = RECENT_FILE.with_name("recent.json.%d.tmp" % os.getpid())
        tmp.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, RECENT_FILE)
    except (ValueError, OSError):
        pass


def live_instances():
    """{path: {path,pid,xid}} de ventanas vivas; de paso limpia las de PIDs muertos."""
    out = {}
    try:
        files = list(INSTANCES_DIR.glob("*.json"))
    except OSError:
        return out
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            try:
                f.unlink()
            except OSError:
                pass
            continue
        if not isinstance(d, dict) or not _pid_alive(d.get("pid")):
            try:
                f.unlink()
            except OSError:
                pass
            continue
        if d.get("path"):
            out[d["path"]] = d
    return out


def most_recent_existing():
    """Ruta del documento mas reciente del MRU que todavia existe en disco, o None."""
    try:
        items = json.loads(RECENT_FILE.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    if not isinstance(items, list):
        return None
    items = [it for it in items if isinstance(it, dict) and it.get("path")]
    items.sort(key=lambda it: it.get("ts") or 0, reverse=True)  # mas reciente primero
    for it in items:
        if os.path.exists(it["path"]):
            return it["path"]
    return None


def pick_file_dialog():
    """Selector GTK para elegir un .md (cuando no hay historial util). None si se cancela."""
    dlg = Gtk.FileChooserDialog(title="Abrir Markdown", action=Gtk.FileChooserAction.OPEN)
    dlg.add_buttons("_Cancelar", Gtk.ResponseType.CANCEL, "_Abrir", Gtk.ResponseType.ACCEPT)
    flt = Gtk.FileFilter()
    flt.set_name("Markdown")
    for pat in ("*.md", "*.markdown", "*.mkd", "*.mdown", "*.mdwn"):
        flt.add_pattern(pat)
    dlg.add_filter(flt)
    flt_all = Gtk.FileFilter()
    flt_all.set_name("Todos los ficheros")
    flt_all.add_pattern("*")
    dlg.add_filter(flt_all)
    target = dlg.get_filename() if dlg.run() == Gtk.ResponseType.ACCEPT else None
    dlg.destroy()
    return target


def display_dir(dirpath):
    """Directorio para mostrar en el panel: '~' si es el home; relativo a el (sin '~/')
    si cuelga del home; absoluto en cualquier otro caso. Siempre termina en '/'."""
    home = str(pathlib.Path.home())
    if dirpath == home:
        d = "~"
    elif dirpath.startswith(home + os.sep):
        d = dirpath[len(home) + 1:]
    else:
        d = dirpath
    return d if d.endswith("/") else d + "/"

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

        # canal JS -> nativo para guardar lo editado y para abrir/enfocar otros documentos
        self.ucm = WebKit2.UserContentManager()
        self.ucm.register_script_message_handler("mdliveSave")
        self.ucm.connect("script-message-received::mdliveSave", self.on_save_message)
        self.ucm.register_script_message_handler("mdliveOpen")
        self.ucm.connect("script-message-received::mdliveOpen", self.on_open_message)
        self.ucm.register_script_message_handler("mdliveCopy")
        self.ucm.connect("script-message-received::mdliveCopy", self.on_copy_message)
        self.ucm.register_script_message_handler("mdliveForget")
        self.ucm.connect("script-message-received::mdliveForget", self.on_forget_message)

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

        # historial MRU + alta/baja de la ventana en el registro de instancias vivas
        record_recent(self.md_path)
        self._inst_file = INSTANCES_DIR / ("%d.json" % os.getpid())
        self.connect("realize", lambda *_: self._register_instance())
        self.connect("destroy", self._on_destroy)

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

    # ---- copiar texto (ruta) al portapapeles del sistema (peticion del panel) ----
    def on_copy_message(self, ucm, js_result):
        try:
            text = js_result.get_js_value().to_string()
        except Exception:
            try:
                text = js_result.get_value().to_string()
            except Exception:
                return
        if not text:
            return
        try:
            cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            cb.set_text(text, -1)
            cb.store()  # conservar el contenido tras cerrar la ventana
        except Exception as e:
            print("mdlive: no se pudo copiar al portapapeles: %s" % e, file=sys.stderr)

    # ---- quitar un documento del historial de recientes (peticion del panel) ----
    def on_forget_message(self, ucm, js_result):
        try:
            target = js_result.get_js_value().to_string()
        except Exception:
            try:
                target = js_result.get_value().to_string()
            except Exception:
                return
        if target:
            forget_recent(target)

    # ---- registro de instancias vivas (para enfocar la ventana ya abierta) ----
    def _register_instance(self):
        try:
            gdkwin = self.get_window()
            xid = int(gdkwin.get_xid()) if gdkwin and hasattr(gdkwin, "get_xid") else 0
        except Exception:
            xid = 0
        try:
            INSTANCES_DIR.mkdir(parents=True, exist_ok=True)
            self._inst_file.write_text(json.dumps(
                {"path": str(self.md_path), "pid": os.getpid(), "xid": xid}), encoding="utf-8")
        except OSError:
            pass

    def _on_destroy(self, *_):
        try:
            self._inst_file.unlink()
        except OSError:
            pass
        Gtk.main_quit()

    # ---- abrir/enfocar otro documento (peticion del panel de recientes) ----
    def on_open_message(self, ucm, js_result):
        try:
            target = js_result.get_js_value().to_string()
        except Exception:
            try:
                target = js_result.get_value().to_string()
            except Exception:
                return
        if target:
            self._open_or_focus(target)

    def _open_or_focus(self, target):
        live = live_instances()
        inst = live.get(target) or live.get(str(pathlib.Path(target).resolve()))
        if inst and self._focus_xid(inst.get("xid")):
            return
        if os.path.exists(target):
            try:
                subprocess.Popen([sys.executable, str(APP_DIR / "mdlive.py"), target],
                                 start_new_session=True)
            except OSError as e:
                print("mdlive: no se pudo abrir %s: %s" % (target, e), file=sys.stderr)

    @staticmethod
    def _focus_xid(xid):
        try:
            xid = int(xid)
        except (TypeError, ValueError):
            return False
        if xid <= 0:
            return False
        for cmd in (["wmctrl", "-i", "-a", "0x%08x" % xid], ["xdotool", "windowactivate", str(xid)]):
            try:
                if subprocess.run(cmd, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL).returncode == 0:
                    return True
            except OSError:
                continue
        return False

    def _recent_payload(self):
        try:
            raw = json.loads(RECENT_FILE.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            raw = []
        live = live_instances()
        items = []
        for it in (raw if isinstance(raw, list) else []):
            if not isinstance(it, dict):
                continue
            p = it.get("path")
            if not p:
                continue
            items.append({
                "path": p,
                "name": it.get("name") or os.path.basename(p),
                "dir": display_dir(os.path.dirname(p)),
                "exists": os.path.exists(p),
                "open": p in live,
                "ts": it.get("ts"),
            })
        # mas reciente primero; los items sin marca de tiempo quedan al final
        items.sort(key=lambda x: x.get("ts") or 0, reverse=True)
        return {"current": str(self.md_path), "items": items}

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
        elif path == "mddir":
            data, mime = str(self.md_path.parent).encode("utf-8"), "text/plain; charset=utf-8"
        elif path == "recent":
            data, mime = json.dumps(self._recent_payload(), ensure_ascii=False).encode("utf-8"), MIME[".json"]
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
    _MD_EXTS = (".md", ".markdown", ".mkd", ".mdown", ".mdwn")

    def _md_target_from_app_uri(self, uri):
        """Si la URI app:// de un enlace apunta a un .md, devuelve su ruta absoluta
        en disco (relativa al dir del .md actual); si no, None. Red de seguridad para
        clics que no pasan por el handler del visor (p.ej. previews del editor)."""
        if not uri.startswith("app://local/"):
            return None
        path = uri.split("app://local/", 1)[-1].split("?", 1)[0].split("#", 1)[0]
        path = urllib.parse.unquote(path)
        if not path or not path.lower().endswith(self._MD_EXTS):
            return None
        if path.startswith("_abs/"):
            return path[len("_abs/"):]
        return str((self.md_path.parent / path).resolve())

    def on_decide_policy(self, webview, decision, decision_type):
        T = WebKit2.PolicyDecisionType
        if decision_type == T.NAVIGATION_ACTION:
            nav = decision.get_navigation_action()
            uri = nav.get_request().get_uri()
            if nav.get_navigation_type() == WebKit2.NavigationType.LINK_CLICKED:
                if not uri.startswith("app://"):
                    decision.ignore()
                    self._open_external(uri)
                    return True
                md = self._md_target_from_app_uri(uri)
                if md:  # enlace a otro .md -> abrir/enfocar en mdlive, no servir crudo
                    decision.ignore()
                    self._open_or_focus(md)
                    return True
        elif decision_type == T.NEW_WINDOW_ACTION:
            nav = decision.get_navigation_action()
            uri = nav.get_request().get_uri()
            decision.ignore()
            md = self._md_target_from_app_uri(uri)
            if md:
                self._open_or_focus(md)
            elif not uri.startswith("app://"):
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
    if len(sys.argv) >= 2:
        target = sys.argv[1]
        if not os.path.exists(target):
            print("No existe: %s" % target, file=sys.stderr)
            sys.exit(1)
    else:
        # sin fichero (p.ej. icono del menu): abrir el mas reciente; si no hay, selector
        target = most_recent_existing() or pick_file_dialog()
        if not target:
            sys.exit(0)  # historial vacio y dialogo cancelado: nada que abrir
    win = MdLive(target)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
