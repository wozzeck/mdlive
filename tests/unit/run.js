#!/usr/bin/env node
// Tests unitarios de mdlive, sin dependencias (node a pelo).
//
// index.html es un unico IIFE, asi que las funciones puras que se prueban van marcadas en el
// propio fuente con `// @test-begin <nombre>` ... `// @test-end`. Este runner carga el
// markdown-it vendorizado (el mismo que usa la app), extrae esos bloques, los evalua en un
// ambito comun con `md` y ejecuta cada tests/unit/*.test.js, que exporta function (t, api, h).
//   t.eq(nombre, obtenido, esperado) / t.ok(nombre, condicion)
//   api = las funciones de los bloques; h.md = markdown-it; h.mkDoc(texto) = Text de CM simulado
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.resolve(__dirname, '..', '..');

const ctx = { console }; ctx.window = ctx; ctx.self = ctx; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(ROOT, 'vendor/markdown-it.min.js'), 'utf8'), ctx);
vm.runInContext(fs.readFileSync(path.join(ROOT, 'vendor/markdown-it-task-lists.min.js'), 'utf8'), ctx);
const md = ctx.markdownit({ html: true, linkify: true, typographer: true });
md.use(ctx.markdownitTaskLists, { enabled: true, label: true });

const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const blocks = {};
for (const m of html.matchAll(/\/\/ @test-begin (\w+)\n([\s\S]*?)\/\/ @test-end/g)) blocks[m[1]] = m[2];
if (!Object.keys(blocks).length) { console.error('index.html: no hay bloques @test-begin'); process.exit(2); }
const code = Object.values(blocks).join('\n');
// nombres de primer nivel (sangria de 2 espacios: la del IIFE); lo de dentro va mas sangrado
const names = [...code.matchAll(/^  (?:function\s+(\w+)|(?:const|let)\s+(\w+)\s*=)/gm)].map((m) => m[1] || m[2]);
const api = new Function('md', code + '\nreturn {' + names.join(', ') + '};')(md);

// Text de CodeMirror simulado: lo justo que usan las funciones (lines, length, line, lineAt, sliceString)
function mkDoc(text) {
  const L = []; let pos = 0;
  text.split('\n').forEach((t, i) => { L.push({ from: pos, to: pos + t.length, text: t, number: i + 1 }); pos += t.length + 1; });
  return {
    lines: L.length, length: text.length, text,
    line: (n) => L[n - 1],
    lineAt: (p) => L.find((l) => p <= l.to) || L[L.length - 1],
    sliceString: (a, b) => text.slice(a, b),
    toString: () => text,
  };
}

let total = 0, failed = 0, file = '';
const t = {
  eq(name, got, want) {
    total++;
    const ok = JSON.stringify(got) === JSON.stringify(want);
    if (!ok) failed++;
    console.log((ok ? '  ok   ' : '  FAIL ') + name + (ok ? '' : '\n         obtenido: ' + JSON.stringify(got) + '\n         esperado: ' + JSON.stringify(want)));
  },
  ok(name, cond, detail) { total++; if (!cond) failed++; console.log((cond ? '  ok   ' : '  FAIL ') + name + (cond || !detail ? '' : '  (' + detail + ')')); },
};
const only = process.argv[2];
for (const f of fs.readdirSync(__dirname).filter((n) => n.endsWith('.test.js') && (!only || n.includes(only))).sort()) {
  file = f; console.log('## ' + f);
  require(path.join(__dirname, f))(t, api, { md, mkDoc });
}
console.log(failed ? '\n' + failed + ' de ' + total + ' FALLAN' : '\n' + total + ' pruebas, todo ok');
process.exit(failed ? 1 : 0);
