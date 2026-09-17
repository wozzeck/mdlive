#!/bin/bash
# Suite completa de mdlive: unitarios (node, sin dependencias) e integracion (la app real
# sobre X11: DISPLAY, xdotool, imagemagick, python3-pil). `tests/run.sh unit` solo unitarios.
cd "$(dirname "$0")/.." || exit 2
fail=0
node tests/unit/run.js || fail=1
if [ "$1" != "unit" ]; then
  for t in tests/gui/test_*.py; do
    echo "## $t"
    python3 "$t" || fail=1
  done
fi
[ $fail = 0 ] && echo "SUITE OK" || echo "SUITE CON FALLOS"
exit $fail
